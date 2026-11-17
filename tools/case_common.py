"""Shared helpers for the case builders (tools/case_*.py): HTTP with retries, NASA CMR pass search, NASA GIBS tile mosaics.

Nothing here invents a number: every helper returns what the API returned, plus the exact URL it asked.
GIBS NISAR tiles are DISPLAY-SCALED PNG (R = B = HH, G = HV, transparent no-data), not calibrated dB.
Everything computed from them is screening only.
"""
import io
import json
import math
import os
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "cases"
CACHE = Path(os.environ.get("FALAKUS_GIBS_CACHE", Path.home() / ".cache" / "falakus-gibs"))
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
NISAR_COLLECTIONS = ("C3622241360-ASF", "C2854338529-ASF")  # validated V1, provisional V1
GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{layer}/default/{date}/{tms}/{z}/{y}/{x}.png"
NISAR_LAYER = ("NISAR_L2_Geocoded_Polarimetric_Covariance", "GoogleMapsCompatible_Level13")
DIST_LAYER = ("OPERA_L3_DIST-ALERT-HLS_Color_Index", "GoogleMapsCompatible_Level12")
UA = {"User-Agent": "falakus-case-builder/1.0"}


def http_get(url, tries=3, timeout=60):
    """GET with 3 tries and backoff. Returns (status, headers, body); 404 is returned, not raised."""
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return e.code, dict(e.headers or {}), b""
            last = e
        except Exception as e:  # network flap
            last = e
        time.sleep(2 * (k + 1) ** 2)
    raise RuntimeError(f"GET failed after {tries} tries: {url}: {last}")


def cmr_url(bbox, temporal=None, collection=NISAR_COLLECTIONS[0], sort="start_date", page_size=2000):
    q = {"collection_concept_id": collection, "bounding_box": ",".join(f"{v:g}" for v in bbox),
         "sort_key": sort, "page_size": page_size}
    if temporal:
        q["temporal"] = f"{temporal[0]},{temporal[1]}"
    return CMR + "?" + urllib.parse.urlencode(q)


def cmr_hits(bbox=None, collection=NISAR_COLLECTIONS[0], temporal=None):
    q = {"collection_concept_id": collection, "page_size": 1, "sort_key": "start_date"}
    if bbox:
        q["bounding_box"] = ",".join(f"{v:g}" for v in bbox)
    if temporal:
        q["temporal"] = f"{temporal[0]},{temporal[1]}"
    url = CMR + "?" + urllib.parse.urlencode(q)
    st, h, b = http_get(url)
    hits = int({k.lower(): v for k, v in h.items()}.get("cmr-hits", -1))
    e = json.loads(b)["feed"]["entry"]
    return dict(url=url, hits=hits, first=(e[0]["title"], e[0]["time_start"]) if e else None)


def parse_id(title):
    """NISAR_L2_PR_GCOV_<cycle>_<track>_<A|D>_<frame>_..._<start>_<stop>_... -> dict."""
    p = title.split("_")
    return dict(cycle=p[4], track=p[5], dir=p[6], frame=p[7])


def nisar_passes(bbox, temporal):
    """Every NISAR GCOV granule (both collections) over bbox, paged with CMR-Search-After. Deduplicated by title."""
    out, urls = {}, []
    for col in NISAR_COLLECTIONS:
        url = cmr_url(bbox, temporal, col)
        urls.append(url)
        after = None
        while True:
            req = urllib.request.Request(url, headers=dict(UA, **({"CMR-Search-After": after} if after else {})))
            for k in range(3):
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        h = {a.lower(): b for a, b in r.headers.items()}
                        body = json.loads(r.read())
                    break
                except Exception:
                    if k == 2:
                        raise
                    time.sleep(2 * (k + 1) ** 2)
            ents = body["feed"]["entry"]
            for e in ents:
                t = e["title"]
                if not t.startswith("NISAR_L2") or "GCOV" not in t:
                    continue
                d = parse_id(t)
                d.update(id=t, start=e["time_start"], collection=col)
                out[t] = d
            after = h.get("cmr-search-after")
            if not ents or not after or len(ents) < 2000:
                break
    return sorted(out.values(), key=lambda d: d["start"]), urls


