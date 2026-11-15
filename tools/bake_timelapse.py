"""Bake yearly cloud-free optical frames for the time-lapse player (web/timelapse.html).

For every place and every summer (Jun-Sep) from 1985 to 2026:
  1. Find Landsat Collection 2 L2 scenes (Landsat 4/5/7/8/9) over the box on Microsoft Planetary Computer (no login);
     small boxes use Sentinel-2 L2A from 2017 on (10 m instead of 30 m).
  2. Crop each scene to the box in Web Mercator (EPSG:3857, so the picture sits 1:1 on the map), lowest cloud first,
     and fill each pixel from the first scene where that pixel is clear (QA_PIXEL / SCL mask). Landsat 7 after
     2003 (scan-line stripes) is only used last, to fill holes: its stripes are no-data, so other scenes cover them.
  3. Natural colour: surface reflectance, one fixed stretch for all years so frames do not flash.
  4. Open water: MNDWI = (green - swir16) / (green + swir16) > 0 on clear pixels, area in km2 on the ground.
Writes data/timelapse/<place>/<year>.jpg and data/timelapse/<place>/index.json; prints one line per frame.
Resume: years already in index.json with a jpg on disk are skipped.
Usage: python tools/bake_timelapse.py aral andijan_res tashkent
"""
import io
import json
import math
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "timelapse"
PC = "https://planetarycomputer.microsoft.com/api"
YEARS = range(1985, 2027)
PLACES = {
    "aral": {"name": "Aral Sea", "bbox": [58.0, 43.6, 61.9, 46.9], "size": 1024, "s2_from": None},
    "andijan_res": {"name": "Andijan reservoir", "bbox": [73.028, 40.684, 73.242, 40.846], "size": 1024, "s2_from": 2017},
    "tashkent": {"name": "Tashkent", "bbox": [69.10, 41.20, 69.45, 41.40], "size": 1024, "s2_from": 2017},
}
LANES = 2         # Planetary Computer throttles more parallel reads


def fetch(req, timeout):
    for attempt in range(6):
        try:
            t0 = time.time(); buf = io.BytesIO()
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                while chunk := resp.read(1 << 20):
                    buf.write(chunk)
                    if time.time() - t0 > 2 * timeout:  # a trickling response must not hang the bake
                        raise TimeoutError("response too slow")
            return buf.getvalue()
        except Exception as ex:
            if getattr(ex, "code", None) in (400, 404) or isinstance(ex, TimeoutError) or "timed out" in str(ex):
                raise  # a slow scene is skipped, not retried: the next-clearest scene of that tile fills in
            if attempt == 5:
                raise
            print(f"   retry {attempt + 1}: {str(ex)[:80]}", flush=True)
            time.sleep(20)


_STAC_CACHE = {}


def stac(body):
    key = json.dumps(body, sort_keys=True)
    if key in _STAC_CACHE:
        return _STAC_CACHE[key]
    r = urllib.request.Request(f"{PC}/stac/v1/search", data=json.dumps(body).encode(),
                               headers={"Content-Type": "application/json"}, method="POST")
    _STAC_CACHE[key] = json.loads(fetch(r, 60))["features"]
    return _STAC_CACHE[key]


def grid_shape(bbox, size):
    xs = math.radians(bbox[2] - bbox[0]) * 6378137.0
    ys = abs(mercator_y(bbox[3]) - mercator_y(bbox[1]))
    return (size, max(1, round(size * xs / ys))) if ys >= xs else (max(1, round(size * ys / xs)), size)


def inv_mercator(y):
    return math.degrees(2 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2)


def crop(collection, item, assets, bbox, size, win=None):
    """Crop only the window (rows, cols) of our 3857 grid that the scene covers: a 1/3 of the bytes on a slow link."""
    H, W = grid_shape(bbox, size)
    rs, cs = win or (slice(0, H), slice(0, W))
    yt, yb = mercator_y(bbox[3]), mercator_y(bbox[1])
    w = bbox[0] + cs.start / W * (bbox[2] - bbox[0]); e = bbox[0] + cs.stop / W * (bbox[2] - bbox[0])
    n = inv_mercator(yt - rs.start / H * (yt - yb)); s = inv_mercator(yt - rs.stop / H * (yt - yb))
    q = "&".join(f"assets={a}" for a in assets)
    url = (f"{PC}/data/v1/item/bbox/{w:.6f},{s:.6f},{e:.6f},{n:.6f}/{cs.stop - cs.start}x{rs.stop - rs.start}.npy"
           f"?collection={collection}&item={item}&{q}&resampling=nearest&dst_crs=epsg:3857")
    return np.load(io.BytesIO(fetch(url, 40)))  # bands in asset order, then the valid mask (0/255)


