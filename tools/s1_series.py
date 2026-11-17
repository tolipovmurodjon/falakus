"""Multi-year radar time-lapse of a box from Sentinel-1 RTC (C-band VV, ESA, via Microsoft Planetary Computer, no login).

NISAR's calibrated public archive starts in June 2026, so for the years before we use Sentinel-1, a radar too
(sees through cloud and at night, ~12-day repeat since 2015). One pass per month (the one closest to the 15th),
cropped to the box on a fixed grid. Water = Lee-filtered VV below T, inside the possible-water zone
(ESA WorldCover water/wetland + 1 km); T is learned on ONE month against a clear Sentinel-2 photo (NDWI > 0)
and then applied to every other month unchanged. The months with a clear photo are scored (held out).
Writes data/s1series/<name>/<YYYY-MM>.png (grey VV) and data/s1series/<name>.json.
Usage: python tools/s1_series.py andijan_res 73.0279 40.6839 73.2421 40.8461 --from 2023-11 --to 2026-11
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import water_road as wr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def months(a, b):
    y, m = map(int, a.split("-")); y2, m2 = map(int, b.split("-"))
    while (y, m) <= (y2, m2):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("w", type=float); ap.add_argument("s", type=float)
    ap.add_argument("e", type=float); ap.add_argument("n", type=float); ap.add_argument("--from", dest="a", default="2023-11"); ap.add_argument("--to", dest="b", default="2026-11"); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(); bbox = [a.w, a.s, a.e, a.n]
    out = ROOT / "data" / "s1series" / a.name; out.mkdir(parents=True, exist_ok=True)
    W = 900; H = int(W * (a.n - a.s) / ((a.e - a.w) * np.cos(np.radians((a.s + a.n) / 2))))
    lon, lat = np.meshgrid(np.linspace(a.w, a.e, W), np.linspace(a.n, a.s, H))
    wc = sorted(wr.stac({"collections": ["esa-worldcover"], "bbox": bbox, "limit": 4}), key=lambda x: x["properties"].get("esa_worldcover:product_version", ""))[-1]
    wcg = wr.sample(wr.crop("esa-worldcover", wc["id"], ["map"], bbox, 1500)[0], lon, lat, bbox)
    px_m = (a.e - a.w) * 111320 * np.cos(np.radians((a.s + a.n) / 2)) / W
    zone = ndimage.binary_dilation(np.isin(wcg, [80, 90]), iterations=max(1, int(1000 / px_m)))
    px_km2 = px_m * ((a.n - a.s) * 110570 / H) / 1e6
    cache = out / "cache"; cache.mkdir(exist_ok=True)  # one .npz per month: a rerun resumes where the network dropped
    todo = [(y, m) for y, m in months(a.a, a.b) if not (cache / f"{y}-{m:02d}.npz").exists()]

    def job(ym_):
        y, m = ym_; cf = cache / f"{y}-{m:02d}.npz"
        try:
            fetch_month(a, bbox, lon, lat, ok_zone=zone, y=y, m=m, out=out, cf=cf, px_km2=px_km2)
        except Exception as ex:  # network gave up after retries: leave no cache file so the next run retries this month
            print(f"{y}-{m:02d}", "FAILED", str(ex)[:80], flush=True)
    with ThreadPoolExecutor(a.workers) as pool:  # network-bound; each month is independent and cached on its own
        list(pool.map(job, todo))
    # second pass, streamed from disk: learn T on the FIRST month with a clear photo, apply it unchanged to every month
    files = sorted(cache.glob("*.npz")); T = None; fit = None
    for cf in files:
        z = np.load(cf, allow_pickle=False)
        if "ow" in z.files:
            f, ok, ow, clear = z["f"].astype(np.float32), z["ok"], z["ow"], z["clear"]
            T = float(max(np.arange(-26, -12, 0.25), key=lambda t: (ok & zone & (f < t) & clear & ow).sum() / max(((ok & zone & (f < t) & clear) | ow).sum(), 1)))
            fit = cf.stem; break
    recs = []
    for cf in files:
        z = np.load(cf, allow_pickle=False)
        if "f" not in z.files:
            continue
        rec = json.loads(str(z["rec"])); f, ok = z["f"].astype(np.float32), z["ok"]
        water = ok & zone & (f < (T if T is not None else -18))
        rec["water_km2"] = round(float(water.sum() * px_km2), 2)
        if cf.stem == fit:
            rec["fit_month"] = True
        elif "ow" in z.files:
            ow, clear = z["ow"], z["clear"]
            u = ((water & clear) | ow).sum(); rec["iou"] = round(float((water & clear & ow).sum() / u), 3) if u else None
            rec["s1_clear_km2"] = round(float((water & clear).sum() * px_km2), 2)  # radar water inside the photo's clear pixels
        recs.append(rec)
    held = [r for r in recs if "iou" in r and r["iou"] is not None]
    score = {"n": len(held), "mean_iou": round(float(np.mean([r["iou"] for r in held])), 3) if held else None,
             "median_iou": round(float(np.median([r["iou"] for r in held])), 3) if held else None,
             "area_mae_km2": round(float(np.mean([abs(r["s1_clear_km2"] - r["s2_water_km2"]) for r in held])), 2) if held else None,
             "area_bias_km2": round(float(np.mean([r["s1_clear_km2"] - r["s2_water_km2"] for r in held])), 2) if held else None}
    print("held-out", score, "T", T, "fit", fit, flush=True)
    (ROOT / "data" / "s1series" / f"{a.name}.json").write_text(json.dumps({"name": a.name, "bbox": bbox, "threshold_db": T, "fit_month": fit, "heldout": score,
        "method": __doc__.split("Writes")[0].strip(), "months": recs}, indent=1))


def retry(fn, *args, tries=4):
    for k in range(tries):
        try:
            return fn(*args)
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))


def fetch_month(a, bbox, lon, lat, ok_zone, y, m, out, cf, px_km2):
    mid = date(y, m, 15); ym = f"{y}-{m:02d}"
    items = retry(wr.stac, {"collections": ["sentinel-1-rtc"], "bbox": bbox, "limit": 40,
                            "datetime": f"{y}-{m:02d}-01T00:00:00Z/{y}-{m:02d}-28T23:59:59Z"})
    if not items:
        np.savez(cf, none=1); print(ym, "no pass", flush=True); return
    it = min(items, key=lambda x: abs((date.fromisoformat(x["properties"]["datetime"][:10]) - mid).days))
    d = it["properties"]["datetime"][:10]
    arr = retry(wr.crop, "sentinel-1-rtc", it["id"], ["vv"], bbox, 1500)
    v = wr.sample(np.where(arr[-1] > 0, arr[0], np.nan) if arr.shape[0] > 1 else arr[0], lon, lat, bbox).astype(np.float32); del arr
    ok = np.isfinite(v) & (v > 0)
    if ok.mean() < 0.8:
        np.savez(cf, none=1); print(ym, d, "partial coverage", flush=True); return
    f = 10 * np.log10(np.maximum(wr.lee(np.where(ok, v, 0)), 1e-6))
    rec = {"month": ym, "date": d, "sensor": "Sentinel-1 C-band VV"}
    # optical check: clearest Sentinel-2 within +-6 days
    d0 = date.fromisoformat(d)
    s2 = retry(wr.stac, {"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 20,
                         "datetime": f"{d0 - timedelta(days=6)}T00:00:00Z/{d0 + timedelta(days=6)}T23:59:59Z", "query": {"eo:cloud_cover": {"lt": 15}}})
    extra = {}
    if s2:
        try:
            best = min(s2, key=lambda x: x["properties"]["eo:cloud_cover"])
            g = retry(wr.crop, "sentinel-2-l2a", best["id"], ["B03", "B08", "SCL"], bbox, 1200)
            clear = wr.sample(~np.isin(g[2], [0, 1, 3, 8, 9, 10, 11]), lon, lat, bbox) & ok  # 11 = snow/ice: NDWI calls snow water
            ow = wr.sample((g[0].astype(float) - g[1]) / np.maximum(g[0].astype(float) + g[1], 1) > 0, lon, lat, bbox) & clear
            if clear.mean() >= 0.7:
                rec["s2_date"] = best["properties"]["datetime"][:10]; rec["s2_water_km2"] = round(float(ow.sum() * px_km2), 2)
                extra = {"ow": ow, "clear": clear}
        except Exception as ex:
            print(ym, "s2 skip", str(ex)[:60], flush=True)
    g8 = np.clip((f + 25) / 22 * 255, 0, 255).astype(np.uint8)
    Image.fromarray(np.dstack([g8, g8, g8, np.where(ok, 255, 0).astype(np.uint8)])).save(out / f"{ym}.png", optimize=True)
    np.savez_compressed(cf, f=f.astype(np.float16), ok=ok, rec=json.dumps(rec), **extra)
    print(ym, d, "photo " + rec.get("s2_date", "") if extra else "", flush=True)


if __name__ == "__main__":
    main()
