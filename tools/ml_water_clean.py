"""Speckle clean-up for the learned NISAR water map, scored on the same held-out days.

The learned map (tools/ml_water.py) finds ~94 % of the photo water (median recall 0.94) but also calls small dark
radar blobs on dry land water (speckle, radar shadow). Rule, fixed in advance and using no labels: a water body must
be at least MIN_KM2 (8-connected pieces of the map). Smaller pieces are dropped.

Scoring uses the held-out error maps written by ml_water.py (data/ml/water_err_<date>.png: blue = both say water,
orange = radar only, magenta = photo only), so every score is still on a day the model never saw. Thresholds 0.05,
0.2 and 1 km2 are all reported, so the choice is visible. Writes data/ml/water_clean.json and
data/ml/water_clean_<date>.png (cleaned map for every pass) plus its km2 series.
Usage: python tools/ml_water_clean.py
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
ML = ROOT / "data" / "ml"
PX = 0.0016  # 40 m x 40 m pixels (km2)
MIN_KM2 = 0.2
TESTS = (0.05, 0.2, 1.0)


def clean(mask, min_km2):
    lab, _ = ndimage.label(mask, structure=np.ones((3, 3)))
    size = np.bincount(lab.ravel())
    keep = np.flatnonzero(size * PX >= min_km2)
    keep = keep[keep > 0]
    return np.isin(lab, keep)


def iou(p, t):
    return float((p & t).sum() / max((p | t).sum(), 1))


def main():
    m = json.loads((ML / "water_model.json").read_text())
    rows = []
    for r in m["held_out"]:
        e = np.array(Image.open(ML / f"water_err_{r['date']}.png"))
        a = e[..., 3] > 0
        both = a & (e[..., 0] == 47) & (e[..., 1] == 111)
        extra = a & (e[..., 0] == 234)
        miss = a & (e[..., 0] == 200)
        pred, truth = both | extra, both | miss
        row = dict(date=r["date"], photo=r["photo"], photo_km2=round(float(truth.sum() * PX), 2), raw_iou=round(iou(pred, truth), 3),
                   raw_precision=round(float((pred & truth).sum() / pred.sum()), 3), recall=round(float((pred & truth).sum() / truth.sum()), 3))
        for t in TESTS:
            c = clean(pred, t)
            row[f"iou_{t}"] = round(iou(c, truth), 3)
            if t == MIN_KM2:
                row["clean_km2"] = round(float(c.sum() * PX), 2)
                row["clean_area_err_km2"] = round(float(c.sum() * PX - truth.sum() * PX), 2)
        rows.append(row)
    med = lambda k: round(float(np.median([x[k] for x in rows])), 3)
    summary = {"raw_iou": med("raw_iou"), "clean_iou": med(f"iou_{MIN_KM2}"), "recall": med("recall"), "raw_precision": med("raw_precision"),
               "sensitivity": {str(t): med(f"iou_{t}") for t in TESTS},
               "clean_area_mae_km2": round(float(np.mean([abs(x["clean_area_err_km2"]) for x in rows])), 2), "min_km2": MIN_KM2, "days": len(rows)}
    series = []
    for s in m["series"]:
        p = np.array(Image.open(ML / f"water_pred_{s['date']}.png"))
        c = clean(p[..., 3] > 0, MIN_KM2)
        rgba = np.zeros(c.shape + (4,), np.uint8)
        rgba[c] = (40, 110, 200, 210)
        Image.fromarray(rgba).save(ML / f"water_clean_{s['date']}.png", optimize=True)
        series.append(dict(date=s["date"], km2=round(float(c.sum() * PX), 2), raw_km2=s["ml_km2"]))
    out = dict(method=__doc__.strip(), summary=summary, held_out=rows, series=series)
    (ML / "water_clean.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(summary, indent=1))
    for x in rows:
        print(x["date"], "photo", x["photo_km2"], "clean", x["clean_km2"], "err", x["clean_area_err_km2"])


if __name__ == "__main__":
    main()
