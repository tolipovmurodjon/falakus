"""Fetch NASA's exact map position (the _LATLON.kml GroundOverlay box) for every NISAR preview picture.

Why: each _LATLON.png preview covers a larger box than the catalogue bounding box. Cropping the picture to its data and
stretching it onto the catalogue box put it 0.5-4 km off (measured against the 20 m science data). The KML says exactly
which lon/lat box the whole PNG covers, so the server can place it with no guessing.

Usage: python tools/fetch_kml_boxes.py [--lanes 2]
Writes data/kml_boxes.json {granule id: [west, south, east, north]}; resumes where it stopped.
Order: frames nearest Central Asia (65E, 41N) first, so the home region is fixed first.
"""
import argparse
import json
import math
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import earthaccess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "kml_boxes.json"
BASE = "https://nisar.asf.earthdatacloud.nasa.gov/NISAR"


def box_from_kml(text):
    m = re.search(r"<coordinates>([^<]+)</coordinates>", text)
    pts = [tuple(map(float, p.split(",")[:2])) for p in m.group(1).split()]
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    return [min(lons), min(lats), max(lons), max(lats)]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--lanes", type=int, default=2); a = ap.parse_args()
    frames = json.load(open(ROOT / "data" / "index.json"))["frames"]
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    dist = lambda f: math.hypot((f["bbox"][0] + f["bbox"][2]) / 2 - 65, (f["bbox"][1] + f["bbox"][3]) / 2 - 41)
    todo = sorted((f for f in frames if f["id"] not in done), key=dist)
    print(f"{len(done)} done, {len(todo)} to fetch", flush=True)
    earthaccess.login(strategy="netrc")
    session = earthaccess.get_requests_https_session()
    lock = threading.Lock(); n = [0]

    def one(f):
        url = f"{BASE}/{f['collection']}/{f['id']}/{f['id']}_LATLON.kml"
        for attempt in range(3):
            try:
                r = session.get(url, timeout=60)
                if r.status_code == 200:
                    box = box_from_kml(r.text)
                    with lock:
                        done[f["id"]] = [round(v, 6) for v in box]; n[0] += 1
                        if n[0] % 100 == 0:
                            OUT.write_text(json.dumps(done)); print(f"{len(done)} boxes", flush=True)
                    return
                if r.status_code in (403, 404):
                    return
            except Exception:
                pass
            time.sleep(10 * (attempt + 1))

    with ThreadPoolExecutor(a.lanes) as ex:
        list(ex.map(one, todo))
    OUT.write_text(json.dumps(done))
    print(f"done: {len(done)} boxes", flush=True)


if __name__ == "__main__":
    main()
