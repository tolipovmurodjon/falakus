"""Download the full-size NISAR GCOV browse image of every frame in data/index.json into data/full/,
so zooming the world radar map past zoom 7 never waits on ASF. Showcase places go first.

Public browse PNGs (no login). Resumable: existing files are skipped. Keep lanes low (ASF throttles).
Usage: python tools/prefetch_full.py [--lanes 3]
"""
import argparse
import json
import math
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FULL = ROOT / "data" / "full"
# lon, lat of the places the demo zooms into
FIRST = [(69.24, 41.31), (72.8, 40.8), (59.5, 44.0), (-74.0, 40.7), (-60.0, -3.1), (-46.6, -23.5), (139.7, 35.7),
         (77.2, 28.6), (31.2, 30.0), (2.35, 48.85), (-118.2, 34.0), (85.3, 27.7), (116.4, 39.9), (37.6, 55.75)]


def dist(f):
    w, s, e, n = f["bbox"]
    cx, cy = (w + e) / 2, (s + n) / 2
    return min(math.hypot((cx - x) * math.cos(math.radians(y)), cy - y) for x, y in FIRST)


def get(f):
    path = FULL / f"{f['id']}.png"
    if path.exists():
        return "skip"
    for k in range(4):
        try:
            req = urllib.request.Request(f["full"], headers={"User-Agent": "falakus-nisar-preview"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            tmp = path.with_suffix(".part")
            tmp.write_bytes(data)
            tmp.replace(path)
            return "ok"
        except Exception:
            time.sleep(3 * (k + 1))
    return "fail"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lanes", type=int, default=3)
    a = ap.parse_args()
    FULL.mkdir(parents=True, exist_ok=True)
    frames = [f for f in json.load(open(ROOT / "data" / "index.json"))["frames"] if f.get("full")]
    frames.sort(key=dist)
    done = {"ok": 0, "skip": 0, "fail": 0}
    t0 = time.time()
    with ThreadPoolExecutor(a.lanes) as ex:
        for i, r in enumerate(ex.map(get, frames), 1):
            done[r] += 1
            if i % 100 == 0:
                print(f"{i}/{len(frames)} {done} {time.time() - t0:.0f}s", flush=True)
    print("done", done, flush=True)


if __name__ == "__main__":
    main()
