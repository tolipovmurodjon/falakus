"""Machine-learned land cover from NISAR time series, tested honestly against ESA WorldCover.

Features per 20 m pixel (from every calibrated pass of a place): mean, std, min, max of HH dB; mean and std of HV dB;
mean HH-HV ratio (dB). Labels: ESA WorldCover 2021 (10 m, independent optical+radar map), via Microsoft Planetary
Computer (no login), grouped into 5 classes. Model: Random Forest. Test: leave-one-place-out (train on all other
places, test on a place never seen), compared with the fixed dB rules in sar_colors.classify.

Usage: python ml_landcover.py [place ...]      (default: every science place with >= 3 passes)
Writes data/ml/landcover_results.json and data/ml/<place>_pred.npz (predicted classes, small).
"""
import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sar_colors  # noqa: E402
from utm_convert import utm_to_lonlat  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCI = ROOT / "data" / "science"
OUT = ROOT / "data" / "ml"
CLASSES = ["water", "built", "trees", "crops & grass", "bare"]
WC = {80: 0, 90: 0, 50: 1, 10: 2, 95: 2, 20: 3, 30: 3, 40: 3, 100: 3, 60: 4, 70: 4}  # WorldCover code -> our class
STEP = 3  # sample every 3rd pixel (60 m) to keep it light


def worldcover(bbox):
    w, s, e, n = bbox
    body = {"collections": ["esa-worldcover"], "bbox": bbox, "limit": 5}
    req = urllib.request.Request("https://planetarycomputer.microsoft.com/api/stac/v1/search", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    items = json.load(urllib.request.urlopen(req, timeout=90))["features"]
    items = sorted(items, key=lambda f: f["properties"].get("esa_worldcover:product_version", ""), reverse=True)
    grid = None
    for it in items:
        url = (f"https://planetarycomputer.microsoft.com/api/data/v1/item/bbox/{w},{s},{e},{n}.npy"
               f"?collection=esa-worldcover&item={it['id']}&assets=map&max_size=2048&resampling=nearest")
        a = np.load(io.BytesIO(urllib.request.urlopen(url, timeout=180).read()))
        v = a[0]; m = a[-1] > 0 if a.shape[0] > 1 else v > 0
        grid = np.where(m, v, 0) if grid is None else np.where(grid > 0, grid, np.where(m, v, 0))
    return grid


def place_samples(place):
    files = sorted((SCI / place).glob("*.npz"))
    stack_hh, stack_hv, meta = [], [], None
    for f in files:
        z = np.load(f)
        if "x0" not in z.files or not z["hv_db"].size:
            continue
        stack_hh.append(z["hh_db"][::STEP, ::STEP].astype(np.float32)); stack_hv.append(z["hv_db"][::STEP, ::STEP].astype(np.float32))
        meta = {k: float(z[k]) for k in ("x0", "y0", "dx", "dy", "zone", "south")}
    if len(stack_hh) < 3:
        return None
    hh = np.stack(stack_hh); hv = np.stack(stack_hv)
    with np.errstate(all="ignore"):
        feats = np.stack([np.nanmean(hh, 0), np.nanstd(hh, 0), np.nanmin(hh, 0), np.nanmax(hh, 0),
                          np.nanmean(hv, 0), np.nanstd(hv, 0), np.nanmean(hh - hv, 0)], -1)
    ny, nx = feats.shape[:2]
    xs = meta["x0"] + (np.arange(nx) * STEP + 0.5) * meta["dx"]
    ys = meta["y0"] - (np.arange(ny) * STEP + 0.5) * meta["dy"]
    X, Y = np.meshgrid(xs, ys)
    lon, lat = utm_to_lonlat(X, Y, int(meta["zone"]), bool(meta["south"]))
    bbox = [float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max())]
    wc = worldcover(bbox)
    H, W = wc.shape
    ci = np.clip(((lon - bbox[0]) / (bbox[2] - bbox[0]) * W).astype(int), 0, W - 1)
    ri = np.clip(((bbox[3] - lat) / (bbox[3] - bbox[1]) * H).astype(int), 0, H - 1)
    lab = np.vectorize(lambda c: WC.get(int(c), -1))(wc[ri, ci])
    rule = sar_colors.classify(np.nanmean(hh, 0), np.nanmean(hv, 0))  # 0 water,1 built,2 plants,3 bare
    rule5 = np.select([rule == 0, rule == 1, rule == 2, rule == 3], [0, 1, 3, 4], -1)  # plants -> crops&grass (rules cannot split trees)
    ok = np.isfinite(feats).all(-1) & (lab >= 0)
    return {"X": feats[ok], "y": lab[ok], "rule": rule5[ok], "shape": (ny, nx), "ok": ok, "feats": feats, "passes": len(stack_hh), "bbox": bbox}


