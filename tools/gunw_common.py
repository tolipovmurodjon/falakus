"""Shared helpers for screening NISAR GUNW (geocoded unwrapped interferogram) BROWSE images.

What we can read without an Earthdata login: NASA CMR metadata (granule names, footprint polygons) and the public
browse PNG of each granule ("..._LATLON.png"): an RGBA picture of the WRAPPED interferometric phase on a north-up
lon/lat grid, transparent outside the swath. The science HDF5 (unwrapped phase, coherence, connected components,
ionosphere layers) needs a login, so everything here is SCREENING from NASA's browse images.

Georeferencing (measured, not assumed): the browse canvas is north-up equirectangular with ~0.00218 deg pixels and
a margin around the swath. We match the four extreme points of the opaque (alpha>0) region to the four corners of
the granule's CMR UMM polygon. On full frames the fit residual is <= 0.006 deg (about 2 px) on all four corners.

Colour -> phase: the browse uses a cyclic colour map (white -> blue -> dark purple -> orange -> white). Coherent
pixels trace a closed loop in RGB. We project RGB on the two main axes of that loop, take the angle around its
centre, and equalise that angle with its own cumulative histogram so that it is ~linear in phase. The sign of the
phase (toward / away from the satellite) is NOT recoverable from colours alone without the colour bar, so counts are
reported as fringe magnitudes.
"""
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = False
ROOT = Path(__file__).resolve().parent.parent
CMR = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
COLLECTIONS = {"C2854335566-ASF": "NISAR_L2_GUNW_PROVISIONAL_V1", "C3622247503-ASF": "NISAR_L2_GUNW_V1"}
WAVELENGTH_M = 0.2384          # NISAR L-band centre frequency 1.257 GHz -> c/f = 0.2384 m
FRINGE_CM = WAVELENGTH_M / 2 * 100   # one 2*pi cycle of interferometric phase = lambda/2 of line-of-sight motion = 11.92 cm
KM_PER_DEG = 111.32


def cmr_url(bbox, start, end, page=1):
    q = [("collection_concept_id", c) for c in COLLECTIONS] + [
        ("bounding_box", ",".join(f"{v:.4f}" for v in bbox)),
        ("temporal", f"{start}T00:00:00Z,{end}T23:59:59Z"), ("page_size", "200"), ("page_num", str(page)),
        ("sort_key", "start_date")]
    return CMR + "?" + urllib.parse.urlencode(q)


def parse_name(name):
    p = name.split("_")
    return {"name": name, "cycle": p[4], "track": p[5], "dir": p[6], "frame": p[7],
            "ref": p[11], "sec": p[13], "ref_date": f"{p[11][:4]}-{p[11][4:6]}-{p[11][6:8]}",
            "sec_date": f"{p[13][:4]}-{p[13][4:6]}-{p[13][6:8]}", "full_frame": p[-3] == "F",
            "days": (np.datetime64(f"{p[13][:4]}-{p[13][4:6]}-{p[13][6:8]}") -
                     np.datetime64(f"{p[11][:4]}-{p[11][4:6]}-{p[11][6:8]}")).astype(int).item()}