# ---------------- GIBS tiles ----------------
def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile_to_lonlat(x, y, z):
    n = 2 ** z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


def scrambled(rgba):
    """Port of the reference guard: real NISAR tiles have alpha 0/255 and green/magenta colour.
    Scrambled ones have random alpha (>25 % mid alpha) or grey static (grey, with big pixel-to-pixel jumps)."""
    a = np.asarray(Image.fromarray(rgba).resize((64, 64), Image.BILINEAR)).astype(int)
    al = a[..., 3]
    mid = ((al > 8) & (al < 247)).mean()
    op = al > 200
    if mid > 0.25:
        return True
    if op.sum() > 200:
        rgb = a[..., :3]
        grey = (rgb.max(-1) - rgb.min(-1)) < 14
        L = rgb.mean(-1)
        jump = np.zeros_like(op)
        jump[:, :-1] = (np.abs(L[:, :-1] - L[:, 1:]) > 55) & op[:, 1:]
        if (grey & op).sum() / op.sum() > 0.85 and (jump & op).sum() / op.sum() > 0.18:
            return True
    return False


def gibs_tile(layer, tms, date, z, x, y, guard=True):
    """Returns (RGBA uint8 256x256 or None, status) where status in ok/empty/missing/scrambled."""
    url = GIBS.format(layer=layer, date=date, tms=tms, z=z, y=y, x=x)
    f = CACHE / layer / date / str(z) / f"{y}_{x}.png"
    if f.exists():
        b = f.read_bytes()
    else:
        try:
            st, _, b = http_get(url)
        except RuntimeError:  # server error after 3 tries: treat the tile as missing, count it
            return None, "missing"
        if st != 200:
            return None, "missing"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b)
    if not b:
        return None, "missing"
    im = np.array(Image.open(io.BytesIO(b)).convert("RGBA"))
    if (im[..., 3] == 0).all():
        return None, "empty"
    if guard and scrambled(im):
        return None, "scrambled"
    return im, "ok"


def mosaic(layer, tms, date, bbox, z, guard=True):
    """Mosaic GIBS tiles over bbox [W,S,E,N] at zoom z, cropped to bbox. Returns (RGBA array, info)."""
    W, S, E, N = bbox
    x0, y0 = lonlat_to_tile(W, N, z)
    x1, y1 = lonlat_to_tile(E, S, z)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    big = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 4), np.uint8)
    stats = {"ok": 0, "empty": 0, "missing": 0, "scrambled": 0}
    jobs = [(tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]
    with ThreadPoolExecutor(8) as ex:  # network-bound: fetch tiles in parallel
        got = list(ex.map(lambda j: gibs_tile(layer, tms, date, z, j[0], j[1], guard), jobs))
    for (tx, ty), (im, st) in zip(jobs, got):
        stats[st] += 1
        if im is not None:
            big[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = im
    c0, r0 = int((x0 - tx0) * 256), int((y0 - ty0) * 256)
    c1, r1 = int((x1 - tx0) * 256), int((y1 - ty0) * 256)
    out = big[r0:r1, c0:c1]
    # pixel area in km2 at the box centre latitude (web-mercator pixel shrinks with cos(lat))
    lat = (S + N) / 2
    px_m = 40075016.686 * math.cos(math.radians(lat)) / (256 * 2 ** z)
    info = dict(date=date, layer=layer, z=z, tiles=stats, shape=list(out.shape[:2]), pixel_m=round(px_m, 1),
                pixel_km2=px_m ** 2 / 1e6,
                url_template=GIBS.format(layer=layer, date=date, tms=tms, z=z, y="{y}", x="{x}"))
    return out, info


def km_box(lon, lat, half_km):
    dlat = half_km / 110.574
    dlon = half_km / (111.320 * math.cos(math.radians(lat)))
    return [round(lon - dlon, 4), round(lat - dlat, 4), round(lon + dlon, 4), round(lat + dlat, 4)]


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
