"""Panama M7.7 (9 Oct 2026, USGS us6000u18k): screen NISAR interferograms (GUNW browse images) for ground motion.

Method (what an InSAR analyst does first, before downloading any HDF5):
  1. List every GUNW pair over the epicentre in CMR (provisional + validated collections).
  2. EVENT pairs span the quake (reference < 9 Oct 17:56 UTC < secondary). CONTROL pairs are on the SAME track,
     direction and frame and end before the quake: same viewing geometry, so anything they also show (orbit ramps,
     ionosphere, troposphere) is not the earthquake.
  3. Georeference each browse PNG from its CMR footprint polygon, mosaic the frames of a pair on one lon/lat grid.
  4. Turn colour back into wrapped phase (cyclic colour map), measure local fringe rate and a pseudo-coherence.
  5. Count fringes along transects through the epicentre (1 fringe = lambda/2 = 11.92 cm line-of-sight), compare
     near-fault vs far-field, event vs control, and against an independent prediction: the USGS finite-fault model's
     surface displacement projected on the radar line of sight, plus USGS's own NISAR range-offset measurements.

Output: data/cases/gunw/panama_summary.json and data/cases/gunw/panama_event_vs_control.jpg
Usage:  python tools/gunw_panama.py
"""
import io
import json
import math
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gunw_common import (FRINGE_CM, KM_PER_DEG, PhaseFromColour, cmr_url, fetch, fringe_fields, georef,  # noqa: E402
                         load_rgba, search)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/cases/gunw"
EVENT_ID = "us6000u18k"
USGS_EVENT = f"https://earthquake.usgs.gov/earthquakes/eventpage/{EVENT_ID}"
USGS_API = f"https://earthquake.usgs.gov/fdsnws/event/1/query?eventid={EVENT_ID}&format=geojson"
EVENT_T = np.datetime64("2026-10-09T17:56")
SEARCH_BBOX = (-81.4, 7.2, -80.2, 7.9)     # around the USGS finite-fault rupture
GRID = (-81.75, 6.95, -79.75, 8.45, 0.0022)  # lon0, lat0, lon1, lat1, step (deg) ~ browse pixel size
BORDER_RGB = (47, 19, 55)                   # constant fill colour on the swath edge (no data)
COH_MIN = 0.5
TRANSECT_KM = 60


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "falakus/1.0"}), timeout=90) as r:
        return json.load(r)


def get_bytes(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "falakus/1.0"}), timeout=120) as r:
        return r.read()


# ---------------------------------------------------------------- USGS: epicentre, finite fault, predicted motion
def usgs():
    ev = get_json(USGS_API)
    lon, lat, dep = ev["geometry"]["coordinates"]
    ff = ev["properties"]["products"]["finite-fault"][0]
    c = ff["contents"]
    ffm = json.loads(get_bytes(c["FFM.geojson"]["url"]))
    disp = np.loadtxt(io.StringIO(get_bytes(c["surface_deformation.disp"]["url"]).decode()), comments="#")
    disp[:, 0] = np.where(disp[:, 0] > 180, disp[:, 0] - 360, disp[:, 0])
    rng = {}
    z = zipfile.ZipFile(io.BytesIO(get_bytes(c["resampled_interferograms.zip"]["url"])))
    for n in z.namelist():
        if n.endswith(".txt"):
            track = n.split("-p")[1][:3]
            rng[track] = {"file": n, "data": np.loadtxt(io.StringIO(z.read(n).decode()), comments="#")}
    patches = [f["geometry"]["coordinates"][0] for f in ffm["features"]]
    slip = [f["properties"]["slip"] for f in ffm["features"]]
    return {"lon": lon, "lat": lat, "depth_km": dep, "mag": ev["properties"]["mag"], "time": ev["properties"]["time"],
            "ff_props": ff["properties"], "ff_url": c["FFM.geojson"]["url"], "disp_url": c["surface_deformation.disp"]["url"],
            "rng_url": c["resampled_interferograms.zip"]["url"], "patches": patches, "slip": slip, "disp": disp, "rngoff": rng}


