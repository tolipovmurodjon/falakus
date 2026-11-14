"""Cut a small crop out of a free sub-metre radar scene (Umbra / Capella / ICEYE open data, CC BY 4.0) and set it
next to our 10 m Sentinel-1 ship detector, so a viewer can zoom from "a 10 m bright dot" to "a 300 m hull".

Why it works: the three companies publish part of their X-band archive as cloud-optimised GeoTIFFs in public AWS
buckets (no login). A COG has a tile index and ready-made overviews, so a crop costs a few MB of HTTP range
requests, not the 0.3-10 GB file. Umbra GEC and Capella GEO are already map-projected; ICEYE GRD is in radar
geometry with 100 ground control points, which GDAL uses to warp it to lon/lat.

Steps per site:
  1. read the overview closest to the output pixel size (window around the bbox only), square to power,
     warp to EPSG:4326 with area averaging (this also smooths speckle), 10*log10 -> dB, stretch p1..p99.7 to grey;
  2. find ships in the crop: pixels > 9 dB above the local sea level (1 km median), blobs >= 6 px, land excluded;
  3. run tools/ship_count.py (same code, same site box, same 2048 px grid) on the Sentinel-1 pass nearest in time,
     keep its detections inside the crop, and pair them with the hi-res ships (nearest within --match-m).
Writes data/hires/<site>/<site>_<date>.png (grey, transparent no-data) and .json (source, licence, time,
resolution, bbox, the Sentinel-1 pass, both point lists, the pairing).
Anchored ships stay put for hours; moving ships do not, so the pairing is only fair for a short time gap.

Usage:
  python tools/hires_fetch.py --list                       # the presets
  python tools/hires_fetch.py panama_anchorage             # one preset (or: all)
  python tools/hires_fetch.py mysite --url <cog> --provider iceye --bbox W S E N --when 2025-11-07T03:33:28Z
         [--s1-bbox W S E N] [--m-per-px 3] [--width 1600] [--no-s1]
Scene search that found the presets (anonymous, 14 Nov 2026): Umbra s3://umbra-open-data-catalog/sar-data/tasks
(8,177 scenes), Capella stac/capella-open-data-by-product-type/capella-open-data-geo (2,286 GEO items), ICEYE
s3://iceye-open-data-catalog/stac-items (711 items).
"""
import argparse
import datetime as dt
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.control import GroundControlPoint
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ship_count  # noqa: E402  (same detector as data/ships/*.json)

GDAL_ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                GDAL_HTTP_MULTIRANGE="YES", GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES", VSI_CACHE="TRUE")
ATTRIBUTION = {
    "iceye": "Contains ICEYE Open Data (c) ICEYE, licensed under CC BY 4.0; cropped, reprojected and stretched by falakus",
    "umbra": "Contains Umbra Open Data (c) Umbra Lab, Inc., licensed under CC BY 4.0; cropped, reprojected and stretched by falakus",
    "capella": "Contains Capella Open Data (c) Capella Space, licensed under CC BY 4.0; cropped, reprojected and stretched by falakus",
}
ICEYE = "https://iceye-open-data-catalog.s3.amazonaws.com/data/spot/"
UMBRA = "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/sar-data/tasks/"
PRESETS = {
    "panama_anchorage": dict(
        provider="iceye", when="2025-11-07T03:33:41Z", mode="spotlight (SLH)", pol="VV", resolution_m=[0.93, 1.0],
        url=ICEYE + "ICEYE_D1X6QK_20251107T033338Z_6934719_X50_SLH/ICEYE_D1X6QK_20251107T033338Z_6934719_X50_SLH_GRD.tif",
        stac="https://iceye-open-data-catalog.s3.amazonaws.com/stac-items/2025/11/ICEYE_D1X6QK_20251107T033338Z_6934719_X50_SLH.json",
        bbox=[-79.5505, 8.836, -79.5035, 8.8825], m_per_px=3.2, s1_bbox=[-79.65, 8.75, -79.4, 8.95], s1_hours=36),
    "bosphorus_anchorage": dict(
        provider="iceye", when="2026-03-22T09:06:12Z", mode="spotlight (SLF)", pol="VV", resolution_m=None,
        url=ICEYE + "ICEYE_SXK973_20260322T090605Z_9361035_X66_SLF/ICEYE_SXK973_20260322T090605Z_9361035_X66_SLF_GRD.tif",
        stac="https://iceye-open-data-catalog.s3.amazonaws.com/stac-items/2026/03/ICEYE_SXK973_20260322T090605Z_9361035_X66_SLF.json",
        bbox=[28.937, 40.976, 29.02, 41.04], m_per_px=4.4, s1_bbox=[28.85, 40.85, 29.15, 41.05], s1_hours=24),
    "dubai_airport": dict(
        provider="umbra", when="2025-12-10T05:59:00Z", mode="SPOTLIGHT (GEC)", pol="VV", resolution_m=[0.5, 0.125],
        url=UMBRA + "AIR/PLACEHOLDER", stac=None, bbox=[55.34, 25.245, 55.365, 25.27], m_per_px=1.0, s1_bbox=None),
}


