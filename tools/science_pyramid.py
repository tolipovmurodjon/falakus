"""Cut calibrated science boxes into Web Mercator tiles (z10-z14) so the map zooms to native 10-20 m like Google Maps.

Usage: python science_pyramid.py <stop_id> [<stop_id> ...]   (default: every stop in data/science)
Uses the newest pass of each stop (data/science/<stop>/<date>.npz) and writes data/scitiles/<z>/<x>/<y>.webp.
Tiles are static files: they load instantly and work on any static host, no NASA login at view time.
Colours: sar_colors.composite (fixed dB scales shared by every place and date).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utm_convert import lonlat_to_utm  # noqa: E402
import sar_colors  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCI = ROOT / "data" / "science"
OUT = ROOT / "data" / "scitiles"
ZOOMS = range(10, 15)


def scale(a, lo, hi):
    return np.clip((np.nan_to_num(a, nan=lo) - lo) / (hi - lo), 0, 1)


def tile_lonlat(z, x, y, n=256):
    s = 2 ** z
    px = (x + (np.arange(n) + 0.5) / n) / s * 360 - 180
    py = y + (np.arange(n) + 0.5) / n
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * py / s))))
    return np.meshgrid(px, lat)


def lonlat_tile(lon, lat, z):
    s = 2 ** z
    x = int((lon + 180) / 360 * s)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * s)
    return x, y


def build(stop, zooms=ZOOMS, themes_on=True):
    files = sorted((SCI / stop).glob("*.npz"))
    files = [f for f in files if "x0" in np.load(f).files]
    if not files:
        print(f"{stop}: no pass with position metadata yet"); return 0
    z_ = np.load(files[-1])
    hh, hv = z_["hh_db"], z_["hv_db"]
    m = {k: float(z_[k]) for k in ("x0", "y0", "dx", "dy", "zone", "south")}
    raw = sar_colors.composite(hh, hv)
    cls = sar_colors.classify(hh, hv)
    shares, has = sar_colors.class_shares(cls)
    major = np.where(has, shares.argmax(0), -1)
    lut = np.vstack([sar_colors.CLASS_RGB, [[0, 0, 0]]]).astype(np.uint8)  # index -1 -> last row
    classed = lut[major]
    # one-theme heatmaps: colour strength = share of that class in the 140 m window (no colour mixing)
    themes = {}
    for name, rgb in (sar_colors.THEME_RGB.items() if themes_on else []):
        f = shares[sar_colors.CLASS_NAMES.index(name)]
        themes[name] = (np.dstack([np.full(f.shape, c, np.uint8) for c in rgb]), (np.clip(f, 0, 1) ** 0.8 * 235).astype(np.uint8))
    del shares
    ok = np.isfinite(hh)
    ny, nx = hh.shape
    # soft edges: alpha fades over the outer ~6 % of the box, so a science area blends into the map instead of a hard square
    ry = np.minimum(np.arange(ny), np.arange(ny)[::-1]) / (0.06 * ny); rx = np.minimum(np.arange(nx), np.arange(nx)[::-1]) / (0.06 * nx)
    feather = np.clip(np.minimum.outer(ry, rx), 0, 1)
    # lon/lat corners of the box, to know which tiles to cut
    from utm_convert import utm_to_lonlat  # noqa: E402
    lons, lats = utm_to_lonlat(np.array([m["x0"], m["x0"] + nx * m["dx"]]), np.array([m["y0"] - ny * m["dy"], m["y0"]]), int(m["zone"]), bool(m["south"]))
    w, e, s_, n_ = lons.min(), lons.max(), lats.min(), lats.max()
    count = 0
    for z in zooms:
        x0, y0 = lonlat_tile(w, n_, z); x1, y1 = lonlat_tile(e, s_, z)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                lon, lat = tile_lonlat(z, x, y)
                ux, uy = lonlat_to_utm(lon, lat, int(m["zone"]), bool(m["south"]))
                ix = np.floor((ux - m["x0"]) / m["dx"]).astype(int); iy = np.floor((m["y0"] - uy) / m["dy"]).astype(int)
                inside = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
                if not inside.any():
                    continue
                ixc, iyc = np.clip(ix, 0, nx - 1), np.clip(iy, 0, ny - 1)
                a = ((inside & ok[iyc, ixc]) * feather[iyc, ixc] * 255).astype(np.uint8)
                if not a.any():
                    continue
                for name, img in (("raw", raw), ("class", classed)):
                    p = OUT / name / str(z) / str(x) / f"{y}.webp"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    al = a if name == "raw" else np.where(major[iyc, ixc] == 3, 0, a).astype(np.uint8)  # bare: photo shows through
                    Image.fromarray(np.dstack([img[iyc, ixc], al]), "RGBA").save(p, "WEBP", quality=82 if name == "raw" else 90, method=3)
                for name, (img, alpha) in themes.items():
                    p = OUT / name / str(z) / str(x) / f"{y}.webp"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    al = np.where(a > 0, alpha[iyc, ixc], 0).astype(np.uint8)
                    Image.fromarray(np.dstack([img[iyc, ixc], al]), "RGBA").save(p, "WEBP", quality=85, method=3)
                count += 1
    idx_path = OUT / "boxes.json"
    idx = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    idx[stop] = {"stop": stop, "bbox": [w, s_, e, n_], "res": round(m["dx"]), "date": files[-1].stem}
    idx_path.write_text(json.dumps(idx, indent=1))
    print(f"{stop}: {count} tiles (z10-14) from {files[-1].stem}, native {m['dx']:.0f} m")
    return count


if __name__ == "__main__":
    stops = sys.argv[1:] or sorted(p.name for p in SCI.iterdir() if p.is_dir())
    for s in stops:
        build(s)
