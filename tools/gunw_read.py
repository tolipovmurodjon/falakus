"""Ground motion from a NISAR interferogram (GUNW): how many centimetres the ground moved between two passes.

Physics: the radar measures the phase of its 23.8 cm wave. If the ground moves toward the satellite between two
passes, the round trip gets shorter and the phase changes; one full cycle (2 pi) = half a wavelength = 11.9 cm
of motion along the line of sight (LOS). NASA's GUNW product already "unwraps" the phase (counts whole cycles).
LOS motion (cm) = -unwrappedPhase * wavelength / (4 pi) * 100. Low-coherence pixels (vegetation change, water,
debris) carry no signal and are masked.

Usage: python gunw_read.py <name> <lon> <lat> <ref YYYYMMDD> <sec YYYYMMDD> [--km 30]
Writes data/motion/<name>/fringes.png, los.png and info.json (bbox, dates, numbers).
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utm_convert import lonlat_to_utm, utm_to_lonlat  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WAVELENGTH_M = 0.2384  # NISAR L-band, 1.257 GHz
G = "/science/LSAR/GUNW/grids/frequencyA/unwrappedInterferogram"


def find(lon, lat, ref, sec):
    d0 = f"{ref[:4]}-{ref[4:6]}-{ref[6:]}"
    url = ("https://cmr.earthdata.nasa.gov/search/granules.json?short_name=NISAR_L2_GUNW_PROVISIONAL_V1&short_name=NISAR_L2_GUNW_V1"
           f"&point={lon},{lat}&page_size=200&temporal={d0}T00:00:00Z,{d0}T23:59:59Z")
    with urllib.request.urlopen(url, timeout=60) as r:
        for e in json.load(r)["feed"]["entry"]:
            t = e["title"]
            dates = [p[:8] for p in t.split("_") if len(p) == 15 and p[8] == "T"]
            if len(dates) >= 4 and dates[0] == ref and dates[2] == sec:
                return t, next(l["href"] for l in e["links"] if l["href"].endswith(".h5"))
    raise SystemExit(f"no GUNW pair {ref} -> {sec} over this point")


def hsv_cycle(phase01):
    """Cyclic rainbow (the classic interferogram look): one full colour cycle per 11.9 cm."""
    h = phase01 * 6.0
    i = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    v = np.ones_like(f); q = 1 - f; t = f
    r = np.choose(i, [v, q, 0 * f, 0 * f, t, v]); g = np.choose(i, [t, v, v, q, 0 * f, 0 * f]); b = np.choose(i, [0 * f, 0 * f, t, v, v, q])
    return (np.dstack([r, g, b]) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name"); ap.add_argument("lon", type=float); ap.add_argument("lat", type=float)
    ap.add_argument("ref"); ap.add_argument("sec"); ap.add_argument("--km", type=float, default=30)
    a = ap.parse_args()
    title, url = find(a.lon, a.lat, a.ref, a.sec)
    import earthaccess
    import h5py
    earthaccess.login(strategy="netrc")
    with h5py.File(earthaccess.open([url])[0], "r") as h:
        g = h[G]
        x = g["xCoordinates"][:]; y = g["yCoordinates"][:]
        epsg = int(np.asarray(g["projection"]).item())
        zone, south = epsg % 100, epsg >= 32701
        cx, cy = lonlat_to_utm(a.lon, a.lat, zone, south)
        r = a.km * 1000
        ix = np.flatnonzero((x >= cx - r) & (x <= cx + r)); iy = np.flatnonzero((y >= cy - r) & (y <= cy + r))
        sl = (slice(iy[0], iy[-1] + 1), slice(ix[0], ix[-1] + 1))
        ph = g["HH/unwrappedPhase"][sl].astype(np.float32)
        coh = g["HH/coherenceMagnitude"][sl].astype(np.float32)
        xs, ys = x[sl[1]], y[sl[0]]
    ok = np.isfinite(ph) & (coh >= 0.3) & (ph != 0)
    los = -ph * WAVELENGTH_M / (4 * np.pi) * 100  # cm, positive = toward the satellite
    los -= np.nanmedian(los[ok])  # reference: the box median is "not moving"
    los[~ok] = np.nan
    if y[1] < y[0] if len(y) > 1 else False:
        pass  # rows already north-up
    else:
        los = los[::-1]; ok = ok[::-1]; ys = ys[::-1]
    out = ROOT / "data" / "motion" / a.name; out.mkdir(parents=True, exist_ok=True)
    alpha = (ok * 215).astype(np.uint8)
    fr = hsv_cycle(np.mod(np.nan_to_num(los), 11.92) / 11.92)
    Image.fromarray(np.dstack([fr, alpha]), "RGBA").save(out / "fringes.png", optimize=True)
    lim = float(np.nanpercentile(np.abs(los[ok]), 98)) if ok.any() else 1.0
    t = np.clip(np.nan_to_num(los) / max(lim, 0.5), -1, 1)
    col = np.dstack([np.where(t > 0, 232, 112), np.where(t > 0, 89, 72), np.where(t > 0, 12, 232)]).astype(np.float32)
    rgb = (255 + (col - 255) * np.abs(t)[..., None]).astype(np.uint8)
    Image.fromarray(np.dstack([rgb, alpha]), "RGBA").save(out / "los.png", optimize=True)
    lons, lats = utm_to_lonlat(np.array([xs[0], xs[-1]]), np.array([ys[-1], ys[0]]), zone, south)
    info = {"name": a.name, "granule": title, "ref": a.ref, "sec": a.sec, "bbox": [float(lons.min()), float(lats.min()), float(lons.max()), float(lats.max())],
            "pixel_m": float(abs(xs[1] - xs[0])), "coherent_pct": round(100 * float(ok.mean()), 1),
            "toward_cm_p99": round(float(np.nanpercentile(los[ok], 99)), 1) if ok.any() else None,
            "away_cm_p1": round(float(np.nanpercentile(los[ok], 1)), 1) if ok.any() else None,
            "cycle_cm": 11.92, "method": "LOS = -unwrappedPhase x 23.84 cm / 4 pi; coherence >= 0.3; box median set to 0"}
    (out / "info.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
