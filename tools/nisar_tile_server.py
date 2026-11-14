"""Phase-0 NISAR world map server: XYZ tiles from real NISAR GCOV browse previews.

Usage: python nisar_tile_server.py [--port 8765]
Reads data/index.json and data/thumb/*.png (see nisar_index.py, fetch_previews.py).

Zoom 0-5: a Web Mercator canvas painted once from every small preview (newest on top).
Zoom 6-7: composited per tile from small previews.
Zoom 8+:  composited from the big (~120 m) previews, streamed from NASA on first use and cached.
Each preview is a lat/lon image of one frame inside a black margin; its corners are the
frame's catalog polygon, so the non-black extent maps linearly to the polygon's lat/lon box.
"""
import argparse
import io
import json
import math
import re
import threading
from urllib.parse import parse_qs, urlparse
import time
import urllib.request
import gzip
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from PIL import Image
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sar_colors  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA, WEB = ROOT / "data", ROOT / "web"
THUMB, FULL = DATA / "thumb", DATA / "full"
CANVAS_Z = 5
CANVAS_N = 256 << CANVAS_Z
TILE = 256
FULL_Z = 7
EMPTY = None

INDEX = json.load(open(DATA / "index.json"))
FRAMES = sorted(INDEX["frames"], key=lambda f: f["start"])
for i, f in enumerate(FRAMES):
    f["order"] = i

# 1-degree grid -> frame indices, for fast "which frames touch this tile"
GRID = {}
for i, f in enumerate(FRAMES):
    w, s, e, n = f["bbox"]
    for gx in range(math.floor(w), math.floor(e) + 1):
        for gy in range(math.floor(s), math.floor(n) + 1):
            GRID.setdefault((gx, gy), []).append(i)


def tile_lonlat(z, x, y):
    n = TILE << z
    px = (x * TILE + np.arange(TILE) + 0.5) / n
    py = (y * TILE + np.arange(TILE) + 0.5) / n
    lon = px * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * py))))
    return np.meshgrid(lon, lat)


def tile_bounds(z, x, y):
    n = 1 << z
    w = x / n * 360 - 180
    e = (x + 1) / n * 360 - 180
    nlat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    slat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return w, slat, e, nlat


def frames_in(w, s, e, n):
    hits = set()
    for gx in range(math.floor(w), math.floor(e) + 1):
        for gy in range(math.floor(max(s, -90)), math.floor(min(n, 89.999)) + 1):
            hits.update(GRID.get((gx, gy), ()))
    out = [i for i in hits if FRAMES[i]["bbox"][0] < e and FRAMES[i]["bbox"][2] > w
           and FRAMES[i]["bbox"][1] < n and FRAMES[i]["bbox"][3] > s]
    return sorted(out)


def load_preview(path, frame):
    """Return (rgba array cropped to data, georef) or None."""
    try:
        im = np.asarray(Image.open(path).convert("RGB"))
    except Exception:
        return None
    mask = im.max(axis=2) > 6
    cols, rows = np.flatnonzero(mask.any(axis=0)), np.flatnonzero(mask.any(axis=1))
    if cols.size < 2 or rows.size < 2:
        return None
    x0, x1, y0, y1 = cols[0], cols[-1] + 1, rows[0], rows[-1] + 1
    # A complete frame fills ~85 % of its preview; a partial pass (a strip) fills far less and would be
    # stretched over the whole catalog box, landing in the wrong place, so it is rejected.
    if (x1 - x0) < 0.7 * im.shape[1] or (y1 - y0) < 0.7 * im.shape[0]:
        return None
    rgba = np.dstack([im[y0:y1, x0:x1], (mask[y0:y1, x0:x1] * 255).astype(np.uint8)])
    w, s, e, n = frame["bbox"]
    return rgba, (w, s, e, n)


def sample_into(out, lon, lat, prev):
    rgba, (w, s, e, n) = prev
    h, wd = rgba.shape[:2]
    inside = (lon >= w) & (lon < e) & (lat > s) & (lat <= n)
    if not inside.any():
        return
    cx = ((lon[inside] - w) / (e - w) * wd).astype(np.int32).clip(0, wd - 1)
    cy = ((n - lat[inside]) / (n - s) * h).astype(np.int32).clip(0, h - 1)
    px = rgba[cy, cx]
    keep = px[:, 3] > 0
    target = out[inside]
    target[keep] = px[keep]
    out[inside] = target