def iceye_props(tags):
    return json.loads(tags["ICEYE_PROPERTIES"]) if "ICEYE_PROPERTIES" in tags else {}


def overview_factor(ds, want_m):
    """Largest overview factor whose pixel is still >= 1.5x finer than the output pixel."""
    if ds.crs:
        px_m = abs(ds.res[0]) * (111320 if ds.crs.is_geographic else 1)
    else:
        px_m = iceye_props(ds.tags()).get("sar:pixel_spacing_range", 0.5)
    best = (0, 1)  # (level index + 1, factor); 0 = full resolution
    for i, f in enumerate(ds.overviews(1)):
        if px_m * f * 1.5 <= want_m:
            best = (i + 1, f)
    return best


def read_power(url, bbox, want_m):
    """Power (DN^2) of the source pixels around bbox, plus how to place them (transform or GCPs)."""
    path = "/vsicurl/" + url
    with rasterio.Env(**GDAL_ENV):
        with rasterio.open(path) as ds:
            level, f = overview_factor(ds, want_m)
            meta = {"native_px_deg_or_m": [abs(ds.res[0]), abs(ds.res[1])] if ds.crs else None,
                    "overview_factor": f, "tags": ds.tags()}
        kw = {"overview_level": level - 1} if level else {}
        with rasterio.open(path, **kw) as ds:
            if ds.crs:  # Umbra GEC / Capella GEO: map-projected
                b = transform_bounds("EPSG:4326", ds.crs, *bbox, densify_pts=21)
                win = ds.window(*b).round_offsets().round_lengths()
                win = win.intersection(rasterio.windows.Window(0, 0, ds.width, ds.height))
                a = ds.read(1, window=win).astype(np.float32)
                return a ** 2, dict(src_transform=ds.window_transform(win), src_crs=ds.crs), meta
            gcps, gcrs = ds.gcps  # ICEYE GRD: radar geometry + GCPs in lon/lat
            rows = np.array([g.row for g in gcps]); cols = np.array([g.col for g in gcps])
            A = np.c_[[g.x for g in gcps], [g.y for g in gcps], np.ones(len(gcps))]
            rc = [np.linalg.lstsq(A, v, rcond=None)[0] for v in (rows, cols)]
            corners = np.array([[x, y, 1] for x in bbox[::2] for y in bbox[1::2]])
            rr = corners @ rc[0]; cc = corners @ rc[1]
            r0, r1 = int(max(0, rr.min() - 50)), int(min(ds.height, rr.max() + 50))
            c0, c1 = int(max(0, cc.min() - 50)), int(min(ds.width, cc.max() + 50))
            a = ds.read(1, window=((r0, r1), (c0, c1))).astype(np.float32)
            g2 = [GroundControlPoint(row=g.row - r0, col=g.col - c0, x=g.x, y=g.y, z=g.z) for g in gcps]
            return a ** 2, dict(gcps=g2, src_crs=gcrs or CRS.from_epsg(4326)), meta


def grid(bbox, m_per_px, max_w):
    w, s, e, n = bbox
    kx = 111320 * np.cos(np.radians((s + n) / 2)); ky = 110574
    W = int(min(max_w, round((e - w) * kx / m_per_px)))
    H = int(round(W * (n - s) * ky / ((e - w) * kx)))
    return W, H, from_origin(w, n, (e - w) / W, (n - s) / H), (e - w) * kx / W


def to_db(power, place, bbox, m_per_px, max_w):
    W, H, tr, m = grid(bbox, m_per_px, max_w)
    out = np.full((H, W), np.nan, np.float32)
    reproject(power, out, src_nodata=0, dst_nodata=np.nan, dst_transform=tr, dst_crs="EPSG:4326",
              resampling=Resampling.average, **place)
    return 10 * np.log10(np.where(out > 0, out, np.nan)), tr, m


