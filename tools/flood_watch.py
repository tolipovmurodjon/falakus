"""Flood watch: NASA EONET flood events mapped with calibrated NISAR GCOV, before vs after, worldwide.

For each EONET flood (data/eonet_v2.json, category Floods) inside NISAR's public window:
  1. NISAR passes over the event point come from the server's /api/series.json (one track and direction).
     before = last pass up to the event date, after = first pass in the 30 days after it.
  2. Read a 20 x 20 km box from both calibrated HDF5 files (gcov_science.read_box), Lee filter (water_road.lee).
  3. Open-water flood = after HH < T and before HH >= T and (after - before) < -3 dB, outside permanent water
     (JRC Global Surface Water occurrence > 50 %). T = -16.75 dB, learned on the Andijan reservoir (not tuned here).
  4. Flooded-vegetation / flooded-town candidates = (after - before) > +3 dB (water under stems and walls doubles the echo).
  5. Outside judge: clearest Sentinel-2 L2A within 5 days after the radar pass; IoU of new water vs NDWI > 0 new water
     (NDWI water after AND NOT JRC permanent water) when the photo is clear enough over the box.
Writes data/floods/<event id>.json and .png (grey HH after, blue = new open water, magenta = brighter = flooded-vegetation candidates).
Usage: python tools/flood_watch.py [--max 40] [--km 10]
"""
import argparse
import json
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gcov_science  # noqa: E402
import water_road as wr  # noqa: E402
from utm_convert import utm_to_lonlat  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "floods"
T_DB = -16.75
NISAR_START = "2026-06-17"


def events():
    d = json.load(open(ROOT / "data" / "eonet_v2.json"))
    ev = d.get("events", d) if isinstance(d, dict) else d
    fl = [e for e in ev if "lood" in str(e.get("category", "")) and e.get("date", "") >= NISAR_START]
    home = lambda e: 0 if (55 <= e["lon"] <= 80 and 35 <= e["lat"] <= 48) else 1  # Central Asia first
    return sorted(fl, key=lambda e: (home(e), e["date"]), reverse=False)


def grid_lonlat(meta, shape):
    ny, nx = shape
    X, Y = np.meshgrid(meta["x0"] + (np.arange(nx) + .5) * meta["dx"], meta["y0"] - (np.arange(ny) + .5) * meta["dy"])
    return utm_to_lonlat(X, Y, int(meta["zone"]), bool(meta["south"]))