def scores(y, p):
    acc = float((y == p).mean())
    k = len(CLASSES); cm = np.zeros((k, k), int)
    for a, b in zip(y, p):
        if 0 <= a < k and 0 <= b < k:
            cm[a, b] += 1
    f1 = {}
    for i, c in enumerate(CLASSES):
        tp = cm[i, i]; fp = cm[:, i].sum() - tp; fn = cm[i, :].sum() - tp
        f1[c] = round(2 * tp / max(2 * tp + fp + fn, 1), 3) if cm[i, :].sum() else None
    pe = (cm.sum(0) * cm.sum(1)).sum() / max(cm.sum() ** 2, 1)
    kappa = (acc - pe) / max(1 - pe, 1e-9)
    return {"accuracy": round(acc, 3), "kappa": round(float(kappa), 3), "f1": f1, "n": int(len(y)), "confusion": cm.tolist()}


def main():
    from sklearn.ensemble import RandomForestClassifier
    places = sys.argv[1:] or sorted(p.name for p in SCI.iterdir() if p.is_dir() and not p.name.startswith("area_"))
    data = {}
    for pl in places:
        try:
            d = place_samples(pl)
        except Exception as ex:
            print(f"{pl}: skipped ({ex})", flush=True); continue
        if d:
            data[pl] = d
            print(f"{pl}: {len(d['y'])} labelled pixels, {d['passes']} passes, classes {np.bincount(d['y'], minlength=5).tolist()}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"classes": CLASSES, "features": ["HH mean", "HH std", "HH min", "HH max", "HV mean", "HV std", "HH-HV mean"],
           "labels": "ESA WorldCover 2021 v200 (10 m), grouped", "test": "leave-one-place-out", "places": {}}
    rng = np.random.default_rng(0)
    for test in data:
        tr = [p for p in data if p != test]
        if not tr:
            continue
        Xtr = np.concatenate([data[p]["X"] for p in tr]); ytr = np.concatenate([data[p]["y"] for p in tr])
        if len(ytr) > 120000:
            idx = rng.choice(len(ytr), 120000, replace=False); Xtr, ytr = Xtr[idx], ytr[idx]
        rf = RandomForestClassifier(n_estimators=80, max_depth=16, min_samples_leaf=3, n_jobs=2, class_weight="balanced_subsample", random_state=0)
        rf.fit(Xtr, ytr)
        d = data[test]; pred = rf.predict(d["X"])
        res["places"][test] = {"ml": scores(d["y"], pred), "rules": scores(d["y"], d["rule"]), "trained_on": tr, "passes": d["passes"]}
        full = np.full(d["shape"], -1, np.int8); full[d["ok"]] = pred
        np.savez_compressed(OUT / f"{test}_pred.npz", pred=full, bbox=np.array(d["bbox"]), step_m=STEP * 20)
        r = res["places"][test]
        print(f"TEST {test:10s} ML acc {r['ml']['accuracy']:.2f} kappa {r['ml']['kappa']:.2f} | rules acc {r['rules']['accuracy']:.2f} kappa {r['rules']['kappa']:.2f}", flush=True)
        if test == list(data)[-1]:
            res["feature_importance"] = dict(zip(res["features"], [round(float(v), 3) for v in rf.feature_importances_]))
    (OUT / "landcover_results.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