class LRU(OrderedDict):
    def __init__(self, size):
        super().__init__()
        self.size, self.lock = size, threading.Lock()

    def get_or(self, key, make):
        with self.lock:
            if key in self:
                self.move_to_end(key)
                return self[key]
        val = make()
        with self.lock:
            self[key] = val
            while len(self) > self.size:
                self.popitem(last=False)
        return val


THUMBS = LRU(1500)
POOL = ThreadPoolExecutor(16)
FULLS = LRU(24)  # each full preview is ~16 MB in RAM
FETCH_LOCKS = {}
FETCH_LOCKS_LOCK = threading.Lock()


def thumb_preview(i):
    f = FRAMES[i]
    return THUMBS.get_or(i, lambda: load_preview(THUMB / f"{f['id']}.png", f))


def full_preview(i):
    f = FRAMES[i]
    if not f.get("full"):
        return thumb_preview(i)
    path = FULL / f"{f['id']}.png"
    if not path.exists():
        with FETCH_LOCKS_LOCK:
            lock = FETCH_LOCKS.setdefault(i, threading.Lock())
        with lock:
            if not path.exists():
                FULL.mkdir(parents=True, exist_ok=True)
                try:
                    req = urllib.request.Request(f["full"], headers={"User-Agent": "falakus-nisar-preview"})
                    with urllib.request.urlopen(req, timeout=120) as r:
                        data = r.read()
                    tmp = path.with_suffix(".part")
                    tmp.write_bytes(data)
                    tmp.replace(path)
                except Exception:
                    return thumb_preview(i)
    return FULLS.get_or(i, lambda: load_preview(path, f))


# ---- zoom 0-5 canvas -------------------------------------------------------
CANVAS = {"img": None, "progress": 0}


def merc_xy(lon, lat):
    lat = np.clip(lat, -85.0511, 85.0511)
    x = (lon + 180) / 360 * CANVAS_N
    y = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * CANVAS_N
    return x, y


def build_canvas():
    have = sum(1 for _ in THUMB.glob("*.png"))
    cache = DATA / f"canvas_z{CANVAS_Z}_{have}.npy"  # a new download count means a rebuild
    if cache.exists():
        CANVAS["img"] = np.load(cache, mmap_mode="r")  # read from disk on demand: 268 MB stays off RAM
        CANVAS["progress"] = len(FRAMES)
        return
    canvas = np.zeros((CANVAS_N, CANVAS_N, 4), np.uint8)
    for k, f in enumerate(FRAMES):
        CANVAS["progress"] = k
        prev = load_preview(THUMB / f"{f['id']}.png", f)
        if prev is None:
            continue
        w, s, e, n = f["bbox"]
        x0, y0 = merc_xy(np.array(w), np.array(n))
        x1, y1 = merc_xy(np.array(e), np.array(s))
        xs = np.unique(np.arange(int(x0), int(np.ceil(x1)) + 1).clip(0, CANVAS_N - 1))
        ys = np.unique(np.arange(int(y0), int(np.ceil(y1)) + 1).clip(0, CANVAS_N - 1))
        lon = (xs + 0.5) / CANVAS_N * 360 - 180
        lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (ys + 0.5) / CANVAS_N))))
        LON, LAT = np.meshgrid(lon, lat)
        patch = canvas[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
        sample_into(patch, LON, LAT, prev)
    np.save(cache, canvas)
    CANVAS["img"] = canvas
    CANVAS["progress"] = len(FRAMES)


def canvas_tile(z, x, y):
    img = CANVAS["img"]
    if img is None:
        return None
    step = 1 << (CANVAS_Z - z)
    size = TILE * step
    block = img[y * size:(y + 1) * size, x * size:(x + 1) * size]
    if step > 1:
        b = block.reshape(TILE, step, TILE, step, 4).astype(np.float32)
        a = b[..., 3:4]
        wsum = a.sum(axis=(1, 3))
        rgb = (b[..., :3] * a).sum(axis=(1, 3)) / np.maximum(wsum, 1)
        alpha = (wsum[..., 0] / (step * step)).clip(0, 255)
        alpha = np.where(alpha > 0, np.maximum(alpha, 200), 0)
        block = np.dstack([rgb, alpha]).astype(np.uint8)
    return block


TILE_CACHE = DATA / "tilecache_hh"  # grayscale HH tiles (one colour, one meaning; RGB preview only on demand)


def render_tile(z, x, y):
    """Disk-cached: each tile is computed once, then served as a file."""
    path = TILE_CACHE / str(z) / str(x) / f"{y}.webp"
    if path.exists():
        body = path.read_bytes()
        return body or EMPTY
    body = _render_tile(z, x, y)
    if z > CANVAS_Z or CANVAS["img"] is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body or b"")
    return body