def mercator_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 6378137.0


def pixel_km2(bbox, h, w):
    """Ground area of each row's pixel in the 3857 grid (true metres = mercator metres * cos(lat))."""
    x_span = math.radians(bbox[2] - bbox[0]) * 6378137.0
    y0, y1 = mercator_y(bbox[3]), mercator_y(bbox[1])
    ys = y0 + (np.arange(h) + 0.5) * (y1 - y0) / h
    lat = 2 * np.arctan(np.exp(ys / 6378137.0)) - math.pi / 2
    dx = x_span / w
    dy = abs(y1 - y0) / h
    return (dx * np.cos(lat)) * (dy * np.cos(lat)) / 1e6  # per row, km2


def candidates(place, year):
    cfg = PLACES[place]
    season = f"{year}-06-01T00:00:00Z/{year}-09-30T23:59:59Z"
    if cfg["s2_from"] and year >= cfg["s2_from"]:
        items = stac({"collections": ["sentinel-2-l2a"], "bbox": cfg["bbox"], "datetime": season, "limit": 200,
                      "query": {"eo:cloud_cover": {"lt": 40}}})
        items.sort(key=lambda it: it["properties"]["eo:cloud_cover"])
        return "sentinel-2-l2a", items
    items = stac({"collections": ["landsat-c2-l2"], "bbox": cfg["bbox"], "datetime": season, "limit": 300,
                  "query": {"eo:cloud_cover": {"lt": 60}}})
    items = [it for it in items if it["properties"].get("platform") in ("landsat-4", "landsat-5", "landsat-7", "landsat-8", "landsat-9")]
    slc_off = lambda it: it["properties"]["platform"] == "landsat-7" and it["properties"]["datetime"][:10] >= "2003-05-31"
    items.sort(key=lambda it: (slc_off(it), it["properties"]["eo:cloud_cover"]))
    return "landsat-c2-l2", items


def read_scene(collection, it, bbox, size):
    """Return reflectance (red, green, blue, swir16) as float32, clear mask, valid mask."""
    win = rect(it, bbox, *grid_shape(bbox, size))
    if win[0].stop - win[0].start < 2 or win[1].stop - win[1].start < 2:
        return None
    if collection == "sentinel-2-l2a":
        a = crop(collection, it["id"], ["B04", "B03", "B02", "B11", "SCL"], bbox, size, win)
        off = 1000 if str(it["properties"].get("s2:processing_baseline", "0")) >= "04.00" else 0
        refl = (a[:4].astype(np.float32) - off) / 10000.0
        valid = (a[-1] > 0) & (a[4] > 0)
        clear = valid & ~np.isin(a[4], [0, 1, 3, 8, 9, 10])
    else:
        a = crop(collection, it["id"], ["red", "green", "blue", "swir16", "qa_pixel"], bbox, size, win)
        refl = a[:4].astype(np.float32) * 2.75e-5 - 0.2
        qa = a[4].astype(np.uint16)
        valid = (a[-1] > 0) & ((qa & 1) == 0) & (a[0] > 0)
        clear = valid & ((qa & (0b11010)) == 0)  # bits 1 dilated cloud, 3 cloud, 4 cloud shadow
    return refl, clear, valid, win


def tile_key(it):
    p = it["properties"]
    return p.get("s2:mgrs_tile") or (p.get("landsat:wrs_path"), p.get("landsat:wrs_row"))