def model_grid(disp):
    """Regular grid (lat, lon) of the USGS model E, N, U surface displacement (m)."""
    lons = np.unique(np.round(disp[:, 0], 4)); lats = np.unique(np.round(disp[:, 1], 4))
    E = np.full((len(lats), len(lons)), np.nan); N = E.copy(); U = E.copy()
    ix = np.searchsorted(lons, np.round(disp[:, 0], 4)); iy = np.searchsorted(lats, np.round(disp[:, 1], 4))
    E[iy, ix], N[iy, ix], U[iy, ix] = disp[:, 3], disp[:, 4], disp[:, 5]
    return lons, lats, E, N, U


def bilinear(lons, lats, A, lon, lat):
    fx = np.interp(lon, lons, np.arange(len(lons))); fy = np.interp(lat, lats, np.arange(len(lats)))
    x0 = np.clip(np.floor(fx).astype(int), 0, len(lons) - 2); y0 = np.clip(np.floor(fy).astype(int), 0, len(lats) - 2)
    tx, ty = fx - x0, fy - y0
    return (A[y0, x0] * (1 - tx) * (1 - ty) + A[y0, x0 + 1] * tx * (1 - ty) + A[y0 + 1, x0] * (1 - tx) * ty + A[y0 + 1, x0 + 1] * tx * ty)


def look_vectors(rng):
    """Unit look vectors (USGS convention, from their NISAR range-offset files) per direction.

    Descending vectors come straight from USGS track 141/040 files. Ascending NISAR (right-looking, heading ~350 deg)
    mirrors the east component; we use that mirror as an approximation (flagged in the JSON)."""
    d = np.median(np.vstack([v["data"][:, 3:6] for v in rng.values()]), axis=0)
    return {"D": d, "A": np.array([-d[0], d[1], d[2]])}


# ---------------------------------------------------------------- granules -> pairs
def pairs_from_cmr():
    gs = search(SEARCH_BBOX, "2026-07-01", "2026-11-15")
    pairs = {}
    for g in gs:
        if not g["browse"]:
            continue
        key = (g["track"], g["dir"], g["ref"][:8], g["sec"][:8])
        pairs.setdefault(key, []).append(g)
    out = []
    for (track, d, r, s), frames in pairs.items():
        t0 = np.datetime64(frames[0]["ref_date"]); t1 = np.datetime64(frames[0]["sec_date"])
        kind = "event" if (np.datetime64(f"{r[:4]}-{r[4:6]}-{r[6:]}T{frames[0]['ref'][9:11]}:{frames[0]['ref'][11:13]}") < EVENT_T <
                           np.datetime64(f"{s[:4]}-{s[4:6]}-{s[6:]}T{frames[0]['sec'][9:11]}:{frames[0]['sec'][11:13]}")) else (
            "control" if t1 <= EVENT_T.astype("datetime64[D]") else "after")
        out.append({"track": track, "dir": d, "ref_date": frames[0]["ref_date"], "sec_date": frames[0]["sec_date"],
                    "days": frames[0]["days"], "kind": kind, "frames": frames})
    return sorted(out, key=lambda p: (p["track"], p["dir"], p["ref_date"]))


def local_path(g, kind):
    sub = OUT if kind == "event" else OUT / "control" if kind == "control" else OUT / "after"
    return sub / (g["name"] + "_LATLON.png")


# ---------------------------------------------------------------- mosaic + colour model
def grid_axes():
    lon0, lat0, lon1, lat1, st = GRID
    lons = np.arange(lon0, lon1, st); lats = np.arange(lat1, lat0, -st)
    return lons, lats


def mosaic(pair, kind, calib):
    lons, lats = grid_axes()
    LON, LAT = np.meshgrid(lons, lats)
    rgb = np.zeros(LON.shape + (3,), np.uint8); ok = np.zeros(LON.shape, bool)
    geo_notes = []
    # frames with more valid data last (they win overlaps)
    for g in pair["frames"]:
        p = local_path(g, kind)
        if not p.exists():
            continue
        a = load_rgba(p)
        alpha = a[..., 3] > 0
        gr = georef(alpha, g["polygon"])
        stack = (g["track"], g["dir"], g["frame"], a.shape)
        if gr and gr["ok"]:
            calib.setdefault(stack, gr)
        else:
            # partial data inside the frame: reuse the transform of a full image of the same stack (same canvas)
            if stack in calib:
                gr = dict(calib[stack], ok=True, residual_deg=None, borrowed=True)
            else:
                geo_notes.append(f"{g['frame']}: no reliable georeference, skipped")
                continue
        g["georef"] = {k: (round(v, 7) if isinstance(v, float) else v) for k, v in gr.items()}
        col = np.round((LON - gr["ox"]) / gr["sx"]).astype(int); row = np.round((LAT - gr["oy"]) / gr["sy"]).astype(int)
        inside = (col >= 0) & (col < a.shape[1]) & (row >= 0) & (row < a.shape[0])
        cc, rr = np.clip(col, 0, a.shape[1] - 1), np.clip(row, 0, a.shape[0] - 1)
        px = a[rr, cc]
        good = inside & (px[..., 3] > 0) & ~np.all(px[..., :3] == BORDER_RGB, axis=-1)
        take = good & ~ok
        rgb[take] = px[take][:, :3]; ok |= good
    return rgb, ok, geo_notes


