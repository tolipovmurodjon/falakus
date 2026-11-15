"""Water-frequency heatmap: how often each spot of the Andijan reservoir was open water across every NISAR pass.

Reads the learned water maps (data/ml/water_pred_<date>.png, written by tools/ml_water.py; water = alpha > 0) and
data/ml/water_model.json (dates, bbox, km2 per pass). Writes:
  data/ml/water_freq.png   RGBA heatmap on the same grid: deep blue = water on every pass, through teal and yellow to
                           orange = water on only a few passes (the shore that dried out); never-water is transparent.
  data/ml/water_freq.json  bbox, number of passes, pixel area, and km2 per frequency band.
Only water connected to an always-wet core of at least 0.16 km2 is kept (scattered one-pass speckle on dry land is dropped and counted).
Pixel area is checked, not assumed: the model's own km2 per pass must give 40 m x 40 m pixels, and the bbox must agree within 10 %.
Usage: python tools/water_frequency.py
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ML = ROOT / "data" / "ml"

# heat ramp: few passes (warm, the drying shore) -> every pass (deep water blue)
STOPS = [(0.0, (245, 166, 35)), (0.35, (233, 216, 76)), (0.6, (94, 196, 182)), (0.85, (47, 111, 209)), (1.0, (20, 58, 140))]


def ramp(t):
    xs = [s[0] for s in STOPS]
    return np.stack([np.interp(t, xs, [s[1][k] for s in STOPS]) for k in range(3)], -1)


def main():
    m = json.loads((ML / "water_model.json").read_text())
    dates = [s["date"] for s in m["series"]]
    km2 = {s["date"]: s["ml_km2"] for s in m["series"]}
    masks = [np.array(Image.open(ML / f"water_pred_{d}.png"))[..., 3] > 0 for d in dates]
    n = len(masks)
    cnt = np.sum(masks, axis=0)
    raw_ever = int((cnt > 0).sum())
    # keep the lake only: connected pieces (8-neighbour) that touch water seen on every pass; drops radar
    # speckle on dry hills that one pass called water
    from scipy import ndimage
    lab, _ = ndimage.label(cnt > 0, structure=np.ones((3, 3)))
    core = np.bincount(lab[(cnt == n)].ravel(), minlength=lab.max() + 1)
    keep = np.flatnonzero(core >= 100)  # >= 0.16 km2 of always-water: a real water body, not a dark hillside
    keep = keep[keep > 0]
    cnt = np.where(np.isin(lab, keep), cnt, 0)
    h, w = cnt.shape
    # pixel area two ways
    w0, s0, e0, n0 = m["bbox"]
    lat = math.radians((s0 + n0) / 2)
    px_bbox = ((e0 - w0) * 111.32 * math.cos(lat) / w) * ((n0 - s0) * 110.57 / h)
    px_model = float(np.median([km2[d] / max(mk.sum(), 1) for d, mk in zip(dates, masks)]))
    # the maps are on a 40 m UTM grid (0.0016 km2); the lon/lat bbox is that grid's slightly larger envelope (~8 %)
    if abs(px_model / 0.0016 - 1) > 0.01 or abs(px_bbox / px_model - 1) > 0.10:
        raise SystemExit(f"pixel area mismatch: bbox {px_bbox:.6f} vs model {px_model:.6f} km2")
    px = px_model
    t = np.where(cnt > 0, (cnt - 1) / max(n - 1, 1), 0)
    rgb = ramp(t).astype(np.uint8)
    a = np.where(cnt > 0, 150 + 90 * t, 0).astype(np.uint8)
    Image.fromarray(np.dstack([rgb, a]), "RGBA").save(ML / "water_freq.png", optimize=True)
    bands = {
        "every_pass": int((cnt == n).sum()),
        "most_passes": int(((cnt >= math.ceil(n / 2)) & (cnt < n)).sum()),
        "few_passes": int(((cnt > 0) & (cnt < math.ceil(n / 2))).sum()),
        "ever": int((cnt > 0).sum()),
        "dropped_speckle": raw_ever - int((cnt > 0).sum()),
    }
    out = {
        "place": "andijan_res", "bbox": m["bbox"], "passes": n, "first": dates[0], "last": dates[-1],
        "pixel_km2": round(px, 6), "pixel_km2_from_bbox": round(px_bbox, 6),
        "km2": {k: round(v * px, 1) for k, v in bands.items()},
        "half": math.ceil(n / 2),
        "method": "Learned NISAR water maps (tools/ml_water.py), one per pass; count how many passes call each pixel water.",
    }
    (ML / "water_freq.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