@lru_cache(maxsize=1024)
def _render_tile(z, x, y):
    if z <= CANVAS_Z:
        arr = canvas_tile(z, x, y)
    else:
        w, s, e, n = tile_bounds(z, x, y)
        ids = frames_in(w, s, e, n)
        arr = np.zeros((TILE, TILE, 4), np.uint8)
        if ids:
            lon, lat = tile_lonlat(z, x, y)
            get = full_preview if z >= FULL_Z else thumb_preview
            for prev in POOL.map(get, ids):  # map keeps order: oldest first, newest painted last
                if prev is not None:
                    sample_into(arr, lon, lat, prev)
    if arr is None or not arr[..., 3].any():
        return EMPTY
    arr[..., 1] = arr[..., 0]; arr[..., 2] = arr[..., 0]  # HH (red channel of NASA's preview) as gray
    buf = io.BytesIO()
    Image.fromarray(arr, "RGBA").save(buf, "WEBP", quality=82, method=2)
    return buf.getvalue()


# ---- time series of one place ------------------------------------------------
SERIES_CACHE = {}
SERIES_COLLECTIONS = ["NISAR_L2_GCOV_V1", "NISAR_L2_GCOV_PROVISIONAL_V1"]
ID_RE = re.compile(r"^NISAR_L2_PR_GCOV_[A-Z0-9_]+$")


def place_series(lon, lat):
    key = (round(lon, 2), round(lat, 2))
    if key in SERIES_CACHE:
        return SERIES_CACHE[key]
    seen, groups = set(), {}
    for sn in SERIES_COLLECTIONS:
        url = (f"https://cmr.earthdata.nasa.gov/search/granules.json?short_name={sn}&point={lon},{lat}"
               f"&temporal=2025-10-01T00:00:00Z,2026-11-14T23:59:59Z&page_size=1000&sort_key=start_date")
        with urllib.request.urlopen(url, timeout=60) as r:
            for g in json.load(r)["feed"]["entry"]:
                rec = None
                p = g["title"].split("_")
                acq = "_".join(p[4:13])
                if acq in seen:
                    continue
                poly = (g.get("polygons") or [[None]])[0][0]
                if not poly:
                    continue
                seen.add(acq)
                v = list(map(float, poly.split()))
                lats, lons = v[0::2], v[1::2]
                rec = {"id": g["title"], "c": sn, "date": g["time_start"][:10], "time": g["time_start"][11:16],
                       "bbox": [min(lons), min(lats), max(lons), max(lats)], "pol": p[9]}
                groups.setdefault(f"{p[5]}_{p[6]}_{p[7]}", []).append(rec)
    if not groups:
        SERIES_CACHE[key] = {"track": None, "frames": []}
        return SERIES_CACHE[key]
    best = max(groups.items(), key=lambda kv: (len({r["date"] for r in kv[1]}), kv[0]))
    frames, dates = [], set()
    for r in sorted(best[1], key=lambda r: r["date"]):
        if r["date"] not in dates:
            dates.add(r["date"]); frames.append(r)
    SERIES_CACHE[key] = {"track": best[0], "frames": frames,
                         "tracks": {k: len(v) for k, v in groups.items()}}
    return SERIES_CACHE[key]


