"""Does the learned water model work at places it never saw? Train on the Andijan reservoir, apply anywhere.

Model and features: tools/ml_water.py (gradient boosting on NISAR HH/HV, texture and the pixel's season history).
Train: all 8 photo-labelled Andijan dates. Apply: every NISAR pass of another place, one pass at a time (memory).
Outside judge at the new place: Sentinel-2 NDWI on its clear days (same rule as before), never used in training.
So the score printed here is a leave-one-PLACE-out test, the hard one.
Writes data/ml/<place>/water_<date>.png and data/ml/<place>/water.json (km² per pass, IoU on photo days).
Usage: python tools/ml_water_transfer.py rogun qoshtepa
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ml_water as mw  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def andijan_model():
    from sklearn.ensemble import HistGradientBoostingClassifier
    mw.PLACE = "andijan_res"; mw.CACHE = ROOT / "data" / "ml" / "s2labels_andijan_res.npz"
    passes = mw.load_passes()
    lon, lat, bbox, _ = mw.grid(passes[0]["z"], passes[0]["hh"].shape)
    labels = mw.s2_labels(passes, lon, lat, bbox)
    F = mw.features(passes)
    rng = np.random.default_rng(0); X, y = [], []
    for d in sorted(labels):
        clear, wet, _ = labels[d]; m = clear & np.isfinite(F[d]).all(-1)
        idx = np.flatnonzero(m.ravel()); yy = wet.ravel()[idx]
        k = min(20000, (yy).sum(), (~yy).sum())
        pick = np.concatenate([rng.choice(idx[yy], k, replace=False), rng.choice(idx[~yy], k, replace=False)])
        X.append(F[d].reshape(-1, len(mw.FEAT))[pick]); y.append(wet.ravel()[pick])
    return HistGradientBoostingClassifier(max_iter=200, max_depth=6, learning_rate=0.08, random_state=0).fit(np.concatenate(X), np.concatenate(y))


def terrain_mask(lon, lat, bbox, max_slope_deg=12):
    """Radar shadow on steep slopes is as dark as water. Like NASA OPERA's water product, rule out ground steeper
    than 12 degrees using the Copernicus 30 m elevation model (Planetary Computer, collection cop-dem-glo-30)."""
    import time
    for attempt in range(6):
        try:
            items = mw.stac({"collections": ["cop-dem-glo-30"], "bbox": bbox, "limit": 8})
            dem = None
            for it in items:
                a = mw.crop("cop-dem-glo-30", it["id"], ["data"], bbox, 1500)[0].astype(np.float32)
                a[a < -1000] = np.nan
                dem = a if dem is None else np.fmax(dem, a)
            break
        except Exception as ex:
            print("dem retry", attempt, str(ex)[:60], flush=True); time.sleep(20); dem = None
    if dem is None:
        print("no elevation model: terrain mask off", flush=True)
        return np.zeros(lon.shape, bool)
    H, W = dem.shape
    dx = (bbox[2] - bbox[0]) / W * 111320 * np.cos(np.radians((bbox[1] + bbox[3]) / 2)); dy = (bbox[3] - bbox[1]) / H * 110540
    gy, gx = np.gradient(np.nan_to_num(dem, nan=np.nanmedian(dem)), dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    steep = mw.sample(slope > max_slope_deg, lon, lat, bbox)
    print(f"terrain mask: {steep.mean() * 100:.0f} % of the box steeper than {max_slope_deg} deg", flush=True)
    return steep


def apply(model, place):
    mw.PLACE = place; mw.CACHE = ROOT / "data" / "ml" / f"s2labels_{place}.npz"
    files = sorted((ROOT / "data" / "science" / place).glob("20*.npz"))
    hhs, oks, used, z0 = [], [], [], None
    for f in files:  # pass 1: the season history of HH only (float16 to keep memory small)
        z = np.load(f); hh = z["hh_db"].astype(np.float32)[::mw.STEP, ::mw.STEP]
        if z0 is None:
            z0 = z
        if hhs and hh.shape != hhs[0].shape:
            continue
        ok = np.isfinite(hh) & np.isfinite(z["hv_db"][::mw.STEP, ::mw.STEP])
        p = mw.lee(np.where(ok, 10 ** (hh / 10), 1e-4))
        hhs.append(np.where(ok, 10 * np.log10(np.maximum(p, 1e-6)), np.nan).astype(np.float16)); oks.append(ok); used.append(f)
    st = np.stack(hhs).astype(np.float32)
    with np.errstate(all="ignore"):
        smin, smed, smax = np.nanmin(st, 0), np.nanmedian(st, 0), np.nanmax(st, 0)
    del st
    lon, lat, bbox, px_km2 = mw.grid(z0, hhs[0].shape)
    steep = terrain_mask(lon, lat, bbox)
    out_dir = ROOT / "data" / "ml" / place; out_dir.mkdir(parents=True, exist_ok=True)
    # photo labels at this place (cached), only to score; the model never trains on them
    lite = []
    for f, ok in zip(used, oks):
        lite.append(dict(date=f.stem[:10], ok=ok))
    try:
        labels = mw.s2_labels(lite, lon, lat, bbox)
    except Exception as ex:
        print("labels failed", ex); labels = {}
    rows = []
    for i, f in enumerate(used):
        z = np.load(f); d = f.stem[:10]
        hv = z["hv_db"].astype(np.float32)[::mw.STEP, ::mw.STEP]; ok = oks[i]
        phv = mw.lee(np.where(ok, 10 ** (hv / 10), 1e-4)); hvf = 10 * np.log10(np.maximum(phv, 1e-6))
        hh = hhs[i].astype(np.float32)
        X = np.stack([hh, hvf, hh - hvf, mw.local_std(np.nan_to_num(hh), 5), mw.local_std(np.nan_to_num(hh), 11), mw.local_std(hvf, 5), smin, smed, smax, hh - smed], -1)
        m = ok & np.isfinite(X).all(-1)
        pr = np.zeros(m.shape, bool); pr[m] = model.predict(X[m])
        pr &= ~steep
        rgba = np.zeros(m.shape + (4,), np.uint8); rgba[pr] = (40, 110, 200, 210)
        Image.fromarray(rgba).save(out_dir / f"water_{d}.png")
        r = dict(date=d, ml_km2=round(float(pr.sum() * px_km2), 2))
        if d in labels:
            clear, wet, s2day = labels[d]; mm = m & clear; ph = wet & mm; u = (pr & mm | ph).sum()
            r.update(photo=s2day, photo_water_km2=round(float(ph.sum() * px_km2), 2), ml_in_clear_km2=round(float((pr & mm).sum() * px_km2), 2),
                     iou=round(float((pr & mm & ph).sum() / u), 3) if u else None)
        rows.append(r); print(place, r, flush=True)
        del X
    ious = [r["iou"] for r in rows if r.get("iou") is not None]
    out = dict(place=place, trained_on="andijan_res (8 photo days)", test="leave-one-place-out: this place never used in training",
               bbox=bbox, passes=rows, median_iou=round(float(np.median(ious)), 3) if ious else None, n_photo_days=len(ious))
    (out_dir / "water.json").write_text(json.dumps(out, indent=1))
    print(place, "median IoU on unseen place:", out["median_iou"], "photo days", len(ious), flush=True)


if __name__ == "__main__":
    model = andijan_model()
    for p in sys.argv[1:]:
        apply(model, p)
