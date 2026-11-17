"""Speckle clean-up for the learned NISAR water map, with an HONEST (nested) choice of the size cut-off.

The learned map (tools/ml_water.py) finds ~94 % of the photo water (median recall 0.94) but also calls small dark
radar blobs on dry land water (speckle, radar shadow). Rule: a water body must be at least C km2 (8-connected pieces
of the map); smaller pieces are dropped.

Why nested: the earlier version fixed C = 0.2 km2 after looking at the held-out IoU of the same 8 days it reported
(test-set tuning, i.e. leakage). Here C is chosen without the scored day:
  for each held-out day d: pick C from GRID that maximises the mean IoU on the OTHER 7 held-out days, apply it to d.
  The reported score (nested_iou) is the median over d of those 8 scores. Ties go to the smaller C.
The raw (no clean-up) IoU and the full sensitivity table (every C on all 8 days) are reported too, so nothing is
hidden. The FINAL MAP (water_clean_<date>.png, the km2 series) uses the C that maximises mean IoU on all 8 days:
that is a map, not a score. The score you quote is nested_iou.

Scoring uses the held-out error maps written by ml_water.py (data/ml/water_err_<date>.png: blue = both say water,
orange = radar only, magenta = photo only), so every score is on a day the model never saw.
Writes data/ml/water_clean.json and data/ml/water_clean_<date>.png (cleaned map for every pass) plus its km2 series.
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
GRID = (0.0, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0)


def clean(mask, min_km2):
    if min_km2 <= 0:
        return mask.copy()
    lab, _ = ndimage.label(mask, structure=np.ones((3, 3)))
    size = np.bincount(lab.ravel())
    keep = np.flatnonzero(size * PX >= min_km2)
    keep = keep[keep > 0]
    return np.isin(lab, keep)


def iou(p, t):
    return float((p & t).sum() / max((p | t).sum(), 1))


def r3(x):
    return round(float(x), 3)


def boot_ci(v, n=10000, seed=0):
    v = np.asarray(v, float)
    rng = np.random.default_rng(seed)
    meds = np.median(v[rng.integers(0, len(v), (n, len(v)))], axis=1)
    return [r3(np.percentile(meds, 2.5)), r3(np.percentile(meds, 97.5))]


def main():
    m = json.loads((ML / "water_model.json").read_text())
    rows, masks = [], []
    for r in m["held_out"]:
        e = np.array(Image.open(ML / f"water_err_{r['date']}.png"))
        a = e[..., 3] > 0
        both = a & (e[..., 0] == 47) & (e[..., 1] == 111)
        extra = a & (e[..., 0] == 234)
        miss = a & (e[..., 0] == 200)
        pred, truth = both | extra, both | miss
        masks.append((pred, truth))
        row = dict(date=r["date"], photo=r["photo"], photo_km2=round(float(truth.sum() * PX), 2), raw_iou=r3(iou(pred, truth)),
                   raw_precision=r3((pred & truth).sum() / pred.sum()), recall=r3((pred & truth).sum() / truth.sum()))
        row["iou_by_cutoff"] = {}
        row["km2_by_cutoff"] = {}
        for c in GRID:
            cm = clean(pred, c)
            row["iou_by_cutoff"][str(c)] = r3(iou(cm, truth))
            row["km2_by_cutoff"][str(c)] = round(float(cm.sum() * PX), 2)
        rows.append(row)

    n = len(rows)
    mat = np.array([[x["iou_by_cutoff"][str(c)] for c in GRID] for x in rows])  # days x cutoffs
    # nested: choose on the other n-1 days
    for i, x in enumerate(rows):
        others = np.delete(mat, i, axis=0).mean(axis=0)
        j = int(np.flatnonzero(others == others.max())[0])  # first = smallest cut-off on ties
        c = GRID[j]
        x["nested_cutoff_km2"] = c
        x["nested_iou"] = r3(mat[i, j])
        x["nested_km2"] = x["km2_by_cutoff"][str(c)]
        x["nested_area_err_km2"] = round(x["nested_km2"] - x["photo_km2"], 2)
    allmean = mat.mean(axis=0)
    final_c = GRID[int(np.flatnonzero(allmean == allmean.max())[0])]

    med = lambda k: r3(np.median([x[k] for x in rows]))
    summary = {
        "nested_iou": med("nested_iou"),
        "nested_iou_mean": r3(np.mean([x["nested_iou"] for x in rows])),
        "nested_cutoffs_chosen": {x["date"]: x["nested_cutoff_km2"] for x in rows},
        "nested_area_mae_km2": round(float(np.mean([abs(x["nested_area_err_km2"]) for x in rows])), 2),
        "nested_area_bias_km2": round(float(np.mean([x["nested_area_err_km2"] for x in rows])), 2),
        "raw_iou": med("raw_iou"),
        "recall": med("recall"),
        "raw_precision": med("raw_precision"),
        "sensitivity_median_iou": {str(c): r3(np.median(mat[:, k])) for k, c in enumerate(GRID)},
        "sensitivity_mean_iou": {str(c): r3(allmean[k]) for k, c in enumerate(GRID)},
        "old_leaky_iou_at_0.2": r3(np.median(mat[:, GRID.index(0.2)])),
        "final_map_cutoff_km2": final_c,
        "final_map_note": "final map; score reported is nested (cut-off for the map chosen on all 8 held-out days)",
        "nested_iou_ci95": boot_ci([x["nested_iou"] for x in rows]),
        "raw_iou_ci95": boot_ci([x["raw_iou"] for x in rows]),
        "ci_method": "percentile bootstrap of the median over the 8 held-out days, 10,000 resamples, seed 0 (per-day scores fixed)",
        "grid_km2": list(GRID),
        "days": n,
    }
    series = []
    for s in m["series"]:
        p = np.array(Image.open(ML / f"water_pred_{s['date']}.png"))
        c = clean(p[..., 3] > 0, final_c)
        rgba = np.zeros(c.shape + (4,), np.uint8)
        rgba[c] = (40, 110, 200, 210)
        Image.fromarray(rgba).save(ML / f"water_clean_{s['date']}.png", optimize=True)
        series.append(dict(date=s["date"], km2=round(float(c.sum() * PX), 2), raw_km2=s["ml_km2"], cutoff_km2=final_c))
    out = dict(method=__doc__.strip(), summary=summary, held_out=rows, series=series)
    (ML / "water_clean.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(summary, indent=1))
    for x in rows:
        print(x["date"], "photo", x["photo_km2"], "cut", x["nested_cutoff_km2"], "iou", x["nested_iou"], "km2", x["nested_km2"], "err", x["nested_area_err_km2"])


if __name__ == "__main__":
    main()