def band_view(rgba, band):
    """NASA's dual-pol preview stores HH in red and HV in green. Show one channel, contrast-stretched."""
    ch = rgba[..., 0 if band == "hh" else 1].astype(np.float32)
    valid = rgba[..., 3] > 0
    lo, hi = 10.0, 235.0  # one fixed scale for every pass, so brightness can be compared across dates
    v = np.clip((ch - lo) / max(hi - lo, 1), 0, 1)
    out = np.zeros_like(rgba)
    out[..., :3] = sar_colors.apply(v, sar_colors.GRAY_LUT if band == "hh" else sar_colors.HV_LUT)
    out[..., 3] = rgba[..., 3]
    return out


@lru_cache(maxsize=8)
def frame_rgba(gid, collection):
    path = FULL / f"{gid}.png"
    if not path.exists():
        FULL.mkdir(parents=True, exist_ok=True)
        url = f"https://nisar.asf.earthdatacloud.nasa.gov/BROWSE/{collection}/{gid}/{gid}_LATLON.png"
        req = urllib.request.Request(url, headers={"User-Agent": "falakus-nisar-preview"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        tmp = path.with_suffix(".part"); tmp.write_bytes(data); tmp.replace(path)
    prev = load_preview(path, {"bbox": [0, 0, 1, 1]})
    return None if prev is None else prev[0]


@lru_cache(maxsize=96)
def frame_image(gid, collection, band="rgb"):
    rgba = frame_rgba(gid, collection)
    if rgba is None:
        return None
    if band in ("hh", "hv"):
        rgba = band_view(rgba, band)
    im = Image.fromarray(rgba, "RGBA")
    if max(im.size) > 2048:
        im.thumbnail((2048, 2048), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=82, method=2)
    return buf.getvalue()


def place_stats(lon, lat, km=15):
    """Per pass, in a box of +-km around the point: estimated open-water km2 (dark HH) and mean HV."""
    ser = place_series(lon, lat)
    out = []
    dlat = km / 111.0
    dlon = km / (111.0 * max(math.cos(math.radians(lat)), 0.2))
    box_km2 = (2 * km) ** 2
    for f in ser["frames"]:
        try:
            rgba = frame_rgba(f["id"], f["c"])
        except Exception:
            rgba = None
        if rgba is None:
            continue
        w, s_, e, n = f["bbox"]
        h, wd = rgba.shape[:2]
        x0 = int((lon - dlon - w) / (e - w) * wd); x1 = int((lon + dlon - w) / (e - w) * wd)
        y0 = int((n - (lat + dlat)) / (n - s_) * h); y1 = int((n - (lat - dlat)) / (n - s_) * h)
        x0, x1, y0, y1 = max(x0, 0), min(x1, wd), max(y0, 0), min(y1, h)
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        cut = rgba[y0:y1, x0:x1]
        valid = cut[..., 3] > 0
        if valid.mean() < 0.6:
            continue
        hh = cut[..., 0][valid].astype(np.float32)
        hv = cut[..., 1][valid].astype(np.float32)
        out.append({"date": f["date"], "water_km2": round(float((hh < 45).mean() * box_km2), 1),
                    "hh": round(float(hh.mean()), 1), "hv": round(float(hv.mean()), 1)})
    return {"box_km": 2 * km, "track": ser.get("track"), "points": out,
            "note": "estimated from NASA preview images (HH = red channel, HV = green channel), not calibrated dB"}


def _unused_frame_image(gid, collection):
    path = FULL / f"{gid}.png"
    if not path.exists():
        FULL.mkdir(parents=True, exist_ok=True)
        url = f"https://nisar.asf.earthdatacloud.nasa.gov/BROWSE/{collection}/{gid}/{gid}_LATLON.png"
        req = urllib.request.Request(url, headers={"User-Agent": "falakus-nisar-preview"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        tmp = path.with_suffix(".part"); tmp.write_bytes(data); tmp.replace(path)
    prev = load_preview(path, {"bbox": [0, 0, 1, 1]})
    if prev is None:
        return None
    im = Image.fromarray(prev[0], "RGBA")
    if max(im.size) > 2048:
        im.thumbnail((2048, 2048), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=82, method=2)
    return buf.getvalue()


@lru_cache(maxsize=32)
def diff_image(c1, g1, c2, g2):
    """Brightness change between two previews of the same track/frame: orange = brighter, violet = darker."""
    a = Image.open(io.BytesIO(frame_image(g1, c1))).convert("RGBA")
    b = Image.open(io.BytesIO(frame_image(g2, c2))).convert("RGBA").resize(a.size, Image.BILINEAR)
    A, B = np.asarray(a).astype(np.float32), np.asarray(b).astype(np.float32)
    la, lb = A[..., :3].mean(axis=2), B[..., :3].mean(axis=2)
    valid = (A[..., 3] > 0) & (B[..., 3] > 0)
    d = (lb - la)
    d = d - np.median(d[valid]) if valid.any() else d  # remove a whole-frame brightness shift
    mag = np.clip(np.abs(d) / 60.0, 0, 1)
    out = np.zeros(A.shape, np.uint8)
    out[..., 0] = np.where(d > 0, 232, 112)
    out[..., 1] = np.where(d > 0, 89, 72)
    out[..., 2] = np.where(d > 0, 12, 232)
    out[..., 3] = np.where(valid & (mag > 0.25), (mag * 255).astype(np.uint8), 0)
    buf = io.BytesIO()
    Image.fromarray(out, "RGBA").save(buf, "WEBP", quality=80, method=2)
    return buf.getvalue()


JOBS = {}
JOB_LANE = threading.Semaphore(2)  # at most 2 NASA reads at once; more just queue
SCI_TILES = DATA / "scitiles"  # cut by tools/science_pyramid.py from calibrated GCOV boxes


S1 = {"t": 0, "body": None}


def sentinel1_mosaic():
    """Sentinel-1 RTC (C-band) mosaic of the last ~4 weeks from Microsoft Planetary Computer: no account needed.
    The mosaic id is registered here (cached 6 h) so the page gets a plain tile URL."""
    if S1["body"] and time.time() - S1["t"] < 6 * 3600:
        return S1["body"]
    end = time.strftime("%Y-%m-%d"); start = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 25 * 86400))
    req = {"collections": ["sentinel-1-rtc"], "filter-lang": "cql2-json",
           "filter": {"op": "anyinteracts", "args": [{"property": "datetime"}, {"interval": [f"{start}T00:00:00Z", f"{end}T23:59:59Z"]}]},
           "sortby": [{"field": "datetime", "direction": "desc"}]}
    r = urllib.request.Request("https://planetarycomputer.microsoft.com/api/data/v1/mosaic/register",
                               data=json.dumps(req).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(r, timeout=60) as resp:
        mid = json.load(resp)["id"]
    tile = (f"https://planetarycomputer.microsoft.com/api/data/v1/mosaic/{mid}/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}@1x"
            "?collection=sentinel-1-rtc&assets=vv&rescale=0,0.4&colormap_name=gray&format=png")
    S1.update(t=time.time(), body={"tiles": [tile], "start": start, "end": end,
                                   "attribution": "Sentinel-1 RTC (Copernicus, ESA) via Microsoft Planetary Computer"})
    return S1["body"]


LASTLOOK = {}


def last_look(lon, lat):
    """Newest NISAR GCOV pass (NASA CMR) and newest Sentinel-1 pass (Planetary Computer) over a point; cached 1 h."""
    key = (round(lon, 2), round(lat, 2))
    hit = LASTLOOK.get(key)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    out = {}
    try:
        url = ("https://cmr.earthdata.nasa.gov/search/granules.json?short_name=NISAR_L2_GCOV_V1&short_name=NISAR_L2_GCOV_PROVISIONAL_V1"
               f"&point={lon},{lat}&sort_key=-start_date&page_size=1")
        with urllib.request.urlopen(url, timeout=40) as r:
            e = json.load(r)["feed"]["entry"]
        if e:
            out["nisar"] = e[0]["time_start"][:16] + "Z"
    except Exception as ex:
        out["nisar_error"] = str(ex)[:80]
    try:
        body = {"collections": ["sentinel-1-rtc"], "intersects": {"type": "Point", "coordinates": [lon, lat]}, "limit": 1,
                "sortby": [{"field": "datetime", "direction": "desc"}]}
        req = urllib.request.Request("https://planetarycomputer.microsoft.com/api/stac/v1/search", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=40) as r:
            f = json.load(r)["features"]
        if f:
            out["s1"] = f[0]["properties"]["datetime"][:16] + "Z"
    except Exception as ex:
        out["s1_error"] = str(ex)[:80]
    LASTLOOK[key] = (time.time(), out)
    return out


# ---- small JSON APIs ------------------------------------------------------
def frames_geojson():
    feats = []
    for f in FRAMES:
        ring = [[round(lo, 3), round(la, 3)] for lo, la in f["corners"] + [f["corners"][0]]]
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                      "properties": {"id": f["id"], "start": f["start"][:16].replace("T", " "),
                                     "track": f["track"], "dir": f["dir"], "frame": f["frame"],
                                     "pol": f["pol"], "mb": f["mb"], "c": "V" if f["collection"].endswith("_V1") and "PROVISIONAL" not in f["collection"] else "P"}})
    return json.dumps({"type": "FeatureCollection", "features": feats}).encode()


FRAMES_GEOJSON = frames_geojson()
EVENTS = {"t": 0, "body": b"{}"}


EONET_CACHE = DATA / "eonet_v2.json"


QUAKE_CACHE = DATA / "usgs_quakes.json"


def usgs_quakes():
    """USGS earthquakes M5+ since NISAR's first science passes (17 Jun 2026); cached on disk."""
    if not QUAKE_CACHE.exists():
        url = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-06-17"
               "&minmagnitude=5&orderby=time&limit=2000")
        with urllib.request.urlopen(url, timeout=90) as r:
            feats = json.load(r)["features"]
        out = [{"id": f["id"], "title": f["properties"]["title"], "category": "Earthquakes",
                "date": time.strftime("%Y-%m-%d", time.gmtime(f["properties"]["time"] / 1000)),
                "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1],
                "depth_km": f["geometry"]["coordinates"][2], "track": [], "closed": "",
                "mag": f["properties"]["mag"], "unit": "M", "tsunami": f["properties"].get("tsunami", 0),
                "sources": [f["properties"]["url"]]} for f in feats]
        QUAKE_CACHE.write_text(json.dumps(out))
    return json.loads(QUAKE_CACHE.read_text())


