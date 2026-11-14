"""Count plane-sized bright objects on the aprons of Tashkent International Airport from Sentinel-1 radar (C-band, VV).

Why it works: apron concrete is smooth, so it scatters the radar pulse away (dark, gamma0 ~0.04). A parked airliner
is a big metal body with wing-fuselage corners that send the pulse straight back (bright, gamma0 > 1). Terminal
buildings, hangars and light masts are also bright, but they are bright on EVERY pass, while a plane comes and goes.
So we count only bright blobs that are NOT bright in most passes:
  static  = pixels whose 3 x 3 neighbourhood is > 1.0 in at least half of the passes (grown by 1 px)
  object  = VV > 1.0 (0 dB) inside the apron outline, not static; blobs merged within 2 px, >= 3 px (~300 m2)
The apron outline was drawn by hand from a cloud-free Sentinel-2 image (30 Oct 2026): main + east apron, west apron,
south apron. Runways are excluded. This counts bright objects, not planes: a fuel truck cluster, a stair car or
a ground-power unit can also make a blob, a plane parked at the same gate on most passes is masked as "static",
and morning (descending) and evening (ascending) passes see corners from different sides, so compare like with like.

Usage: python apron_count.py [--days 45] [--max 8] [--check out.png]
Writes data/ships/apron_tashkent.json: per pass date, object count and positions.
"""
import argparse
import io
import json
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
PC = "https://planetarycomputer.microsoft.com/api"
BBOX = [69.25, 41.24, 69.31, 41.28]
W, H = 560, 440  # ~9.5 m pixels, close to the 10 m RTC grid; fixed so every pass lands on the same grid
APRONS = {  # lon, lat outlines from Sentinel-2 L2A 2026-10-30
    "main_west_east": [(69.27062, 41.26523), (69.27304, 41.26523), (69.27304, 41.26477), (69.2792, 41.26477), (69.27946, 41.26227),
                       (69.28562, 41.26205), (69.28562, 41.26068), (69.27679, 41.26068), (69.27304, 41.26009), (69.27062, 41.25841),
                       (69.26607, 41.25782), (69.26457, 41.25886), (69.265, 41.26091), (69.27009, 41.26114), (69.27036, 41.26318)],
    "south": [(69.26125, 41.25364), (69.26848, 41.25364), (69.26848, 41.25136), (69.26125, 41.25136)],
}
BRIGHT = 1.0


def search(bbox, days):
    end = time.strftime("%Y-%m-%d"); start = time.strftime("%Y-%m-%d", time.gmtime(time.time() - days * 86400))
    body = {"collections": ["sentinel-1-rtc"], "bbox": bbox, "datetime": f"{start}/{end}", "limit": 100,
            "sortby": [{"field": "datetime", "direction": "desc"}]}
    req = urllib.request.Request(f"{PC}/stac/v1/search", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)["features"]


def fetch(item, bbox, w, h):
    x0, y0, x1, y1 = bbox
    url = f"{PC}/data/v1/item/bbox/{x0},{y0},{x1},{y1}/{w}x{h}.npy?collection=sentinel-1-rtc&item={item}&assets=vv"
    with urllib.request.urlopen(url, timeout=180) as r:
        a = np.load(io.BytesIO(r.read()))
    v = a[0].astype(np.float32)
    return np.where((a[-1] > 0) & np.isfinite(v) & (v > 0), v, np.nan)


def to_px(lon, lat):
    return (lon - BBOX[0]) / (BBOX[2] - BBOX[0]) * W, (BBOX[3] - lat) / (BBOX[3] - BBOX[1]) * H


def to_lonlat(row, col):
    return round(BBOX[0] + (col + 0.5) / W * (BBOX[2] - BBOX[0]), 5), round(BBOX[3] - (row + 0.5) / H * (BBOX[3] - BBOX[1]), 5)


def apron_mask():
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for poly in APRONS.values():
        d.polygon([to_px(*p) for p in poly], fill=1)
    return np.array(m) > 0


def static_mask(stack):
    hits = ndimage.maximum_filter(np.nan_to_num(stack, nan=0.0), size=(1, 3, 3)) > BRIGHT
    return ndimage.binary_dilation(hits.mean(0) >= 0.5, iterations=1)


