"""One long, multi-sensor water record for a place: each sensor its OWN measured product, each scored on the same answer key.

No pixels are blended across sensors (the NASA OPERA DSWx / JRC Global Surface Water rule). Every sensor makes its own
open-water area (km2) on the same box, every sensor is checked against clear-sky optical photos, and the series are put
on one timeline with one colour per sensor. Sources, all already in the repo except the Landsat check:
  Landsat      data/timelapse/<place>/index.json frames whose source is Landsat (summer Jun-Sep cloud-free mosaics,
               MNDWI > 0). Scored by --landsat-check: Landsat 8/9 scenes within +-3 days of a clear Sentinel-2 month,
               MNDWI > 0 vs Sentinel-2 NDWI > 0 on the pixels clear in both (IoU, area error).
  Sentinel-2   data/forecast/<place>_s2_monthly.json, months with >= 70 % of the box clear (NDWI > 0). This IS the
               answer key; its own check is index agreement (NDWI monthly vs MNDWI time-lapse frame on the same date).
  Sentinel-1   data/s1series/<place>.json (tools/s1_series.py: Lee-filtered VV < T, T learned on one month, frozen).
  NISAR        data/ml/water_clean.json (learned map + nested size clean-up; nested held-out IoU).
Cross-sensor agreement where they overlap is reported (S1 vs S2 same month, NISAR vs nearest S2 within 6 days, ...).
Writes data/cases/record/<place>.json and <place>.png.
Usage: python tools/record_build.py andijan_res [--landsat-check]
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cases" / "record"
COLORS = {"Landsat": "#E8A33D", "Sentinel-2": "#4FC3F7", "Sentinel-1": "#B39DDB", "NISAR": "#5EE6A8"}
BAND = {"Landsat": "optical", "Sentinel-2": "optical", "Sentinel-1": "C-band radar", "NISAR": "L-band radar"}


def load(p):
    p = ROOT / p
    return json.loads(p.read_text()) if p.exists() else None


def same_box(a, b, tol=0.002):
    return a is not None and b is not None and all(abs(x - y) <= tol for x, y in zip(a, b))


def area_deg(b):
    return (b[2] - b[0]) * (b[3] - b[1])


def landsat_check(place, bbox, s2m):
    """Landsat 8/9 MNDWI vs the Sentinel-2 photo on the same box, scenes within +-3 days, pixels clear in both."""
    import water_road as wr
    W = 600; H = int(W * (bbox[3] - bbox[1]) / ((bbox[2] - bbox[0]) * np.cos(np.radians((bbox[1] + bbox[3]) / 2))))
    lon, lat = np.meshgrid(np.linspace(bbox[0], bbox[2], W), np.linspace(bbox[3], bbox[1], H))
    px_km2 = ((bbox[2] - bbox[0]) * 111320 * np.cos(np.radians((bbox[1] + bbox[3]) / 2)) / W) * ((bbox[3] - bbox[1]) * 110570 / H) / 1e6
    rows = []
    for mon, r in sorted(s2m["months"].items()):
        if not r.get("use"):
            continue
        d = date.fromisoformat(r["date"])
        try:
            ls = wr.stac({"collections": ["landsat-c2-l2"], "bbox": bbox, "limit": 20,
                          "datetime": f"{d - timedelta(days=3)}T00:00:00Z/{d + timedelta(days=3)}T23:59:59Z",
                          "query": {"eo:cloud_cover": {"lt": 20}, "platform": {"in": ["landsat-8", "landsat-9"]}}})
            if not ls:
                continue
            best = min(ls, key=lambda x: x["properties"]["eo:cloud_cover"])
            s2 = wr.stac({"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 10, "datetime": f"{d}T00:00:00Z/{d}T23:59:59Z"})
            if not s2:
                continue
            s2it = min(s2, key=lambda x: x["properties"]["eo:cloud_cover"])
            g = wr.crop("landsat-c2-l2", best["id"], ["green", "swir16", "qa_pixel"], bbox, 600)
            gr, sw = g[0].astype(np.float32) * 2.75e-5 - 0.2, g[1].astype(np.float32) * 2.75e-5 - 0.2  # C2 L2 scale/offset
            qa = g[2].astype(np.int64)
            lclear = wr.sample((g[0] > 0) & ((qa & 1) == 0) & ((qa & 0b11010) == 0), lon, lat, bbox)
            with np.errstate(all="ignore"):
                lw = wr.sample(np.nan_to_num((gr - sw) / (gr + sw), nan=-1) > 0, lon, lat, bbox)
            s = wr.crop("sentinel-2-l2a", s2it["id"], ["B03", "B08", "SCL"], bbox, 900)
            sclear = wr.sample(~np.isin(s[2], [0, 1, 3, 8, 9, 10, 11]), lon, lat, bbox)
            sw2 = wr.sample((s[0].astype(float) - s[1]) / np.maximum(s[0].astype(float) + s[1], 1) > 0, lon, lat, bbox)
        except Exception as ex:
            print(mon, "skip", str(ex)[:60], flush=True); continue
        both = lclear & sclear
        if both.mean() < 0.7:
            continue
        a_, b_ = lw & both, sw2 & both; u = (a_ | b_).sum()
        row = {"month": mon, "landsat_date": best["properties"]["datetime"][:10], "landsat": best["properties"]["platform"], "s2_date": r["date"],
               "joint_clear_pct": round(float(both.mean() * 100), 1), "iou": round(float((a_ & b_).sum() / u), 3) if u else None,
               "landsat_km2": round(float(a_.sum() * px_km2), 2), "s2_km2": round(float(b_.sum() * px_km2), 2)}
        rows.append(row); print(row, flush=True)
    res = {"place": place, "bbox": bbox, "method": "Landsat 8/9 C2 L2 MNDWI>0 vs Sentinel-2 L2A NDWI>0, scenes within +-3 days, pixels clear in both (>=70 % of box)", "pairs": rows}
    (OUT / f"{place}_landsat_check.json").write_text(json.dumps(res, indent=1))
    return res


def stats(pairs):
    """pairs: list of (sensor_km2, reference_km2)."""
    if not pairs:
        return None
    d = np.array([a - b for a, b in pairs], float)
    return {"n": len(pairs), "mae_km2": round(float(np.abs(d).mean()), 2), "bias_km2": round(float(d.mean()), 2),
            "median_abs_pct": round(float(np.median(np.abs(d) / np.maximum([b for _, b in pairs], 1e-6) * 100)), 1)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("place"); ap.add_argument("--landsat-check", action="store_true")
    a = ap.parse_args(); place = a.place
    OUT.mkdir(parents=True, exist_ok=True)
    s2m = load(f"data/forecast/{place}_s2_monthly.json"); tl = load(f"data/timelapse/{place}/index.json")
    s1 = load(f"data/s1series/{place}.json"); ni = load("data/ml/water_clean.json") if place == "andijan_res" else None
    nim = load("data/ml/water_model.json") if ni else None
    box = s2m["bbox"]
    series, validation, notes, excluded = [], {}, [], []

    # ---- Sentinel-2 (the answer key) ----
    s2 = {k: v for k, v in s2m["months"].items() if v.get("use")}
    for k, v in sorted(s2.items()):
        series.append({"sensor": "Sentinel-2", "band": BAND["Sentinel-2"], "date": v["date"], "km2": v["water_km2"]})
    s2_by_date = {v["date"]: v["water_km2"] for v in s2.values()}

    # ---- Landsat (summer mosaics from the time-lapse) ----
    if tl and same_box(tl["bbox"], box):
        idx_pairs = []
        for f in tl["frames"]:
            if f["source"].startswith("Landsat"):
                sc = max(f.get("scenes", []), key=lambda x: x.get("share", 0), default=None)
                d0, d1 = date.fromisoformat(f["dates"][0]), date.fromisoformat(f["dates"][-1])
                series.append({"sensor": "Landsat", "band": BAND["Landsat"], "date": sc["date"] if sc else f["dates"][0], "km2": f["water_km2"],
                               "platform": f["source"].split("(")[-1].rstrip(")"), "mosaic_days": (d1 - d0).days,
                               "note": "summer cloud-free mosaic (Jun-Sep); date = scene filling most pixels"})
            elif f["dates"][0] == f["dates"][-1] and f["dates"][0] in s2_by_date:
                idx_pairs.append((f["water_km2"], s2_by_date[f["dates"][0]]))  # same S2 scene, MNDWI vs NDWI
        if idx_pairs:
            st = stats(idx_pairs)
            validation["Sentinel-2"] = {"metric": "reference (answer key); self-check = MNDWI (time-lapse) minus NDWI (monthly) on the same scene, km2",
                                        "value": st["mae_km2"], "bias_km2": st["bias_km2"], "n": st["n"], "source": f"data/timelapse/{place}/index.json vs data/forecast/{place}_s2_monthly.json"}
            notes.append(f"Index choice matters: on the same Sentinel-2 scene, MNDWI (used for Landsat) minus NDWI (used for the S2 record) = {st['bias_km2']:+} km2 on average (n={st['n']}).")
    else:
        excluded.append("Landsat: time-lapse box differs from the record box")
    lc = load(f"data/cases/record/{place}_landsat_check.json")
    if a.landsat_check or (lc is None and tl):
        lc = landsat_check(place, box, s2m) if a.landsat_check else lc
    if lc and lc["pairs"]:
        P = [p for p in lc["pairs"] if p["iou"] is not None]; st = stats([(p["landsat_km2"], p["s2_km2"]) for p in P])
        validation["Landsat"] = {"metric": "median IoU vs Sentinel-2 photo (Landsat 8/9, +-3 days, jointly clear pixels)", "value": round(float(np.median([p["iou"] for p in P])), 3),
                                 "mean_iou": round(float(np.mean([p["iou"] for p in P])), 3), "area_mae_km2": st["mae_km2"], "area_bias_km2": st["bias_km2"], "n": len(P),
                                 "source": f"data/cases/record/{place}_landsat_check.json",
                                 "caveat": "scored on Landsat 8/9 (2017-2026); the 1993-2016 record also uses Landsat 5/7 and multi-date summer mosaics, which this does not score"}
    else:
        validation["Landsat"] = {"metric": "not scored", "value": None, "n": 0, "source": "run tools/record_build.py --landsat-check"}

    # ---- Sentinel-1 ----
    if s1 and same_box(s1["bbox"], box):
        for r in s1["months"]:
            series.append({"sensor": "Sentinel-1", "band": BAND["Sentinel-1"], "date": r["date"], "km2": r["water_km2"], **({"fit_month": True} if r.get("fit_month") else {})})
        h = s1.get("heldout") or {}
        validation["Sentinel-1"] = {"metric": "median IoU vs Sentinel-2 photo (+-6 days), held-out months (threshold learned on one month, frozen)",
                                    "value": h.get("median_iou"), "mean_iou": h.get("mean_iou"), "area_mae_km2": h.get("area_mae_km2"), "area_bias_km2": h.get("area_bias_km2"),
                                    "n": h.get("n", 0), "threshold_db": s1.get("threshold_db"), "fit_month": s1.get("fit_month"), "source": f"data/s1series/{place}.json"}
    elif s1:
        excluded.append("Sentinel-1: box differs")

    # ---- NISAR ----
    if ni:
        nb = nim.get("bbox") if nim else None
        for r in ni["series"]:
            series.append({"sensor": "NISAR", "band": BAND["NISAR"], "date": r["date"], "km2": r["km2"]})
        sm = ni["summary"]
        validation["NISAR"] = {"metric": "median IoU vs Sentinel-2 photo, nested held-out (clean-up size chosen without the scored day)", "value": sm["nested_iou"],
                               "area_mae_km2": sm.get("nested_area_mae_km2"), "area_bias_km2": sm.get("nested_area_bias_km2"), "n": len(ni["held_out"]), "source": "data/ml/water_clean.json"}
        if nb and not same_box(nb, box):
            # how much does the larger NISAR grid change the photo's own km2? same photo day on both grids
            bx = [(h["photo_km2"], s2_by_date[h["photo"]]) for h in ni["held_out"] if h.get("photo") in s2_by_date and h.get("photo_km2") is not None]
            extra = f"; same Sentinel-2 photo measured on both grids differs by {stats(bx)['bias_km2']:+} km2 on average (n={len(bx)})" if bx else ""
            notes.append(f"NISAR grid is the UTM envelope of the box, {area_deg(nb) / area_deg(box) * 100 - 100:.0f} % larger in area than the record box{extra}. Kept on the chart, flagged.")
            validation["NISAR"]["box_note"] = "UTM envelope, slightly larger than record box"

    # ---- cross-sensor agreement where they overlap ----
    by = {}
    for r in series:
        by.setdefault(r["sensor"], []).append(r)
    s2_by_month = {k: v["water_km2"] for k, v in s2.items()}

    def nearest_s2(d, days):
        d = date.fromisoformat(d); best = None
        for k, v in s2_by_date.items():
            dd = abs((date.fromisoformat(k) - d).days)
            if dd <= days and (best is None or dd < best[0]):
                best = (dd, v)
        return best[1] if best else None

    agree = {}
    if "Sentinel-1" in by:
        agree["Sentinel-1 vs Sentinel-2, same month (all months, not only +-6 d)"] = stats([(r["km2"], s2_by_month[r["date"][:7]]) for r in by["Sentinel-1"] if r["date"][:7] in s2_by_month and not r.get("fit_month")])
        agree["Sentinel-1 vs Sentinel-2 within 6 days"] = stats([(r["km2"], nearest_s2(r["date"], 6)) for r in by["Sentinel-1"] if nearest_s2(r["date"], 6) is not None and not r.get("fit_month")])
        hm = [r for r in s1["months"] if "iou" in r]
        lo_ = [r for r in hm if r["s2_water_km2"] < 25]; hi_ = [r for r in hm if r["s2_water_km2"] >= 35]
        if lo_ and hi_:
            f = lambda v: (round(float(np.mean([r["s1_clear_km2"] - r["s2_water_km2"] for r in v])), 1), round(float(np.median([r["iou"] for r in v])), 2), len(v))
            (bl, il, nl), (bh, ih, nh) = f(lo_), f(hi_)
            notes.append(f"Sentinel-1 C-band over-counts when the reservoir is drawn down: photo < 25 km2 -> S1 {bl:+} km2, IoU {il} (n={nl}); "
                         f"photo >= 35 km2 (full) -> S1 {bh:+} km2, IoU {ih} (n={nh}). Likely cause (not measured): exposed wet bed / mud flats are smooth and radar-dark in VV; "
                         f"frozen threshold {s1.get('threshold_db')} dB was learned on {s1.get('fit_month')}.")
        mo = {}
        for r in by["Sentinel-1"]:
            mo[r["date"][5:7]] = mo.get(r["date"][5:7], []) + [(r["km2"], s2_by_month.get(r["date"][:7]))]
        agree["Sentinel-1 minus Sentinel-2 by calendar month (bias km2)"] = {m: round(float(np.mean([a_ - b_ for a_, b_ in v if b_ is not None])), 2) for m, v in sorted(mo.items()) if any(b_ is not None for _, b_ in v)}
    if "NISAR" in by:
        agree["NISAR vs Sentinel-2 within 6 days"] = stats([(r["km2"], nearest_s2(r["date"], 6)) for r in by["NISAR"] if nearest_s2(r["date"], 6) is not None])
        if "Sentinel-1" in by:
            s1m = {r["date"][:7]: r["km2"] for r in by["Sentinel-1"]}
            agree["NISAR vs Sentinel-1 same month"] = stats([(r["km2"], s1m[r["date"][:7]]) for r in by["NISAR"] if r["date"][:7] in s1m])
    if "Landsat" in by:
        agree["Landsat summer mosaic vs Sentinel-2 same year Jun-Sep median (no year overlaps: Landsat frames stop 2016, S2 record starts 2017)"] = None

    cover = {s: {"from": min(r["date"] for r in v), "to": max(r["date"] for r in v), "n": len(v)} for s, v in by.items()}
    notes += [
        "No pixels are blended across sensors: each point is one sensor's own water map on one date.",
        "Landsat points are summer (Jun-Sep) cloud-free mosaics; mosaic_days says how many days the mosaic spans. Treat as 'summer level', not a single-day reading.",
        "Sentinel-2 points are single clear scenes (>= 70 % of the box clear, NDWI > 0); cloudy months are left out, not guessed.",
        "Sentinel-1 (C-band VV) and NISAR (L-band HH) water = dark radar inside the possible-water zone (ESA WorldCover water/wetland + 1 km).",
    ]
    series.sort(key=lambda r: r["date"])
    res = {"place": place, "name": (tl or {}).get("name", place), "unit": "km2", "bbox": box, "coverage": cover, "series": series,
           "validation": validation, "agreement": agree, "excluded": excluded, "notes": notes, "method": __doc__.split("Writes")[0].strip()}
    (OUT / f"{place}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({"coverage": cover, "validation": validation, "agreement": agree, "notes": notes, "excluded": excluded}, indent=1))
    chart(res, OUT / f"{place}.png")


def chart(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as md
    import matplotlib.pyplot as plt
    bg, fg, mut = "#07111F", "#E6EDF5", "#7D8DA6"
    fig, ax = plt.subplots(figsize=(14, 5.2), dpi=110); fig.patch.set_facecolor(bg); ax.set_facecolor(bg)
    for s in ["Landsat", "Sentinel-2", "Sentinel-1", "NISAR"]:
        pts = [r for r in res["series"] if r["sensor"] == s]
        if not pts:
            continue
        x = [date.fromisoformat(r["date"]) for r in pts]; y = [r["km2"] for r in pts]
        v = res["validation"].get(s, {}); tag = f"IoU {v['value']:.2f}, n={v['n']}" if isinstance(v.get("value"), float) and "IoU" in v.get("metric", "") else "answer key" if s == "Sentinel-2" else "not scored"
        kw = dict(s=34 if s in ("Landsat", "NISAR") else 16, color=COLORS[s], alpha=.95 if s != "Sentinel-1" else .8, zorder=3 if s in ("NISAR", "Landsat") else 2, linewidths=0)
        ax.plot(x, y, color=COLORS[s], lw=.8, alpha=.35, zorder=1)
        ax.scatter(x, y, label=f"{s} ({BAND[s]}) - {tag}", **kw)
    for sp in ax.spines.values():
        sp.set_color("#1B2A40")
    ax.tick_params(colors=mut); ax.xaxis.set_major_locator(md.YearLocator(2)); ax.xaxis.set_major_formatter(md.DateFormatter("%Y"))
    ax.grid(color="#1B2A40", lw=.6); ax.set_ylabel("open water, km²", color=mut)
    ax.set_title(f"{res['name']}: one record, four sensors, each scored against clear Sentinel-2 photos", color=fg, loc="left", fontsize=12)
    lg = ax.legend(loc="upper left", frameon=False, fontsize=9)
    for t in lg.get_texts():
        t.set_color(fg)
    fig.tight_layout(); fig.savefig(path, facecolor=bg); plt.close(fig)


if __name__ == "__main__":
    main()
