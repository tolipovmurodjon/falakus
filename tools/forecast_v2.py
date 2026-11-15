"""Water forecast from ten years of monthly water: next 30 days and next 3 months, tested on months it never saw.

Record: tools/s2_history.py (Sentinel-2 monthly water, clear months only). For months NISAR saw (Jun 2026 on), the
learned NISAR water map (data/ml/water_model.json) fills cloudy months, scaled to the photo record by the median
ratio on the days both exist, so radar and photo speak the same units.
Models, all predicting month t+h from data up to month t:
  persistence (same as the last month), seasonal (same month last year), climatology (that month's average so far),
  ridge (month cycle sin/cos, last value, last value's anomaly vs its month average, target month's average,
  value 12 months before the target).
Test: walk-forward from Jan 2023 to the last month; each prediction only sees earlier months. Score: mean absolute
error (km²). The 8-in-10 band comes from the model's own test misses (10th and 90th percentile).
Writes data/forecast/<place>_v2.json and prints the table.  Usage: python tools/forecast_v2.py andijan_res
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def months_between(a, b):
    out = []; y, m = map(int, a.split("-")); yb, mb = map(int, b.split("-"))
    while (y, m) <= (yb, mb):
        out.append(f"{y}-{m:02d}"); m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def shift(key, k):
    y, m = map(int, key.split("-")); i = y * 12 + (m - 1) + k
    return f"{i // 12}-{i % 12 + 1:02d}"


def main(place):
    h = json.loads((ROOT / "data/forecast" / f"{place}_s2_monthly.json").read_text())
    series = {k: v["water_km2"] for k, v in h["months"].items() if v["use"] and v["water_km2"] is not None}
    src = {k: "photo" for k in series}
    mlf = ROOT / "data/ml/water_model.json"
    if place == "andijan_res" and mlf.exists():
        ml = json.loads(mlf.read_text())
        ratio = np.median([r["photo_water_km2"] / r["ml_km2"] for r in ml["held_out"] if r["ml_km2"] > 0])
        by_month = {}
        for s in ml["series"]:
            by_month.setdefault(s["date"][:7], []).append(s["ml_km2"])
        for k, v in by_month.items():
            if k not in series:
                series[k] = round(float(np.mean(v)) * ratio, 2); src[k] = "radar"
    keys = months_between(min(series), max(series))

    def clim(month, upto):
        vals = [series[k] for k in series if k[5:] == month and k < upto]
        return float(np.mean(vals)) if vals else None

    def feats(t, target):
        last = series.get(t); c_t = clim(t[5:], t); c_y = clim(target[5:], t); ly = series.get(shift(target, -12), c_y)  # cloudy last year: use that month's average
        if last is None or c_t is None or c_y is None or ly is None:
            return None
        mo = int(target[5:]); return [np.sin(2 * np.pi * mo / 12), np.cos(2 * np.pi * mo / 12), last, last - c_t, c_y, ly]

    from sklearn.linear_model import Ridge
    res = {}
    for hz in (1, 3):
        errs = {"persistence": [], "seasonal": [], "climatology": [], "ridge": []}; rows = []
        for t in keys:
            target = shift(t, hz)
            if target < "2023-01" or target not in series or t not in series:
                continue
            X, y = [], []
            for tt in keys:  # training pairs that end before t
                tg = shift(tt, hz)
                if tg > t or tg not in series:
                    continue
                f = feats(tt, tg)
                if f is not None:
                    X.append(f); y.append(series[tg])
            f = feats(t, target)
            if f is None or len(X) < 24:
                continue
            truth = series[target]
            pred = {"persistence": series[t], "seasonal": series.get(shift(target, -12)), "climatology": clim(target[5:], t),
                    "ridge": float(Ridge(alpha=1.0).fit(np.array(X), np.array(y)).predict([f])[0])}
            for k, v in pred.items():
                if v is not None:
                    errs[k].append(v - truth)
            rows.append({"from": t, "target": target, "truth": truth, **{k: round(v, 2) for k, v in pred.items() if v is not None}})
        mae = {k: round(float(np.mean(np.abs(v))), 2) for k, v in errs.items() if v}
        band = [round(float(np.percentile(errs["ridge"], 10)), 2), round(float(np.percentile(errs["ridge"], 90)), 2)] if errs["ridge"] else None
        res[f"h{hz}"] = {"n_test": len(rows), "mae_km2": mae, "ridge_error_p10_p90": band, "test": rows}
        print(f"horizon {hz} month(s): n={len(rows)} MAE km2", mae, "ridge 80% error band", band, flush=True)
    # forecast from the last month
    last = keys[-1]; fc = []
    for hz in (1, 2, 3):
        target = shift(last, hz); X, y = [], []
        for tt in keys:
            tg = shift(tt, hz)
            if tg in series and tg <= last:
                f = feats(tt, tg)
                if f is not None:
                    X.append(f); y.append(series[tg])
        f = feats(last, target)
        if f is None:
            continue
        v = float(Ridge(alpha=1.0).fit(np.array(X), np.array(y)).predict([f])[0])
        b = res["h1" if hz == 1 else "h3"]["ridge_error_p10_p90"]
        hist = [series[k] for k in series if k[5:] == target[5:]]
        fc.append({"month": target, "km2": round(v, 2), "low": round(v + b[0], 2), "high": round(v + b[1], 2),
                   "typical": round(float(np.mean(hist)), 2), "min": round(min(hist), 2), "max": round(max(hist), 2),
                   "driest_year": min((k for k in series if k[5:] == target[5:]), key=lambda k: series[k])[:4]})
    out = {"place": place, "method": __doc__.split("Writes")[0].strip(), "record_from": keys[0], "record_to": last,
           "n_months": len(series), "n_photo": sum(1 for v in src.values() if v == "photo"), "n_radar": sum(1 for v in src.values() if v == "radar"),
           "series": [{"month": k, "km2": series[k], "from": src[k]} for k in sorted(series)], "skill": res, "forecast": fc}
    for r in fc:
        print("forecast", r, flush=True)
    (ROOT / "data/forecast" / f"{place}_v2.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "andijan_res")