def detect(v, apron, static):
    cand = np.nan_to_num(v, nan=0.0) > BRIGHT
    cand &= apron & ~static
    lab, n = ndimage.label(ndimage.binary_dilation(cand, iterations=2))
    if n == 0:
        return []
    idx = range(1, n + 1)
    sizes = ndimage.sum(cand, lab, idx); cents = ndimage.center_of_mass(cand, lab, idx)
    peaks = ndimage.maximum(np.where(cand, v, 0), lab, idx)
    return [(c, int(s), float(p)) for c, s, p in zip(cents, sizes, peaks) if s >= 3]


def save_check(path, v, objs, apron, static):
    g = np.clip((10 * np.log10(np.nan_to_num(v, nan=1e-4)) + 22) / 25 * 255, 0, 255).astype(np.uint8)
    rgb = np.stack([g] * 3, -1)
    rgb[static & apron] = (rgb[static & apron] * 0.5 + np.array([0, 0, 120])).astype(np.uint8)  # static bright = blue tint
    im = Image.fromarray(rgb).resize((W * 2, H * 2), Image.NEAREST); d = ImageDraw.Draw(im)
    for poly in APRONS.values():
        d.polygon([(2 * x, 2 * y) for x, y in (to_px(*p) for p in poly)], outline=(255, 200, 0))
    for (r, c), _, _ in objs:
        d.ellipse([2 * c - 9, 2 * r - 9, 2 * c + 9, 2 * r + 9], outline=(255, 40, 40), width=2)
    im.crop((180, 260, 700, 660)).save(path, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=45); ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--check", help="save a PNG of the newest ascending pass with detections")
    a = ap.parse_args()
    by_pass = defaultdict(list); direction = {}
    for f in search(BBOX, a.days):
        key = f["properties"]["datetime"][:13]
        by_pass[key].append(f["id"]); direction[key] = f["properties"].get("sat:orbit_state", "?")
    keys, stack = [], []
    for key in sorted(by_pass, reverse=True)[: a.max]:
        mosaic = None
        for item in by_pass[key]:
            try:
                v = fetch(item, BBOX, W, H)
            except Exception as ex:
                print(f"{key} {item[-30:]} fetch failed: {ex}", flush=True)
                continue
            mosaic = v if mosaic is None else np.where(np.isfinite(mosaic), mosaic, v)
        if mosaic is not None and np.isfinite(mosaic).mean() > 0.9:
            keys.append(key); stack.append(mosaic)
    stack = np.stack(stack)
    apron = apron_mask() & np.isfinite(stack).all(0)
    static = static_mask(stack)
    px_m2 = ((BBOX[2] - BBOX[0]) * 111320 * np.cos(np.radians(41.26)) / W) * ((BBOX[3] - BBOX[1]) * 110570 / H)
    out, checked = [], False
    for key, v in zip(keys, stack):
        objs = detect(v, apron, static)
        out.append({"date": key[:10], "time_utc": key[11:13] + ":00", "direction": direction[key], "objects": len(objs),
                    "points": [[*to_lonlat(r, c), s, round(10 * np.log10(p), 1)] for (r, c), s, p in objs]})
        print(f"{key}  {direction[key]:10s}  plane-sized bright objects {len(objs):3d}", flush=True)
        if a.check and not checked and direction[key] == "ascending":
            save_check(a.check, v, objs, apron, static); checked = True
    dst = ROOT / "data" / "ships"; dst.mkdir(parents=True, exist_ok=True)
    (dst / "apron_tashkent.json").write_text(json.dumps({
        "name": "apron_tashkent", "label": "plane-sized bright objects on the aprons (not a plane count)", "bbox": BBOX,
        "source": "Sentinel-1 RTC VV (Copernicus/ESA) via Microsoft Planetary Computer; apron outline from Sentinel-2 L2A 2026-10-30",
        "method": f"VV > {BRIGHT} (0 dB) inside the apron outline, minus pixels bright in >= half the passes; blobs merged within 2 px, >= 3 px",
        "apron_km2": round(float(apron.sum() * px_m2 / 1e6), 2), "static_px_in_apron": int((static & apron).sum()),
        "caveats": ["counts bright metal objects, not planes", "a plane parked in the same spot on most passes is masked as static",
                    "morning (descending) and evening (ascending) passes differ in geometry and in traffic: compare same direction only"],
        "apron_outlines": APRONS, "points_format": "[lon, lat, size_px, peak_dB]",
        "passes": sorted(out, key=lambda d: d["date"])}, indent=1))


if __name__ == "__main__":
    main()
