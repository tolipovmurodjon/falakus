"""Outside check for chapter 2: NISAR radar vegetation index (RVI, from water_road.py) vs Sentinel-2 NDVI over the same
ESA WorldCover cropland, clearest photo within +-6 days of each pass (clouds/snow masked by SCL). Prints r and writes
the pairs into data/waterroad/<place>_ndvi.json.  Usage: python tools/rvi_vs_ndvi.py fergana
"""
import json, sys
from datetime import date, timedelta
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import water_road as wr

ROOT = Path(__file__).resolve().parent.parent
name = sys.argv[1]
P = json.loads((ROOT / f"data/waterroad/{name}.json").read_text())["passes"]
bbox = json.loads((ROOT / f"data/science/{name}/frames.json").read_text())["bbox"]
W = 500; H = int(W * (bbox[3] - bbox[1]) / ((bbox[2] - bbox[0]) * np.cos(np.radians((bbox[1] + bbox[3]) / 2))))
lon, lat = np.meshgrid(np.linspace(bbox[0], bbox[2], W), np.linspace(bbox[3], bbox[1], H))
wc = sorted(wr.stac({"collections": ["esa-worldcover"], "bbox": bbox, "limit": 4}), key=lambda x: x["properties"].get("esa_worldcover:product_version", ""))[-1]
crop = wr.sample(wr.crop("esa-worldcover", wc["id"], ["map"], bbox, 1500)[0], lon, lat, bbox) == 40
out = []
for p in P:
    d = date.fromisoformat(p["date"])
    it = wr.stac({"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 20, "datetime": f"{d - timedelta(days=6)}T00:00:00Z/{d + timedelta(days=6)}T23:59:59Z", "query": {"eo:cloud_cover": {"lt": 30}}})
    rec = {"date": p["date"], "rvi": p.get("rvi_crop")}
    if it:
        b = min(it, key=lambda x: x["properties"]["eo:cloud_cover"])
        g = wr.crop("sentinel-2-l2a", b["id"], ["B04", "B08", "SCL"], bbox, 1000)
        clear = wr.sample(~np.isin(g[2], [0, 1, 3, 8, 9, 10, 11]), lon, lat, bbox) & crop & wr.sample(g[0] > 0, lon, lat, bbox)
        if clear.mean() > 0.1 * crop.mean() and clear.sum() > 500:
            r4, r8 = [wr.sample(x.astype(float), lon, lat, bbox) for x in (g[0], g[1])]
            nd = (r8 - r4) / np.maximum(r8 + r4, 1)
            rec.update({"s2_date": b["properties"]["datetime"][:10], "ndvi_crop": round(float(np.median(nd[clear])), 3), "clear_crop_pct": round(float(clear.sum() / crop.sum() * 100), 1)})
    out.append(rec); print(rec, flush=True)
pr = np.array([(r["rvi"], r["ndvi_crop"]) for r in out if r.get("ndvi_crop") is not None and r["rvi"] is not None])
res = {"pairs": out, "n": int(len(pr)), "r": round(float(np.corrcoef(pr[:, 0], pr[:, 1])[0, 1]), 3) if len(pr) > 2 else None}
(ROOT / f"data/waterroad/{name}_ndvi.json").write_text(json.dumps(res, indent=1))
print("n", res["n"], "r(RVI, NDVI)", res["r"])
