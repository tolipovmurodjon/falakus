"""Ten years of monthly open water for a box from Sentinel-2 L2A (2017-2026), the training record for the forecast.

For each month: every Sentinel-2 scene over the box with scene cloud < 60 %; keep the scene whose box is clearest
(SCL: drop no-data, saturated, cloud shadow, clouds, cirrus, snow); water = NDWI (B03-B08)/(B03+B08) > 0.
Months with < 70 % of the box clear are marked "cloudy" and their km² is not used for training (we do not guess).
Writes data/forecast/<place>_s2_monthly.json (resumes: months already measured are skipped).
Usage: python tools/s2_history.py andijan_res 73.028 40.684 73.242 40.846 [--start 2017-01]
"""
import argparse
import calendar
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_road import crop, stac  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def retry(fn, *a, **k):
    for attempt in range(6):
        try:
            return fn(*a, **k)
        except Exception as ex:
            print("  retry", attempt, str(ex)[:70], flush=True); time.sleep(20)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("place"); ap.add_argument("w", type=float); ap.add_argument("s", type=float); ap.add_argument("e", type=float); ap.add_argument("n", type=float)
    ap.add_argument("--start", default="2017-01"); ap.add_argument("--end", default="2026-11")
    a = ap.parse_args()
    bbox = [a.w, a.s, a.e, a.n]
    out_f = ROOT / "data" / "forecast" / f"{a.place}_s2_monthly.json"
    rec = json.loads(out_f.read_text()) if out_f.exists() else {"place": a.place, "bbox": bbox, "method": __doc__.split("Writes")[0].strip(), "months": {}}
    y, m = map(int, a.start.split("-")); ye, me = map(int, a.end.split("-"))
    px_km2 = None
    while (y, m) <= (ye, me):
        key = f"{y}-{m:02d}"
        if key not in rec["months"]:
            last = calendar.monthrange(y, m)[1]
            items = retry(stac, {"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 40,
                                 "datetime": f"{key}-01T00:00:00Z/{key}-{last}T23:59:59Z", "query": {"eo:cloud_cover": {"lt": 60}},
                                 "sortby": [{"field": "eo:cloud_cover", "direction": "asc"}]}) or []
            best = None
            for it in items[:6]:  # the 6 least cloudy scenes are enough to find the clearest box
                arr = retry(crop, "sentinel-2-l2a", it["id"], ["B03", "B08", "SCL"], bbox, 600)
                if arr is None:
                    continue
                g, nir, scl = arr[0].astype(np.float32), arr[1].astype(np.float32), arr[2]
                clear = ~np.isin(scl, [0, 1, 3, 8, 9, 10, 11])
                if best is None or clear.mean() > best[1]:
                    wet = ((g - nir) / np.maximum(g + nir, 1) > 0) & clear
                    H, W = scl.shape
                    px_km2 = ((bbox[2] - bbox[0]) * 111.32 * np.cos(np.radians((bbox[1] + bbox[3]) / 2)) / W) * ((bbox[3] - bbox[1]) * 110.54 / H)
                    best = (it["properties"]["datetime"][:10], float(clear.mean()), float(wet.sum() * px_km2))
                if best and best[1] > 0.97:
                    break
            if best:
                rec["months"][key] = {"date": best[0], "clear_pct": round(best[1] * 100, 1), "water_km2": round(best[2], 2), "use": best[1] >= 0.7}
            else:
                rec["months"][key] = {"date": None, "clear_pct": 0, "water_km2": None, "use": False}
            print(key, rec["months"][key], flush=True)
            out_f.write_text(json.dumps(rec, indent=1))
        m += 1
        if m > 12:
            m, y = 1, y + 1
    used = [v for v in rec["months"].values() if v["use"]]
    print(f"{len(rec['months'])} months, {len(used)} clear enough to use", flush=True)


if __name__ == "__main__":
    main()
