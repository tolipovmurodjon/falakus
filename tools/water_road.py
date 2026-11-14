"""The water road: Andijan reservoir -> Fergana fields -> Aral Sea, from calibrated NISAR GCOV dB.

For every stored pass of a place (data/science/<place>/*.npz, HH and HV gamma0 in dB on NASA's UTM grid):
  1. Lee speckle filter (7x7, on power, local coefficient of variation) on HH and HV.
  2. Water mask = filtered HH < T, only inside the "possible water" zone (ESA WorldCover water/wetland + 1 km). T is learned on the FIRST pass only (best IoU against its Sentinel-2 photo) and then
     tested on every later pass, which it never saw. HV is not used: over calm water NISAR's HV sits at its noise floor
     (about -23 dB), so it cannot separate water (measured on the Andijan reservoir, 14 Nov).
  3. Dual-pol radar vegetation index RVI = 4*HV / (HH + HV) (power), averaged over cropland pixels
     (ESA WorldCover class 40); grows as stems and leaves grow, drops when a field is cut.
  4. Outside judge: for each pass, the clearest Sentinel-2 L2A scene within 3 days (cloud < 20 %) gives a water mask
     NDWI = (B03 - B08) / (B03 + B08) > 0 on the same grid; IoU = |radar & optical| / |radar | optical|.
Writes data/waterroad/<place>.json and prints one line per pass.
Usage: python tools/water_road.py andijan fergana aral
"""
import io
import json
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utm_convert import utm_to_lonlat  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PC = "https://planetarycomputer.microsoft.com/api"
STEP = 2  # 40 m analysis grid: keeps memory small on the laptop


def lee(power, size=7):
    mean = ndimage.uniform_filter(power, size); sq = ndimage.uniform_filter(power * power, size)
    var = np.maximum(sq - mean * mean, 0)
    noise = np.nanmedian(var / np.maximum(mean * mean, 1e-12))  # speckle variance (CV^2) estimated from the scene
    w = np.clip(1 - noise * mean * mean / np.maximum(var, 1e-12), 0, 1)
    return mean + w * (power - mean)


def stac(body):
    r = urllib.request.Request(f"{PC}/stac/v1/search", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(r, timeout=90))["features"]


def crop(collection, item, assets, bbox, size, extra=""):
    w, s, e, n = bbox
    q = "&".join(f"assets={a}" for a in assets)
    url = f"{PC}/data/v1/item/bbox/{w},{s},{e},{n}.npy?collection={collection}&item={item}&{q}&max_size={size}&resampling=nearest{extra}"
    return np.load(io.BytesIO(urllib.request.urlopen(url, timeout=180).read()))


def sample(grid, lon, lat, bbox):
    H, W = grid.shape
    ci = np.clip(((lon - bbox[0]) / (bbox[2] - bbox[0]) * W).astype(int), 0, W - 1)
    ri = np.clip(((bbox[3] - lat) / (bbox[3] - bbox[1]) * H).astype(int), 0, H - 1)
    return grid[ri, ci]


