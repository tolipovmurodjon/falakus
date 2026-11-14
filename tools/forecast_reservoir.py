"""Forecast the Andijan reservoir's water area 1-3 months ahead, and prove it against baselines on months it never saw.

Data: one value per month, Nov 2023 -> Nov 2026. Truth = Sentinel-2 photo water (clear, snow masked) when that month has
a clear photo; otherwise the Sentinel-1 radar water corrected by the photo-vs-radar fit of the SAME calendar season
(the radar over-counts drained mud in autumn). Each month is tagged photo / radar so the chart can show it.
Models, all walk-forward one step ahead over Jan-Nov 2026 (never trained on the month they predict):
  persistence = last month, seasonal = same month last year, ridge = month-of-year (sin, cos) + last month + same month last year.
Writes data/forecast/andijan_res.json.  Usage: python tools/forecast_reservoir.py
"""
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
M = json.loads((ROOT / "data/s1series/andijan_res.json").read_text())["months"]

# radar -> photo correction per season (fit on months that have both)
pairs = [(m["water_km2"], m["s2_water_km2"], int(m["month"][5:])) for m in M if m.get("s2_water_km2") is not None]
season = lambda mo: 0 if mo in (3, 4, 5, 6, 7) else 1  # fill season / drawdown+winter
corr = {}
for sz in (0, 1):
    p = np.array([(a, b) for a, b, mo in pairs if season(mo) == sz])
    corr[sz] = np.polyfit(p[:, 0], p[:, 1], 1) if len(p) >= 4 else np.array([1.0, 0.0])
series = []
for m in M:
    mo = int(m["month"][5:])
    if m.get("s2_water_km2") is not None:
        series.append((m["month"], m["s2_water_km2"], "photo"))
    else:
        a, b = corr[season(mo)]
        series.append((m["month"], round(float(a * m["water_km2"] + b), 2), "radar"))
months = [s[0] for s in series]; y = np.array([s[1] for s in series])


def feats(i):
    mo = int(months[i][5:])
    return [math.sin(2 * math.pi * mo / 12), math.cos(2 * math.pi * mo / 12), y[i - 1], y[i - 12]]


def ridge(X, t, lam=1.0):
    X = np.c_[np.ones(len(X)), X]; I = np.eye(X.shape[1]); I[0, 0] = 0
    return np.linalg.solve(X.T @ X + lam * I, X.T @ t)


test = [i for i, m in enumerate(months) if m >= "2026-01"]
err = {"persistence": [], "seasonal": [], "ridge": []}; rows = []
for i in test:
    tr = [k for k in range(12, i)]
    w = ridge(np.array([feats(k) for k in tr]), y[tr])
    pr = float(w[0] + np.dot(w[1:], feats(i)))
    rows.append({"month": months[i], "truth": float(y[i]), "truth_from": series[i][2], "ridge": round(pr, 2), "persistence": float(y[i - 1]), "seasonal": float(y[i - 12])})
    for k, v in (("persistence", y[i - 1]), ("seasonal", y[i - 12]), ("ridge", pr)):
        err[k].append(abs(v - y[i]))
mae = {k: round(float(np.mean(v)), 2) for k, v in err.items()}
# forecast 3 months ahead, recursive, error band = test MAE grown with horizon
w = ridge(np.array([feats(k) for k in range(12, len(y))]), y[12:])
ext_m, ext_y = list(months), list(y); fc = []
for h in range(1, 4):
    yy, mm = int(ext_m[-1][:4]), int(ext_m[-1][5:]) + 1
    if mm == 13:
        yy, mm = yy + 1, 1
    nm = f"{yy}-{mm:02d}"; ext_m.append(nm)
    f = [math.sin(2 * math.pi * mm / 12), math.cos(2 * math.pi * mm / 12), ext_y[-1], ext_y[-12]]
    v = float(w[0] + np.dot(w[1:], f)); ext_y.append(v)
    fc.append({"month": nm, "km2": round(v, 1), "band_km2": round(mae["ridge"] * math.sqrt(h), 1)})
out = {"method": __doc__.split("Writes")[0].strip(), "season_correction": {str(k): [round(float(x), 3) for x in v] for k, v in corr.items()},
       "series": [{"month": a, "km2": b, "from": c} for a, b, c in series], "test": rows, "mae_km2": mae, "forecast": fc,
       "beats_baselines": mae["ridge"] < min(mae["persistence"], mae["seasonal"])}
(ROOT / "data/forecast").mkdir(parents=True, exist_ok=True)
(ROOT / "data/forecast/andijan_res.json").write_text(json.dumps(out, indent=1))
print("MAE km2 on Jan-Nov 2026 (never trained on):", mae, "| beats both baselines:", out["beats_baselines"])
for r in rows: print(" ", r)
print("forecast:", fc)
