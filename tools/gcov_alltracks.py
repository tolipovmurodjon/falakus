"""Read EVERY calibrated NISAR GCOV pass over a box, from all orbit tracks and both releases (provisional + validated).

The time player uses one track (same geometry pass to pass). For water AREA the geometry matters little, so all tracks
together give a look every ~4-5 days instead of every 12. Saves data/science/<stop>_all/<date>_<track><A|D>.npz (16-bit),
same format as gcov_science.py, so tools/water_road.py runs on it unchanged.
Usage: python tools/gcov_alltracks.py andijan_res 73.135 40.765 --km 9
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

import numpy as np

import gcov_science

ROOT = Path(__file__).resolve().parent.parent


def granules(lon, lat):
    out = []
    for sn in ("NISAR_L2_GCOV_PROVISIONAL_V1", "NISAR_L2_GCOV_V1"):
        u = f"https://cmr.earthdata.nasa.gov/search/granules.json?short_name={sn}&point={lon},{lat}&page_size=500&sort_key=start_date"
        for e in json.load(urllib.request.urlopen(u, timeout=120))["feed"]["entry"]:
            h5 = [l["href"] for l in e["links"] if l["href"].endswith(".h5") and l["href"].startswith("https")]
            if h5:
                p = e["title"].split("_")
                out.append({"date": e["time_start"][:10], "id": e["title"], "url": h5[0], "track": p[5], "dir": p[6]})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("stop"); ap.add_argument("lon", type=float); ap.add_argument("lat", type=float)
    ap.add_argument("--km", type=float, default=9); a = ap.parse_args()
    import earthaccess
    earthaccess.login(strategy="netrc")
    out = ROOT / "data" / "science" / f"{a.stop}_all"; out.mkdir(parents=True, exist_ok=True)
    for g in granules(a.lon, a.lat):
        f = out / f"{g['date']}_{g['track']}{g['dir']}.npz"
        if f.exists():
            continue
        for attempt in range(3):
            try:
                hh, hv, px, meta = gcov_science.read_box(earthaccess.open([g["url"]])[0], a.lon, a.lat, a.km)
                np.savez_compressed(f, hh_db=hh.astype(np.float16), hv_db=(hv if hv is not None else np.array([])).astype(np.float16), **meta)
                print(g["date"], g["track"], g["dir"], hh.shape, flush=True); break
            except Exception as ex:
                if "outside" in str(ex) or attempt == 2:
                    print(g["date"], g["track"], "skip", str(ex)[:80], flush=True); break
                time.sleep(20 * (attempt + 1))


if __name__ == "__main__":
    main()