def eonet_events():
    if EVENTS["t"]:
        return EVENTS["body"]
    raw = EONET_CACHE.read_bytes() if EONET_CACHE.exists() else refresh_eonet()
    items = json.loads(raw)
    try:
        items += usgs_quakes()
    except Exception as ex:
        print("usgs quakes unavailable:", ex, flush=True)
    items.sort(key=lambda d: d["date"], reverse=True)
    EVENTS.update(t=time.time(), body=json.dumps(items).encode())
    return EVENTS["body"]


def refresh_eonet():
    url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=all&start=2026-09-01&end=2026-11-14&limit=3000"
    with urllib.request.urlopen(url, timeout=150) as r:
        events = json.load(r)["events"]
    out = []
    fires = []
    for ev in events:
        geo = ev["geometry"][-1]
        if geo["type"] == "Point":
            lon, lat = geo["coordinates"][:2]
        else:
            ring = geo["coordinates"][0]
            lon, lat = sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)
        track = [g["coordinates"][:2] for g in ev["geometry"] if g["type"] == "Point"]
        item = {"id": ev["id"], "title": ev["title"], "category": ev["categories"][0]["title"],
                "date": geo["date"][:10], "lon": lon, "lat": lat, "track": track[-60:] if len(track) > 1 else [],
                "closed": (ev.get("closed") or "")[:10], "mag": geo.get("magnitudeValue"),
                "unit": geo.get("magnitudeUnit"), "sources": [s["url"] for s in ev.get("sources", [])][:3]}
        (fires if item["category"] == "Wildfires" else out).append(item)
    fires.sort(key=lambda d: -(d["mag"] or 0))
    out += fires[:200]
    out.sort(key=lambda d: d["date"], reverse=True)
    body = json.dumps(out).encode()
    EONET_CACHE.write_bytes(body)
    EVENTS.update(t=0)  # the next eonet_events() call merges the fresh file with USGS quakes
    return body


