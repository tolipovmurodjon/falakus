"""'What happened here?' for any box on Earth, from calibrated NISAR GCOV at native 10-20 m.

The server calls run() in a background thread. It finds the NISAR passes over the box centre (one
track/frame, the same rule as the time player), reads only the box from up to 4 passes spread over the
record (first, two middle, last), classifies every pixel (water / built-up / plants / bare, rules in
sar_colors.classify), measures each class in km2, measures the HH change first -> last, cuts 20 m map tiles
of the newest pass, and writes a plain-English summary from those numbers only.
"""
import json
import time
import urllib.request
from pathlib import Path

import numpy as np

import gcov_science
import sar_colors
import science_pyramid

ROOT = Path(__file__).resolve().parent.parent
MAX_HALF_KM = 12.5  # 25 x 25 km at most: about 1-2 minutes per pass over the network


def _pick(frames, n=4):
    if len(frames) <= n:
        return frames
    idx = sorted({0, len(frames) - 1, len(frames) // 3, 2 * len(frames) // 3})
    return [frames[i] for i in idx]


def run(job, w, s, e, n, base="http://127.0.0.1:8765"):
    lon, lat = (w + e) / 2, (s + n) / 2
    half_km = min(MAX_HALF_KM, max(2.0, max((e - w) * 111 * np.cos(np.radians(lat)), (n - s) * 111) / 2))
    job.update(state="finding passes", progress=0.05, lon=lon, lat=lat, box_km=round(2 * half_km, 1))
    with urllib.request.urlopen(f"{base}/api/series.json?lon={lon:.4f}&lat={lat:.4f}", timeout=240) as r:
        series = json.load(r)
    frames = series.get("frames", [])
    if not frames:
        job.update(state="done", progress=1, error="No NISAR pass covers this point yet (NISAR images land, ice and coasts, not the open ocean).")
        return
    pick = _pick(frames)
    import earthaccess
    earthaccess.login(strategy="netrc")
    stop = f"area_{job['id']}"
    out = ROOT / "data" / "science" / stop
    out.mkdir(parents=True, exist_ok=True)
    passes = []
    for k, f in enumerate(pick):
        job.update(state=f"reading pass {k + 1} of {len(pick)} ({f['date']}) from NASA", progress=0.1 + 0.8 * k / len(pick))
        url = f"https://nisar.asf.earthdatacloud.nasa.gov/NISAR/{f['c']}/{f['id']}/{f['id']}.h5"
        try:
            hh, hv, px, meta = gcov_science.read_box(earthaccess.open([url])[0], lon, lat, half_km)
        except Exception as ex:
            passes.append({"date": f["date"], "skipped": str(ex)[:120]})
            continue
        np.savez_compressed(out / f"{f['date']}.npz", hh_db=hh, hv_db=hv if hv is not None else np.array([]), **meta)
        cls = sar_colors.classify(hh, hv)
        km2 = {name: round(float((cls == i).sum() * px / 1e6), 2) for i, name in enumerate(sar_colors.CLASS_NAMES)}
        passes.append({"date": f["date"], "id": f["id"], "res_m": round(meta["dx"]), "km2": km2,
                       "hh_db": round(float(np.nanmedian(hh)), 2),
                       "hv_db": round(float(np.nanmedian(hv)), 2) if hv is not None else None, "_hh": hh})
    good = [p for p in passes if "km2" in p]
    if not good:
        job.update(state="done", progress=1, error="NASA files could not be read for this box (partial frames). Try a point a little inland.")
        return
    first, last = good[0], good[-1]
    h = min(first["_hh"].shape[0], last["_hh"].shape[0]); w_ = min(first["_hh"].shape[1], last["_hh"].shape[1])
    d = last["_hh"][:h, :w_] - first["_hh"][:h, :w_]
    ok = np.isfinite(d)
    px_km2 = (first["res_m"] ** 2) / 1e6
    changed = {"brighter_km2": round(float((d[ok] > 3).sum() * px_km2), 2), "darker_km2": round(float((d[ok] < -3).sum() * px_km2), 2),
               "share_pct": round(float(100 * (np.abs(d[ok]) > 3).mean()), 1) if ok.any() else 0}
    for p in good:
        p.pop("_hh", None)
    job.update(state="cutting 20 m map tiles", progress=0.93)
    science_pyramid.build(stop)
    total = sum(first["km2"].values()) or 1
    share = {k: round(100 * v / total) for k, v in last["km2"].items()}
    main = max(share, key=share.get)
    dw = last["km2"]["water"] - first["km2"]["water"]; dp = last["km2"]["plants"] - first["km2"]["plants"]
    sentence = (f"This {job['box_km']} x {job['box_km']} km box is mostly {main} ({share[main]} %). "
                f"From {first['date']} to {last['date']}, open water went {first['km2']['water']} -> {last['km2']['water']} km2 "
                f"({'+' if dw >= 0 else ''}{dw:.1f}), plant cover {first['km2']['plants']} -> {last['km2']['plants']} km2 "
                f"({'+' if dp >= 0 else ''}{dp:.1f}), and {changed['share_pct']} % of the ground changed brightness by more than 3 dB "
                f"({changed['brighter_km2']} km2 brighter, {changed['darker_km2']} km2 darker).")
    job.update(state="done", progress=1, result={"passes": passes, "changed": changed, "share_pct": share, "sentence": sentence,
               "track": series.get("track"), "res_m": first["res_m"], "stop": stop,
               "method": "NISAR GCOV gamma0 (provisional), calibrated dB; classes by fixed dB rules (sar_colors.classify); change = HH last - first, |change| > 3 dB."})
    job["finished"] = time.time()
