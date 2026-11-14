"""ALOS PALSAR (JAXA, L-band like NISAR) over a box, 2006-2011, from ASF's radiometrically terrain-corrected (RTC) archive.

Same wavelength (23.6 cm) as NISAR, so the same physics: calm water = mirror = dark HH.
For each scene: download the RTC_LOW_RES zip (30 m, ~50-75 MB, Earthdata login via earthaccess), read HH (and HV)
gamma0 inside the zip, crop to the box on the water_road grid, Lee filter, water = HH < the NISAR cut-off (-16.75 dB,
learned on NISAR, NOT re-tuned), inside the same possible-water zone. Outside judge: the clearest Landsat 5/7
Collection-2 L2 scene within +-8 days (Planetary Computer), water = MNDWI > 0 on clear pixels -> IoU.
Writes data/alos/<name>/<date>.png (grey HH) and data/alos/<name>.json.
Usage: python tools/alos_series.py andijan_res 73.135 40.765 73.0279 40.6839 73.2421 40.8461
"""
import argparse
import io
import json
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import urllib.request
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import water_road as wr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
T_DB = -16.75


def scenes(lon, lat):
    u = (f"https://api.daac.asf.alaska.edu/services/search/param?platform=ALOS&processingLevel=RTC_LOW_RES"
         f"&intersectsWith=POINT({lon}%20{lat})&output=json&maxResults=200")
    L = json.load(urllib.request.urlopen(u, timeout=120))
    L = L[0] if L and isinstance(L[0], list) else L
    seen, out = set(), []
    for x in sorted(L, key=lambda x: x["startTime"]):
        d = x["startTime"][:10]
        if d not in seen:
            seen.add(d); out.append({"date": d, "url": x["downloadUrl"], "pol": x.get("polarization", "")})
    return out


