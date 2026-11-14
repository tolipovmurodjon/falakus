"""Per-pass water outline for the time-lapse: Lee-filtered HH below the chapter's cut-off, keeping only the dark region
connected to the lake (seed point), so hill shadows (separate dark patches) are not drawn. Same grid as the radar frames.
Writes data/waterroad/wl_<stop>_<date>.png (blue fill + white shore line) and prints km2 per pass for a cross-check.
Usage: python tools/water_outlines.py andijan_res 73.10 40.765 -16.75
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_road import lee  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
stop, lon, lat, T = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
d = ROOT / "data/science" / stop
bbox = json.loads((d / "frames.json").read_text())["bbox"]
for f in sorted(d.glob("*.npz")):
    z = np.load(f); hh = z["hh_db"].astype(np.float32); ok = np.isfinite(hh)
    fl = 10 * np.log10(np.maximum(lee(np.where(ok, 10 ** (hh / 10), 0)), 1e-6))
    dark = ok & (fl < T)
    dark = ndimage.binary_opening(dark, iterations=1)
    lab, _ = ndimage.label(dark)
    r = int((bbox[3] - lat) / (bbox[3] - bbox[1]) * hh.shape[0]); c = int((lon - bbox[0]) / (bbox[2] - bbox[0]) * hh.shape[1])
    ys, xs = np.nonzero(lab)
    k = lab[r, c] if lab[r, c] else (lab[ys[np.argmin((ys - r) ** 2 + (xs - c) ** 2)], xs[np.argmin((ys - r) ** 2 + (xs - c) ** 2)]] if ys.size else 0)
    lake = lab == k if k else np.zeros_like(dark)
    lake = ndimage.binary_fill_holes(lake)
    edge = lake & ~ndimage.binary_erosion(lake, iterations=2)
    rgba = np.zeros(hh.shape + (4,), np.uint8)
    rgba[lake] = (37, 99, 235, 90); rgba[edge] = (255, 255, 255, 235)
    Image.fromarray(rgba).save(ROOT / "data/waterroad" / f"wl_{stop}_{f.stem}.png", optimize=True)
    print(f.stem, "lake km2", round(float(lake.sum() * float(z["dx"]) * float(z["dy"]) / 1e6), 1))
