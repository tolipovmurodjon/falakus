"""Small point file for the Explorer's "Where NISAR looked" heatmap and for event briefings.

Reads data/index.json (the NISAR GCOV frame index, ~17 MB) and writes data/explorer/nisar_passes.json:
one row per frame, [day offset from `first`, 4 footprint corners as lon,lat rounded to 0.01 deg].
The page derives each frame centre from its corners (heatmap point) and uses the corners to say whether
a NISAR pass covered an event. The server serves data/explorer/*.json (not *.geojson), so the file is
compact JSON that explorer.js turns into GeoJSON.
Usage: python tools/explorer_density.py
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "index.json"
OUT = ROOT / "data" / "explorer" / "nisar_passes.json"


def main():
    idx = json.loads(SRC.read_text())
    frames = idx["frames"]
    days = sorted(f["start"][:10] for f in frames)
    first, last = days[0], days[-1]
    d0 = date.fromisoformat(first)
    rows, wrapped = [], 0
    for f in frames:
        ring = f["corners"][:4]
        lons = [p[0] for p in ring]
        if max(lons) - min(lons) > 180:  # crosses the antimeridian: keep the ring continuous (lon > 180 allowed)
            ring = [[p[0] + 360 if p[0] < 0 else p[0], p[1]] for p in ring]
            wrapped += 1
        day = (date.fromisoformat(f["start"][:10]) - d0).days
        rows.append([day] + [round(v, 2) for p in ring for v in p])
    out = {"about": "NISAR L2 GCOV frames in data/index.json: one row per frame, day offset from 'first', then 4 corners lon,lat",
           "collection": sorted({f["collection"] for f in frames}),
           "first": first, "last": last, "count": len(rows), "cols": ["day", "x1", "y1", "x2", "y2", "x3", "y3", "x4", "y4"], "f": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"{OUT.relative_to(ROOT)}: {len(rows)} frames, {first}..{last}, {wrapped} cross the antimeridian, {OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
