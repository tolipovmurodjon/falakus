"""Index every NISAR GCOV frame in a date window from NASA CMR (no login needed).

Usage: python nisar_index.py <out.json> [--days 12] [--end YYYY-MM-DD]
Without --end it picks the 12-day window with the most unique frames since 1 Oct 2026.
Validated (V1) wins over provisional for the same acquisition.
"""
import argparse
import datetime as dt
import json
import urllib.request
from collections import Counter

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
COLLECTIONS = ["NISAR_L2_GCOV_V1", "NISAR_L2_GCOV_PROVISIONAL_V1"]


def search(short_name, start, end):
    url = (f"{CMR}?short_name={short_name}&temporal={start}T00:00:00Z,{end}T23:59:59Z"
           f"&page_size=2000&sort_key=start_date")
    out, after = [], None
    while True:
        req = urllib.request.Request(url, headers={"CMR-Search-After": after} if after else {})
        with urllib.request.urlopen(req, timeout=180) as r:
            after = r.headers.get("CMR-Search-After")
            page = json.load(r)["feed"]["entry"]
        out += page
        if len(page) < 2000 or not after:
            return out


def acquisition_key(title):
    # Same radar acquisition appears in both collections; key on track/frame/mode/pol/time.
    p = title.split("_")
    return "_".join(p[4:13])


def to_record(g, short_name):
    poly = (g.get("polygons") or [[None]])[0][0]
    if not poly:
        return None
    v = list(map(float, poly.split()))
    lats, lons = v[0::2], v[1::2]
    if max(lons) - min(lons) > 180:  # crosses the antimeridian; skip for phase 0
        return None
    links = [l["href"] for l in g.get("links", []) if l.get("href", "").startswith("https") and "/BROWSE/" in l["href"]]
    thumb = next((l for l in links if l.endswith("_LATLON_thumbnail.png")), None)
    full = next((l for l in links if l.endswith("_LATLON.png")), None)
    if not thumb:
        return None
    p = g["title"].split("_")
    return {
        "id": g["title"], "collection": short_name, "start": g["time_start"],
        "track": p[5], "dir": p[6], "frame": p[7], "mode": p[8], "pol": p[9],
        "bbox": [min(lons), min(lats), max(lons), max(lats)],
        "corners": [[lo, la] for la, lo in zip(lats, lons)],
        "thumb": thumb, "full": full,
        "mb": round(float(g.get("granule_size") or 0), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--days", type=int, default=12)
    ap.add_argument("--end")
    a = ap.parse_args()

    today = dt.date(2026, 11, 14)
    lo = dt.date(2026, 10, 1)
    records = {}
    for sn in COLLECTIONS:  # validated first, so it wins
        for g in search(sn, lo.isoformat(), today.isoformat()):
            rec = to_record(g, sn)
            if rec and acquisition_key(rec["id"]) not in records:
                records[acquisition_key(rec["id"])] = rec
    per_day = Counter(r["start"][:10] for r in records.values())

    if a.end:
        end = dt.date.fromisoformat(a.end)
    else:
        best = max((sum(per_day[(e - dt.timedelta(days=i)).isoformat()] for i in range(a.days)), e)
                   for e in (lo + dt.timedelta(days=k) for k in range(a.days - 1, (today - lo).days + 1)))
        end = best[1]
    start = end - dt.timedelta(days=a.days - 1)
    keep = [r for r in records.values() if start.isoformat() <= r["start"][:10] <= end.isoformat()]
    keep.sort(key=lambda r: r["start"])
    json.dump({"window": [start.isoformat(), end.isoformat()], "count": len(keep),
               "per_day": dict(sorted(per_day.items())), "frames": keep}, open(a.out, "w"), indent=0)
    print("per day:", dict(sorted(per_day.items())))
    print(f"window {start} -> {end}: {len(keep)} frames "
          f"({Counter(r['collection'] for r in keep)})")


if __name__ == "__main__":
    main()
