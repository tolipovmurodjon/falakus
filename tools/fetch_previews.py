"""Download NISAR browse previews listed in an index (no login needed).

Usage: python fetch_previews.py <index.json> <out dir> [--kind thumb|full] [--bbox w,s,e,n] [--threads 32]
Skips files already on disk, so it can be re-run safely.
"""
import argparse
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    req = urllib.request.Request(url, headers={"User-Agent": "falakus-nisar-preview"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            tmp = dest.with_suffix(".part")
            tmp.write_bytes(data)
            tmp.replace(dest)
            return "ok"
        except Exception as e:  # network hiccups: retry, then report
            err = e
    return f"fail {err}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("index")
    ap.add_argument("out")
    ap.add_argument("--kind", default="thumb", choices=["thumb", "full"])
    ap.add_argument("--bbox")
    ap.add_argument("--threads", type=int, default=32)
    ap.add_argument("--reverse", action="store_true", help="start from the newest frame")
    a = ap.parse_args()

    frames = json.load(open(a.index))["frames"]
    if a.bbox:
        w, s, e, n = map(float, a.bbox.split(","))
        frames = [f for f in frames if f["bbox"][0] < e and f["bbox"][2] > w and f["bbox"][1] < n and f["bbox"][3] > s]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(f[a.kind], out / f"{f['id']}.png") for f in frames if f.get(a.kind)]
    if a.reverse:
        jobs.reverse()
    done = {"ok": 0, "skip": 0, "fail": 0}
    with ThreadPoolExecutor(a.threads) as ex:
        for i, res in enumerate(ex.map(lambda j: fetch(*j), jobs), 1):
            done[res.split()[0]] += 1
            if i % 1000 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} {done}", flush=True)


if __name__ == "__main__":
    main()