def colour_model(mosaics):
    samp = []
    rs = np.random.default_rng(0)
    for rgb, ok in mosaics:
        v = rgb[ok]
        if len(v):
            samp.append(v[rs.choice(len(v), min(len(v), 40000), replace=False)])
    pfc0 = PhaseFromColour(np.vstack(samp))
    # second pass: refit the angle equalisation on COHERENT pixels only (noise is not uniformly distributed in colour)
    samp2 = []
    for rgb, ok in mosaics:
        ph = pfc0(rgb)
        _, _, coh = fringe_fields(ph, ok)
        v = rgb[ok & (coh > 0.7)]
        if len(v):
            samp2.append(v[rs.choice(len(v), min(len(v), 40000), replace=False)])
    return PhaseFromColour(np.vstack(samp2)) if samp2 else pfc0


# ---------------------------------------------------------------- measurements
def km_xy(lon, lat, lon0, lat0):
    return (lon - lon0) * KM_PER_DEG * math.cos(math.radians(lat0)), (lat - lat0) * KM_PER_DEG


def transect_points(lon0, lat0, az_deg, half_km, step_km=0.24):
    s = np.arange(-half_km, half_km + 1e-6, step_km)
    dx, dy = s * math.sin(math.radians(az_deg)), s * math.cos(math.radians(az_deg))
    return s, lon0 + dx / (KM_PER_DEG * math.cos(math.radians(lat0))), lat0 + dy / KM_PER_DEG


def sample(A, lon, lat):
    lons, lats = grid_axes(); st = GRID[4]
    c = np.round((lon - lons[0]) / st).astype(int); r = np.round((lats[0] - lat) / st).astype(int)
    inside = (c >= 0) & (c < A.shape[1]) & (r >= 0) & (r < A.shape[0])
    v = np.full(lon.shape, np.nan)
    v[inside] = A[r[inside], c[inside]]
    return v


def count_fringes(s, ph, coh, ramp_cyc_per_km=0.0):
    """Walk the transect; inside coherent runs add wrapped phase steps. Returns totals and segment details.

    'abs_sum' = sum over coherent runs of |net fringes in the run|: a lower bound on fringes crossed (phase across
    incoherent gaps is unknown). ramp is removed per km of transect when given (deramped count)."""
    good = (coh > COH_MIN) & np.isfinite(ph)
    runs, cur = [], []
    for i in range(len(s)):
        if good[i]:
            cur.append(i)
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    runs = [r for r in runs if len(r) >= 8]   # >= ~2 km of continuous coherent phase
    segs = []
    for r in runs:
        d = np.diff(ph[r]); d = (d + 0.5) % 1.0 - 0.5
        d = d - ramp_cyc_per_km * np.diff(s[r])
        segs.append({"from_km": round(float(s[r[0]]), 1), "to_km": round(float(s[r[-1]]), 1), "net_fringes": round(float(d.sum()), 2)})
    covered = sum(sg["to_km"] - sg["from_km"] for sg in segs)
    return {"abs_fringes": round(sum(abs(sg["net_fringes"]) for sg in segs), 1), "coherent_km": round(covered, 1),
            "length_km": round(float(s[-1] - s[0]), 1), "segments": len(segs), "segs": segs}


