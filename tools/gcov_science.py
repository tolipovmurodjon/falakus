"""Science mode: calibrated NISAR GCOV gamma0 (dB) for a small box around a place, every pass.

Reads only the box from each full .h5 over HTTPS (earthaccess + h5py), never the whole file.
Needs Boss's Earthdata login in ~/_netrc (or ~/.netrc). Run with plain `python` (not -I) so the
user-installed earthaccess and h5py are found.

Usage: python gcov_science.py <stop_id> <lon> <lat> [--km 15] [--base http://127.0.0.1:8765]
Writes data/science/<stop_id>/<date>.npz (hh_db, hv_db) and data/science/<stop_id>/stats.json.
"""
import argparse
import json
import math
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "science"
GRID = "/science/LSAR/GCOV/grids/frequencyA"


def utm_from_lonlat(lon, lat, zone, south):
    """WGS84 -> UTM (Snyder's series; accurate to well under 1 m inside a zone)."""
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f); ep2 = e2 / (1 - e2)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    phi, lam = math.radians(lat), math.radians(lon)
    n = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    t, c = math.tan(phi) ** 2, ep2 * math.cos(phi) ** 2
    A = math.cos(phi) * (lam - lon0)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi
             - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * phi)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * phi)
             - (35 * e2 ** 3 / 3072) * math.sin(6 * phi))
    x = k0 * n * (A + (1 - t + c) * A ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * A ** 5 / 120) + 500000
    y = k0 * (m + n * math.tan(phi) * (A * A / 2 + (5 - t + 9 * c + 4 * c * c) * A ** 4 / 24
                                       + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * A ** 6 / 720))
    return x, (y + 10000000 if south else y)


def otsu(values):
    hist, edges = np.histogram(values, bins=256)
    p = hist / max(hist.sum(), 1)
    w = np.cumsum(p); mu = np.cumsum(p * (edges[:-1] + edges[1:]) / 2)
    between = (mu[-1] * w - mu) ** 2 / np.maximum(w * (1 - w), 1e-12)
    return float((edges[:-1] + edges[1:])[np.argmax(between)] / 2)


def read_box(fh, lon, lat, km):
    import h5py
    with h5py.File(fh, "r") as h:
        g = h[GRID]
        epsg = int(np.asarray(g["projection"]).item()) if "projection" in g else None
        x, y = g["xCoordinates"][:], g["yCoordinates"][:]
        if not epsg or not (32601 <= epsg <= 32660 or 32701 <= epsg <= 32760):
            raise RuntimeError(f"unsupported projection EPSG {epsg}")
        zone, south = epsg % 100, epsg >= 32701
        cx, cy = utm_from_lonlat(lon, lat, zone, south)
        r = km * 1000
        ix = np.flatnonzero((x >= cx - r) & (x <= cx + r)); iy = np.flatnonzero((y >= cy - r) & (y <= cy + r))
        if ix.size < 4 or iy.size < 4:
            raise RuntimeError("box outside this frame")
        sl = (slice(iy[0], iy[-1] + 1), slice(ix[0], ix[-1] + 1))
        hh = g["HHHH"][sl].astype(np.float32)
        hv = g["HVHV"][sl].astype(np.float32) if "HVHV" in g else None
        px = abs(float(x[1] - x[0])) * abs(float(y[1] - y[0]))
    db = lambda a: 10 * np.log10(np.where(a > 0, a, np.nan))
    return db(hh), (db(hv) if hv is not None else None), px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stop"); ap.add_argument("lon", type=float); ap.add_argument("lat", type=float)
    ap.add_argument("--km", type=float, default=15); ap.add_argument("--base", default="http://127.0.0.1:8765")
    a = ap.parse_args()
    import earthaccess
    earthaccess.login(strategy="netrc")
    with urllib.request.urlopen(f"{a.base}/api/series.json?lon={a.lon:.3f}&lat={a.lat:.3f}", timeout=180) as r:
        frames = json.load(r)["frames"]
    out = OUT / a.stop; out.mkdir(parents=True, exist_ok=True)
    results = []
    for f in frames:
        url = f"https://nisar.asf.earthdatacloud.nasa.gov/NISAR/{f['c']}/{f['id']}/{f['id']}.h5"
        try:
            fh = earthaccess.open([url])[0]
            hh, hv, px = read_box(fh, a.lon, a.lat, a.km)
        except Exception as e:
            print(f"{f['date']}  skip: {e}", flush=True)
            continue
        np.savez_compressed(out / f"{f['date']}.npz", hh_db=hh, hv_db=hv if hv is not None else np.array([]))
        results.append({"date": f["date"], "id": f["id"], "hh": hh, "hv": hv, "px": px})
        print(f"{f['date']}  box {hh.shape}  HH median {np.nanmedian(hh):.1f} dB", flush=True)
    if not results:
        print("no passes read"); return
    thr = otsu(np.concatenate([r["hh"][np.isfinite(r["hh"])] for r in results]))
    stats = {"stop": a.stop, "box_km": 2 * a.km, "water_threshold_db": round(thr, 2), "source": "NISAR GCOV gamma0, calibrated dB (provisional)", "points": []}
    for r in results:
        hh = r["hh"]; ok = np.isfinite(hh)
        stats["points"].append({"date": r["date"], "id": r["id"],
                                "water_km2": round(float((hh[ok] < thr).sum() * r["px"] / 1e6), 2),
                                "hh_db": round(float(np.nanmedian(hh)), 2),
                                "hv_db": round(float(np.nanmedian(r["hv"])), 2) if r["hv"] is not None else None})
    (out / "stats.json").write_text(json.dumps(stats, indent=1))
    p = stats["points"]
    print(f"threshold {thr:.2f} dB | water {p[0]['water_km2']} km2 ({p[0]['date']}) -> {p[-1]['water_km2']} km2 ({p[-1]['date']})")


if __name__ == "__main__":
    main()
