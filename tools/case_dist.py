"""Independent cross-check: NASA OPERA DIST-ALERT (HLS optical vegetation-disturbance status) from GIBS.

We did not make this product, so agreement with it is an outside check of a radar flag.
GIBS colour classes (colormap OPERA_Vegetation_Disturbance_Status.xml): 0 no disturbance (18,18,18);
1 first detection <50 %, 2 provisional <50 %, 3 confirmed <50 %, 4 first >=50 %, 5 provisional >=50 %,
6 confirmed >=50 %, 7 confirmed <50 % finished, 8 confirmed >=50 % finished; transparent = no data (cloud / no HLS).
Pixels whose colour is not a palette entry (grey static seen in some GIBS DIST tiles) are treated as no data.
"Disturbed" here = any class 1-8. Each GIBS day only holds that day's HLS scenes, so each side is a composite:
for every pixel, the LATEST valid value in a window of WIN days ending on the date.
NEW disturbance in the window = disturbed after AND not disturbed before (both seen).
"""
import datetime as dt

import numpy as np
from scipy import ndimage

from case_common import DIST_LAYER, mosaic

WIN = 10
DIST_LATEST = "2026-11-05"  # last DIST-ALERT date in GIBS GetCapabilities on 15 Nov 2026
COLORS = np.array([(18, 18, 18), (0, 85, 85), (137, 127, 78), (222, 224, 67), (0, 136, 136), (228, 135, 39),
                   (224, 27, 7), (119, 119, 119), (221, 221, 221)])


def classify(im):
    a = im[..., 3] > 0
    d = ((im[..., None, :3].astype(int) - COLORS[None, None]) ** 2).sum(-1)
    cls = d.argmin(-1)
    exact = d.min(-1) <= 3 * 6 ** 2  # colour must be a palette entry; GIBS also returns grey static that is not
    return np.where(a & exact, cls, -1)


def composite(bbox, end, z, win=WIN, forward=False):
    """Latest valid class per pixel over [end-win, end] (or earliest over [end, end+win] if forward)."""
    e = dt.date.fromisoformat(end)
    days = [e + dt.timedelta(i) for i in range(0, win + 1)] if forward else [e - dt.timedelta(i) for i in range(0, win + 1)]
    days = [d for d in days if d.isoformat() <= DIST_LATEST]
    out, used = None, []
    for d in days:  # nearest day to `end` first; first valid value wins
        im, info = mosaic(*DIST_LAYER, d.isoformat(), bbox, z, guard=False)
        c = classify(im)
        if out is None:
            out = np.full(c.shape, -1)
        fill = (out < 0) & (c >= 0)
        if fill.any():
            used.append(d.isoformat())
        out[fill] = c[fill]
    return out, used


def agreement(flag, valid, bbox, before, after, z, tol_px=1):
    """Both-direction agreement between a radar flag mask and NEW DIST disturbance between before and after."""
    b, ub = composite(bbox, before, z)
    a, ua = composite(bbox, after, z, forward=True)
    if a.shape != flag.shape:
        a = a[:flag.shape[0], :flag.shape[1]]
        b = b[:flag.shape[0], :flag.shape[1]]
    seen = valid & (a >= 0) & (b >= 0)
    new = seen & (a >= 1) & (b == 0)
    res = dict(product="OPERA_L3_DIST-ALERT-HLS_Color_Index (GIBS)", before_window_days=ub, after_window_days=ua,
               seen_by_both_pct=round(float(seen.sum() / max(valid.sum(), 1) * 100), 1), tolerance_px=tol_px,
               disturbed_def="any DIST class 1-8 after, class 0 before")
    if seen.sum() < 1000:
        res["result"] = "no independent product covers this event (too few cloud-free DIST pixels on both sides)"
        return res
    st = np.ones((3, 3), bool)
    newd = ndimage.binary_dilation(new, st, tol_px) if tol_px else new
    fl = flag & seen
    fld = ndimage.binary_dilation(fl, st, tol_px) if tol_px else fl
    res.update(radar_flag_px=int(fl.sum()), dist_new_px=int(new.sum()),
               dist_new_share_of_seen_pct=round(float(new.sum() / seen.sum() * 100), 2),
               radar_flag_share_of_seen_pct=round(float(fl.sum() / seen.sum() * 100), 2),
               radar_flags_also_dist_pct=round(float((fl & newd).sum() / max(fl.sum(), 1) * 100), 1) if fl.sum() else None,
               dist_new_also_radar_pct=round(float((new & fld).sum() / max(new.sum(), 1) * 100), 1) if new.sum() else None)
    # chance level: a random pixel lands within tol of DIST-new this often
    res["chance_radar_flags_also_dist_pct"] = round(float((newd & seen).sum() / seen.sum() * 100), 1)
    res["chance_dist_new_also_radar_pct"] = round(float((fld & seen).sum() / seen.sum() * 100), 1)
    return res