def analyse(rgb, ok, pfc, lon0, lat0):
    ph = pfc(rgb); ph[~ok] = np.nan
    gx, gy, coh = fringe_fields(np.nan_to_num(ph), ok)
    lons, lats = grid_axes(); LON, LAT = np.meshgrid(lons, lats)
    X, Y = km_xy(LON, LAT, lon0, lat0); R = np.hypot(X, Y)
    px_km_x = GRID[4] * KM_PER_DEG * math.cos(math.radians(lat0)); px_km_y = GRID[4] * KM_PER_DEG
    fx, fy = gx / px_km_x, -gy / px_km_y          # cycles per km, east / north
    rate = np.hypot(fx, fy)
    c = coh > COH_MIN
    near, far = c & (R <= 30), c & (R >= 60) & (R <= 110)
    ramp = (float(np.median(fx[far])), float(np.median(fy[far]))) if far.sum() > 500 else (0.0, 0.0)
    res = np.hypot(fx - ramp[0], fy - ramp[1])
    stats = {
        "valid_px_within_30km": int((ok & (R <= 30)).sum()),
        "coherent_frac_within_30km": round(float(c[R <= 30].sum() / max((ok & (R <= 30)).sum(), 1)), 3),
        "coherent_frac_60_110km": round(float(c[(R >= 60) & (R <= 110)].sum() / max((ok & (R >= 60) & (R <= 110)).sum(), 1)), 3),
        "fringe_rate_near_cyc_per_km": round(float(np.median(rate[near])), 3) if near.sum() > 200 else None,
        "fringe_rate_far_cyc_per_km": round(float(np.median(rate[far])), 3) if far.sum() > 200 else None,
        "ramp_cyc_per_km_east_north": [round(ramp[0], 3), round(ramp[1], 3)],
        "ramp_fringes_per_100km": round(100 * math.hypot(*ramp), 1),
        "deramped_rate_near": round(float(np.median(res[near])), 3) if near.sum() > 200 else None,
        "deramped_rate_far": round(float(np.median(res[far])), 3) if far.sum() > 200 else None,
    }
    return ph, coh, rate, res, ramp, stats


# ---------------------------------------------------------------- figure
def render_panel(rgb, ok, coh, title, sub, ev, patches, transects, crop, size=520):
    lons, lats = grid_axes(); st = GRID[4]
    lo0, la0, lo1, la1 = crop
    c0, c1 = int((lo0 - lons[0]) / st), int((lo1 - lons[0]) / st)
    r0, r1 = int((lats[0] - la1) / st), int((lats[0] - la0) / st)
    img = np.full(rgb.shape, 255, np.uint8); img[ok] = rgb[ok]
    # grey-out incoherent pixels lightly so coherent fringes stand out
    inc = ok & (coh <= COH_MIN)
    img[inc] = (0.35 * img[inc] + 0.65 * 200).astype(np.uint8)
    im = Image.fromarray(img[r0:r1, c0:c1]).resize((size, int(size * (r1 - r0) / (c1 - c0))), Image.BILINEAR)
    W, H = im.size
    d = ImageDraw.Draw(im)

    def xy(lon, lat):
        return (lon - lo0) / (lo1 - lo0) * W, (la1 - lat) / (la1 - la0) * H
    # rupture outline: convex hull of all USGS finite-fault patches (surface projection)
    d.line([xy(*pt) for pt in hull(patches)] + [xy(*hull(patches)[0])], fill=(10, 10, 10), width=2)
    for name, (lo, la) in transects.items():
        d.line([xy(lo[0], la[0]), xy(lo[-1], la[-1])], fill=(0, 0, 0), width=2)
        d.text(xy(lo[-1], la[-1]), name, fill=(0, 0, 0), font=FONT_S)
    x, y = xy(ev["lon"], ev["lat"])
    star = [(x + r * math.sin(a), y - r * math.cos(a)) for i in range(10) for a, r in [(i * math.pi / 5, 13 if i % 2 == 0 else 5.5)]]
    d.polygon(star, fill=(255, 215, 0), outline=(0, 0, 0))
    canvas = Image.new("RGB", (W, H + 46), "white")
    canvas.paste(im, (0, 46))
    dd = ImageDraw.Draw(canvas)
    dd.text((6, 4), title, fill=(0, 0, 0), font=FONT_B)
    dd.text((6, 26), sub, fill=(60, 60, 60), font=FONT_S)
    dd.rectangle([0, 46, W - 1, H + 45], outline=(0, 0, 0))
    return canvas


def hull(patches):
    pts = sorted({(round(p[0], 5), round(p[1], 5)) for pa in patches for p in pa})
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def font(sz, bold=False):
    for f in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else []) + ["/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"]:
        try:
            return ImageFont.truetype(f, sz)
        except Exception:
            pass
    return ImageFont.load_default()


FONT_B, FONT_S = font(17, True), font(13)


