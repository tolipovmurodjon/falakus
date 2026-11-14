"""HV (plant echo) change map between two NISAR passes, on the same grid the app draws, for the Fergana chapter.

HV power is averaged over 5 x 5 pixels (100 m) to calm the speckle, then the change in dB:
red = HV fell by more than 2 dB (leaves and stems gone: harvest), green = rose by more than 2 dB (growth), clear = less than 2 dB.
Prints the share of the box in each class. Usage: python tools/hv_change.py fergana 2026-07-02 2026-10-30
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
stop, a, b = sys.argv[1:4]
d = ROOT / "data" / "science" / stop
za, zb = np.load(d / f"{a}.npz"), np.load(d / f"{b}.npz")
ha, hb = za["hv_db"].astype(np.float32), zb["hv_db"].astype(np.float32)
h, w = min(ha.shape[0], hb.shape[0]), min(ha.shape[1], hb.shape[1]); ha, hb = ha[:h, :w], hb[:h, :w]
ok = np.isfinite(ha) & np.isfinite(hb)
pa = ndimage.uniform_filter(np.where(ok, 10 ** (ha / 10), 0), 5); pb = ndimage.uniform_filter(np.where(ok, 10 ** (hb / 10), 0), 5)
diff = 10 * np.log10(np.maximum(pb, 1e-6) / np.maximum(pa, 1e-6))
fell, rose = ok & (diff < -2), ok & (diff > 2)
rgba = np.zeros((h, w, 4), np.uint8)
rgba[fell] = (192, 57, 43, 210); rgba[rose] = (107, 142, 61, 210)
out = ROOT / "data" / "waterroad" / f"{stop}_hvchange.png"
Image.fromarray(rgba).save(out, optimize=True)
res = {"from": a, "to": b, "fell_pct": round(float(fell.sum() / ok.sum() * 100), 1), "rose_pct": round(float(rose.sum() / ok.sum() * 100), 1),
       "median_change_db": round(float(np.median(diff[ok])), 2), "pixel_m": 20, "smoothing_m": 100}
(ROOT / "data" / "waterroad" / f"{stop}_hvchange.json").write_text(json.dumps(res, indent=1)); print(res)
