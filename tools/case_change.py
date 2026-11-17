"""Radar change screening from NASA GIBS NISAR tiles: the "4x normal wobble" test, on display-scaled radar.

Input: three same-track NISAR dates over a box: prior, before, after (tools/case_passes.py finds them).
  quiet pair  = before - prior   (nothing should have happened: tells us how much the radar wobbles anyway)
  event pair  = after  - before   (or after - start, if a "start" date is given: long-span change)
Steps (all on GIBS PNG values 0-255, NOT calibrated dB):
  1. Mosaic GIBS tiles over the box at zoom z; drop scrambled tiles (random alpha / grey static) and no-data.
  2. Channel: HH = red (GIBS colour: R = B = HH, G = HV) or HV = green.
  3. 3x3 mean over valid pixels (speckle), then differences; each pair's median is removed (date-to-date offset).
  4. Robust spread of the quiet pair: sigma = 1.4826 x MAD. Flag event pixels with |change| > K x sigma (K = 4).
  5. Keep flagged groups of >= MIN_PX connected pixels (8-connected) so single speckle pixels don't count.
  6. False-alarm baseline: the same test applied to the quiet pair itself.
Output: flagged km2 (brighter / darker), quiet-pair km2, a transparent PNG change map over the bbox
(EPSG:3857 image stretched over the lon/lat bbox): orange = brighter, blue = darker.
Display-scaled GIBS radar, not calibrated dB; screening only.
"""
import numpy as np
from PIL import Image
from scipy import ndimage

from case_common import NISAR_LAYER, mosaic

K = 4.0
MIN_PX = 4
ORANGE = (232, 89, 12, 230)
BLUE = (28, 91, 217, 230)


def channel(im, ch):
    return im[..., {"HH": 0, "HV": 1}[ch]].astype(float)


def smooth(x, valid):
    w = ndimage.uniform_filter(valid.astype(float), 3)
    s = ndimage.uniform_filter(np.where(valid, x, 0.0), 3)
    return np.where(w > 0, s / np.maximum(w, 1e-9), 0.0)


def keep_groups(m, min_px=MIN_PX):
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    if n == 0:
        return m
    size = np.bincount(lab.ravel())
    ok = np.flatnonzero(size >= min_px)
    ok = ok[ok > 0]
    return np.isin(lab, ok)


def load(dates, bbox, z):
    ims, infos = {}, {}
    for k, d in dates.items():
        ims[k], infos[k] = mosaic(*NISAR_LAYER, d, bbox, z)
    return ims, infos


def screen(bbox, dates, z=11, ch="HH", out_png=None, k=K, sign=0):
    """dates: dict(prior=, before=, after=) as YYYY-MM-DD. sign: 0 both directions, -1 only drops, +1 only rises."""
    ims, infos = load(dates, bbox, z)
    valid = np.ones(ims["after"].shape[:2], bool)
    for im in ims.values():
        valid &= im[..., 3] == 255
    vf = valid.copy()
    sm = {kk: smooth(channel(im, ch), vf) for kk, im in ims.items()}
    valid = ndimage.binary_erosion(valid, np.ones((3, 3)))  # no edge pixels
    px_km2 = infos["after"]["pixel_km2"]
    res = dict(bbox=bbox, dates=dates, zoom=z, channel=ch, k=k, min_group_px=MIN_PX, pixel_m=infos["after"]["pixel_m"],
               tiles={kk: v["tiles"] for kk, v in infos.items()}, valid_km2=round(float(valid.sum() * px_km2), 1))
    if valid.sum() < 1000:
        res["error"] = "too few valid pixels on all dates"
        return res, None
    rb = ims["after"][..., 0][valid].astype(int) - ims["after"][..., 2][valid].astype(int)
    res["r_minus_b_abs_median"] = float(np.median(np.abs(rb)))
    evt = sm["after"] - sm["start" if "start" in sm else "before"]  # optional explicit event start (long-span change)
    evt -= np.median(evt[valid])
    flags = {}
    if "prior" in sm:
        q = sm["before"] - sm["prior"]
        q -= np.median(q[valid])
        mad = float(np.median(np.abs(q[valid])))
        sigma = 1.4826 * mad
        res["quiet_sigma"] = round(sigma, 2)
        res["threshold"] = round(k * sigma, 2)
        res["threshold_from"] = f"{k:g} x robust spread (1.4826 x MAD) of the quiet pair {dates['prior']} -> {dates['before']}"

        def flag(x):
            hi = keep_groups(valid & (x > k * sigma)) if sign >= 0 else np.zeros_like(valid)
            lo = keep_groups(valid & (x < -k * sigma)) if sign <= 0 else np.zeros_like(valid)
            return hi, lo
        qh, ql = flag(q)
        res["quiet_flag_km2"] = round(float((qh | ql).sum() * px_km2), 2)
        res["quiet_flag_pct"] = round(float((qh | ql).sum() / valid.sum() * 100), 3)
    hi, lo = flag(evt)
    res["brighter_km2"] = round(float(hi.sum() * px_km2), 2)
    res["darker_km2"] = round(float(lo.sum() * px_km2), 2)
    res["flag_km2"] = round(float((hi | lo).sum() * px_km2), 2)
    res["flag_pct"] = round(float((hi | lo).sum() / valid.sum() * 100), 3)
    res["event_spread"] = round(1.4826 * float(np.median(np.abs(evt[valid]))), 2)
    res["ratio_vs_quiet"] = round(res["flag_km2"] / res["quiet_flag_km2"], 2) if res.get("quiet_flag_km2") else None
    if out_png:
        rgba = np.zeros(valid.shape + (4,), np.uint8)
        rgba[valid] = (255, 255, 255, 40)
        rgba[hi] = ORANGE
        rgba[lo] = BLUE
        out_png.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgba).save(out_png, optimize=True)
        res["png"] = str(out_png)
    res["label"] = "display-scaled GIBS radar, not calibrated dB; screening only"
    return res, dict(hi=hi, lo=lo, valid=valid, ims=ims)
