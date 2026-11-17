"""forecast_v3: does bias-corrected Sentinel-1 make ML beat the best baseline at h=1,3,6 months?

Answer key = Sentinel-2 clear months (data/cases/record/andijan_res.json). Walk-forward, expanding window:
at origin month t only data with month <= t is used. Inside each fold, S1 is corrected to S2 units with a
per-season linear fit (S2 ~ a + b*S1) on overlap months <= t; the filled series = S2 where clear, else corrected S1.
Models: persistence (last S2), seasonal naive (S2 same month last year, else last earlier year), climatology
(S2 month mean of training), ridge (S2-only features), ridge+S1, small gradient boosting (+S1).
Claim ML skill at h only if (ML - best baseline) MAE difference has a moving-block bootstrap 95% CI below 0.
"""
import json, sys
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor

PLACE = sys.argv[1] if len(sys.argv) > 1 else "andijan_res"
REC = f"data/cases/record/{PLACE}.json"
OUT = f"data/forecast/{PLACE}_v3.json"
PNG = f"data/forecast/{PLACE}_v3.png"
HZ = [1, 3, 6]
MIN_TRAIN = 24   # minimum training pairs before a fold is scored
SEASON = lambda m: (m % 12) // 3   # DJF, MAM, JJA, SON
rng = np.random.default_rng(0)

d = json.load(open(REC))
def monthly(sensor):
    acc = {}
    for r in d["series"]:
        if r["sensor"] == sensor:
            y, m = int(r["date"][:4]), int(r["date"][5:7])
            acc.setdefault(y * 12 + m - 1, []).append(r["km2"])
    return {k: float(np.mean(v)) for k, v in acc.items()}
S2, S1 = monthly("Sentinel-2"), monthly("Sentinel-1")
T0, T1 = min(min(S1), min(S2)), max(max(S1), max(S2))
lab = lambda k: f"{k // 12}-{k % 12 + 1:02d}"

def fold_data(t):
    """Everything a forecaster standing at month t may use."""
    s2 = {k: v for k, v in S2.items() if k <= t}
    s1 = {k: v for k, v in S1.items() if k <= t}
    coef = {}
    for se in range(4):
        ks = [k for k in s2 if k in s1 and SEASON(k % 12) == se]
        if len(ks) >= 4:
            b, a = np.polyfit([s1[k] for k in ks], [s2[k] for k in ks], 1)
        else:
            ks = [k for k in s2 if k in s1]
            a, b = (np.mean([s2[k] - s1[k] for k in ks]), 1.0) if ks else (-8.1, 1.0)
        coef[se] = (a, b)
    s1c = {k: coef[SEASON(k % 12)][0] + coef[SEASON(k % 12)][1] * v for k, v in s1.items()}
    fill = {**s1c, **s2}
    clim = {}
    for m in range(12):
        v = [x for k, x in s2.items() if k % 12 == m]
        clim[m] = float(np.mean(v)) if v else float(np.mean(list(s2.values())))
    return s2, s1c, fill, clim

def last(series, k, lo=T0):
    while k >= lo:
        if k in series: return k, series[k]
        k -= 1
    return None, None

def baselines(s2, clim, t, tgt):
    _, p = last(s2, t)
    sn = None; k = tgt - 12
    while k >= T0:
        if k in s2 and k <= t: sn = s2[k]; break
        k -= 12
    return {"persistence": p, "seasonal": sn if sn is not None else clim[tgt % 12], "climatology": clim[tgt % 12]}

def feats(s2, s1c, fill, clim, s, tgt, use_s1):
    ks, ls = last(s2, s)
    m = tgt % 12
    f = [ls, ls - clim[ks % 12], clim[m], np.sin(2 * np.pi * m / 12), np.cos(2 * np.pi * m / 12), s - ks]
    if use_s1:
        src = fill
        v0 = last(src, s)[1]; v1 = last(src, s - 1)[1] or v0; v3 = last(src, s - 3)[1] or v0
        f += [v0, v0 - clim[s % 12], v0 - v1, v0 - v3, s1c.get(s, v0)]
    return f

