"""Render science-mode passes (calibrated dB boxes) into map images at full 20 m resolution.

Usage: python science_render.py <stop_id> <lon> <lat> [--km 15]
Reads data/science/<stop>/<date>.npz, writes data/science/<stop>/img/<date>_{rgb,hh,hv}.webp,
<date>_change.webp (vs the first pass) and data/science/<stop>/frames.json.
Colours: rgb = R HH (-22..-5 dB), G HV (-28..-12 dB), B HH/HV ratio (0..12 dB), the UAVSAR postcard idea:
water dark, cities white-pink, forests and crops green, bare soil blue-magenta.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def scale(a, lo, hi):
    return np.clip((np.nan_to_num(a, nan=lo) - lo) / (hi - lo), 0, 1)


def save(arr, alpha, path):
    rgba = np.dstack([arr, (alpha * 255).astype(np.uint8)])
    im = Image.fromarray(rgba, "RGBA")
    if max(im.size) > 4096:  # keeps big boxes fast to load; 100 km stays at ~25 m per pixel
        im.thumbnail((4096, 4096), Image.LANCZOS)
    im.save(path, "WEBP", quality=85, method=3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stop"); ap.add_argument("lon", type=float); ap.add_argument("lat", type=float)
    ap.add_argument("--km", type=float, default=15)
    a = ap.parse_args()
    d = ROOT / "data" / "science" / a.stop
    img = d / "img"; img.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in d.glob("*.npz"))
    if not files:
        print("no passes"); return
    dlat = a.km / 111.0
    dlon = a.km / (111.0 * math.cos(math.radians(a.lat)))
    bbox = [a.lon - dlon, a.lat - dlat, a.lon + dlon, a.lat + dlat]
    first = None
    frames = []
    global RES
    RES = 20
    for f in files:
        z = np.load(f)
        hh, hv = z["hh_db"], z["hv_db"]
        ok = np.isfinite(hh).astype(np.float32)
        date = f.stem
        RES = round(2 * a.km * 1000 / hh.shape[1])
        g = (scale(hh, -25, -3) * 255).astype(np.uint8)
        save(np.dstack([g, g, g]), ok, img / f"{date}_hh.webp")
        if hv.size:
            r = scale(hh, -22, -5); gg = scale(hv, -28, -12); b = scale(hh - hv, 0, 12)
            save((np.dstack([r, gg, b]) * 255).astype(np.uint8), ok, img / f"{date}_rgb.webp")
            v = scale(hv, -28, -12)
            save((np.dstack([v * 120, 40 + v * 215, v * 60])).astype(np.uint8), ok, img / f"{date}_hv.webp")
        if first is None:
            first = hh
        else:
            h = min(first.shape[0], hh.shape[0]); w = min(first.shape[1], hh.shape[1])
            diff = hh[:h, :w] - first[:h, :w]  # dB log-ratio vs the first pass
            mag = np.clip(np.abs(np.nan_to_num(diff)) / 6, 0, 1)
            up = diff > 0
            col = np.zeros((h, w, 3), np.uint8)
            col[..., 0] = np.where(up, 255, 40); col[..., 1] = np.where(up, 80, 120); col[..., 2] = np.where(up, 40, 255)
            save(col, np.where(np.abs(np.nan_to_num(diff)) > 3, mag, 0), img / f"{date}_change.webp")
        frames.append({"date": date, "sci": True, "bbox": bbox, "res": RES})
    (d / "frames.json").write_text(json.dumps({"stop": a.stop, "bbox": bbox, "resolution_m": RES, "frames": frames}, indent=1))
    print(f"{a.stop}: {len(frames)} passes rendered at 20 m -> {img}")


if __name__ == "__main__":
    main()
