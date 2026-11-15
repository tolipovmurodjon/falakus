"""Learned radar water map for the Andijan reservoir: gradient boosting on NISAR HH/HV, labelled by Sentinel-2 photos.

Why: the one-number rule (filtered HH < T) agrees with the photo at median IoU 0.58. Wet mud and wind-roughened
water break a single cut-off; texture, HV and the pixel's own history can tell them apart.

Data: every NISAR GCOV pass in data/science/andijan_res (HH, HV gamma0 dB, 20 m, read at 40 m).
Labels: Sentinel-2 L2A within 3 days, NDWI = (B03 - B08)/(B03 + B08) > 0 on clear-sky pixels (SCL), same grid.
Features per pixel (all from radar, no photo, no map of where water "should" be):
  Lee-filtered HH and HV, HH - HV, HH local std 5x5 and 11x11, HH min / median / max over all passes of the
  season (the pixel's history), this pass's HH minus the season median (change), HV local std 5x5.
Model: sklearn HistGradientBoostingClassifier (200 trees, depth 6), class-balanced sample of 40k pixels per date.
Test: leave-one-DATE-out. The model never sees the photo of the day it is scored on. Same pixels, same days for
  the threshold baseline (the rule from tools/water_road.py: HH < T inside the water zone, T fit on the first date).
Null control: the same model trained on shuffled labels must collapse (rules/null-control-before-any-score).
Writes data/ml/water_model.json (scores per date + summary) and data/ml/water_pred_<date>.png (water masks).
Usage: python tools/ml_water.py
"""
import json
import time
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utm_convert import utm_to_lonlat  # noqa: E402
from water_road import STEP, crop, lee, sample, stac  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PLACE = "andijan_res"
CACHE = ROOT / "data" / "ml" / f"s2labels_{PLACE}.npz"
FEAT = ["HH", "HV", "HH-HV", "HH std 5", "HH std 11", "HV std 5", "HH season min", "HH season median", "HH season max", "HH minus season median"]


def local_std(a, n):
    m = ndimage.uniform_filter(a, n); s = ndimage.uniform_filter(a * a, n)
    return np.sqrt(np.maximum(s - m * m, 0))


def load_passes():
    files = sorted((ROOT / "data" / "science" / PLACE).glob("20*.npz"))
    out = []
    for f in files:
        z = np.load(f)
        hh = z["hh_db"].astype(np.float32)[::STEP, ::STEP]; hv = z["hv_db"].astype(np.float32)[::STEP, ::STEP]
        ok = np.isfinite(hh) & np.isfinite(hv)
        phh = lee(np.where(ok, 10 ** (hh / 10), 1e-4)); phv = lee(np.where(ok, 10 ** (hv / 10), 1e-4))
        with np.errstate(all="ignore"):
            out.append(dict(date=f.stem[:10], ok=ok, hh=10 * np.log10(np.maximum(phh, 1e-6)), hv=10 * np.log10(np.maximum(phv, 1e-6)), z=z))
    return out


def grid(z, shape):
    ny, nx = shape; dx, dy = float(z["dx"]) * STEP, float(z["dy"]) * STEP
    X, Y = np.meshgrid(float(z["x0"]) + (np.arange(nx) + .5) * dx, float(z["y0"]) - (np.arange(ny) + .5) * dy)
    lon, lat = utm_to_lonlat(X, Y, int(z["zone"]), bool(z["south"]))
    return lon, lat, [float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max())], dx * dy / 1e6


def s2_labels(passes, lon, lat, bbox):
    if CACHE.exists():
        c = np.load(CACHE)
        return {k: (c[k][0], c[k][1], str(c["day_" + k])) for k in c.files if not k.startswith("day_")}
    labels = {}
    for p in passes:
        t = date.fromisoformat(p["date"])
        s2 = None
        for attempt in range(6):  # Planetary Computer drops connections from here; retry with a pause
            try:
                s2 = stac({"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 30,
                           "datetime": f"{t - timedelta(days=3)}T00:00:00Z/{t + timedelta(days=3)}T23:59:59Z", "query": {"eo:cloud_cover": {"lt": 20}}})
                break
            except Exception as ex:
                print(p["date"], "stac retry", attempt, str(ex)[:60], flush=True); time.sleep(20)
        if s2 is None:
            continue
        days = {}
        for it in s2:
            days.setdefault(it["properties"]["datetime"][:10], []).append(it)
        best = None
        for day, items in days.items():
            try:
                g = nir = scl = None
                for it in items:
                    a = crop("sentinel-2-l2a", it["id"], ["B03", "B08", "SCL"], bbox, 1500)
                    if g is None:
                        g, nir, scl = a[0].astype(np.float32), a[1].astype(np.float32), a[2].copy()
                    else:
                        fill = (scl == 0) & (a[2] > 0)
                        g[fill], nir[fill], scl[fill] = a[0][fill], a[1][fill], a[2][fill]
                clear = sample(~np.isin(scl, [0, 1, 3, 8, 9, 10]), lon, lat, bbox) & p["ok"]
                if best is None or clear.mean() > best[1].mean():
                    best = (day, clear, sample((g - nir) / np.maximum(g + nir, 1) > 0, lon, lat, bbox))
            except Exception as ex:
                print(p["date"], "s2 fail", str(ex)[:80], flush=True)
        if best and best[1].mean() > 0.3:
            labels[p["date"]] = (best[1], best[2], best[0]); print(p["date"], "label from", best[0], f"clear {best[1].mean():.0%}", flush=True)
    np.savez_compressed(CACHE, **{k: np.stack([v[0], v[1]]) for k, v in labels.items()}, **{"day_" + k: v[2] for k, v in labels.items()})
    return labels