def rect(it, bbox, h, w):
    """Pixel rows/cols of the scene's lon/lat bounding box inside our 3857 grid."""
    b = it.get("bbox") or bbox
    x0 = int(np.clip((b[0] - bbox[0]) / (bbox[2] - bbox[0]) * w, 0, w)); x1 = int(np.clip(math.ceil((b[2] - bbox[0]) / (bbox[2] - bbox[0]) * w), 0, w))
    yt, yb = mercator_y(bbox[3]), mercator_y(bbox[1])
    r0 = int(np.clip((yt - mercator_y(min(b[3], 85))) / (yt - yb) * h, 0, h)); r1 = int(np.clip(math.ceil((yt - mercator_y(max(b[1], -85))) / (yt - yb) * h), 0, h))
    return slice(r0, r1), slice(x0, x1)


class Mosaic:
    def __init__(self, shape):
        self.comp = None; self.used = []; self.shape = shape

    def add(self, it, res, year_tag):
        refl_w, clear_w, valid_w, (rs, cs) = res
        H, W = self.shape
        refl = np.zeros((4, H, W), np.float32); clear = np.zeros((H, W), bool); valid = np.zeros((H, W), bool)
        hh, ww = clear_w.shape
        refl[:, rs.start:rs.start + hh, cs.start:cs.start + ww] = refl_w; clear[rs.start:rs.start + hh, cs.start:cs.start + ww] = clear_w
        valid[rs.start:rs.start + hh, cs.start:cs.start + ww] = valid_w
        if self.comp is None:
            self.comp = np.zeros_like(refl); self.filled = np.zeros(clear.shape, bool)
            self.backup = np.zeros_like(refl); self.any_fill = np.zeros(clear.shape, bool); self.from_main = np.zeros(clear.shape, bool)
        take = clear & ~self.filled
        if take.any():
            self.comp[:, take] = refl[:, take]; self.filled |= take
            if year_tag:
                self.from_main |= take
            p = it["properties"]
            self.used.append({"id": it["id"], "date": p["datetime"][:10], "platform": p.get("platform", ""),
                              "cloud": round(float(p.get("eo:cloud_cover", 0)), 1), "share": round(float(take.mean() * 100), 1)})
        btake = valid & ~self.any_fill
        self.backup[:, btake] = refl[:, btake]; self.any_fill |= btake

    def needs(self, it, bbox):
        if self.comp is None:
            return True
        h, w = self.filled.shape
        rs, cs = rect(it, bbox, h, w)
        sub = self.filled[rs, cs]
        return sub.size > 0 and (~sub).mean() > 0.002


def fill_rounds(mosaic, collection, items, bbox, size, main, rounds=4):
    """Round r reads the r-th clearest scene of every tile whose footprint still has holes."""
    tiles = {}
    for it in items:
        tiles.setdefault(tile_key(it), []).append(it)
    with ThreadPoolExecutor(LANES) as pool:
        for r in range(rounds):
            todo = [lst[r] for lst in tiles.values() if len(lst) > r and mosaic.needs(lst[r], bbox)]
            todo.sort(key=lambda it: it["properties"].get("eo:cloud_cover", 0))
            if not todo:
                break
            for i in range(0, len(todo), LANES):
                batch = [it for it in todo[i:i + LANES] if mosaic.needs(it, bbox)]
                for it, res in zip(batch, pool.map(lambda it: _safe_read(collection, it, bbox, size), batch)):
                    if res is not None:
                        mosaic.add(it, res, main)
            if mosaic.comp is not None and mosaic.filled.mean() > 0.998:
                break