def search(bbox, start, end):
    """All GUNW granules (provisional + validated) touching bbox in [start, end]; one dict per granule."""
    out, page = {}, 1
    while True:
        with urllib.request.urlopen(cmr_url(bbox, start, end, page), timeout=90) as r:
            d = json.load(r)
        for it in d["items"]:
            u = it["umm"]
            pts = u["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]["GPolygons"][0]["Boundary"]["Points"]
            urls = [x["URL"] for x in u.get("RelatedUrls", []) if x["URL"].startswith("https")]
            png = next((x for x in urls if x.endswith("_LATLON.png")), None)
            g = parse_name(u["GranuleUR"])
            g.update(polygon=[[p["Longitude"], p["Latitude"]] for p in pts], browse=png,
                     h5=next((x for x in urls if x.endswith(".h5")), None),
                     collection=it["meta"]["collection-concept-id"])
            out[g["name"]] = g
        if len(d["items"]) < 200:
            break
        page += 1
    return sorted(out.values(), key=lambda g: (g["track"], g["dir"], g["ref"], g["frame"]))


def fetch(url, path):
    path = Path(path)
    if path.exists():
        try:
            Image.open(path).load()
            return path
        except Exception:
            path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "falakus-screening/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    path.write_bytes(data)
    Image.open(path).load()
    return path


def georef(alpha, polygon):
    """Fit lon = ox + sx*col, lat = oy + sy*row from alpha extremes <-> polygon corners. Returns dict or None."""
    ys, xs = np.nonzero(alpha)
    if len(xs) < 1000:
        return None
    pts = np.array(polygon[:-1] if polygon[0] == polygon[-1] else polygon)
    L = (xs.min(), ys[xs == xs.min()].mean()); R = (xs.max(), ys[xs == xs.max()].mean())
    T = (xs[ys == ys.min()].mean(), ys.min()); B = (xs[ys == ys.max()].mean(), ys.max())
    w, e = pts[pts[:, 0].argmin()], pts[pts[:, 0].argmax()]
    n, s = pts[pts[:, 1].argmax()], pts[pts[:, 1].argmin()]
    sx = (e[0] - w[0]) / max(R[0] - L[0], 1); ox = w[0] - sx * L[0]
    sy = (n[1] - s[1]) / min(T[1] - B[1], -1); oy = n[1] - sy * T[1]
    res = max(abs(oy + sy * L[1] - w[1]), abs(oy + sy * R[1] - e[1]), abs(ox + sx * T[0] - n[0]), abs(ox + sx * B[0] - s[0]))
    lat = pts[:, 1].mean()
    # pixel must be ~square on the ground and the four corners must agree
    ratio = (sx * math.cos(math.radians(lat))) / (-sy)
    ok = res < 0.02 and 0.9 < ratio < 1.1
    return {"ox": ox, "sx": sx, "oy": oy, "sy": sy, "residual_deg": float(res), "ok": bool(ok)}


def load_rgba(path):
    return np.asarray(Image.open(path).convert("RGBA"))


class PhaseFromColour:
    """Cyclic colour map -> phase in cycles [0,1). Learned once from coherent pixels of several images."""

    def __init__(self, samples_rgb):
        x = samples_rgb.astype(float)
        self.mu = x.mean(0)
        u, s, vt = np.linalg.svd(x - self.mu, full_matrices=False)
        self.axes = vt[:2]
        ang = self._angle(x)
        self.q = np.quantile(ang, np.linspace(0, 1, 513))

    def _angle(self, rgb):
        p = (rgb.astype(float) - self.mu) @ self.axes.T
        return np.arctan2(p[..., 1], p[..., 0])

    def __call__(self, rgb):
        a = self._angle(rgb)
        return np.interp(a, self.q, np.linspace(0, 1, 513)) % 1.0


def box(a, k):
    """Box mean with window k (odd), same shape, edges handled by cumulative sums."""
    pad = k // 2
    ap = np.pad(a, pad, mode="edge")
    c = ap.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return s / (k * k)


def fringe_fields(phase_cyc, valid, k=7):
    """Local fringe rate (cycles per pixel) in x/y and a pseudo-coherence in [0,1].

    For each neighbour pair the wrapped phase step is exp(i*2pi*dphi). Averaging those unit vectors over a k x k window:
    a smooth fringe pattern gives a consistent step (|mean| ~ 1), speckle noise (water, decorrelated ground) gives
    random steps (|mean| ~ 0). The angle of the mean is the local fringe rate.
    """
    z = np.exp(2j * np.pi * phase_cyc)
    zx = z[:, 1:] * np.conj(z[:, :-1]); zx = np.pad(zx, ((0, 0), (0, 1)), mode="edge")
    zy = z[1:, :] * np.conj(z[:-1, :]); zy = np.pad(zy, ((0, 1), (0, 0)), mode="edge")
    v = valid.astype(float)
    vx = v * np.roll(v, -1, 1); vy = v * np.roll(v, -1, 0)
    mx = box(zx.real * vx, k) + 1j * box(zx.imag * vx, k); nx = box(vx, k) + 1e-9
    my = box(zy.real * vy, k) + 1j * box(zy.imag * vy, k); ny = box(vy, k) + 1e-9
    mx, my = mx / nx, my / ny
    coh = 0.5 * (np.abs(mx) + np.abs(my))
    gx = np.angle(mx) / (2 * np.pi); gy = np.angle(my) / (2 * np.pi)
    return gx, gy, coh * (box(v, k) > 0.6)