def find_ships(db, m_per_px):
    """Bright compact blobs on dark sea. Returns [row, col, length_m] per blob."""
    ok = np.isfinite(db)
    k = max(1, int(round(25 / m_per_px)))  # work at ~25 m for the background
    small = np.nan_to_num(db, nan=np.nanmax(db))[::k, ::k]
    bg = ndimage.median_filter(small, size=max(5, int(1000 / 25)))  # ~1 km local sea level
    sea_level = np.nanpercentile(db[ok], 30)
    land = ndimage.binary_dilation(ndimage.uniform_filter(small, 5) > sea_level + 6, iterations=4)
    up = lambda m: np.kron(m, np.ones((k, k)))[: db.shape[0], : db.shape[1]]
    bgu = up(bg); landu = up(land) > 0.5
    cand = ok & ~landu & (db > bgu + 9)
    lab, n = ndimage.label(ndimage.binary_dilation(cand, iterations=max(1, int(15 / m_per_px))))
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        px = cand[sl] & (lab[sl] == i)
        if px.sum() < 6:
            continue
        r, c = np.nonzero(px)
        L = (np.hypot(np.ptp(r), np.ptp(c)) + 1) * m_per_px
        out.append([sl[0].start + r.mean(), sl[1].start + c.mean(), round(float(L))])
    return out


