"""Find slick candidates (oil or calm-water look-alikes) on the Caspian Sea off Baku from Sentinel-1 radar (C-band, VV).

Why it works: wind makes small ripples that scatter the radar pulse back (sea looks grey). A film of oil damps those
ripples, so an oil slick is a DARK patch, usually long and thin because wind and current stretch it. Low wind also
makes dark sea (a look-alike), and so do rain cells, current fronts and natural surfactant films, so a radar alone
cannot prove oil. We keep only dark features that are elongated, and call them "slick candidates":
  dark      = VV (dB) more than 6 dB below the sea background, where background = the brighter of a ~2 km and a
              ~16 km running median (the 16 km one stops a big slick from hiding inside its own median)
  candidate = 8-connected dark blob, length > 1 km, elongation > 3 (max of PCA length/width and length^2/area)
Land is what is brighter than the sea in most passes: regions over 15 km2 (Absheron, its spit and the big islands)
are masked with a 1 km band; smaller bright regions are structures (Neft Dashlari, platforms), masked with ~200 m.
Below the radar noise floor (very calm sea, VV < about -22 dB) slicks cannot show, so calm passes report few.

Bright points at sea are counted with the ship idea (much brighter than the local sea). A point that is bright in at
least half the passes that saw it is a fixed structure (platform, trestle, pier); the others are transient (ships).

Usage: python slick_find.py [--days 45] [--max 8] [--check out.png]
Writes data/ships/slicks_baku.json.
"""
import argparse
import io
import json
import math
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
PC = "https://planetarycomputer.microsoft.com/api"
BBOX = [50.0, 39.9, 51.2, 40.55]  # east of Baku: Absheron tip, its islands, Neft Dashlari, open sea to the south-east
W, H = 1600, 1130  # ~64 m pixels on a fixed grid so passes line up
KX = (BBOX[2] - BBOX[0]) * 111.32 * math.cos(math.radians((BBOX[1] + BBOX[3]) / 2)) / W  # km per pixel, east
KY = (BBOX[3] - BBOX[1]) * 110.57 / H  # km per pixel, south
NEFT_DASHLARI = (50.85, 40.23)
DARK_DB, MIN_LEN_KM, MIN_ELONG = 6.0, 1.0, 3.0


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


def lonlat(row, col):
    return round(BBOX[0] + (col + 0.5) / W * (BBOX[2] - BBOX[0]), 5), round(BBOX[3] - (row + 0.5) / H * (BBOX[3] - BBOX[1]), 5)


def upsample(a, f):
    return np.kron(a, np.ones((f, f), np.float32))[:H, :W]


def land_masks(stack):
    """Bright-in-most-passes regions: big ones are land, small ones are structures."""
    votes = np.zeros((H, W), np.int16); seen = np.zeros((H, W), np.int16)
    for v in stack:
        ok = np.isfinite(v)
        smooth = ndimage.uniform_filter(np.nan_to_num(v), 9) / np.maximum(ndimage.uniform_filter(ok.astype(np.float32), 9), 1e-6)
        votes += (smooth > 2 * np.nanmedian(v)) & ok; seen += ok
    bright = (votes >= np.maximum(seen / 2, 1)) & (seen > 0)
    lab, n = ndimage.label(bright)
    area = ndimage.sum(bright, lab, range(1, n + 1)) * KX * KY
    big = np.isin(lab, 1 + np.nonzero(area > 15)[0])
    return big, bright & ~big


def sea_background_db(d):
    r2 = upsample(ndimage.median_filter(d[::4, ::4], size=9), 4)     # ~2 km
    r16 = upsample(ndimage.median_filter(d[::16, ::16], size=17), 16)  # ~16 km
    return np.maximum(r2, r16)


def find_slicks(v, excl):
    ok = np.isfinite(v); sea = ok & ~excl
    if sea.sum() < 1000:
        return [], sea, None
    lin = np.where(sea, v, np.nanmedian(v[sea]))
    d = 10 * np.log10(lin); ref = sea_background_db(d)
    dark = (d < ref - DARK_DB) & ndimage.binary_erosion(sea, iterations=3)
    lab, _ = ndimage.label(ndimage.binary_closing(dark, iterations=1) & sea, structure=np.ones((3, 3)))
    found = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None:
            continue
        yy, xx = np.nonzero(lab[sl] == i)
        if len(yy) < 8:
            continue
        yy = yy + sl[0].start; xx = xx + sl[1].start
        ev, evec = np.linalg.eigh(np.cov(np.vstack([xx * KX, yy * KY])))
        length = math.sqrt(12 * max(ev[1], 0)); width = max(math.sqrt(12 * max(ev[0], 0)), KX)
        area = len(yy) * KX * KY
        elong = max(length / width, length * length / area)
        ex, ey = evec[:, 1]  # long axis, x east, y south
        keep = length > MIN_LEN_KM and elong > MIN_ELONG
        found.append({"keep": keep, "id": i, "lab": lab, "lon_lat": lonlat(yy.mean(), xx.mean()), "length_km": round(length, 2),
                      "width_km": round(width, 2), "area_km2": round(area, 2), "elongation": round(elong, 1),
                      "angle_deg": round(math.degrees(math.atan2(ex, -ey)) % 180),
                      "contrast_db": round(float(np.mean(ref[yy, xx] - d[yy, xx])), 1)})
    return found, sea, d