def bake_year(place, year, index):
    cfg = PLACES[place]
    bbox, size = cfg["bbox"], cfg["size"]
    collection, items = candidates(place, year)
    if not items:
        print(f"{place} {year}: no scenes", flush=True)
        return None
    m = Mosaic(grid_shape(bbox, size))
    fill_rounds(m, collection, items, bbox, size, True)
    if m.comp is None or not m.used:
        print(f"{place} {year}: no clear pixels", flush=True)
        return None
    if m.filled.mean() < 0.4:  # mostly missing: leave the year out rather than show a patchwork
        print(f"{place} {year}: only {m.filled.mean() * 100:.0f} % clear, skipped", flush=True)
        return None
    gap_years = []
    for y2 in (year - 1, year + 1):  # holes (no scene that summer) are filled from the next-door summers, and labelled
        if m.filled.mean() > 0.998 or y2 not in YEARS:
            continue
        c2, it2 = candidates(place, y2)
        if c2 == collection and it2:
            before = m.filled.mean()
            fill_rounds(m, c2, it2, bbox, size, False, rounds=2)
            if m.filled.mean() > before + 1e-4:
                gap_years.append(y2)
    comp, filled, used = m.comp, m.filled, m.used
    any_fill, backup = m.any_fill, m.backup
    clear_pct = float(filled.mean() * 100)
    hole = ~filled & any_fill
    comp[:, hole] = backup[:, hole]  # cloudy-but-valid pixels where no clear view exists
    r, g, b, sw = comp
    rgb = np.stack([r, g, b], -1)
    rgb = np.clip(rgb / 0.32, 0, 1) ** (1 / 1.5)  # one fixed stretch for every year
    img = Image.fromarray((rgb * 255).astype(np.uint8))
    d = OUT / place; d.mkdir(parents=True, exist_ok=True)
    img.save(d / f"{year}.jpg", quality=75, optimize=True)
    with np.errstate(all="ignore"):
        mndwi = (g - sw) / (g + sw)
    water = filled & (mndwi > 0)
    km2 = pixel_km2(bbox, *water.shape)
    water_km2 = float((water * km2[:, None]).sum())
    sats = sorted({u["platform"] or "sentinel-2" for u in used})
    frame = {"year": year, "file": f"{year}.jpg",
             "source": "Sentinel-2 L2A" if collection == "sentinel-2-l2a" else "Landsat C2 L2 (" + ", ".join(s.replace("landsat-", "L") for s in sats) + ")",
             "collection": collection,
             "dates": [min(u["date"] for u in used), max(u["date"] for u in used)],
             "scenes": used, "scene_count": len(used),
             "cloud_pct": round(100 - clear_pct, 1),
             "from_other_years_pct": round(float((filled & ~m.from_main).mean() * 100), 1), "other_years": gap_years,
             "scene_cloud_pct": round(sum(u["cloud"] * u["share"] for u in used) / max(sum(u["share"] for u in used), 1e-6), 1),
             "water_km2": round(water_km2, 1),
             "size": [img.width, img.height]}
    print(f"{place} {year}: {frame['source']}, {len(used)} scenes {frame['dates'][0]}..{frame['dates'][1]}, "
          f"clear {clear_pct:.1f} % ({frame['from_other_years_pct']} % from {gap_years or '-'}), water {water_km2:,.0f} km2, {(d / frame['file']).stat().st_size // 1024} KB", flush=True)
    return frame


def _safe_read(collection, it, bbox, size):
    try:
        return read_scene(collection, it, bbox, size)
    except Exception as ex:
        print(f"   skip {it['id']}: {str(ex)[:90]}", flush=True)
        return None


def save_frame(place, year, frame):
    cfg = PLACES[place]
    d = OUT / place; d.mkdir(parents=True, exist_ok=True)
    path = d / "index.json"
    index = json.loads(path.read_text()) if path.exists() else {}
    index.update({"place": place, "name": cfg["name"], "bbox": cfg["bbox"], "crs": "EPSG:3857 image over the lon/lat bbox",
                  "method": __doc__.split("Writes")[0].strip()})
    frames = {f["year"]: f for f in index.get("frames", [])}
    if frame:
        frames[year] = frame
    index["frames"] = [frames[y] for y in sorted(frames)]
    path.write_text(json.dumps(index, indent=1))
    return frames


def bake(place):
    """Each year runs in its own process with a hard time limit: a dropped connection can hang a socket for an hour."""
    import subprocess
    frames = save_frame(place, None, None)
    for year in YEARS:
        if year in frames and (OUT / place / frames[year]["file"]).exists():
            continue
        for attempt in range(1):
            try:
                subprocess.run([sys.executable, "-u", __file__, "--one", place, str(year)], timeout=360, check=False)
                break
            except subprocess.TimeoutExpired:
                print(f"{place} {year}: timed out (attempt {attempt + 1})", flush=True)
    print(f"{place}: {len(save_frame(place, None, None))} frames", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--one"]:
        place, year = sys.argv[2], int(sys.argv[3])
        try:
            save_frame(place, year, bake_year(place, year, None))
        except Exception as ex:
            print(f"{place} {year}: failed {str(ex)[:120]}", flush=True)
    else:
        for p in sys.argv[1:] or list(PLACES):
            bake(p)
