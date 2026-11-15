"""Radar NDVI: a plant-health map on every NISAR pass, also under cloud (Fergana fields).

Why: NDVI needs sunlight in red and near-infrared, so cloud blanks it. L-band HV echo comes from leaves and stems
(volume scattering), so it tracks plant growth and harvest through cloud and at night. A model learns the link
from clear days and then fills the cloudy ones (SAR gap-filling).

Data: every NISAR GCOV pass in data/science/fergana (HH, HV gamma0 dB, read at 40 m).
Labels: Sentinel-2 L2A within 3 days, NDVI = (B08 - B04)/(B08 + B04) on clear-sky pixels (SCL), same grid.
Features (radar only): HH, HV, HH-HV, radar vegetation index RVI = 4 HV / (HH + HV) (linear), HV local std 5x5,
  HV season min / median / max, this pass's HV minus the season median (change).
Model: sklearn HistGradientBoostingRegressor, 40k random clear pixels per date.
Test: leave-one-DATE-out; the model never sees the photo of the day it is scored on.
Baselines on the same pixels: (a) each pixel's mean NDVI on the other photo days (what a map of "usual greenness"
  gives), (b) a straight line on HV alone. Null control: the same model on shuffled labels must collapse.
Writes data/ml/ndvi/ndvi_model.json and data/ml/ndvi/ndvi_<date>.png (predicted NDVI on every pass).
Usage: python tools/ml_ndvi.py
"""
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ml_water as mw  # noqa: E402
from water_road import crop, sample, stac  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PLACE = "fergana"
OUT = ROOT / "data" / "ml" / "ndvi"
CACHE = ROOT / "data" / "ml" / f"s2ndvi_{PLACE}.npz"
FEAT = ["HH", "HV", "HH-HV", "RVI", "HV std 5", "HV season min", "HV season median", "HV season max", "HV minus season median"]


def s2_ndvi(passes, lon, lat, bbox):
    if CACHE.exists():
        c = np.load(CACHE)
        return {k: (c[k][0] > 0.5, c[k][1], str(c["day_" + k])) for k in c.files if not k.startswith("day_")}
    labels = {}
    for p in passes:
        t = date.fromisoformat(p["date"]); s2 = None
        for attempt in range(6):
            try:
                s2 = stac({"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 30,
                           "datetime": f"{t - timedelta(days=3)}T00:00:00Z/{t + timedelta(days=3)}T23:59:59Z", "query": {"eo:cloud_cover": {"lt": 30}}})
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
                red = nir = scl = None
                for it in items:
                    a = crop("sentinel-2-l2a", it["id"], ["B04", "B08", "SCL"], bbox, 1500)
                    if red is None:
                        red, nir, scl = a[0].astype(np.float32), a[1].astype(np.float32), a[2].copy()
                    else:
                        fill = (scl == 0) & (a[2] > 0)
                        red[fill], nir[fill], scl[fill] = a[0][fill], a[1][fill], a[2][fill]
                clear = sample(np.isin(scl, [4, 5]), lon, lat, bbox) & p["ok"]  # vegetation or bare soil only: no water, cloud, shadow, snow
                ndvi = sample((nir - red) / np.maximum(nir + red, 1), lon, lat, bbox).astype(np.float32)
                if best is None or clear.mean() > best[1].mean():
                    best = (day, clear, ndvi)
            except Exception as ex:
                print(p["date"], "s2 fail", str(ex)[:80], flush=True)
        if best and best[1].mean() > 0.3:
            labels[p["date"]] = (best[1], best[2], best[0]); print(p["date"], "NDVI from", best[0], f"clear {best[1].mean():.0%}", flush=True)
    np.savez_compressed(CACHE, **{k: np.stack([v[0].astype(np.float32), v[1]]) for k, v in labels.items()}, **{"day_" + k: v[2] for k, v in labels.items()})
    return labels


def features(passes):
    stack = np.where(np.stack([p["ok"] for p in passes]), np.stack([p["hv"] for p in passes]), np.nan)
    with np.errstate(all="ignore"):
        smin, smed, smax = np.nanmin(stack, 0), np.nanmedian(stack, 0), np.nanmax(stack, 0)
    F = {}
    for p in passes:
        hh, hv = p["hh"], p["hv"]; lhh, lhv = 10 ** (hh / 10), 10 ** (hv / 10)
        rvi = 4 * lhv / np.maximum(lhh + lhv, 1e-6)
        F[p["date"]] = np.stack([hh, hv, hh - hv, rvi, mw.local_std(hv, 5), smin, smed, smax, hv - smed], -1).astype(np.float32)
    return F


def scores(y, p):
    mae = float(np.mean(np.abs(y - p))); r2 = float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))
    return round(mae, 4), round(r2, 3)