def read_band(zbytes, tag, bbox, lon, lat):
    import rasterio
    from rasterio.warp import transform_bounds
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    name = next((n for n in z.namelist() if n.endswith(f"_{tag}.tif") or n.endswith(f"_{tag}.tiff") or f"_{tag}." in n.split("/")[-1] and n.endswith((".tif", ".tiff"))), None)
    if not name:
        return None
    with rasterio.MemoryFile(z.read(name)) as mf, mf.open() as ds:
        b = transform_bounds("EPSG:4326", ds.crs, *bbox)
        win = ds.window(*b).round_offsets().round_lengths()
        arr = ds.read(1, window=win, boundless=True, fill_value=0).astype(np.float32)
        wb = ds.window_bounds(win)
        from rasterio.warp import transform
        xs, ys = transform("EPSG:4326", ds.crs, lon.ravel().tolist(), lat.ravel().tolist())
        col = ((np.array(xs) - wb[0]) / (wb[2] - wb[0]) * arr.shape[1]).astype(int)
        row = ((wb[3] - np.array(ys)) / (wb[3] - wb[1]) * arr.shape[0]).astype(int)
        okk = (col >= 0) & (col < arr.shape[1]) & (row >= 0) & (row < arr.shape[0])
        v = np.zeros(lon.size, np.float32); v[okk] = arr[row[okk], col[okk]]
        return v.reshape(lon.shape)  # gamma0 power


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("lon", type=float); ap.add_argument("lat", type=float)
    for k in "wsen":
        ap.add_argument(k, type=float)
    a = ap.parse_args(); bbox = [a.w, a.s, a.e, a.n]
    import earthaccess
    earthaccess.login(strategy="netrc"); sess = earthaccess.get_requests_https_session()
    out = ROOT / "data" / "alos" / a.name; out.mkdir(parents=True, exist_ok=True)
    W = 600; H = int(W * (a.n - a.s) / ((a.e - a.w) * np.cos(np.radians((a.s + a.n) / 2))))
    lon, lat = np.meshgrid(np.linspace(a.w, a.e, W), np.linspace(a.n, a.s, H))
    px_m = (a.e - a.w) * 111320 * np.cos(np.radians((a.s + a.n) / 2)) / W
    px_km2 = px_m * ((a.n - a.s) * 110570 / H) / 1e6
    wc = sorted(wr.stac({"collections": ["esa-worldcover"], "bbox": bbox, "limit": 4}), key=lambda x: x["properties"].get("esa_worldcover:product_version", ""))[-1]
    zone = ndimage.binary_dilation(np.isin(wr.sample(wr.crop("esa-worldcover", wc["id"], ["map"], bbox, 1500)[0], lon, lat, bbox), [80, 90]), iterations=max(1, int(1000 / px_m)))
    recs = []
    for sc in scenes(a.lon, a.lat):
        try:
            r = sess.get(sc["url"], timeout=600); r.raise_for_status(); zb = r.content
            hh = read_band(zb, "HH", bbox, lon, lat); hv = read_band(zb, "HV", bbox, lon, lat)
        except Exception as ex:
            print(sc["date"], "skip", str(ex)[:90], flush=True); continue
        if hh is None:
            print(sc["date"], "no HH"); continue
        ok = hh > 0
        if ok.mean() < 0.8:
            print(sc["date"], "partial", round(ok.mean(), 2)); continue
        f = 10 * np.log10(np.maximum(wr.lee(np.where(ok, hh, 0)), 1e-6))
        water = ok & zone & (f < T_DB)
        rec = {"date": sc["date"], "sensor": "ALOS PALSAR L-band", "pol": sc["pol"], "water_km2": round(float(water.sum() * px_km2), 2)}
        if hv is not None and (hv > 0).mean() > 0.8:
            rec["hv_median_db"] = round(float(np.median(10 * np.log10(np.maximum(hv[ok & ~water], 1e-6)))), 2)
        d = date.fromisoformat(sc["date"])
        ls = wr.stac({"collections": ["landsat-c2-l2"], "bbox": bbox, "limit": 30, "datetime": f"{d - timedelta(days=8)}T00:00:00Z/{d + timedelta(days=8)}T23:59:59Z",
                      "query": {"eo:cloud_cover": {"lt": 20}}})
        if ls:
            best = min(ls, key=lambda x: x["properties"]["eo:cloud_cover"])
            try:
                g = wr.crop("landsat-c2-l2", best["id"], ["green", "swir16", "qa_pixel"], bbox, 600)
                clear = wr.sample((g[2].astype(np.int64) & 0b11000) == 0, lon, lat, bbox) & ok & wr.sample(g[0] > 0, lon, lat, bbox)
                gr, sw = g[0].astype(float), g[1].astype(float)
                ow = wr.sample((gr - sw) / np.maximum(gr + sw, 1) > 0, lon, lat, bbox) & clear & zone
                if clear.mean() > 0.6:
                    u = ((water & clear) | ow).sum()
                    rec.update({"landsat_date": best["properties"]["datetime"][:10], "landsat": best["properties"].get("platform", ""),
                                "landsat_water_km2": round(float(ow.sum() * px_km2), 2), "iou": round(float((water & clear & ow).sum() / u), 3) if u else None})
            except Exception as ex:
                rec["landsat_error"] = str(ex)[:80]
        g8 = np.clip((f + 25) / 22 * 255, 0, 255).astype(np.uint8)
        Image.fromarray(np.dstack([g8, g8, g8, np.where(ok, 255, 0).astype(np.uint8)])).save(out / f"{sc['date']}.png", optimize=True)
        recs.append(rec); print(rec, flush=True)
        (ROOT / "data" / "alos" / f"{a.name}.json").write_text(json.dumps({"name": a.name, "bbox": bbox, "threshold_db": T_DB, "method": __doc__.split("Writes")[0].strip(), "scenes": recs}, indent=1))


if __name__ == "__main__":
    main()