res = {}; preds_all = {}
for h in HZ:
    E = {k: [] for k in ["persistence", "seasonal", "climatology", "ridge_s2", "ridge_s1", "gbr_s1"]}; rows = []
    for t in range(T0 + 12, T1 - h + 1):
        tgt = t + h
        if tgt not in S2: continue
        s2, s1c, fill, clim = fold_data(t)
        if len(s2) < 6: continue
        X0, X1, y = [], [], []
        for tt in sorted(s2):
            s = tt - h
            if tt > t or last(s2, s)[0] is None: continue
            X0.append(feats(s2, s1c, fill, clim, s, tt, False)); X1.append(feats(s2, s1c, fill, clim, s, tt, True)); y.append(s2[tt])
        if len(y) < MIN_TRAIN: continue
        p = baselines(s2, clim, t, tgt)
        f0 = feats(s2, s1c, fill, clim, t, tgt, False); f1 = feats(s2, s1c, fill, clim, t, tgt, True)
        p["ridge_s2"] = float(make_pipeline(StandardScaler(), Ridge(alpha=3.0)).fit(X0, y).predict([f0])[0])
        p["ridge_s1"] = float(make_pipeline(StandardScaler(), Ridge(alpha=3.0)).fit(X1, y).predict([f1])[0])
        p["gbr_s1"] = float(GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8,
                                                      random_state=0).fit(X1, y).predict([f1])[0])
        for k in E: E[k].append(p[k] - S2[tgt])
        rows.append({"origin": lab(t), "target": lab(tgt), "obs": round(S2[tgt], 2), **{k: round(v, 2) for k, v in p.items()}})
    E = {k: np.array(v) for k, v in E.items()}
    mae = {k: float(np.mean(np.abs(v))) for k, v in E.items()}
    best_b = min(["persistence", "seasonal", "climatology"], key=mae.get)
    def ci(model, B=4000, L=6):
        dd = np.abs(E[model]) - np.abs(E[best_b]); n = len(dd); nb = int(np.ceil(n / L))
        st = rng.integers(0, n - L + 1, size=(B, nb))
        idx = (st[:, :, None] + np.arange(L)).reshape(B, -1)[:, :n]
        bs = dd[idx].mean(1)
        return [round(float(dd.mean()), 2), round(float(np.percentile(bs, 2.5)), 2), round(float(np.percentile(bs, 97.5)), 2)]
    diffs = {m: ci(m) for m in ["ridge_s2", "ridge_s1", "gbr_s1"]}
    best_ml = min(diffs, key=lambda m: diffs[m][0])
    band = {m: [round(float(np.percentile(-E[m], 10)), 2), round(float(np.percentile(-E[m], 90)), 2)] for m in diffs}
    res[h] = {"n": len(rows), "mae_km2": {k: round(v, 2) for k, v in mae.items()}, "best_baseline": best_b,
              "diff_vs_best_baseline_mean_ci95": diffs, "best_ml": best_ml,
              "residual_band_80_obs_minus_pred": band, "test": rows}
    preds_all[h] = rows
    print(f"h={h} n={len(rows)}", {k: round(v, 2) for k, v in mae.items()}, "best base", best_b, diffs, flush=True)

claim = {h: bool(res[h]["diff_vs_best_baseline_mean_ci95"][res[h]["best_ml"]][2] < 0) for h in HZ}

# forecast from the latest month with any data
forecast = {}
t = T1
s2, s1c, fill, clim = fold_data(t)
for h in HZ:
    if not claim[h]: continue
    m = res[h]["best_ml"]; use = m != "ridge_s2"
    X, y = [], []
    for tt in sorted(s2):
        s = tt - h
        if last(s2, s)[0] is None: continue
        X.append(feats(s2, s1c, fill, clim, s, tt, use)); y.append(s2[tt])
    f = feats(s2, s1c, fill, clim, t, t + h, use)
    mdl = make_pipeline(StandardScaler(), Ridge(alpha=3.0)) if m.startswith("ridge") else \
        GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)
    v = float(mdl.fit(X, y).predict([f])[0]); lo, hi = res[h]["residual_band_80_obs_minus_pred"][m]
    forecast[h] = {"model": m, "origin": lab(t), "month": lab(t + h), "km2": round(v, 2), "low": round(v + lo, 2), "high": round(v + hi, 2)}

notes = [
    "Targets are Sentinel-2 clear months only; S1 enters only as features, corrected per season (DJF/MAM/JJA/SON linear S2~S1) on overlap months <= origin in every fold.",
    "Best baseline is chosen after the fact on the same test months (favours the baseline); best ML is the lowest-MAE of three ML variants (favours ML) - read the claim with that in mind.",
    "CI = moving-block bootstrap (block 6 months, 4000 reps) of mean paired |error| difference ML - best baseline; negative = ML better.",
    "80% band = 10th..90th percentile of out-of-sample (obs - pred) residuals of that model at that horizon.",
    f"Folds scored only once >= {MIN_TRAIN} training pairs exist; S1 starts {lab(min(S1))}, S2 {lab(min(S2))}.",
]
out = {"place": PLACE, "method": __doc__.strip(), "horizons": {str(h): res[h] for h in HZ},
       "claim": {str(h): claim[h] for h in HZ}, "forecast_next": {str(h): v for h, v in forecast.items()}, "notes": notes}
json.dump(out, open(OUT, "w"), separators=(",", ":"))
print("claim", claim, "forecast", forecast)

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 3, figsize=(10, 3.2), facecolor="#0e1116")
names = ["persistence", "seasonal", "climatology", "ridge_s2", "ridge_s1", "gbr_s1"]
cols = ["#6b7280"] * 3 + ["#60a5fa", "#34d399", "#f59e0b"]
for a, h in zip(ax, HZ):
    a.set_facecolor("#0e1116"); v = [res[h]["mae_km2"][n] for n in names]
    a.barh(names, v, color=cols); a.invert_yaxis()
    for i, x in enumerate(v): a.text(x + 0.1, i, f"{x:.2f}", va="center", color="#d1d5db", fontsize=7)
    a.set_title(f"h={h} mo  n={res[h]['n']}  claim={'YES' if claim[h] else 'no'}", color="#e5e7eb", fontsize=9)
    a.tick_params(colors="#9ca3af", labelsize=7); [s.set_color("#374151") for s in a.spines.values()]
    a.set_xlabel("MAE km²", color="#9ca3af", fontsize=7)
    if h != 1: a.set_yticklabels([])
fig.suptitle("Andijan reservoir: walk-forward MAE vs Sentinel-2 (S1 bias-corrected in-fold)", color="#e5e7eb", fontsize=10)
fig.tight_layout(); fig.savefig(PNG, dpi=110, facecolor=fig.get_facecolor())
