"""Find a RADARSAT-1 (CSA, C-band HH) scene over a lon/lat box and cut it out as a lon/lat PNG.

How it works:
1. Searches the public NRCan EODMS STAC (no login) collection `Radarsat-1-L1-COG`
   for scenes that intersect the box; footprints come from the STAC geometry.
2. Picks the earliest scene in the date range that covers the box best, and maps it
   to its key in the open S3 bucket `radarsat-r1-l1-cog` (ca-central-1).
3. Reads only the pixels around the box over HTTP range requests (GDAL /vsicurl/).
   The files are not map-projected: they carry ~15 GCPs, so the window is warped to
   EPSG:4326 with a thin-plate-spline GCP transform.
4. The DNs are uint8 with no calibration LUT in the header, so the PNG is
   20*log10(DN) with a 2-98 percentile stretch (relative dB, not sigma0).

Usage: python tools/rs1_fetch.py <out_dir> [west south east north] [--from 1996-01-01 --to 2000-12-31] [--width 1500] [--stretch LO HI]
Aral example: python tools/rs1_fetch.py data/history/aral 59.7 45.0 60.3 45.6 --stretch 25.9 36.2
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.control import GroundControlPoint
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window
from shapely.geometry import box, shape

STAC = "https://www.eodms-sgdot.nrcan-rncan.gc.ca/search/search"
BUCKET = "https://radarsat-r1-l1-cog.s3.ca-central-1.amazonaws.com"
COLLECTION = "Radarsat-1-L1-COG"


def search(bbox, start, end):
    q = urllib.parse.urlencode({"collections": COLLECTION, "bbox": ",".join(map(str, bbox)),
                                "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z", "limit": 100})
    with urllib.request.urlopen(f"{STAC}?{q}", timeout=120) as r:
        return json.load(r)["features"]


def s3_key(item):
    """The STAC cog href is sometimes an EODMS API link that needs a login; find the open S3 key instead."""
    href = item["assets"]["cog"]["href"]
    if "radarsat-r1-l1-cog/" in href or "radarsat-r1-l1-cog.s3" in href:
        return href.split("amazonaws.com/")[1].removeprefix("radarsat-r1-l1-cog/")
    p = item["properties"]
    dt = p["datetime"]
    prefix = f"{int(dt[:4])}/{int(dt[5:7])}/RS1_{p['order_key']}_"
    with urllib.request.urlopen(f"{BUCKET}/?list-type=2&prefix={urllib.parse.quote(prefix)}", timeout=60) as r:
        listing = r.read().decode()
    keys = [k.split("</Key>")[0] for k in listing.split("<Key>")[1:]]
    if not keys:
        raise SystemExit(f"no open S3 file for {item['id']} ({prefix})")
    return keys[0]


def warp_box(url, bbox, width):
    w, s, e, n = bbox
    height = round(width * (n - s) / (e - w))
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"), rasterio.open(f"/vsicurl/{url}") as src:
        gcps, _ = src.gcps
        # Find the source window around the box: fit pixel = f(lon, lat) from the GCPs (2nd order).
        A = np.array([[1, g.x, g.y, g.x * g.y, g.x ** 2, g.y ** 2] for g in gcps])
        col_c = np.linalg.lstsq(A, [g.col for g in gcps], rcond=None)[0]
        row_c = np.linalg.lstsq(A, [g.row for g in gcps], rcond=None)[0]
        corners = [(x, y) for x in (w, e) for y in (s, n)]
        cols = [np.dot([1, x, y, x * y, x * x, y * y], col_c) for x, y in corners]
        rows = [np.dot([1, x, y, x * y, x * x, y * y], row_c) for x, y in corners]
        pad = 200
        c0, c1 = max(0, int(min(cols)) - pad), min(src.width, int(max(cols)) + pad)
        r0, r1 = max(0, int(min(rows)) - pad), min(src.height, int(max(rows)) + pad)
        if c1 <= c0 or r1 <= r0:
            raise SystemExit("box is outside this scene")
        data = src.read(1, window=Window(c0, r0, c1 - c0, r1 - r0)).astype("float32")
        tags = src.tags()
    shifted = [GroundControlPoint(row=g.row - r0, col=g.col - c0, x=g.x, y=g.y) for g in gcps]
    data[data == 0] = np.nan
    out = np.full((height, width), np.nan, "float32")
    reproject(data, out, gcps=shifted, src_crs=CRS.from_epsg(4326), src_nodata=np.nan,
              dst_transform=from_bounds(w, s, e, n, width, height), dst_crs="EPSG:4326",
              dst_nodata=np.nan, resampling=Resampling.bilinear, SRC_METHOD="GCP_TPS")
    return out, tags


def to_png(dn, path, stretch=None):
    from PIL import Image
    db = 20 * np.log10(dn)
    valid = np.isfinite(db)
    lo, hi = stretch or np.percentile(db[valid], [2, 98])
    g = np.clip((db - lo) / (hi - lo) * 255, 0, 255)
    rgba = np.zeros(dn.shape + (4,), "uint8")
    rgba[..., :3] = np.where(valid, g, 0)[..., None].astype("uint8")
    rgba[..., 3] = np.where(valid, 255, 0)
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)
    return float(lo), float(hi), float(valid.mean() * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("bbox", nargs="*", type=float, default=[59.7, 45.0, 60.3, 45.6])
    ap.add_argument("--from", dest="start", default="1996-01-01")
    ap.add_argument("--to", dest="end", default="2000-12-31")
    ap.add_argument("--width", type=int, default=1500)
    # A box that is nearly all water makes its own 2-98 percentiles useless; pass the
    # percentiles of a wider run (printed in its json) so water stays dark next to land.
    ap.add_argument("--stretch", nargs=2, type=float, metavar=("LO", "HI"))
    a = ap.parse_args()
    B = box(*a.bbox)
    items = search(a.bbox, a.start, a.end)
    if not items:
        raise SystemExit("no scenes in that box and date range")
    for it in items:
        it["_cov"] = shape(it["geometry"]).intersection(B).area / B.area * 100
    items.sort(key=lambda it: (-round(it["_cov"]), it["properties"]["datetime"]))
    for it in items:
        print(f"{it['properties']['datetime'][:10]}  {it['properties']['beam_mnemonic']:5}  footprint covers {it['_cov']:.0f}%")
    it = items[0]
    p = it["properties"]
    key = s3_key(it)
    print("picked", key)
    dn, tags = warp_box(f"{BUCKET}/{key}", a.bbox, a.width)
    day = p["datetime"][:10]
    a.out_dir.mkdir(parents=True, exist_ok=True)
    png = a.out_dir / f"rs1_{day.replace('-', '')}.png"
    lo, hi, cov = to_png(dn, png, a.stretch)
    meta = {
        "source": f"CSA RADARSAT-1 (Open Government Licence - Canada), s3://radarsat-r1-l1-cog/{key}",
        "date": day, "time_utc": p["datetime"][11:19], "mode": p["beam_mode"], "product_type": p["product_type"],
        "orbit": p["sat:orbit_state"], "incidence_deg": float(tags.get("CEOS_INC_ANGLE", "nan")),
        "pol": "HH", "band": "C 5.6 cm", "bbox": a.bbox,
        "stretch": f"20*log10(DN) -> {lo:.1f}..{hi:.1f} relative dB, not sigma0; "
                   + ("fixed, from the 2-98 percentiles of a wider run" if a.stretch else "2-98 percentile of this box"),
        "calibrated": False, "georef": f"{len(rasterio.open(f'/vsicurl/{BUCKET}/{key}').gcps[0])} scene GCPs, thin-plate spline",
        "coverage_pct_of_box": round(cov, 1),
    }
    png.with_suffix(".json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