def one(e, km, earthaccess):
    with urllib.request.urlopen(f"http://127.0.0.1:8765/api/series.json?lon={e['lon']:.3f}&lat={e['lat']:.3f}", timeout=240) as r:
        frames = json.load(r).get("frames", [])
    t = e["date"]; t_end = str(date.fromisoformat(t) + timedelta(days=30))
    pre = [f for f in frames if NISAR_START <= f["date"] <= t]; post = [f for f in frames if t < f["date"] <= t_end]
    if not pre or not post:
        return {"id": e["id"], "title": e["title"], "date": t, "lon": e["lon"], "lat": e["lat"], "status": "no NISAR pass before and after", "passes": len(frames)}
    a, b = pre[-1], post[0]
    boxes = []
    for f in (a, b):
        url = f"https://nisar.asf.earthdatacloud.nasa.gov/NISAR/{f['c']}/{f['id']}/{f['id']}.h5"
        for attempt in range(3):
            try:
                hh, hv, px, meta = gcov_science.read_box(earthaccess.open([url])[0], e["lon"], e["lat"], km); break
            except Exception as ex:
                if "outside" in str(ex) or attempt == 2:
                    return {"id": e["id"], "title": e["title"], "date": t, "lon": e["lon"], "lat": e["lat"], "status": f"read failed: {str(ex)[:80]}"}
                time.sleep(20 * (attempt + 1))
        boxes.append((hh.astype(np.float32), meta))
    (h0, m0), (h1, m1) = boxes
    n = min(h0.shape[0], h1.shape[0]); m = min(h0.shape[1], h1.shape[1]); h0, h1 = h0[:n, :m], h1[:n, :m]
    ok = np.isfinite(h0) & np.isfinite(h1)
    f0 = 10 * np.log10(np.maximum(wr.lee(np.where(ok, 10 ** (h0 / 10), 0)), 1e-6)); f1 = 10 * np.log10(np.maximum(wr.lee(np.where(ok, 10 ** (h1 / 10), 0)), 1e-6))
    lon, lat = grid_lonlat(m1, (n, m)); bbox = [float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max())]
    perm = np.zeros((n, m), bool)
    try:
        gsw = wr.stac({"collections": ["jrc-gsw"], "bbox": bbox, "limit": 4})
        if gsw:
            perm = wr.sample(wr.crop("jrc-gsw", gsw[0]["id"], ["occurrence"], bbox, 1500)[0], lon, lat, bbox) > 50
    except Exception:
        pass
    d = f1 - f0
    new_water = ok & (f1 < T_DB) & (f0 >= T_DB) & (d < -3) & ~perm
    new_water = ndimage.binary_opening(new_water, iterations=1)
    brighter = ok & (d > 3) & ~perm
    brighter = ndimage.binary_opening(brighter, iterations=1)
    px_km2 = m1["dx"] * m1["dy"] / 1e6
    rec = {"id": e["id"], "title": e["title"], "date": t, "lon": e["lon"], "lat": e["lat"], "status": "mapped", "source": e.get("sources", []),
           "before": a["date"], "after": b["date"], "box_km": 2 * km, "bbox": bbox, "res_m": round(m1["dx"]),
           "new_open_water_km2": round(float(new_water.sum() * px_km2), 2), "brighter_km2": round(float(brighter.sum() * px_km2), 2),
           "permanent_water_km2": round(float((perm & ok).sum() * px_km2), 2), "threshold_db": T_DB}
    # outside judge: Sentinel-2 within 5 days after the radar pass
    s2 = wr.stac({"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 20, "datetime": f"{b['date']}T00:00:00Z/{date.fromisoformat(b['date']) + timedelta(days=5)}T23:59:59Z"})
    if s2:
        best = min(s2, key=lambda x: x["properties"]["eo:cloud_cover"])
        rec["s2_date"], rec["s2_cloud_pct"] = best["properties"]["datetime"][:10], round(best["properties"]["eo:cloud_cover"])
        try:
            arr = wr.crop("sentinel-2-l2a", best["id"], ["B03", "B08", "SCL"], bbox, 1200)
            clear = wr.sample(~np.isin(arr[2], [0, 1, 3, 8, 9, 10]), lon, lat, bbox) & ok
            ow = wr.sample((arr[0].astype(float) - arr[1]) / np.maximum(arr[0].astype(float) + arr[1], 1) > 0, lon, lat, bbox) & ~perm & clear
            rec["s2_clear_pct"] = round(float(clear.mean() * 100), 1)
            if clear.mean() > 0.3:
                rw = (ok & (f1 < T_DB) & ~perm) & clear; u = (rw | ow).sum()
                rec["s2_water_outside_perm_km2"] = round(float(ow.sum() * px_km2), 2)
                rec["radar_water_outside_perm_km2"] = round(float(rw.sum() * px_km2), 2)
                rec["iou_vs_s2"] = round(float((rw & ow).sum() / u), 3) if u else None
        except Exception as ex:
            rec["s2_error"] = str(ex)[:80]
    g = np.clip((f1 + 25) / 30 * 255, 0, 255).astype(np.uint8)
    rgb = np.dstack([g, g, g]); rgb[new_water] = (37, 99, 235); rgb[brighter] = (214, 51, 132)
    alpha = np.where(ok, 255, 0).astype(np.uint8)
    Image.fromarray(np.dstack([rgb, alpha])).save(OUT / f"{e['id']}.png", optimize=True)
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--max", type=int, default=40); ap.add_argument("--km", type=float, default=10); a = ap.parse_args()
    import earthaccess
    earthaccess.login(strategy="netrc")
    OUT.mkdir(parents=True, exist_ok=True)
    idx = OUT / "index.json"
    done = {r["id"]: r for r in json.loads(idx.read_text())} if idx.exists() else {}
    for e in events()[: a.max]:
        if e["id"] in done and not str(done[e["id"]].get("status", "")).startswith(("error", "read failed")):
            continue  # retry only events that failed on a network error
        try:
            r = one(e, a.km, earthaccess)
        except Exception as ex:
            r = {"id": e["id"], "title": e["title"], "date": e["date"], "lon": e["lon"], "lat": e["lat"], "status": f"error: {str(ex)[:80]}"}
        done[e["id"]] = r
        (OUT / f"{e['id']}.json").write_text(json.dumps(r, indent=1))
        idx.write_text(json.dumps(list(done.values()), indent=1))
        print(r.get("title"), "|", r.get("status"), "|", r.get("before"), "->", r.get("after"), "| new water", r.get("new_open_water_km2"),
              "km2 | brighter", r.get("brighter_km2"), "| S2", r.get("s2_cloud_pct"), "% cloud, IoU", r.get("iou_vs_s2"), flush=True)


if __name__ == "__main__":
    main()
