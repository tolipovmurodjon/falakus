"""Live calibrated NISAR tiles at native resolution (10-20 m), anywhere, streamed from NASA's cloud.

For a Web Mercator tile it picks the newest GCOV frame of the 12-day index that covers the tile, reads only
the needed window of HHHH/HVHV from the .h5 over HTTPS (earthaccess session + block cache), and colours it:
R = HH (-22..-5 dB), G = HV (-28..-12 dB), B = HH/HV ratio (0..12 dB). Needs Boss's Earthdata netrc and the
user-installed earthaccess + h5py (run the server with plain `python`, not `-I`).
"""
import io
import math
import threading
from collections import OrderedDict

import numpy as np
from PIL import Image

GRID = "/science/LSAR/GCOV/grids/frequencyA"
_session = {"fs": None}
_lock = threading.Lock()
_files = OrderedDict()  # granule id -> (h5 file, meta), newest last


def _fs():
    if _session["fs"] is None:
        import earthaccess
        earthaccess.login(strategy="netrc")
        _session["fs"] = earthaccess.get_fsspec_https_session()
    return _session["fs"]


def _open(frame):
    gid = frame["id"]
    if gid in _files:
        _files.move_to_end(gid)
        return _files[gid]
    import h5py
    coll = frame["collection"]
    url = f"https://nisar.asf.earthdatacloud.nasa.gov/NISAR/{coll}/{gid}/{gid}.h5"
    fh = _fs().open(url, block_size=4 * 1024 * 1024, cache_type="blockcache")
    h = h5py.File(fh, "r")
    g = h[GRID]
    x = g["xCoordinates"][:]; y = g["yCoordinates"][:]
    epsg = int(np.asarray(g["projection"]).item())
    meta = {"x0": float(x[0]), "dx": float(x[1] - x[0]), "nx": x.size, "y0": float(y[0]), "dy": float(y[1] - y[0]), "ny": y.size,
            "zone": epsg % 100, "south": epsg >= 32701, "hv": "HVHV" in g, "g": g}
    _files[gid] = (h, meta)
    while len(_files) > 12:
        _, (old, _m) = _files.popitem(last=False)
        try:
            old.close()
        except Exception:
            pass
    return _files[gid]


def lonlat_to_utm(lon, lat, zone, south):
    """Vectorised WGS84 -> UTM (Snyder series)."""
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f); ep2 = e2 / (1 - e2)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    phi, lam = np.radians(lat), np.radians(lon)
    sp, cp = np.sin(phi), np.cos(phi)
    n = a / np.sqrt(1 - e2 * sp ** 2); t = np.tan(phi) ** 2; c = ep2 * cp ** 2; A = cp * (lam - lon0)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * np.sin(2 * phi)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * np.sin(4 * phi) - (35 * e2 ** 3 / 3072) * np.sin(6 * phi))
    x = k0 * n * (A + (1 - t + c) * A ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * A ** 5 / 120) + 500000
    y = k0 * (m + n * np.tan(phi) * (A * A / 2 + (5 - t + 9 * c + 4 * c * c) * A ** 4 / 24 + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * A ** 6 / 720))
    return x, (y + 10000000 if south else y)


def _scale(a, lo, hi):
    return np.clip((np.nan_to_num(a, nan=lo) - lo) / (hi - lo), 0, 1)


def render(frame, lon, lat):
    """lon, lat: 256x256 arrays of tile pixel centres. Returns WebP bytes or None."""
    with _lock:  # h5py over one HTTPS handle is not thread-safe
        h, m = _open(frame)
        ux, uy = lonlat_to_utm(lon, lat, m["zone"], m["south"])
        ix = np.floor((ux - m["x0"]) / m["dx"]).astype(np.int64)
        iy = np.floor((uy - m["y0"]) / m["dy"]).astype(np.int64)
        inside = (ix >= 0) & (ix < m["nx"]) & (iy >= 0) & (iy < m["ny"])
        if not inside.any():
            return None
        x0, x1 = int(ix[inside].min()), int(ix[inside].max()) + 1
        y0, y1 = int(iy[inside].min()), int(iy[inside].max()) + 1
        hh = m["g"]["HHHH"][y0:y1, x0:x1].astype(np.float32)
        hv = m["g"]["HVHV"][y0:y1, x0:x1].astype(np.float32) if m["hv"] else None
    jx, jy = np.clip(ix - x0, 0, x1 - x0 - 1), np.clip(iy - y0, 0, y1 - y0 - 1)
    shh = hh[jy, jx]
    with np.errstate(divide="ignore", invalid="ignore"):
        dhh = 10 * np.log10(np.where(shh > 0, shh, np.nan))
        if hv is not None:
            shv = hv[jy, jx]; dhv = 10 * np.log10(np.where(shv > 0, shv, np.nan))
            rgb = np.dstack([_scale(dhh, -22, -5), _scale(dhv, -28, -12), _scale(dhh - dhv, 0, 12)])
        else:
            g = _scale(dhh, -25, -3); rgb = np.dstack([g, g, g])
    alpha = (inside & np.isfinite(dhh)).astype(np.uint8) * 255
    if not alpha.any():
        return None
    buf = io.BytesIO()
    Image.fromarray(np.dstack([(rgb * 255).astype(np.uint8), alpha]), "RGBA").save(buf, "WEBP", quality=85, method=2)
    return buf.getvalue()


def utm_to_lonlat(x, y, zone, south):
    """Vectorised UTM -> WGS84 (Snyder inverse series), used to find a box's tile range."""
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f); ep2 = e2 / (1 - e2); e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    x = np.asarray(x, float) - 500000; y = np.asarray(y, float) - (10000000 if south else 0)
    mu = y / k0 / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    p1 = mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu) + (151 * e1 ** 3 / 96) * np.sin(6 * mu)
    n1 = a / np.sqrt(1 - e2 * np.sin(p1) ** 2); t1 = np.tan(p1) ** 2; c1 = ep2 * np.cos(p1) ** 2
    r1 = a * (1 - e2) / (1 - e2 * np.sin(p1) ** 2) ** 1.5; d = x / (n1 * k0)
    lat = p1 - (n1 * np.tan(p1) / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24 + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / np.cos(p1)
    return np.degrees(lon) + (zone - 1) * 6 - 180 + 3, np.degrees(lat)
