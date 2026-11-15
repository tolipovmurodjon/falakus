"""NISAR (NASA GIBS) frame over a lon/lat box, resampled to plate carree to match tools/rs1_fetch.py output.

- Pass dates come from NASA CMR (both NISAR GCOV collections); GIBS tiles only have data on pass dates.
- Tiles at zoom z are fetched; scrambled tiles (random alpha / grey static, see case_common.scrambled)
  are re-requested with a `?r=n` cache-buster up to 5 times.
- The mosaic is warped from web-mercator to an equirectangular grid exactly matching the RS1 box/size.
- Output is greyscale of the R channel (R = B = HH display-scaled in GIBS), not calibrated dB.

Usage (as a module): best_nisar(bbox, width) -> (grey uint8 HxW, valid mask, info)
"""
import io
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from case_common import NISAR_COLLECTIONS, lonlat_to_tile, scrambled  # noqa: E402

GIBS = ("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/NISAR_L2_Geocoded_Polarimetric_Covariance/default/"
        "{date}/GoogleMapsCompatible_Level13/{z}/{y}/{x}.png")
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
UA = {"User-Agent": "falakus-history/1.0"}
CACHE = Path.home() / ".cache" / "falakus-gibs-history"


def get(url, timeout=60):
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return e.code, b""
        except Exception:
            pass
        time.sleep(1 + k)
    return 0, b""


def pass_dates(bbox):
    dates = {}
    for col in NISAR_COLLECTIONS:
        q = urllib.parse.urlencode({"collection_concept_id": col, "bounding_box": ",".join(map(str, bbox)),
                                    "sort_key": "-start_date", "page_size": 40})
        st, b = get(f"{CMR}?{q}")
        for e in json.loads(b)["feed"]["entry"]:
            dates.setdefault(e["time_start"][:10], []).append(e["title"])
    return dict(sorted(dates.items(), reverse=True))


def bad(im, nbytes):
    """Scramble check: case_common.scrambled (random alpha / grey static on a 64 px thumbnail) plus two
    full-resolution tests seen on 2026 tiles: (1) opaque grey static (real NISAR tiles are colour, R != B),
    (2) fully transparent tiles that still weigh tens of kB (a real empty tile compresses to < 2 kB)."""
    a = im.astype(int)
    op = a[..., 3] > 200
    if (a[..., 3] == 0).all():
        return nbytes > 5000
    if scrambled(im):
        return True
    if op.sum() > 2000:
        grey = ((a[..., :3].max(-1) - a[..., :3].min(-1)) < 6)[op].mean()
        # dark open water is also grey in the composite, but smooth; static jumps pixel to pixel
        L = a[..., :3].mean(-1)
        jump = np.abs(L[:, 1:] - L[:, :-1])[op[:, 1:]].mean()
        if grey > 0.9 and (jump > 25 or L[op].mean() > 40):  # bright or jumpy grey = static
            return True
        if (a[..., :3].max(-1) == 0)[op].mean() > 0.5:  # opaque pure black with sparse dots
            return True
    return False


def save(f, b):
    try:  # cache only; a full disk must not stop the run
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b)
    except OSError:
        pass


def tile(date, z, x, y):
    f = CACHE / date / str(z) / f"{y}_{x}.png"
    if f.exists():
        b = f.read_bytes()
        if not b:
            return None, "missing"
        im = np.array(Image.open(io.BytesIO(b)).convert("RGBA"))
        if not bad(im, len(b)):
            return im, "ok"
        f.unlink()
    url = GIBS.format(date=date, z=z, y=y, x=x)
    last = "missing"
    for n in range(int(__import__("os").environ.get("FALAKUS_GIBS_TRIES", "6"))):
        st, b = get(url if n == 0 else f"{url}?r={n}")
        if st != 200 or not b:
            save(f, b"")
            return None, "missing"
        im = np.array(Image.open(io.BytesIO(b)).convert("RGBA"))
        if not bad(im, len(b)):
            save(f, b)
            return im, "ok" if n == 0 else f"ok_after_{n}_retries"
        last = "scrambled"
    if (im[..., 3] == 0).all():
        return None, "empty_after_retries"
    return None, last


def mosaic_lonlat(date, bbox, z, width):
    W, S, E, N = bbox
    height = round(width * (N - S) / (E - W))
    x0, y0 = lonlat_to_tile(W, N, z)
    x1, y1 = lonlat_to_tile(E, S, z)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    big = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 4), np.uint8)
    stats = {}
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            im, st = tile(date, z, tx, ty)
            stats[st] = stats.get(st, 0) + 1
            if im is not None:
                big[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = im
    # equirectangular target grid -> fractional mercator pixel in `big`
    lons = W + (np.arange(width) + 0.5) / width * (E - W)
    lats = N - (np.arange(height) + 0.5) / height * (N - S)
    n = 2 ** z
    px = ((lons + 180) / 360 * n - tx0) * 256
    py = ((1 - np.arcsinh(np.tan(np.radians(lats))) / math.pi) / 2 * n - ty0) * 256
    from scipy.ndimage import map_coordinates
    PY, PX = np.meshgrid(py - 0.5, px - 0.5, indexing="ij")
    r = map_coordinates(big[..., 0].astype("float32"), [PY, PX], order=1, mode="nearest")
    a = map_coordinates(big[..., 3].astype("float32"), [PY, PX], order=0, mode="nearest")
    return r, a > 128, stats


def best_nisar(bbox, width, z=11, max_dates=8):
    """Try recent pass dates, keep the one with the highest valid coverage of the box."""
    dates = pass_dates(bbox)
    best = None
    for d in list(dates)[:max_dates]:
        r, valid, stats = mosaic_lonlat(d, bbox, z, width)
        cov = float(valid.mean())
        print(f"  NISAR {d}: coverage {cov*100:.0f}%  tiles {stats}")
        if best is None or cov > best[2] + 0.02:
            best = (d, (r, valid, stats), cov)
        if cov > 0.97:
            break
    d, (r, valid, stats), cov = best
    return r, valid, dict(date=d, granules=dates[d], tiles=stats, coverage_pct=round(cov * 100, 1), zoom=z)
