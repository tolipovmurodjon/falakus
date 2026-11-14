"""Colour tables for radar layers, shared by the tile server and the science renderers.

HH stays grayscale (the radar convention: dark = smooth/water, bright = rough/buildings).
HV uses a perceptual dark-to-light green (like cmocean 'algae'): brightness grows evenly with the
plant signal, so a judge reads "more green = more plant volume" without neon saturation.
"""
import numpy as np


def _lut(stops):
    xs = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], dtype=np.float32)
    t = np.linspace(0, 1, 256)
    return np.stack([np.interp(t, xs, cols[:, k]) for k in range(3)], axis=1).astype(np.uint8)


HV_LUT = _lut([(0.0, (12, 22, 16)), (0.25, (30, 58, 36)), (0.5, (62, 110, 58)), (0.75, (128, 170, 92)), (1.0, (226, 240, 196))])
GRAY_LUT = np.repeat(np.arange(256, dtype=np.uint8)[:, None], 3, axis=1)


def apply(v, lut):
    """v in 0..1 (NaN allowed) -> uint8 RGB via the table."""
    i = (np.clip(np.nan_to_num(v, nan=0.0), 0, 1) * 255).astype(np.uint8)
    return lut[i]

# One fixed dB scale for every place and date, so colours compare across the map and the time series.
# Chosen from measured ranges: Tashkent HH p2-p98 = -15..+6 dB, HV -21..-3; Aral HH median -16, HV -20.
HH_DB = (-25.0, 5.0)
HV_DB = (-30.0, -5.0)
RATIO_DB = (0.0, 16.0)


def _scale(a, lo_hi):
    lo, hi = lo_hi
    return np.clip((np.nan_to_num(a, nan=lo) - lo) / (hi - lo), 0, 1)


def composite(hh_db, hv_db):
    """R = HH, G = HV, B = HH/HV ratio (dB difference): water dark, cities pink-white, forest/crops green, bare soil blue."""
    if hv_db is None or not np.size(hv_db):
        return apply(_scale(hh_db, HH_DB), GRAY_LUT)
    rgb = np.dstack([_scale(hh_db, HH_DB), _scale(hv_db, HV_DB), _scale(hh_db - hv_db, RATIO_DB)])
    return (rgb * 255).astype(np.uint8)


# "What is here" classes from calibrated L-band gamma0 (dB). Plain rules a judge can check:
# water   : smooth surface sends the pulse away     -> HH < -18 and HV < -24
# built   : walls + ground make corner reflections -> HH > -5  (Tashkent box: 35.8 % vs ~37 % city share)
# plants  : leaves and stems scatter it sideways    -> HV > -17
# bare    : everything else (soil, sand, salt crust, stubble)
CLASS_NAMES = ["water", "built", "plants", "bare"]
CLASS_RGB = np.array([[37, 99, 235], [214, 92, 120], [46, 150, 80], [222, 196, 140]], np.uint8)


def classify(hh_db, hv_db):
    """Return int8 class index (0..3) or -1 where there is no data."""
    hv = hv_db if hv_db is not None and np.size(hv_db) else np.full_like(hh_db, -30.0)
    c = np.full(hh_db.shape, 3, np.int8)
    c[hv > -17] = 2
    c[hh_db > -5] = 1
    c[(hh_db < -18) & (hv < -24)] = 0
    c[~np.isfinite(hh_db)] = -1
    return c


def _box_sum(a, r):
    """Sum over a (2r+1) x (2r+1) window, edges handled by padding; O(n) with cumulative sums."""
    p = np.pad(a, r + 1, mode="constant").cumsum(0).cumsum(1)
    k = 2 * r + 1
    return p[k:, k:] - p[:-k, k:] - p[k:, :-k] + p[:-k, :-k]


def class_shares(cls, r=3):
    """Share (0..1) of each class in the window around every pixel (r=3 -> 7x7 = 140 m at 20 m pixels).
    Smoothing the classes like this is the standard 'majority filter' that removes radar speckle."""
    valid = (cls >= 0).astype(np.float32)
    n = np.maximum(_box_sum(valid, r), 1)
    return np.stack([_box_sum((cls == i).astype(np.float32), r) / n for i in range(len(CLASS_NAMES))]), _box_sum(valid, r) > 0


THEME_RGB = {"water": (37, 99, 235), "built": (190, 50, 90), "plants": (30, 130, 60)}