def bright_points(v, big):
    ok = np.isfinite(v); sea = ok & ~ndimage.binary_dilation(big, iterations=16)
    lin = np.where(sea, v, np.nanmedian(v[sea]) if sea.any() else 1.0)
    ref = upsample(ndimage.median_filter(lin[::4, ::4], size=9), 4)
    return sea & (lin > np.maximum(0.3, 20 * ref))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=45); ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--check", help="save a PNG of the pass with the most candidate area")
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
        if mosaic is not None and np.isfinite(mosaic).mean() > 0.1:
            keys.append(key); stack.append(mosaic)
    big, structures = land_masks(stack)
    excl = ndimage.binary_dilation(big, iterations=16) | ndimage.binary_dilation(structures, iterations=3)

    points = [bright_points(v, big) for v in stack]
    hits = sum(ndimage.binary_dilation(p, iterations=2).astype(np.int16) for p in points)
    seen = sum(np.isfinite(v).astype(np.int16) for v in stack)
    fixed_zone = ndimage.binary_dilation((hits >= np.maximum(seen / 2, 2)) & (seen >= 2), iterations=3)  # sites within ~400 m merge into one
    flab, nfixed = ndimage.label(fixed_zone)
    fixed = [lonlat(*c) for c in ndimage.center_of_mass(fixed_zone, flab, range(1, nfixed + 1))]
    near_nd = [p for p in fixed if math.hypot((p[0] - NEFT_DASHLARI[0]) * 85.0, (p[1] - NEFT_DASHLARI[1]) * 110.6) < 8]

    out, best = [], None
    for key, v, pts in zip(keys, stack, points):
        found, sea, d = find_slicks(v, excl)
        cands = [{k: f[k] for k in ("lon_lat", "length_km", "width_km", "area_km2", "elongation", "angle_deg", "contrast_db")} for f in found if f["keep"]]
        plab, npts = ndimage.label(ndimage.binary_dilation(pts, iterations=2))
        on_fixed = len(set(np.unique(plab[fixed_zone & (plab > 0)])) - {0})
        total = round(sum(c["area_km2"] for c in cands), 1)
        out.append({"date": key[:10], "time_utc": key[11:13] + ":00", "direction": direction[key],
                    "box_seen_pct": round(100 * float(np.isfinite(v).mean())), "sea_seen_km2": round(float(sea.sum() * KX * KY)),
                    "sea_median_db": round(float(10 * np.log10(np.nanmedian(v[sea]))), 1) if sea.any() else None,
                    "slick_candidates": len(cands), "slick_km2": total, "bright_points": npts,
                    "bright_on_fixed_sites": on_fixed, "bright_transient": npts - on_fixed,
                    "candidates": sorted(cands, key=lambda c: -c["area_km2"])})
        print(f"{key}  {direction[key]:10s} seen {np.isfinite(v).mean():4.0%}  slick candidates {len(cands):3d}  {total:6.1f} km2"
              f"  bright points {npts:3d} ({on_fixed} on fixed sites)", flush=True)
        if a.check and d is not None and (best is None or total > best[0]):
            best = (total, key, d, found)
    if a.check and best:
        save_check(a.check, best, excl, fixed_zone)
        print(f"check image: {best[1]} -> {a.check}")
    dst = ROOT / "data" / "ships"; dst.mkdir(parents=True, exist_ok=True)
    (dst / "slicks_baku.json").write_text(json.dumps({
        "name": "slicks_baku", "label": "slick candidates (oil or calm water look-alike)", "bbox": BBOX,
        "source": "Sentinel-1 RTC VV (Copernicus/ESA) via Microsoft Planetary Computer",
        "method": f"VV > {DARK_DB:g} dB below the brighter of a 2 km and 16 km sea median; 8-connected blobs with length > {MIN_LEN_KM:g} km "
                  f"and elongation > {MIN_ELONG:g}; land (bright in most passes, > 15 km2) masked with 1 km, structures with ~200 m",
        "caveats": ["radar alone cannot tell oil from low-wind water, rain cells or natural films", "slicks touching platforms are cut by the structure mask",
                    "big round dark patches are rejected as not elongated, even if they are oil", "passes cover different parts of the box (see box_seen_pct)"],
        "candidate_format": "lon_lat = centroid; angle_deg = long axis bearing from north (0-180)",
        "fixed_bright_structures": nfixed, "fixed_near_neft_dashlari_8km": len(near_nd), "fixed_points": fixed,
        "passes": sorted(out, key=lambda p: p["date"])}, indent=1))


def save_check(path, best, excl, fixed_zone):
    total, key, d, found = best
    g = np.clip((d + 28) / 26 * 255, 0, 255).astype(np.uint8)
    rgb = np.stack([g] * 3, -1)
    lab = found[0]["lab"] if found else np.zeros(d.shape, int)
    kept = np.isin(lab, [f["id"] for f in found if f["keep"]]); rejected = np.isin(lab, [f["id"] for f in found if not f["keep"]])
    rgb[excl] = (rgb[excl] * 0.5).astype(np.uint8)
    rgb[kept] = (255, 50, 50); rgb[rejected] = (60, 150, 255)
    rgb[ndimage.binary_dilation(excl) ^ excl] = (255, 210, 0)
    rgb[ndimage.binary_dilation(fixed_zone, iterations=2) ^ fixed_zone] = (0, 255, 200)
    Image.fromarray(rgb).crop((250, 80, 1600, 1080)).resize((1080, 800), Image.LANCZOS).save(path, optimize=True)


if __name__ == "__main__":
    main()
