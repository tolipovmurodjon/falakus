"""Independent check of the reservoir water AREA with NASA ICESat-2 laser water LEVELS (ATL13 inland water surface height).

A lake's area and its water level must move together along one curve (the shape of the valley it fills).
For each ATL13 granule over the box: read every beam's water-surface segments inside the box, keep the
reservoir's own water body (the most common inland_water_body_id), and take the median height.
Then pair each laser date with the nearest monthly area (Sentinel-2 photo, else corrected Sentinel-1 radar,
from data/forecast/andijan_res.json) and with the nearest NISAR pass, and report Spearman / Pearson r.
Writes data/waterroad/andijan_res_icesat2.json.  Usage: python tools/icesat2_levels.py
"""
import json
import urllib.request
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BOX = [73.03, 40.68, 73.24, 40.85]


def granules():
    u = ("https://cmr.earthdata.nasa.gov/search/granules.json?short_name=ATL13&version=007"
         f"&bounding_box={','.join(map(str, BOX))}&temporal=2025-01-01T00:00:00Z,2026-11-15T00:00:00Z&page_size=200")
    out = []
    for e in json.load(urllib.request.urlopen(u, timeout=120))["feed"]["entry"]:
        h5 = [l["href"] for l in e["links"] if l["href"].endswith(".h5") and l["href"].startswith("https")]
        if h5:
            out.append((e["time_start"][:10], h5[0]))
    return out


def main():
    import earthaccess
    import h5py
    earthaccess.login(strategy="netrc")
    recs = []
    for d, url in granules():
        try:
            fh = earthaccess.open([url])[0]
            hts, ids = [], []
            with h5py.File(fh, "r") as h:
                for b in ("gt1l", "gt1r", "gt2l", "gt2r", "gt3l", "gt3r"):
                    if b not in h:
                        continue
                    g = h[b]
                    lat, lon = g["segment_lat"][:], g["segment_lon"][:]
                    m = (lon >= BOX[0]) & (lon <= BOX[2]) & (lat >= BOX[1]) & (lat <= BOX[3])
                    if m.any():
                        hts.append(g["ht_water_surf"][:][m]); ids.append(g["inland_water_body_id"][:][m])
            if not hts:
                print(d, "no water segments in box", flush=True); continue
            ht, wid = np.concatenate(hts), np.concatenate(ids)
            ok = np.isfinite(ht) & (ht < 3000) & (ht > 0)
            vals, cnt = np.unique(wid[ok], return_counts=True)
            main_id = vals[np.argmax(cnt)]
            sel = ok & (wid == main_id)
            rec = {"date": d, "level_m": round(float(np.median(ht[sel])), 2), "spread_m": round(float(np.std(ht[sel])), 2), "segments": int(sel.sum()), "water_body_id": int(main_id)}
            recs.append(rec); print(rec, flush=True)
            (ROOT / "data/waterroad/andijan_res_icesat2_partial.json").write_text(json.dumps(recs, indent=1))
        except Exception as ex:
            print(d, "fail", str(ex)[:100], flush=True)
    # pair with areas
    fc = json.loads((ROOT / "data/forecast/andijan_res.json").read_text())["series"]
    nis = json.loads((ROOT / "data/waterroad/andijan_res.json").read_text())["passes"]
    for r in recs:
        m = r["date"][:7]
        s = next((x for x in fc if x["month"] == m), None)
        if s:
            r["month_area_km2"], r["month_area_from"] = s["km2"], s["from"]
        dd = date.fromisoformat(r["date"])
        near = min(nis, key=lambda p: abs((date.fromisoformat(p["date"]) - dd).days))
        if abs((date.fromisoformat(near["date"]) - dd).days) <= 8:
            r["nisar_date"], r["nisar_km2"] = near["date"], near["water_km2"]
    out = {"method": __doc__.split("Writes")[0].strip(), "levels": recs}
    P = [(r["level_m"], r["month_area_km2"]) for r in recs if "month_area_km2" in r and r["segments"] >= 20]
    if len(P) >= 4:
        a = np.array(P)
        from scipy.stats import spearmanr
        out["n"] = len(a); out["pearson_r"] = round(float(np.corrcoef(a[:, 0], a[:, 1])[0, 1]), 3); out["spearman_r"] = round(float(spearmanr(a[:, 0], a[:, 1])[0]), 3)
        print("level vs monthly area: n", len(a), "pearson", out["pearson_r"], "spearman", out["spearman_r"])
    (ROOT / "data/waterroad/andijan_res_icesat2.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
