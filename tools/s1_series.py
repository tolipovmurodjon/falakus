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
from datetime import date
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
    ap.add_argument("e", type=float); ap.add_argument("n", type=float); ap.add_argument("--from", dest="a", default="2023-11"); ap.add_argument("--to", dest="b", default="2026-11")
    a = ap.parse_args(); bbox = [a.w, a.s, a.e, a.n]
    out = ROOT / "data" / "s1series" / a.name; out.mkdir(parents=True, exist_ok=True)
    W = 900; H = int(W * (a.n - a.s) / ((a.e - a.w) * np.cos(np.radians((a.s + a.n) / 2))))
    lon, lat = np.meshgrid(np.linspace(a.w, a.e, W), np.linspace(a.n, a.s, H))
    wc = sorted(wr.stac({"collections": ["esa-worldcover"], "bbox": bbox, "limit": 4}), key=lambda x: x["properties"].get("esa_worldcover:product_version", ""))[-1]
    wcg = wr.sample(wr.crop("esa-worldcover", wc["id"], ["map"], bbox, 1500)[0], lon, lat, bbox)
    px_m = (a.e - a.w) * 111320 * np.cos(np.radians((a.s + a.n) / 2)) / W
    zone = ndimage.binary_dilation(np.isin(wcg, [80, 90]), iterations=max(1, int(1000 / px_m)))
    px_km2 = px_m * ((a.n - a.s) * 110570 / H) / 1e6
    recs, T = [], None
    for y, m in months(a.a, a.b):
        mid = date(y, m, 15)
        items = wr.stac({"collections": ["sentinel-1-rtc"], "bbox": bbox, "limit": 40,
                         "datetime": f"{y}-{m:02d}-01T00:00:00Z/{y}-{m:02d}-28T23:59:59Z"})
        if not items:
            continue
        it = min(items, key=lambda x: abs((date.fromisoformat(x["properties"]["datetime"][:10]) - mid).days))
        d = it["properties"]["datetime"][:10]
        try:
            arr = wr.crop("sentinel-1-rtc", it["id"], ["vv"], bbox, 1500)
        except Exception as ex:
            print(d, "skip", str(ex)[:60], flush=True); continue
        v = wr.sample(np.where(arr[-1] > 0, arr[0], np.nan) if arr.shape[0] > 1 else arr[0], lon, lat, bbox).astype(np.float32)
        ok = np.isfinite(v) & (v > 0)
        if ok.mean() < 0.8:
            continue
        f = 10 * np.log10(np.maximum(wr.lee(np.where(ok, v, 0)), 1e-6))
        rec = {"month": f"{y}-{m:02d}", "date": d, "sensor": "Sentinel-1 C-band VV"}
        # optical check: clearest Sentinel-2 within +-6 days
        s2 = wr.stac({"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 20, "datetime": f"{d}T00:00:00Z/{d}T23:59:59Z".replace(d + "T00", str(date.fromordinal(date.fromisoformat(d).toordinal() - 6)) + "T00").replace(d + "T23", str(date.fromordinal(date.fromisoformat(d).toordinal() + 6)) + "T23"),
                      "query": {"eo:cloud_cover": {"lt": 15}}})
        ow = clear = None
        if s2:
            try:
                best = min(s2, key=lambda x: x["properties"]["eo:cloud_cover"])
                g = wr.crop("sentinel-2-l2a", best["id"], ["B03", "B08", "SCL"], bbox, 1200)
                clear = wr.sample(~np.isin(g[2], [0, 1, 3, 8, 9, 10, 11]), lon, lat, bbox) & ok  # 11 = snow/ice: NDWI calls snow water
                ow = wr.sample((g[0].astype(float) - g[1]) / np.maximum(g[0].astype(float) + g[1], 1) > 0, lon, lat, bbox) & clear
                if clear.mean() < 0.7:
                    ow = None
                else:
                    rec["s2_date"] = best["properties"]["datetime"][:10]; rec["s2_water_km2"] = round(float(ow.sum() * px_km2), 2)
            except Exception:
                ow = None
        g8 = np.clip((f + 25) / 22 * 255, 0, 255).astype(np.uint8)
        Image.fromarray(np.dstack([g8, g8, g8, np.where(ok, 255, 0).astype(np.uint8)])).save(out / f"{y}-{m:02d}.png", optimize=True)
        recs.append((rec, f.astype(np.float16), ok, ow, clear)); print(rec["month"], rec["date"], "photo" if ow is not None else "", flush=True)
    # second pass: learn T on the FIRST month with a clear photo, apply it unchanged to every month
    fit = next((k for k, r in enumerate(recs) if r[3] is not None), None)
    if fit is not None:
        _, f, ok, ow, clear = recs[fit]
        T = float(max(np.arange(-26, -12, 0.25), key=lambda t: (ok & zone & (f < t) & clear & ow).sum() / max(((ok & zone & (f < t) & clear) | ow).sum(), 1)))
    for k, (rec, f, ok, ow, clear) in enumerate(recs):
        water = ok & zone & (f < (T if T is not None else -18))
        rec["water_km2"] = round(float(water.sum() * px_km2), 2)
        if k == fit:
            rec["fit_month"] = True
        elif ow is not None:
            u = ((water & clear) | ow).sum(); rec["iou"] = round(float((water & clear & ow).sum() / u), 3) if u else None
        print(rec, flush=True)
    recs = [r[0] for r in recs]
    if T is not None:  # months before the fit month used the placeholder: recompute is cheap only with arrays; mark them
        for r in recs:
            r["threshold_db"] = T
    (ROOT / "data" / "s1series" / f"{a.name}.json").write_text(json.dumps({"name": a.name, "bbox": bbox, "threshold_db": T, "method": __doc__.split("Writes")[0].strip(), "months": recs}, indent=1))


if __name__ == "__main__":
    main()