def place(name):
    files = sorted(f for f in (ROOT / "data" / "science" / name).glob("20*.npz"))
    out = {"place": name, "method": __doc__.split("Writes")[0].strip(), "passes": []}
    lon = lat = bbox = crop_mask = None
    T = {"t": None, "fit_on": None}
    for f in files:
        z = np.load(f)
        if "x0" not in z.files:
            continue
        hh = z["hh_db"].astype(np.float32)[::STEP, ::STEP]; hv = z["hv_db"].astype(np.float32)[::STEP, ::STEP]
        if lon is None or lon.shape != hh.shape:
            ny, nx = hh.shape; dx, dy = float(z["dx"]) * STEP, float(z["dy"]) * STEP
            X, Y = np.meshgrid(float(z["x0"]) + (np.arange(nx) + .5) * dx, float(z["y0"]) - (np.arange(ny) + .5) * dy)
            lon, lat = utm_to_lonlat(X, Y, int(z["zone"]), bool(z["south"]))
            bbox = [float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max())]
            wc = stac({"collections": ["esa-worldcover"], "bbox": bbox, "limit": 4})
            wc = sorted(wc, key=lambda x: x["properties"].get("esa_worldcover:product_version", ""))[-1]
            wcg = sample(crop("esa-worldcover", wc["id"], ["map"], bbox, 1500)[0], lon, lat, bbox)
            crop_mask = wcg == 40
            # where water can be: ESA WorldCover water + wetland, grown by 1 km (OPERA-style "possible water" mask)
            zone = ndimage.binary_dilation(np.isin(wcg, [80, 90]), iterations=max(1, int(1000 / dx)))
            px_km2 = dx * dy / 1e6
        ok = np.isfinite(hh) & np.isfinite(hv)
        phh = lee(np.where(ok, 10 ** (hh / 10), 0)); phv = lee(np.where(ok, 10 ** (hv / 10), 0))
        with np.errstate(all="ignore"):
            fhh = 10 * np.log10(phh)
            rvi = 4 * phv / (phh + phv)
        if T["t"] is None:
            T["t"] = -18.0  # placeholder until the first Sentinel-2 match fits it
        water = ok & zone & (fhh < T["t"])
        d = f.stem
        rec = {"date": d, "water_km2": round(float(water.sum() * px_km2), 2),
               "rvi_crop": round(float(np.nanmean(rvi[ok & crop_mask])), 3) if (ok & crop_mask).any() else None,
               "hv_crop_db": round(float(10 * np.log10(np.nanmean(phv[ok & crop_mask]))), 2) if (ok & crop_mask).any() else None}
        # outside judge: clearest Sentinel-2 within 3 days
        t = date.fromisoformat(d)
        s2 = stac({"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 30,
                   "datetime": f"{t - timedelta(days=3)}T00:00:00Z/{t + timedelta(days=3)}T23:59:59Z",
                   "query": {"eo:cloud_cover": {"lt": 20}}})
        days = {}
        for it in s2:
            days.setdefault(it["properties"]["datetime"][:10], []).append(it)
        best_day = None
        for day, items in days.items():  # stitch every tile of that day; keep the day with the most clear sky over the box
            try:
                g = nir = scl = None
                for it in items:
                    a = crop("sentinel-2-l2a", it["id"], ["B03", "B08", "SCL"], bbox, 1500)
                    if g is None:
                        g, nir, scl = a[0].astype(np.float32), a[1].astype(np.float32), a[2].copy()
                    else:
                        fill = (scl == 0) & (a[2] > 0)
                        g[fill], nir[fill], scl[fill] = a[0][fill], a[1][fill], a[2][fill]
                clear = ~np.isin(scl, [0, 1, 3, 8, 9, 10])  # drop no-data, saturated, cloud shadow, clouds, cirrus
                opt_clear = sample(clear, lon, lat, bbox) & ok
                if best_day is None or opt_clear.mean() > best_day[1].mean():
                    best_day = (day, opt_clear, sample((g - nir) / np.maximum(g + nir, 1) > 0, lon, lat, bbox))
            except Exception as ex:
                rec["s2_error"] = str(ex)[:100]
        if best_day and T["fit_on"] is None:
            day, opt_clear, opt_w = best_day
            best = max(np.arange(-24, -12, 0.25), key=lambda t: ((ok & zone & (fhh < t) & opt_clear & opt_w).sum() / max(((ok & zone & (fhh < t) & opt_clear) | (opt_w & opt_clear)).sum(), 1)))
            T.update(t=float(best), fit_on=d); water = ok & zone & (fhh < T["t"])
            rec.update(water_km2=round(float(water.sum() * px_km2), 2))
            out["threshold_db"] = T["t"]; out["threshold_fit_on"] = d
        if best_day:
            day, opt_clear, opt_w = best_day
            rec["held_out"] = d != T["fit_on"]
            rw, ow = water & opt_clear, opt_w & opt_clear
            union = (rw | ow).sum()
            rec.update(s2_date=day, s2_clear_pct=round(float(opt_clear.mean() * 100), 1), radar_water_in_clear_km2=round(float(rw.sum() * px_km2), 2),
                       s2_water_km2=round(float(ow.sum() * px_km2), 2), iou=round(float((rw & ow).sum() / union), 3) if union else None)
        out["passes"].append(rec)
        print(name, rec, flush=True)
    out["bbox"] = bbox
    (ROOT / "data" / "waterroad").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "waterroad" / f"{name}.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    for p in sys.argv[1:] or ["andijan", "fergana", "aral"]:
        place(p)
