"""Pre-load every tour stop's time series, frame images and the world-map tiles around it through the running server.

Usage: python prewarm.py [--base http://127.0.0.1:8765]
Prints per stop: number of passes, seconds to warm, failures.
"""
import argparse
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

STOPS = Path(__file__).resolve().parent.parent / "web" / "stops.js"


def stops():
    text = STOPS.read_text(encoding="utf-8")
    return [(m.group(1), float(m.group(2)), float(m.group(3)))
            for m in re.finditer(r'id: "([a-z_]+)".*?lon: (-?[\d.]+), lat: (-?[\d.]+)', text, re.S)]


def map_tiles(lon, lat, zooms=range(6, 11), r=1):
    """The 3 x 3 world-map tiles around a point for each zoom the page requests (preview tiles stop at z10)."""
    import math
    for z in zooms:
        n = 2 ** z
        x = int((lon + 180) / 360 * n)
        y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                yield f"/tiles/{z}/{(x + dx) % n}/{y + dy}.webp"


def get(url, timeout=180):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print("   fail", url.rsplit("/", 1)[-1][:70], e, flush=True)
        return b""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8765")
    a = ap.parse_args()
    for sid, lon, lat in stops():
        t = time.time()
        s = json.loads(get(f"{a.base}/api/series.json?lon={lon:.3f}&lat={lat:.3f}"))
        frames = s.get("frames", [])
        urls = [f"{a.base}/api/frame/{f['c']}/{f['id']}.webp" for f in frames] + [a.base + t for t in map_tiles(lon, lat)]
        if len(frames) > 1:
            f0, f1 = frames[0], frames[-1]
            urls.append(f"{a.base}/api/diff/{f0['c']}/{f0['id']}/{f1['c']}/{f1['id']}.webp")
        fails = 0
        with ThreadPoolExecutor(3) as ex:  # gentle on memory and on NASA
            for ok in ex.map(lambda u: bool(get(u)), urls):
                fails += 0 if ok else 1
        print(f"{sid:10s} {len(frames):2d} passes  {frames[0]['date'] if frames else '-'} -> {frames[-1]['date'] if frames else '-'}"
              f"  track {s.get('track')}  {time.time() - t:5.1f}s  fails {fails}", flush=True)


if __name__ == "__main__":
    main()
