"""WGS84 <-> UTM conversions (Snyder series), vectorised with numpy.

Used to place calibrated NISAR GCOV boxes (stored on their UTM grid) onto Web Mercator map tiles.
"""
import math

import numpy as np


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