# ---------------------------------------------------------------- main
def main():
    ev = usgs()
    lon0, lat0 = ev["lon"], ev["lat"]
    print(f"USGS {EVENT_ID}: M{ev['mag']} at {lon0},{lat0} depth {ev['depth_km']} km")
    pairs = pairs_from_cmr()
    # keep event pairs, and controls that are 12-day and on the same track/dir as an event pair
    ev_keys = {(p["track"], p["dir"]) for p in pairs if p["kind"] == "event"}
    pairs = [p for p in pairs if p["kind"] == "event" or (p["kind"] == "control" and (p["track"], p["dir"]) in ev_keys)]
    for p in pairs:
        for g in p["frames"]:
            try:
                fetch(g["browse"], local_path(g, p["kind"]))
            except Exception as e:
                print("download failed", g["name"], e)
    calib, mos = {}, {}
    # calibrate stacks from full images first (event + controls), then mosaic
    for p in sorted(pairs, key=lambda p: -sum(g["full_frame"] for g in p["frames"])):
        rgb, ok, notes = mosaic(p, p["kind"], calib)
        mos[id(p)] = (rgb, ok); p["geo_notes"] = notes
    pfc = colour_model(list(mos.values()))
    lv = look_vectors(ev["rngoff"])
    mlon, mlat, E, N, U = model_grid(ev["disp"])
    strike = float(ev["ff_props"].get("model-strike", 295))
    tr_def = {"along-strike": strike % 180, "across-strike": (strike + 90) % 180, "N-S": 0.0}
    tr_pts = {k: transect_points(lon0, lat0, az, TRANSECT_KM) for k, az in tr_def.items()}

    # predicted LOS (USGS finite-fault model) and USGS NISAR range-offset LOS along each transect
    def predicted(direction, s, lo, la):
        e, n, u = (bilinear(mlon, mlat, A, lo, la) for A in (E, N, U))
        los = e * lv[direction][0] + n * lv[direction][1] + u * lv[direction][2]
        return los

    results = []
    for p in pairs:
        rgb, ok = mos[id(p)]
        if ok.sum() < 1000:
            p["note"] = "no browse data on the grid"
            continue
        ph, coh, rate, res, ramp, stats = analyse(rgb, ok, pfc, lon0, lat0)
        p["stats"] = stats
        p["transects"] = {}
        for name, (s, lo, la) in tr_pts.items():
            phs, cs = sample(ph, lo, la), sample(coh, lo, la)
            ramp_along = ramp[0] * math.sin(math.radians(tr_def[name])) + ramp[1] * math.cos(math.radians(tr_def[name]))
            raw = count_fringes(s, phs, cs)
            der = count_fringes(s, phs, cs, ramp_along)
            pred = predicted(p["dir"], s, lo, la)
            ok_pred = np.isfinite(pred)
            pred_fr = float(np.nansum(np.abs(np.diff(pred[ok_pred])))) * 100 / FRINGE_CM if ok_pred.sum() > 2 else None
            p["transects"][name] = {
                "azimuth_deg": round(tr_def[name], 1), "raw": {k: v for k, v in raw.items() if k != "segs"},
                "deramped": {k: v for k, v in der.items() if k != "segs"}, "segments_deramped": der["segs"],
                "los_cm_range_deramped": [round(max(der["abs_fringes"] - 1, 0) * FRINGE_CM, 1), round((der["abs_fringes"] + 1) * FRINGE_CM, 1)],
                "usgs_model_fringes_along_line": round(pred_fr, 1) if pred_fr is not None else None,
                "usgs_model_los_span_cm": round(float(np.nanmax(pred) - np.nanmin(pred)) * 100, 1) if ok_pred.sum() > 2 else None,
            }
        p["_ph"], p["_coh"] = ph, coh
        results.append(p)
        print(f"{p['kind']:7s} {p['track']}{p['dir']} {p['ref_date']}->{p['sec_date']} ({p['days']}d) "
              f"coh<=30km {stats['coherent_frac_within_30km']} far {stats['coherent_frac_60_110km']} "
              f"rate near/far {stats['fringe_rate_near_cyc_per_km']}/{stats['fringe_rate_far_cyc_per_km']} "
              f"deramped {stats['deramped_rate_near']}/{stats['deramped_rate_far']} ramp/100km {stats['ramp_fringes_per_100km']} | "
              + " ".join(f"{k}:{v['raw']['abs_fringes']}/{v['deramped']['abs_fringes']}({v['deramped']['coherent_km']}km)" for k, v in p["transects"].items()))

    # USGS range offsets (independent measurement of the same NISAR passes; pixel offsets, not phase)
    rng_summary = {}
    for t, v in ev["rngoff"].items():
        d = v["data"]; X, Y = km_xy(d[:, 0], d[:, 1], lon0, lat0); R = np.hypot(X, Y)
        rng_summary[t] = {"file": v["file"], "points": int(len(d)),
                          "los_m_p5_p95": [round(float(np.percentile(d[:, 2], 5)), 2), round(float(np.percentile(d[:, 2], 95)), 2)],
                          "median_abs_los_m_within_20km": round(float(np.median(np.abs(d[R <= 20, 2]))), 2) if (R <= 20).any() else None,
                          "median_abs_los_m_beyond_50km": round(float(np.median(np.abs(d[R >= 50, 2]))), 2) if (R >= 50).any() else None}
    model_max = {"max_horizontal_m": round(float(np.nanmax(np.hypot(E, N))), 2), "max_abs_vertical_m": round(float(np.nanmax(np.abs(U))), 2)}

    # ---------------- figure: per track, event vs closest 12-day control
    crop = (-81.55, 6.95, -79.95, 8.25)
    rows = []
    for (t, dr) in sorted({(p["track"], p["dir"]) for p in results if p["kind"] == "event"}):
        evp = [p for p in results if p["kind"] == "event" and (p["track"], p["dir"]) == (t, dr)]
        cps = [p for p in results if p["kind"] == "control" and (p["track"], p["dir"]) == (t, dr)]
        evp = sorted(evp, key=lambda p: p["days"])[0]
        cps = sorted(cps, key=lambda p: (p["days"] != 12, -np.datetime64(p["sec_date"]).astype(int)))
        rows.append((evp, cps[0] if cps else None))
    trn = {k[:5] if k != "N-S" else "N-S": (lo, la) for k, (s, lo, la) in tr_pts.items()}
    panels = []
    for evp, cp in rows:
        row = []
        for p, lab in ((evp, "EVENT"), (cp, "CONTROL (before quake)")):
            if p is None:
                row.append(None); continue
            rgb, ok = mos[id(p)]
            tx = p["transects"]
            sub = (f"deramped fringes on transects: " + ", ".join(f"{k[:6]} {v['deramped']['abs_fringes']}" for k, v in tx.items())
                   + f" | ramp {p['stats']['ramp_fringes_per_100km']}/100 km")
            row.append(render_panel(rgb, ok, p["_coh"], f"{lab}  track {p['track']}{p['dir']}  {p['ref_date']} -> {p['sec_date']}",
                                    sub, ev, ev["patches"], trn, crop))
        panels.append(row)
    pw = max(im.size[0] for r in panels for im in r if im); ph_ = max(im.size[1] for r in panels for im in r if im)
    head = 96
    fig = Image.new("RGB", (2 * pw + 30, head + len(panels) * (ph_ + 12) + 40), "white")
    d = ImageDraw.Draw(fig)
    d.text((10, 8), "Panama M7.7, 9 Oct 2026: NISAR interferograms, event vs control pairs on the same track",
           fill=(0, 0, 0), font=font(19, True))
    d.text((10, 34), "1 colour cycle = 11.9 cm line-of-sight motion (L-band, lambda 23.8 cm). Star = USGS epicentre; outline = USGS finite-fault rupture;", fill=(40, 40, 40), font=FONT_S)
    d.text((10, 50), "black lines = transects. Greyed = low coherence (water, vegetation change, broken ground). Source: NASA GUNW browse images.", fill=(40, 40, 40), font=FONT_S)
    d.text((10, 68), "Screening only: wrapped phase, no ionospheric/orbit correction. Controls can carry ramps too: judge the PATTERN near the rupture.", fill=(150, 30, 30), font=FONT_S)
    for i, row in enumerate(panels):
        for j, im in enumerate(row):
            if im:
                fig.paste(im, (10 + j * (pw + 10), head + i * (ph_ + 12)))
            else:
                d.text((10 + j * (pw + 10) + 20, head + i * (ph_ + 12) + 60), "no 12-day control pair in CMR for this track", fill=(0, 0, 0), font=FONT_B)
    d.text((10, fig.size[1] - 28), f"Sources: NASA CMR {', '.join(['C2854335566-ASF', 'C3622247503-ASF'])}; USGS {EVENT_ID} finite-fault model. Script: tools/gunw_panama.py",
           fill=(80, 80, 80), font=FONT_S)
    fig.save(OUT / "panama_event_vs_control.jpg", quality=88)

    # ---------------- summary JSON
    def clean(p):
        return {"kind": p["kind"], "track": p["track"], "dir": p["dir"], "direction": "descending" if p["dir"] == "D" else "ascending",
                "ref_date": p["ref_date"], "sec_date": p["sec_date"], "days": p["days"],
                "frames": [{"name": g["name"], "frame": g["frame"], "full_frame": g["full_frame"], "browse_png": g["browse"],
                            "local_png": str(local_path(g, p["kind"]).relative_to(ROOT)), "footprint": g["polygon"],
                            "georef": g.get("georef")} for g in p["frames"]],
                "stats": p.get("stats"), "transects": p.get("transects"), "note": p.get("note")}

    evs = [p for p in results if p["kind"] == "event"]; cps = [p for p in results if p["kind"] == "control"]

    def agg(ps, key):
        v = [p["stats"][key] for p in ps if p["stats"].get(key) is not None]
        return round(float(np.median(v)), 3) if v else None
    comparison = {k: {"event_median": agg(evs, k), "control_median": agg(cps, k)} for k in
                  ("coherent_frac_within_30km", "coherent_frac_60_110km", "fringe_rate_near_cyc_per_km", "fringe_rate_far_cyc_per_km",
                   "deramped_rate_near", "deramped_rate_far", "ramp_fringes_per_100km")}
    summary = {
        "event": {"usgs_id": EVENT_ID, "url": USGS_EVENT, "mag": ev["mag"], "lon": lon0, "lat": lat0, "depth_km": ev["depth_km"],
                  "time_utc": str(np.datetime64(ev["time"], "ms")),
                  "finite_fault": {k: ev["ff_props"].get(k) for k in ("model-strike", "model-dip", "model-rake", "model-length", "model-width", "maximum-slip")},
                  "finite_fault_geojson": ev["ff_url"], "model_surface_displacement": ev["disp_url"], "usgs_range_offsets_zip": ev["rng_url"],
                  "model_max_surface_motion": model_max},
        "physics": {"wavelength_m": 0.2384, "fringe_cm_los": round(FRINGE_CM, 2),
                    "note": "1 colour cycle = lambda/2 of line-of-sight motion. Ascending and descending tracks look from opposite sides, "
                            "so the same ground motion gives different fringe patterns."},
        "method": ["CMR search of GUNW provisional + validated collections over the rupture box",
                   "event pairs span 2026-10-09T17:56Z; controls = same track/direction, secondary date before the quake",
                   "browse PNG georeferenced by matching alpha extremes to the CMR UMM polygon (residual reported per frame)",
                   "colour -> wrapped phase via cyclic colour loop (PCA angle, histogram-equalised on coherent pixels)",
                   f"pseudo-coherence = consistency of phase steps in a 7x7 window; coherent if > {COH_MIN}",
                   "planar ramp = median fringe gradient 60-110 km from the epicentre; 'deramped' removes it",
                   f"transects +/-{TRANSECT_KM} km through the epicentre; fringes counted only inside coherent runs >= 2 km, so counts are LOWER BOUNDS; +/-1 fringe reading uncertainty",
                   "independent check: USGS finite-fault surface displacement projected on the NISAR look vector (USGS range-offset files give the descending vector; ascending mirrored)"],
        "look_vectors_usgs_convention": {k: [round(float(x), 3) for x in v] for k, v in lv.items()},
        "comparison_event_vs_control": comparison,
        "usgs_nisar_range_offsets": rng_summary,
        "pairs": [clean(p) for p in results],
        "figure": "data/cases/gunw/panama_event_vs_control.jpg",
        "cmr_query": cmr_url(SEARCH_BBOX, "2026-07-01", "2026-11-15"),
        "quality": "screening from NASA browse images (wrapped phase rendering). Deformation in cm needs the unwrapped GUNW HDF5 "
                   "(Earthdata login) plus ionospheric correction (split-spectrum layer in the product).",
    }
    (OUT / "panama_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({"comparison": comparison, "rngoff": rng_summary, "model": model_max}, indent=1))


if __name__ == "__main__":
    main()