def s1_nearest(when, site_bbox, hours):
    """Run ship_count's detector on the Sentinel-1 pass nearest to `when` (all frames of that pass)."""
    t = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
    body = {"collections": ["sentinel-1-rtc"], "bbox": site_bbox, "limit": 100,
            "datetime": f"{(t - dt.timedelta(hours=hours)).isoformat()}/{(t + dt.timedelta(hours=hours)).isoformat()}"}
    req = urllib.request.Request(f"{ship_count.PC}/stac/v1/search", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        feats = json.load(r)["features"]
    if not feats:
        return None
    by_pass = defaultdict(list)
    for f in feats:
        by_pass[f["properties"]["datetime"][:13]].append(f)
    key = min(by_pass, key=lambda k: abs((dt.datetime.fromisoformat(k + ":00:00+00:00") - t).total_seconds()))
    mosaic = None
    for f in by_pass[key]:
        v = ship_count.fetch(f["id"], site_bbox)
        if mosaic is not None and v.shape != mosaic.shape:
            v = ndimage.zoom(v, (mosaic.shape[0] / v.shape[0], mosaic.shape[1] / v.shape[1]), order=0)[: mosaic.shape[0], : mosaic.shape[1]]
        mosaic = v if mosaic is None else np.where(np.isfinite(mosaic), mosaic, v)
    ships, _ = ship_count.detect(mosaic)
    w, s, e, n = site_bbox; H, W = mosaic.shape
    pts = [[round(w + (c[1] + 0.5) / W * (e - w), 5), round(n - (c[0] + 0.5) / H * (n - s), 5)] for c in ships]
    t1 = min(dt.datetime.fromisoformat(f["properties"]["datetime"].replace("Z", "+00:00")) for f in by_pass[key])
    return {"items": [f["id"] for f in by_pass[key]], "time_utc": t1.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dt_hours": round((t1 - t).total_seconds() / 3600, 2), "grid_px": [W, H],
            "grid_m_per_px": round((e - w) * 111320 * np.cos(np.radians((s + n) / 2)) / W, 1), "points_all": pts}


def pair(a, b, max_m):
    """Greedy nearest pairing of two lon/lat lists; returns index pairs and distances (m)."""
    if not a or not b:
        return []
    A = np.array(a); B = np.array(b); lat = np.radians(A[:, 1].mean())
    d = np.hypot((A[:, None, 0] - B[None, :, 0]) * 111320 * np.cos(lat), (A[:, None, 1] - B[None, :, 1]) * 110574)
    out, used_a, used_b = [], set(), set()
    for i, j in sorted(np.ndindex(d.shape), key=lambda ij: d[ij]):
        if d[i, j] > max_m:
            break
        if i not in used_a and j not in used_b:
            used_a.add(i); used_b.add(j); out.append([int(i), int(j), round(float(d[i, j]))])
    return out


def run(site, p, max_w, match_m, use_s1, out_root):
    when = p["when"]; bbox = p["bbox"]
    power, place, meta = read_power(p["url"], bbox, p["m_per_px"])
    ip = iceye_props(meta["tags"])
    if ip:  # ICEYE: take time, resolution and geometry from the file itself
        when = ip["datetime"][:19] + "Z"
        p = dict(p, pol="/".join(ip["sar:polarizations"]), mode=f'{ip["sar:instrument_mode"]} ({ip.get("iceye:processing_mode", "")})',
                 resolution_m=[round(ip["sar:resolution_range"], 2), round(ip["sar:resolution_azimuth"], 2)],
                 geometry={"orbit": ip.get("sat:orbit_state"), "incidence_deg": round(ip.get("view:incidence_angle", 0), 1),
                           "pixel_spacing_m": [ip.get("sar:pixel_spacing_range"), ip.get("sar:pixel_spacing_azimuth")],
                           "looks": [ip.get("sar:looks_range"), ip.get("sar:looks_azimuth")], "platform": ip.get("platform")})
    db, tr, m = to_db(power, place, bbox, p["m_per_px"], max_w)
    ok = np.isfinite(db)
    lo, hi = np.nanpercentile(db, [1, 99.7])
    grey = np.clip((np.nan_to_num(db, nan=lo) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
    dst = out_root / site; dst.mkdir(parents=True, exist_ok=True)
    name = f"{site}_{when[:10]}"
    Image.fromarray(np.dstack([grey, np.where(ok, 255, 0).astype(np.uint8)]), "LA").save(dst / f"{name}.png", optimize=True)
    H, W = db.shape
    to_ll = lambda r, c: [round(tr.c + (c + 0.5) * tr.a, 6), round(tr.f + (r + 0.5) * tr.e, 6)]
    ships = find_ships(db, m)
    hi_pts = [to_ll(r, c) + [L] for r, c, L in ships]
    rec = {"site": site, "provider": p["provider"], "licence": "CC-BY 4.0", "source_url": p["url"], "stac_item": p.get("stac"),
           "datetime_utc": when, "resolution_m": p.get("resolution_m"), "resolution_note": "[range, azimuth] metres",
           "mode": p["mode"], "pol": p["pol"], "geometry": p.get("geometry"), "bbox": bbox,
           "png": f"{name}.png", "png_px": [W, H], "png_m_per_px": round(m, 2), "overview_factor_read": meta["overview_factor"],
           "stretch_db": [round(float(lo), 1), round(float(hi), 1)], "attribution": ATTRIBUTION[p["provider"]],
           "hires_ships_auto": {"method": "> 9 dB above 1 km sea median, blobs >= 6 px, land + 100 m band masked",
                                "count": len(hi_pts), "points": hi_pts, "point_format": "[lon, lat, length_m]"}}
    if use_s1 and p.get("s1_bbox"):
        s1 = s1_nearest(when, p["s1_bbox"], p.get("s1_hours", 24))
        if s1:
            inside = []
            for lon, lat in s1.pop("points_all"):
                c = int((lon - tr.c) / tr.a); r = int((lat - tr.f) / tr.e)
                if 0 <= r < H and 0 <= c < W and ok[r, c]:
                    inside.append([lon, lat])
            pr = pair(inside, [q[:2] for q in hi_pts], match_m)
            s1.update({"site_bbox": p["s1_bbox"], "method": "tools/ship_count.py detect(), same site box and grid as data/ships",
                       "count_in_crop": len(inside), "points_in_crop": inside,
                       "pairing": {"max_m": match_m, "pairs_s1_hires_m": pr, "matched": len(pr),
                                   "s1_unmatched": len(inside) - len(pr), "hires_unmatched": len(hi_pts) - len(pr)}})
        rec["sentinel1"] = s1
    (dst / f"{name}.json").write_text(json.dumps(rec, indent=1))
    kb = (dst / f"{name}.png").stat().st_size // 1024
    print(f"{site}: {W}x{H} px at {m:.2f} m/px, {kb} KB, hi-res ships {len(hi_pts)}"
          + (f", S1 {rec['sentinel1']['time_utc']} (dt {rec['sentinel1']['dt_hours']} h) in crop {rec['sentinel1']['count_in_crop']},"
             f" paired {rec['sentinel1']['pairing']['matched']}" if rec.get("sentinel1") else ""), flush=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", nargs="?"); ap.add_argument("--list", action="store_true")
    ap.add_argument("--url"); ap.add_argument("--provider", choices=list(ATTRIBUTION)); ap.add_argument("--when")
    ap.add_argument("--bbox", nargs=4, type=float); ap.add_argument("--s1-bbox", nargs=4, type=float)
    ap.add_argument("--m-per-px", type=float, default=3.0); ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--match-m", type=float, default=400); ap.add_argument("--no-s1", action="store_true")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "hires")
    a = ap.parse_args()
    if a.list or not a.site:
        for k, v in PRESETS.items():
            print(f"{k:22s} {v['provider']:7s} {v['when']} bbox {v['bbox']}")
        return
    if a.url:
        PRESETS[a.site] = dict(provider=a.provider, when=a.when, mode="", pol="", url=a.url, bbox=a.bbox,
                               m_per_px=a.m_per_px, s1_bbox=a.s1_bbox, s1_hours=24)
    for site in (PRESETS if a.site == "all" else [a.site]):
        run(site, PRESETS[site], a.width, a.match_m, not a.no_s1, a.out)


if __name__ == "__main__":
    main()
