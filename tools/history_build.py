"""Then-vs-now radar pairs and radar time series: CSA RADARSAT-1 (1996-2013, C-band HH) vs NISAR 2026 (NASA GIBS).

Outputs (served by the local server through the web/cases -> data/cases symlink):
  data/cases/history/<place>_rs1_<date>.jpg, <place>_nisar_<date>.jpg, <place>_meta.json
  data/cases/history/<place>_series.json  (with --series)

RADARSAT-1: tools/rs1_fetch.py search + warp (open S3 COG, GCP thin-plate spline to EPSG:4326). All frames from the
same day that touch the box are warped and merged. Grey = 20*log10(DN) with one fixed stretch per place (relative dB,
uncalibrated, so beams differ somewhat in brightness). NISAR: tools/history_gibs.py, R channel (HH display scale).

Usage: python tools/history_build.py <place> W S E N [--series] [--width 1400] [--dates 1997-07-16,...]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import box, shape
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rs1_fetch import BUCKET, s3_key, search, warp_box  # noqa: E402
from history_gibs import best_nisar  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "cases" / "history"


def rs1_day(items, bbox, width):
    """Warp every frame of one day over the box and merge (first valid pixel wins)."""
    acc, used = None, []
    for it in items:
        key = s3_key(it)
        try:
            dn, tags = warp_box(f"{BUCKET}/{key}", bbox, width)
        except SystemExit as e:
            print("   skip", key, e)
            continue
        acc = dn if acc is None else np.where(np.isfinite(acc), acc, dn)
        used.append(key)
    return acc, used


def to_jpg(grey_f, valid, path):
    g = np.where(valid, np.clip(grey_f, 0, 255), 0).astype("uint8")
    Image.fromarray(g, "L").save(path, quality=88, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("place")
    ap.add_argument("bbox", nargs=4, type=float)
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--series", action="store_true", help="all years 1996-2013, else only the earliest good day")
    ap.add_argument("--min-cov", type=float, default=60)
    ap.add_argument("--dates", help="comma list of RS1 dates to use (overrides auto pick)")
    ap.add_argument("--stretch", nargs=2, type=float)
    ap.add_argument("--nisar-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    B = box(*a.bbox)
    items = []
    for y0, y1 in [(1996, 2000), (2001, 2006), (2007, 2013)]:
        items += search(a.bbox, f"{y0}-01-01", f"{y1}-12-31")
    days = {}
    for it in items:
        d = it["properties"]["datetime"][:10]
        days.setdefault(d, []).append(it)
    cov = {d: unary_union([shape(i["geometry"]) for i in its]).intersection(B).area / B.area * 100
           for d, its in days.items()}
    good = sorted(d for d in days if cov[d] >= a.min_cov)
    if a.dates:
        good = a.dates.split(",")
    elif not a.series:
        good = good[:1]
    else:  # one per year: best coverage, then earliest
        per = {}
        for d in good:
            y = d[:4]
            if y not in per or cov[d] > cov[per[y]] + 5:
                per[y] = d
        good = sorted(per.values())
    print("RS1 days:", [(d, round(cov[d]), days[d][0]["properties"]["beam_mnemonic"]) for d in good])
    frames, stretch = [], a.stretch
    prev = OUT / (f"{a.place}_series.json" if a.series else f"{a.place}_meta.json")
    if a.nisar_only and prev.exists():  # keep the RADARSAT-1 frames already written, redo only NISAR
        old = json.loads(prev.read_text())
        frames = [fr for fr in old["frames"] if fr["sensor"].startswith("RADARSAT")]
        stretch, good = old["rs1_stretch_db"], []
    for d in good:
        dn, used = rs1_day(days[d], a.bbox, a.width)
        if dn is None:
            continue
        db = 20 * np.log10(dn)
        valid = np.isfinite(db)
        if valid.mean() < 0.3:
            print("  ", d, "too little coverage", valid.mean())
            continue
        if stretch is None:  # fixed per place, from the first (earliest) frame
            stretch = [float(v) for v in np.percentile(db[valid], [2, 98])]
        lo, hi = stretch
        f = f"{a.place}_rs1_{d}.jpg"
        to_jpg((db - lo) / (hi - lo) * 255, valid, OUT / f)
        p = days[d][0]["properties"]
        frames.append(dict(date=d, sensor="RADARSAT-1 (CSA), C-band HH", file=f, beam=p["beam_mnemonic"],
                           orbit=p.get("sat:orbit_state"), scenes=[f"s3://radarsat-r1-l1-cog/{k}" for k in used],
                           coverage_pct=round(float(valid.mean()) * 100, 1)))
        print("  wrote", f, frames[-1]["coverage_pct"], "%")
    r, valid, info = best_nisar(a.bbox, a.width)
    vals = r[valid]
    lo, hi = np.percentile(vals, [2, 98])
    f = f"{a.place}_nisar_{info['date']}.jpg"
    to_jpg((r - lo) / (hi - lo) * 255, valid, OUT / f)
    frames.append(dict(date=info["date"], sensor="NISAR (NASA-ISRO), L-band, NASA GIBS", file=f,
                       granules=info["granules"], tiles=info["tiles"], coverage_pct=info["coverage_pct"], zoom=info["zoom"]))
    print("  wrote", f, info)
    meta = dict(place=a.place, bbox=a.bbox, width=a.width,
                rs1_stretch_db=[round(v, 2) for v in stretch] if stretch else None,
                rs1_note="20*log10(DN), relative dB, uncalibrated; one fixed stretch for all RADARSAT-1 frames of this place",
                nisar_note="GIBS NISAR GCOV display PNG, R channel (HH), 2-98 % stretch; not calibrated",
                frames=frames)
    name = f"{a.place}_series.json" if a.series else f"{a.place}_meta.json"
    (OUT / name).write_text(json.dumps(meta, indent=1))
    print("wrote", name)


if __name__ == "__main__":
    main()
