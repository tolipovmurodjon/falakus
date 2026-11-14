"""Count large ships at sea from Sentinel-1 radar (C-band, VV), pass by pass, with no login.

Why it works: calm sea scatters the radar pulse away (dark, gamma0 ~0.005), while a steel hull and deck
make corner reflectors that send it straight back (bright, gamma0 > 0.3). A ship is a small bright blob
surrounded by dark water. This is the CFAR idea used by maritime agencies, kept simple and checkable:
  candidate = VV > 0.25 (linear) AND the 41 x 41 px neighbourhood median is sea-dark (< 0.03)
  blobs are merged within 3 px (one ship + its radar cross sidelobes = one detection), size >= 3 px.
Land and a ~250 m shore band are excluded (piers and coast edges gave false hits), so ships moored at a quay are not counted.

Usage: python ship_count.py <name> <w> <s> <e> <n> [--days 45] [--max 10]
Writes data/ships/<name>.json: per pass date, ship count, sea area seen, and ship positions.
"""
import argparse
import io
import json
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
PC = "https://planetarycomputer.microsoft.com/api"


def search(bbox, days):
    end = time.strftime("%Y-%m-%d"); start = time.strftime("%Y-%m-%d", time.gmtime(time.time() - days * 86400))
    body = {"collections": ["sentinel-1-rtc"], "bbox": bbox, "datetime": f"{start}/{end}", "limit": 100,
            "sortby": [{"field": "datetime", "direction": "desc"}]}
    req = urllib.request.Request(f"{PC}/stac/v1/search", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)["features"]


def fetch(item, bbox, size=2048):
    w, s, e, n = bbox
    url = f"{PC}/data/v1/item/bbox/{w},{s},{e},{n}.npy?collection=sentinel-1-rtc&item={item}&assets=vv&max_size={size}"
    with urllib.request.urlopen(url, timeout=180) as r:
        a = np.load(io.BytesIO(r.read()))
    v = a[0].astype(np.float32)
    ok = (a[-1] > 0) & np.isfinite(v) & (v > 0) if a.shape[0] > 1 else np.isfinite(v) & (v > 0)
    return np.where(ok, v, np.nan)


def detect(v):
    ok = np.isfinite(v)
    vv = np.nan_to_num(v, nan=1.0)  # no-data counts as "not sea" for the neighbourhood test
    med = ndimage.median_filter(vv[::4, ::4], size=11)  # ~41 px neighbourhood, computed at 1/4 scale for speed
    land = ndimage.binary_dilation(med > 0.05, iterations=3)  # land and its ~250 m shore band (piers, breakwaters, coast edges)
    up = lambda m: np.kron(m, np.ones((4, 4), bool))[: v.shape[0], : v.shape[1]]
    sea_dark = up((med < 0.03) & ~land)
    cand = ok & (vv > 0.25) & sea_dark
    lab, n = ndimage.label(ndimage.binary_dilation(cand, iterations=3))
    if n == 0:
        return [], ok & sea_dark
    sizes = ndimage.sum(cand, lab, range(1, n + 1))
    cents = ndimage.center_of_mass(cand, lab, range(1, n + 1))
    return [c for c, sz in zip(cents, sizes) if sz >= 3], ok & sea_dark


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name"); ap.add_argument("bbox", nargs=4, type=float)
    ap.add_argument("--days", type=int, default=45); ap.add_argument("--max", type=int, default=10)
    a = ap.parse_args()
    w, s, e, n = a.bbox
    by_pass = defaultdict(list)
    for f in search(a.bbox, a.days):
        by_pass[f["properties"]["datetime"][:13]].append(f["id"])  # frames of one pass share the hour
    out = []
    for key in sorted(by_pass, reverse=True)[: a.max]:
        mosaic = None
        for item in by_pass[key]:
            try:
                v = fetch(item, a.bbox)
            except Exception as ex:
                print(f"{key} {item[-30:]} fetch failed: {ex}", flush=True)
                continue
            if mosaic is not None and v.shape != mosaic.shape:  # frames of one pass can differ by a few pixels: resample onto the first grid
                v = ndimage.zoom(v, (mosaic.shape[0] / v.shape[0], mosaic.shape[1] / v.shape[1]), order=0)[: mosaic.shape[0], : mosaic.shape[1]]
            mosaic = v if mosaic is None else np.where(np.isfinite(mosaic), mosaic, v)
        if mosaic is None:
            continue
        seen = float(np.isfinite(mosaic).mean())
        if seen < 0.25:
            print(f"{key}  only {seen:.0%} of the box seen, skipped", flush=True)
            continue
        ships, sea = detect(mosaic)
        H, W = mosaic.shape
        pts = [[round(w + (c[1] + 0.5) / W * (e - w), 5), round(n - (c[0] + 0.5) / H * (n - s), 5)] for c in ships]
        px_km2 = ((e - w) * 111.32 * np.cos(np.radians((s + n) / 2)) / W) * ((n - s) * 110.57 / H)
        local_h = (int(key[11:13]) + (w + e) / 2 / 15) % 24  # local solar time of the pass
        out.append({"date": key[:10], "time_utc": key[11:13] + ":00", "local_solar_h": round(local_h, 1),
                    "light": "night" if (local_h < 6 or local_h >= 18) else "day", "ships": len(pts), "box_seen_pct": round(100 * seen),
                    "sea_km2": round(float(sea.sum() * px_km2)), "points": pts, "frames": by_pass[key]})
        print(f"{key}  ships {len(pts):4d}  {out[-1]['light']:5s}  box seen {seen:.0%}", flush=True)
    dst = ROOT / "data" / "ships"; dst.mkdir(parents=True, exist_ok=True)
    (dst / f"{a.name}.json").write_text(json.dumps({"name": a.name, "bbox": a.bbox, "source": "Sentinel-1 RTC VV (Copernicus/ESA) via Microsoft Planetary Computer",
                                                   "method": "VV > 0.25 with sea-dark 41 px neighbourhood (median < 0.03), blobs merged within 3 px, >= 3 px",
                                                   "passes": sorted(out, key=lambda d: d["date"])}, indent=1))


if __name__ == "__main__":
    main()