TILE_RE = re.compile(r"^/tiles/(\d+)/(\d+)/(\d+)\.webp$")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(WEB), **k)

    def log_message(self, *a):
        pass

    def send_bytes(self, body, ctype, cache="public, max-age=86400", code=200):
        gz = ctype.endswith("json") and "gzip" in (self.headers.get("Accept-Encoding") or "") and len(body) > 2000
        if gz:
            body = gzip.compress(body, 5)
        self.send_response(code)
        if gz:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", cache)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        ms = re.match(r"^/scitiles/(raw|class|water|built|plants)/(\d+)/(\d+)/(\d+)\.webp$", path)
        if ms:
            kind, (z, x, y) = ms.group(1), map(int, ms.groups()[1:])
            f = SCI_TILES / kind / str(z) / str(x) / f"{y}.webp"
            return self.send_bytes(f.read_bytes(), "image/webp", cache="no-cache") if f.exists() else self.send_bytes(b"", "image/webp", code=204)
        m = TILE_RE.match(path)
        if m:
            z, x, y = map(int, m.groups())
            if z <= CANVAS_Z and CANVAS["img"] is None:
                return self.send_bytes(b"", "image/webp", cache="no-store", code=204)
            body = render_tile(z, x, y)
            if body is None:
                return self.send_bytes(b"", "image/webp", code=204)
            return self.send_bytes(body, "image/webp")
        if path == "/api/series.json":
            q = parse_qs(urlparse(self.path).query)
            try:
                body = json.dumps(place_series(float(q["lon"][0]), float(q["lat"][0]))).encode()
            except Exception as e:
                return self.send_bytes(json.dumps({"error": str(e)}).encode(), "application/json", code=502)
            return self.send_bytes(body, "application/json", cache="max-age=3600")
        m5 = re.match(r"^/science/([a-z_]+)/(frames\.json|img/[0-9-]+_(?:rgb|hh|hv|change)\.webp)$", path)
        if m5:
            f = DATA / "science" / m5.group(1) / m5.group(2)
            if not f.exists():
                return self.send_bytes(b"", "text/plain", cache="no-store", code=404)
            return self.send_bytes(f.read_bytes(), "application/json" if f.suffix == ".json" else "image/webp", cache="no-cache")
        m4 = re.match(r"^/api/science/([a-z_]+)\.json$", path)
        if m4:
            f = DATA / "science" / m4.group(1) / "stats.json"
            if not f.exists():
                return self.send_bytes(b"{}", "application/json", cache="no-store", code=404)
            return self.send_bytes(f.read_bytes(), "application/json", cache="no-store")
        if path == "/api/stats.json":
            q = parse_qs(urlparse(self.path).query)
            try:
                body = json.dumps(place_stats(float(q["lon"][0]), float(q["lat"][0]), float(q.get("km", ["15"])[0]))).encode()
            except Exception as e:
                return self.send_bytes(json.dumps({"error": str(e)}).encode(), "application/json", code=502)
            return self.send_bytes(body, "application/json", cache="max-age=3600")
        m2 = re.match(r"^/api/frame/(NISAR_L2_GCOV_(?:PROVISIONAL_|BETA_)?V1)/([A-Za-z0-9_]+)\.webp$", path)
        if m2 and ID_RE.match(m2.group(2)):
            try:
                band = parse_qs(urlparse(self.path).query).get("band", ["rgb"])[0]
                body = frame_image(m2.group(2), m2.group(1), band if band in ("hh", "hv") else "rgb")
            except Exception:
                body = None
            if not body:
                return self.send_bytes(b"", "image/webp", code=404)
            return self.send_bytes(body, "image/webp")
        m3 = re.match(r"^/api/diff/(NISAR_L2_GCOV_(?:PROVISIONAL_|BETA_)?V1)/([A-Za-z0-9_]+)/(NISAR_L2_GCOV_(?:PROVISIONAL_|BETA_)?V1)/([A-Za-z0-9_]+)\.webp$", path)
        if m3 and ID_RE.match(m3.group(2)) and ID_RE.match(m3.group(4)):
            try:
                body = diff_image(*m3.groups())
            except Exception:
                body = None
            if not body:
                return self.send_bytes(b"", "image/webp", code=404)
            return self.send_bytes(body, "image/webp")
        if path == "/api/frames.geojson":
            return self.send_bytes(FRAMES_GEOJSON, "application/geo+json")
        if path == "/api/events.json":
            try:
                return self.send_bytes(eonet_events(), "application/json", cache="max-age=600")
            except Exception as e:
                return self.send_bytes(json.dumps({"error": str(e)}).encode(), "application/json", code=502)
        if path == "/api/analyze":
            q = parse_qs(urlparse(self.path).query)
            try:
                w, s_, e, n = (float(q[k][0]) for k in ("w", "s", "e", "n"))
            except (KeyError, ValueError):
                return self.send_bytes(b'{"error":"need w,s,e,n"}', "application/json", cache="no-store", code=400)
            jid = f"{int(time.time() * 1000) % 10**9:09d}"
            job = {"id": jid, "state": "queued", "progress": 0, "bbox": [w, s_, e, n]}
            JOBS[jid] = job

            def work():
                with JOB_LANE:
                    try:
                        import analyze_area
                        analyze_area.run(job, w, s_, e, n)
                    except Exception as ex:
                        job.update(state="done", progress=1, error=f"analysis failed: {ex}"[:300])
            threading.Thread(target=work, daemon=True).start()
            return self.send_bytes(json.dumps({"id": jid}).encode(), "application/json", cache="no-store")
        mj = re.match(r"^/api/job/(\d+)\.json$", path)
        if mj:
            job = JOBS.get(mj.group(1))
            if not job:
                return self.send_bytes(b'{"error":"unknown job"}', "application/json", cache="no-store", code=404)
            return self.send_bytes(json.dumps(job).encode(), "application/json", cache="no-store")
        if path == "/api/lastlook.json":
            q = parse_qs(urlparse(self.path).query)
            try:
                lon, lat = float(q["lon"][0]), float(q["lat"][0])
            except (KeyError, ValueError):
                return self.send_bytes(b"{}", "application/json", code=400)
            return self.send_bytes(json.dumps(last_look(lon, lat)).encode(), "application/json", cache="no-store")
        if path == "/api/ships.json":
            idx = []
            for f in sorted((DATA / "ships").glob("*.json")):
                j = json.loads(f.read_text())
                if "passes" not in j or not j["passes"] or "ships" not in j["passes"][0] or "sea_km2" not in j["passes"][0]:
                    continue  # only sea ship counts (slick and airport results live in the same folder)
                idx.append({"name": j["name"], "bbox": j["bbox"], "source": j.get("source"), "method": j.get("method"),
                            "passes": [{k: p[k] for k in ("date", "time_utc", "light", "ships", "sea_km2") if k in p} for p in j["passes"]]})
            return self.send_bytes(json.dumps(idx).encode(), "application/json", cache="no-store")
        mship = re.match(r"^/api/ships/([a-z_]+)\.json$", path)
        if mship:
            f = DATA / "ships" / f"{mship.group(1)}.json"
            return self.send_bytes(f.read_bytes(), "application/json", cache="no-store") if f.exists() else self.send_bytes(b"{}", "application/json", code=404)
        if path == "/api/s1.json":
            return self.send_bytes(json.dumps(sentinel1_mosaic()).encode(), "application/json", cache="no-store")
        if path == "/api/science_boxes.json":
            f = SCI_TILES / "boxes.json"
            boxes = list(json.loads(f.read_text()).values()) if f.exists() else []
            return self.send_bytes(json.dumps([{**b, "bbox": [float(v) for v in b["bbox"]]} for b in boxes]).encode(), "application/json", cache="no-store")
        if path == "/api/status.json":
            body = json.dumps({"window": INDEX["window"], "frames": len(FRAMES),
                               "tb": round(sum(f["mb"] for f in FRAMES) / 1e6, 1),
                               "canvas_ready": CANVAS["img"] is not None,
                               "canvas_progress": CANVAS["progress"]}).encode()
            return self.send_bytes(body, "application/json", cache="no-store")
        if path in ("/", "/index.html") or path.endswith((".html", ".js", ".css")):
            self.no_cache = True
        return super().do_GET()

    def end_headers(self):
        if getattr(self, "no_cache", False):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    threading.Thread(target=build_canvas, daemon=True).start()
    threading.Thread(target=eonet_events, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"NISAR map on http://127.0.0.1:{a.port}  ({len(FRAMES)} frames, window {INDEX['window']})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