# ---------------- OPERA DSWx-S1 (water) ----------------
DSWX_LAYER = ("OPERA_L3_Dynamic_Surface_Water_Extent-Sentinel-1", "GoogleMapsCompatible_Level12")
# colormap OPERA_Dynamic_Surface_Water_Extent_S1.xml: 0 not water (255,255,255), 1 open water (0,0,255),
# 3 (0,255,0), 250 HAND-masked (200,200,200), 251 layover/shadow (128,128,128); transparent = no data
DSWX_COLORS = np.array([(255, 255, 255), (0, 0, 255), (0, 255, 0), (200, 200, 200), (128, 128, 128)])


def dswx_classes(im):
    a = im[..., 3] > 0
    d = ((im[..., None, :3].astype(int) - DSWX_COLORS[None, None]) ** 2).sum(-1)
    c = d.argmin(-1)
    ok = a & (d.min(-1) <= 3 * 6 ** 2) & (c <= 1)  # only clear water / not-water count as seen
    return np.where(ok, c, -1)


def dswx_compare(water, valid, bbox, date, z, win=6):
    """NISAR dark-water mask vs OPERA DSWx-S1 open water (class 1), composite of the days nearest `date` (+-win)."""
    e = dt.date.fromisoformat(date)
    days = [e]
    for i in range(1, win + 1):
        days += [e - dt.timedelta(i), e + dt.timedelta(i)]
    out, used = None, []
    for d in days:
        if d > dt.date.today():
            continue
        im, _ = mosaic(*DSWX_LAYER, d.isoformat(), bbox, z, guard=False)
        c = dswx_classes(im)[:water.shape[0], :water.shape[1]]
        if out is None:
            out = np.full(water.shape, -1)
        fill = (out < 0) & (c >= 0)
        if fill.any():
            used.append(d.isoformat())
        out[fill] = c[fill]
    seen = valid & (out >= 0)
    res = dict(product="OPERA_L3_Dynamic_Surface_Water_Extent-Sentinel-1 (GIBS)", days_used=used, seen_pct=round(float(seen.sum() / max(valid.sum(), 1) * 100), 1))
    if seen.sum() < 500:
        res["result"] = "no independent product covers this place on these dates (too few DSWx-S1 pixels)"
        return res
    dw = seen & (out == 1)
    nw = seen & water
    inter = (dw & nw).sum()
    res.update(nisar_dark_also_dswx_pct=round(float(inter / max(nw.sum(), 1) * 100), 1),
               dswx_water_also_nisar_pct=round(float(inter / max(dw.sum(), 1) * 100), 1),
               iou=round(float(inter / max((dw | nw).sum(), 1)), 3), dswx_water_pct_of_seen=round(float(dw.sum() / seen.sum() * 100), 2),
               nisar_dark_pct_of_seen=round(float(nw.sum() / seen.sum() * 100), 2))
    return res
