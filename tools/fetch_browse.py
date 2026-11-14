"""Find NISAR granules over named points via NASA CMR and download their public browse PNGs.

For each place, picks the track/frame with the most dates so a time series is
geometrically consistent (same look angle), then grabs its browse images.
"""
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
OUT = Path(sys.argv[1])

PLACES = [
    # name, product short name, lon, lat, how many dates, which browse suffixes
    ("aral_west", "NISAR_L2_GCOV_PROVISIONAL_V1", 58.9, 45.2, 8, ["_LATLON_thumbnail.png"]),
    ("aral_east", "NISAR_L2_GCOV_PROVISIONAL_V1", 60.3, 45.4, 8, ["_LATLON_thumbnail.png"]),
    ("aral_pols", "NISAR_L2_GCOV_PROVISIONAL_V1", 59.5, 43.8, 1, ["_NATIVE_A_HHHH.png", "_NATIVE_A_HVHV.png", "_LATLON.png"]),
    ("fergana", "NISAR_L2_GCOV_PROVISIONAL_V1", 71.8, 40.6, 6, ["_LATLON_thumbnail.png"]),
    ("rogun", "NISAR_L2_GCOV_PROVISIONAL_V1", 69.77, 38.70, 6, ["_LATLON_thumbnail.png"]),
    ("qoshtepa", "NISAR_L2_GCOV_PROVISIONAL_V1", 66.6, 36.9, 6, ["_LATLON_thumbnail.png"]),
    ("tashkent_gunw", "NISAR_L2_GUNW_PROVISIONAL_V1", 69.25, 41.3, 2, None),
    ("fedchenko_goff", "NISAR_L2_GOFF_PROVISIONAL_V1", 72.25, 38.8, 2, None),
    ("uzb_soilmoist", "NISAR_L3_SME2_PROVISIONAL_V1", 64.5, 41.0, 2, None),
]


def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def granules(short_name, lon, lat):
    url = f"{CMR}?short_name={short_name}&point={lon},{lat}&page_size=300&sort_key=start_date"
    return get_json(url)["feed"]["entry"]


def track_frame(title):
    p = title.split("_")
    # NISAR_L2_PR_GCOV_<cycle>_<track>_<dir>_<frame>_...
    return f"{p[5]}_{p[6]}_{p[7]}"


def download(url, dest):
    if dest.exists():
        return dest.stat().st_size
    req = urllib.request.Request(url, headers={"User-Agent": "nisar-browse-fetch"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    dest.write_bytes(data)
    return len(data)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, prod, lon, lat, n, suffixes in PLACES:
        gs = granules(prod, lon, lat)
        by_tf = defaultdict(list)
        for g in gs:
            by_tf[track_frame(g["title"])].append(g)
        if not by_tf:
            report[name] = {"granules": 0}
            print(name, "NO DATA")
            continue
        best_tf, best = max(by_tf.items(), key=lambda kv: len({g["time_start"][:10] for g in kv[1]}))
        dated = {}
        for g in best:
            dated.setdefault(g["time_start"][:10], g)
        dates = sorted(dated)
        if len(dates) > n:
            step = (len(dates) - 1) / (n - 1) if n > 1 else 0
            dates = [dates[round(i * step)] for i in range(n)] if n > 1 else [dates[-1]]
        files = []
        for d in dates:
            g = dated[d]
            browse = [l["href"] for l in g.get("links", []) if l.get("href", "").startswith("https") and "/BROWSE/" in l["href"]]
            if suffixes:
                pick = [b for b in browse for s in suffixes if b.endswith(s)]
            else:
                pick = browse
            for b in pick:
                dest = OUT / f"{name}__{d}__{b.rsplit('/', 1)[1][-40:]}"
                try:
                    size = download(b, dest)
                    files.append({"date": d, "file": dest.name, "bytes": size})
                except Exception as e:
                    files.append({"date": d, "url": b, "error": str(e)})
        report[name] = {
            "product": prod, "point": [lon, lat], "granules": len(gs),
            "tracks": len(by_tf), "best_track_frame": best_tf,
            "dates_on_best": len({g["time_start"][:10] for g in best}),
            "polygon": (best[0].get("polygons") or [[None]])[0][0],
            "files": files,
        }
        print(name, len(gs), "granules,", len(by_tf), "track/frames, best", best_tf, "->", len(files), "files")
    (OUT / "report.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