def colour(nd, ok):
    """NDVI -0.1..0.8 on a brown -> green ramp; no-data transparent."""
    t = np.clip((nd + 0.1) / 0.9, 0, 1)
    lo, hi = np.array([156, 112, 64]), np.array([28, 120, 52])
    rgb = (lo[None, None] * (1 - t[..., None]) + hi[None, None] * t[..., None]).astype(np.uint8)
    return np.dstack([rgb, np.where(ok & np.isfinite(nd), 220, 0).astype(np.uint8)])


def main():
    from sklearn.ensemble import HistGradientBoostingRegressor
    mw.PLACE = PLACE
    passes = mw.load_passes()
    lon, lat, bbox, _ = mw.grid(passes[0]["z"], passes[0]["hh"].shape)
    labels = s2_ndvi(passes, lon, lat, bbox)
    F = features(passes); dates = sorted(labels)
    print("photo days:", len(dates), dates, flush=True)
    rng = np.random.default_rng(0)

    def sample_day(d, k=40000):
        clear, nd, _ = labels[d]; m = clear & np.isfinite(F[d]).all(-1) & np.isfinite(nd)
        idx = np.flatnonzero(m.ravel()); idx = rng.choice(idx, min(k, idx.size), replace=False)
        return idx, F[d].reshape(-1, len(FEAT))[idx], nd.ravel()[idx]

    S = {d: sample_day(d) for d in dates}
    rows = []
    for d in dates:
        tr = [x for x in dates if x != d]
        X = np.concatenate([S[x][1] for x in tr]); y = np.concatenate([S[x][2] for x in tr])
        m = HistGradientBoostingRegressor(max_iter=250, max_depth=6, learning_rate=0.08, random_state=0).fit(X, y)
        idx, Xt, yt = S[d]
        ml = scores(yt, m.predict(Xt))
        # baseline a: each pixel's mean NDVI on the other photo days (where it is clear there)
        stack = np.stack([np.where(labels[x][0], labels[x][1], np.nan) for x in tr]).reshape(len(tr), -1)
        with np.errstate(all="ignore"):
            clim = np.nanmean(stack[:, idx], 0)
        okc = np.isfinite(clim); clim_s = scores(yt[okc], clim[okc])
        # baseline b: straight line on HV alone
        a, b = np.polyfit(X[:, 1], y, 1); hv_s = scores(yt, a * Xt[:, 1] + b)
        rows.append(dict(date=d, photo=labels[d][2], n=int(yt.size), ml_mae=ml[0], ml_r2=ml[1], usual_mae=clim_s[0], usual_r2=clim_s[1],
                         hv_line_mae=hv_s[0], hv_line_r2=hv_s[1], mean_ndvi=round(float(yt.mean()), 3)))
        print(rows[-1], flush=True)
    # null control: shuffled labels, scored on the first held-out date
    d = dates[0]; tr = [x for x in dates if x != d]
    X = np.concatenate([S[x][1] for x in tr]); y = rng.permutation(np.concatenate([S[x][2] for x in tr]))
    null = scores(S[d][2], HistGradientBoostingRegressor(max_iter=250, max_depth=6, learning_rate=0.08, random_state=0).fit(X, y).predict(S[d][1]))
    med = lambda k: round(float(np.median([r[k] for r in rows])), 4)  # noqa: E731
    summary = dict(ml_mae=med("ml_mae"), ml_r2=med("ml_r2"), usual_mae=med("usual_mae"), usual_r2=med("usual_r2"),
                   hv_line_mae=med("hv_line_mae"), hv_line_r2=med("hv_line_r2"), null_mae=null[0], null_r2=null[1], n_photo_days=len(dates))
    print("SUMMARY", summary, flush=True)
    # final model on all photo days -> predicted NDVI on EVERY pass (also the cloudy ones)
    X = np.concatenate([S[x][1] for x in dates]); y = np.concatenate([S[x][2] for x in dates])
    m = HistGradientBoostingRegressor(max_iter=250, max_depth=6, learning_rate=0.08, random_state=0).fit(X, y)
    OUT.mkdir(parents=True, exist_ok=True); series = []
    for p in passes:
        f = F[p["date"]]; ok = p["ok"] & np.isfinite(f).all(-1)
        pred = np.full(ok.shape, np.nan, np.float32); pred[ok] = m.predict(f[ok])
        Image.fromarray(colour(pred, ok), "RGBA").save(OUT / f"ndvi_{p['date']}.png")
        series.append(dict(date=p["date"], mean_ndvi=round(float(np.nanmean(pred)), 3), photo_day=p["date"] in labels))
    (OUT / "ndvi_model.json").write_text(json.dumps(dict(place=PLACE, bbox=bbox, features=FEAT, held_out=rows, summary=summary, series=series,
                                                         test="leave-one-date-out; baselines on the same pixels; shuffled-label control"), indent=1))


if __name__ == "__main__":
    main()