def features(passes):
    stack = np.stack([p["hh"] for p in passes]); good = np.stack([p["ok"] for p in passes])
    stack = np.where(good, stack, np.nan)
    with np.errstate(all="ignore"):
        smin, smed, smax = np.nanmin(stack, 0), np.nanmedian(stack, 0), np.nanmax(stack, 0)
    F = {}
    for p in passes:
        hh, hv = p["hh"], p["hv"]
        F[p["date"]] = np.stack([hh, hv, hh - hv, local_std(hh, 5), local_std(hh, 11), local_std(hv, 5), smin, smed, smax, hh - smed], -1).astype(np.float32)
    return F


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else None


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    passes = load_passes()
    lon, lat, bbox, px_km2 = grid(passes[0]["z"], passes[0]["hh"].shape)
    labels = s2_labels(passes, lon, lat, bbox)
    F = features(passes)
    rng = np.random.default_rng(0)
    wr = json.loads((ROOT / "data" / "waterroad" / f"{PLACE}.json").read_text())
    T = wr.get("threshold_db", -18.0)
    dates = sorted(labels)
    print("photo-labelled dates:", dates, "threshold", T, flush=True)

    def train(ds, shuffle=False):
        X, y = [], []
        for d in ds:
            clear, wet, _ = labels[d]; m = clear & np.isfinite(F[d]).all(-1)
            idx = np.flatnonzero(m.ravel()); yy = wet.ravel()[idx]
            pos, neg = idx[yy], idx[~yy]
            k = min(20000, len(pos), len(neg))
            pick = np.concatenate([rng.choice(pos, k, replace=False), rng.choice(neg, k, replace=False)])
            X.append(F[d].reshape(-1, len(FEAT))[pick]); y.append(wet.ravel()[pick])
        X, y = np.concatenate(X), np.concatenate(y)
        if shuffle:
            y = rng.permutation(y)
        return HistGradientBoostingClassifier(max_iter=200, max_depth=6, learning_rate=0.08, random_state=0).fit(X, y)

    rows = []
    for d in dates:
        clear, wet, s2day = labels[d]
        m = clear & np.isfinite(F[d]).all(-1)
        model = train([x for x in dates if x != d])
        pr = np.zeros(m.shape, bool); pr[m] = model.predict(F[d][m])
        hh = F[d][..., 0]
        rule = m & (hh < T)
        null = train([x for x in dates if x != d], shuffle=True)
        pn = np.zeros(m.shape, bool); pn[m] = null.predict(F[d][m])
        r = dict(date=d, photo=s2day, clear_pct=round(float(clear.mean() * 100), 1),
                 photo_water_km2=round(float((wet & m).sum() * px_km2), 2),
                 ml_km2=round(float(pr.sum() * px_km2), 2), rule_km2=round(float(rule.sum() * px_km2), 2),
                 ml_iou=round(iou(pr, wet & m), 3), rule_iou=round(iou(rule, wet & m), 3), null_iou=round(iou(pn, wet & m), 3))
        rows.append(r); print(r, flush=True)
    summ = {k: round(float(np.median([r[k] for r in rows])), 3) for k in ("ml_iou", "rule_iou", "null_iou")}
    summ["ml_area_mae_km2"] = round(float(np.mean([abs(r["ml_km2"] - r["photo_water_km2"]) for r in rows])), 2)
    summ["rule_area_mae_km2"] = round(float(np.mean([abs(r["rule_km2"] - r["photo_water_km2"]) for r in rows])), 2)
    print("SUMMARY (median over held-out dates):", summ, flush=True)
    if summ["null_iou"] > 0.5 * summ["ml_iou"]:
        print("NULL CONTROL FAILED: shuffled labels score too high, the test leaks. Not writing results.")
        return

    final = train(dates)
    imp = {}
    try:
        from sklearn.inspection import permutation_importance
        d = dates[-1]; clear, wet, _ = labels[d]; m = clear & np.isfinite(F[d]).all(-1)
        idx = rng.choice(np.flatnonzero(m.ravel()), min(20000, m.sum()), replace=False)
        pi = permutation_importance(final, F[d].reshape(-1, len(FEAT))[idx], wet.ravel()[idx], n_repeats=3, random_state=0)
        imp = {f: round(float(v), 4) for f, v in sorted(zip(FEAT, pi.importances_mean), key=lambda t: -t[1])}
    except Exception as ex:
        print("importance skipped", ex)
    from PIL import Image
    series = []
    for p in passes:
        d = p["date"]; m = np.isfinite(F[d]).all(-1) & p["ok"]
        pr = np.zeros(m.shape, bool); pr[m] = final.predict(F[d][m])
        series.append(dict(date=d, ml_km2=round(float(pr.sum() * px_km2), 2), photo_labelled=d in labels))
        rgba = np.zeros(m.shape + (4,), np.uint8); rgba[pr] = (40, 110, 200, 210)
        Image.fromarray(rgba).save(ROOT / "data" / "ml" / f"water_pred_{d}.png")
    out = dict(method=__doc__.split("Writes")[0].strip(), features=FEAT, threshold_db=T, bbox=bbox, held_out=rows, summary=summ,
               importance=imp, series=series)
    (ROOT / "data" / "ml" / "water_model.json").write_text(json.dumps(out, indent=1))
    print("wrote data/ml/water_model.json")


if __name__ == "__main__":
    main()
