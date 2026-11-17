"""World-place cases: one same-track NISAR stack per place from NASA CMR + GIBS, screened the same honest way.

For each place (box of +-HALF km around a point):
  1. CMR: every public NISAR GCOV pass (both collections) since 2025-10-01; the earliest / latest pass at the place.
  2. Track: the track + direction with the most dates GIBS can serve (GIBS has no NISAR 2026-07-27..08-09).
     Only that track is used, so the viewing geometry never changes.
  3. GIBS NISAR mosaics (zoom Z) for every date of that track; a COMMON mask = pixels valid on every kept date
     (dates covering < 50 % of the best date's area are dropped), so every number in a series is over the same ground.
  4. Change test for every kind (same idea as tools/case_change.py): 3x3 mean, each pass minus the FIRST pass, median
     removed; flag |change| > 4 x robust spread (1.4826 x MAD) of the quiet pair (first two passes, 12 days apart);
     groups >= 4 px. Series = changed km2 per pass vs the first pass; series[0] is the quiet pair (the baseline).
     HH (red) for water / built / ice / neutral, HV (green) drops for forest.
     Why not a water/bright threshold: on GIBS display tiles, dry salt flats at Lake Urmia are DARKER than its water
     (checked against OPERA DSWx-S1), so "dark = water" fails; a change test needs no such assumption.
  5. Independent checks: water - OPERA DSWx-S1 water area at the first and last pass (+-4 days) and whether NISAR
     flags sit where DSWx water changed; forest - OPERA DIST-ALERT new disturbance; others - none exists.
Display-scaled GIBS radar, not calibrated dB; screening only.
Usage: python tools/case_world.py [id ...]   (writes data/cases/<id>.json, data/cases/img/<id>_change.png, adds ids to
       data/cases/index.json; GIBS tiles for each place are deleted from the cache after the place is done)
"""
import json
import shutil
import sys
from datetime import datetime, timezone

import numpy as np
from PIL import Image

from scipy import ndimage

from case_change import K, keep_groups, smooth
from case_common import CACHE, CASES, NISAR_LAYER, km_box, mosaic, nisar_passes, write_json
from case_dist import DSWX_LAYER, agreement, dswx_classes

IMG = CASES / "img"
REPO = "https://github.com/tolipovmurodjon/falakus/blob/main/"
GIBS_NISAR = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/NISAR_L2_Geocoded_Polarimetric_Covariance/default/{date}/GoogleMapsCompatible_Level13/{z}/{y}/{x}.png"
SCREEN = "screening only: display-scaled GIBS tiles, not calibrated gamma0"
GAP = ("2026-07-27", "2026-08-09")
Z = 10
HALF = 12
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")

P = {
    "jakobshavn": dict(lon=-49.6, lat=69.2, kind="ice", title="Jakobshavn Isbrae: ice front and melange", place="Ilulissat Icefjord, Greenland",
                       what="Greenland's fastest glacier calves into a fjord packed with ice melange.",
                       why="Where the ice front sits, and whether open water replaces melange, tracks how fast ice leaves the ice sheet.",
                       physics="Rough crevassed ice and melange scatter the radar back (bright); calm open water mirrors it away (dark)."),
    "pineisland": dict(lon=-100.0, lat=-75.2, kind="ice", title="Pine Island Glacier: ice shelf change", place="Amundsen Sea, West Antarctica",
                       what="One of Antarctica's fastest-thinning glaciers flows into a floating ice shelf.",
                       why="Rifts, calving and sea ice at the front change how much ice the shelf holds back.",
                       physics="Crevassed ice and rough sea ice are bright; smooth new ice or open water is dark."),
    "urmia": dict(lon=45.4, lat=37.7, kind="water", title="Lake Urmia: water vs salt flat", place="Lake Urmia, Iran",
                  what="A hypersaline lake that has lost much of its water, leaving salt flats.",
                  why="Wind-blown salt from a drying lake harms farms and health around it.",
                  physics="Calm water is dark; wet, smooth salt crust can also look dark, so dark area is an upper bound on water."),
    "deadsea": dict(lon=35.5, lat=31.5, kind="water", title="Dead Sea: shoreline and evaporation ponds", place="Dead Sea, Israel / Jordan / West Bank",
                    what="A terminal lake whose level falls about a metre a year, with large evaporation ponds in the south.",
                    why="Falling water exposes sinkholes and changes the shoreline people depend on.",
                    physics="Calm water is dark; wind roughening can brighten it, and salt crust can look dark."),
    "charvak": dict(lon=69.95, lat=41.62, kind="water", title="Charvak reservoir: seasonal drawdown", place="Charvak reservoir, Tashkent region, Uzbekistan",
                    what="The reservoir that stores water for Tashkent and the Chirchik valley.",
                    why="It fills with snowmelt and is drawn down for irrigation and power, like Andijan upstream.",
                    physics="Calm water is dark; exposed wet shore can also look dark and steep banks cast radar shadow."),
    "nile_delta": dict(lon=31.0, lat=30.9, kind="water", title="Nile delta: irrigation season water", place="Nile delta, Egypt",
                       what="Egypt's breadbasket, irrigated from the Nile through canals and flooded rice fields.",
                       why="Flooded fields and canals show when and where water is used through the summer rice season.",
                       physics="Flooded fields are dark before plants grow; standing crops in water can turn bright (double bounce)."),
    "mekong": dict(lon=105.8, lat=10.0, kind="water", title="Mekong delta: monsoon flooding and rice", place="Mekong delta, Vietnam",
                   what="A delta of rice fields, rivers and canals that floods every monsoon.",
                   why="Flood timing decides planting and harvests for millions of farmers.",
                   physics="Open flood water is dark; flooded rice can be bright (double bounce), so dark area is open water only."),
    "dubai": dict(lon=55.15, lat=25.1, kind="built", title="Dubai: built-up area", place="Dubai, United Arab Emirates",
                  what="A city that keeps building, including on reclaimed land.",
                  why="New buildings and land change where people live and how the coast behaves.",
                  physics="Walls and ground form corner reflectors, so buildings are among the brightest radar targets."),
    "lagos": dict(lon=3.4, lat=6.5, kind="built", title="Lagos: built-up area", place="Lagos, Nigeria",
                  what="One of Africa's fastest-growing cities, on lagoons and coast.",
                  why="New building on wetlands and coast changes flood risk.",
                  physics="Buildings form corner reflectors and look very bright; water and lagoons are dark."),
    "mumbai": dict(lon=72.88, lat=19.07, kind="built", title="Mumbai: built-up area", place="Mumbai, India",
                   what="A dense coastal megacity under monsoon cloud for months each year.",
                   why="Radar keeps watching the city when cameras see only cloud.",
                   physics="Buildings form corner reflectors and look very bright; the sea is dark."),
    "borneo": dict(lon=114.0, lat=-2.3, kind="forest", title="Central Kalimantan: peat forest change", place="Central Kalimantan, Borneo, Indonesia",
                   what="Peat swamp forest and plantations, with clearing and dry-season fires.",
                   why="Cleared or burned peat releases large amounts of carbon.",
                   physics="L-band HV comes from branches and trunks (volume scattering); clearing or burning drops HV by several dB."),
    "gaza": dict(lon=34.4, lat=31.45, kind="neutral", place="Gaza Strip"),
    "ukraine_east": dict(lon=38.0, lat=48.6, kind="neutral", place="Donetsk region, eastern Ukraine", title="Donetsk region, eastern Ukraine: radar backscatter change",
                         what="Radar backscatter change over a 24 km box since the first public NISAR pass.", why="Radar shows surface change, not its cause.",
                         physics="Radar backscatter depends on surface roughness, moisture and structures."),
}


def in_gap(d):
    return GAP[0] <= d <= GAP[1]


def dswx_area(bbox, date, shape, win=4):
    """OPERA DSWx-S1 class per pixel (1 water, 0 not water, -1 unseen), nearest days to `date` first."""
    e = datetime.fromisoformat(date).date()
    from datetime import timedelta
    days = [e] + [e + timedelta(s * i) for i in range(1, win + 1) for s in (-1, 1)]
    out, used = np.full(shape, -1), []
    for d in days:
        if d.isoformat() > NOW:
            continue
        im, _ = mosaic(*DSWX_LAYER, d.isoformat(), bbox, Z, guard=False)
        c = dswx_classes(im)[:shape[0], :shape[1]]
        fill = (out < 0) & (c >= 0)
        if fill.any():
            used.append(d.isoformat())
        out[fill] = c[fill]
    return out, used


def cmr_link(bbox):
    return ("https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C2854338529-ASF&bounding_box="
            + ",".join(map(str, bbox)) + "&temporal=2025-10-01T00:00:00Z," + NOW + "T23:59:59Z&sort_key=start_date")


def num(label, value, unit, source):
    return dict(label=label, value=value, unit=unit, source=source)


def stack(bbox, dates):
    ims, infos = {}, {}
    for d in dates:
        ims[d], infos[d] = mosaic(*NISAR_LAYER, d, bbox, Z)
    # reference ground = pixels seen on >= 60 % of passes; keep passes that see >= 90 % of it
    V = {d: (ims[d][..., 3] == 255) & (ims[d][..., :3].sum(-1) > 0) for d in dates}  # GIBS also serves opaque black no-data
    best = max(int(v.sum()) for v in V.values())
    seen = [d for d in dates if best and V[d].sum() >= 0.3 * best]  # GIBS has no tile for some CMR passes
    if not seen:
        return ims, infos, [], np.zeros(V[dates[0]].shape, bool)
    ref = np.mean([V[d] for d in seen], axis=0) >= 0.6
    keep = [d for d in dates if ref.sum() and (V[d] & ref).sum() >= 0.9 * ref.sum()]
    common = ref.copy()
    for d in keep:
        common &= V[d]
    return ims, infos, keep, common


def build(cid):
    c = P[cid]
    bbox = km_box(c["lon"], c["lat"], HALF)
    passes, urls = nisar_passes(bbox, ("2025-10-01T00:00:00Z", NOW + "T23:59:59Z"))
    src = f"data/cases/{cid}.json (tools/case_world.py)"
    out = dict(id=cid, place=c["place"], bbox=bbox, center=[c["lon"], c["lat"]], zoom=10, quality="screening", quality_note=SCREEN, generated=NOW)
    if not passes:
        out.update(title=c.get("title", c["place"]), date=NOW, before=None, after=None, track=None,
                   finding="No public NISAR GCOV pass covers this place in NASA CMR yet.", numbers=[],
                   sections=dict(what=c.get("what", ""), why=c.get("why", ""), radar="No NISAR data in the public archive here yet.",
                                 validation="Nothing to validate.", limits="Coverage only.", sources=[{"name": "NASA CMR query", "url": cmr_link(bbox)}]))
        return out
    first, last = passes[0], passes[-1]
    groups = {}
    for p in passes:
        if not in_gap(p["start"][:10]):
            groups.setdefault(p["track"] + p["dir"], {}).setdefault(p["start"][:10], p)
    tried = []
    for tk, gp in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:3]:  # most passes first
        dates = sorted(gp)
        ims, infos, keep, common = stack(bbox, dates)
        tried.append(f"{tk}: {len(keep)} usable passes, {int(common.sum())} common px")
        if len(keep) >= 3 and common.sum() >= 500:
            break
    else:
        raise RuntimeError("too little common ground on GIBS: " + "; ".join(tried))
    out["tracks_tried"] = tried
    px = infos[dates[0]]["pixel_km2"]
    d0, dn = keep[0], keep[-1]
    trk = tk[:3] + tk[3]
    arch = dict(first_pass=first["start"], first_id=first["id"], last_pass=last["start"], last_id=last["id"], granules=len(passes),
                tracks={k: len(v) for k, v in groups.items()}, cmr=urls)
    out.update(archive=arch, track=trk, track_direction={"A": "ascending", "D": "descending"}[tk[3]], incidence_deg=None,
               incidence_note="not in CMR granule metadata", stack_dates=keep, dropped_dates=[d for d in dates if d not in keep],
               common_km2=round(float(common.sum() * px), 1), before=d0, after=dn, date=dn,
               tiles={d: infos[d]["tiles"] for d in dates})
    nums = [num("First public NISAR pass here", first["start"][:10], "date", "NASA CMR"),
            num(f"Passes used (track {trk}, same geometry)", len(keep), "passes", "NASA CMR + GIBS"),
            num("Ground compared on every pass", out["common_km2"], "km2", src)]
    srcs = [{"name": "NASA CMR NISAR passes here", "url": cmr_link(bbox)}, {"name": "GIBS NISAR GCOV layer", "url": GIBS_NISAR},
            {"name": "Case script", "url": REPO + "tools/case_world.py"}]
    k = c["kind"]
    ch, sign = {"ice": ("HH", 0), "neutral": ("HH", 0), "forest": ("HV", -1), "water": ("HH", 0), "built": ("HH", 0)}[k]
    ci = {"HH": 0, "HV": 1}[ch]
    sm = {d: smooth(ims[d][..., ci].astype(float), common) for d in keep}
    valid = ndimage.binary_erosion(common, np.ones((3, 3)))
    while True:  # a quiet pair with zero spread means GIBS served the same picture twice: skip to the next pair
        q = sm[keep[1]] - sm[keep[0]]
        q -= np.median(q[valid])
        sigma = 1.4826 * float(np.median(np.abs(q[valid])))
        if sigma >= 0.5:
            break
        out.setdefault("skipped_identical_passes", []).append(keep[0])
        keep = keep[1:]
        if len(keep) < 3:
            raise RuntimeError(f"no radar signal in GIBS tiles here (quiet-pair spread {sigma:.2f})")
    d0 = keep[0]
    out.update(before=d0, stack_dates=keep)
    T = K * sigma

    def flags(d):
        x = sm[d] - sm[d0]
        x -= np.median(x[valid])
        hi = keep_groups(valid & (x > T)) if sign >= 0 else np.zeros_like(valid)
        lo = keep_groups(valid & (x < -T)) if sign <= 0 else np.zeros_like(valid)
        return hi, lo
    series = []
    for d in keep[1:]:
        hi, lo = flags(d)
        series.append({"date": d, "changed_km2": round(float((hi | lo).sum() * px), 2), "brighter_km2": round(float(hi.sum() * px), 2),
                       "darker_km2": round(float(lo.sum() * px), 2)})
    hi, lo = flags(dn)
    qk = series[0]["changed_km2"]
    fk = series[-1]["changed_km2"]
    rgba = np.zeros(valid.shape + (4,), np.uint8)
    rgba[valid] = (255, 255, 255, 40)
    rgba[hi] = (232, 89, 12, 230)
    rgba[lo] = (28, 91, 217, 230)
    IMG.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba).save(IMG / f"{cid}_change.png", optimize=True)
    out.update(series=series, method=dict(channel=ch, k=K, quiet_pair=[d0, keep[1]], quiet_sigma=round(sigma, 2), threshold=round(T, 2), min_group_px=4,
                                          note="each pass compared with the FIRST pass of the stack; series[0] is the quiet pair (12 days) = baseline"),
               image={"png": f"data/cases/img/{cid}_change.png", "bbox": bbox, "legend": "orange = brighter than the first pass, blue = darker, faint white = compared"})
    nums += [num(f"Changed > 4x the quiet wobble, {d0} to {dn}", fk, "km2", src),
             num(f"Same test on the quiet pair {d0} to {keep[1]} (baseline)", qk, "km2", src),
             num("Of which brighter", round(float(hi.sum() * px), 2), "km2", src), num("Of which darker", round(float(lo.sum() * px), 2), "km2", src),
             num("Largest change on any pass vs the first", max(s["changed_km2"] for s in series), "km2", src)]
    quiet_txt = f"Quiet pair {d0} to {keep[1]}: {qk} km2 flagged by the same test."
    base_lim = "Display-scaled GIBS radar, not calibrated dB; screening only. A 12-day quiet pair understates a 4-month seasonal change. "
    if k == "water":
        a0, u0 = dswx_area(bbox, d0, valid.shape)
        a1, u1 = dswx_area(bbox, dn, valid.shape)
        seen = valid & (a0 >= 0) & (a1 >= 0)
        if seen.sum() >= 500:
            w0, w1 = (a0 == 1) & seen, (a1 == 1) & seen
            dsw_ch = (w0 ^ w1)
            fl = (hi | lo) & seen
            st = np.ones((3, 3), bool)
            dch = ndimage.binary_dilation(dsw_ch, st)
            dc = dict(product="OPERA_L3_Dynamic_Surface_Water_Extent-Sentinel-1 (GIBS)", days_start=u0, days_end=u1,
                      seen_pct=round(float(seen.sum() / valid.sum() * 100), 1),
                      dswx_water_start_km2=round(float(w0.sum() * px), 2), dswx_water_end_km2=round(float(w1.sum() * px), 2),
                      dswx_changed_km2=round(float(dsw_ch.sum() * px), 2),
                      nisar_flags_on_dswx_change_pct=round(float((fl & dch).sum() / max(fl.sum(), 1) * 100), 1) if fl.sum() else None,
                      chance_pct=round(float((dch & seen).sum() / seen.sum() * 100), 1), tolerance_px=1)
            nums += [num(f"OPERA DSWx-S1 water near {d0}", dc["dswx_water_start_km2"], "km2", src),
                     num(f"OPERA DSWx-S1 water near {dn}", dc["dswx_water_end_km2"], "km2", src),
                     num("NISAR-flagged pixels where DSWx water also changed (chance)", f"{dc['nisar_flags_on_dswx_change_pct']} ({dc['chance_pct']})", "%", src)]
            val = (quiet_txt + f" OPERA DSWx-S1 (Sentinel-1, NASA JPL, not ours): water {dc['dswx_water_start_km2']} -> {dc['dswx_water_end_km2']} km2 over the same ground; "
                   f"{dc['nisar_flags_on_dswx_change_pct']} % of NISAR-flagged pixels sit where DSWx water changed (chance {dc['chance_pct']} %).")
        else:
            dc = {"result": "no independent product covers this place on these dates (too few DSWx-S1 pixels)", "days_start": u0, "days_end": u1}
            val = quiet_txt + " OPERA DSWx-S1: no coverage on these dates."
        out["independent_check"] = dc
        srcs.append({"name": "GIBS OPERA DSWx-S1 colormap", "url": "https://gibs.earthdata.nasa.gov/colormaps/v1.3/OPERA_Dynamic_Surface_Water_Extent_S1.xml"})
        finding = f"{fk} km2 of the box changed by more than 4x the 12-day wobble between {d0} and {dn} ({round(float(lo.sum() * px), 2)} km2 darker, {round(float(hi.sum() * px), 2)} km2 brighter), vs {qk} km2 in the quiet pair."
        radar = f"{c['physics']} Same track {trk}, {len(keep)} passes, each compared with the first."
        limits = base_lim + "Darker is not always more water and brighter is not always less: wind, wet salt and crops change HH too."
    elif k == "built":
        out["independent_check"] = "no independent product covers built-up change"
        val = quiet_txt + " No independent product covers built-up change."
        finding = (f"{round(float(hi.sum() * px), 2)} km2 became brighter (built-like) and {round(float(lo.sum() * px), 2)} km2 darker between {d0} and {dn}, vs {qk} km2 in the quiet pair. "
                   "Only 5 months of public NISAR data, so construction change is expected to be small.")
        radar = f"{c['physics']} Same track {trk}, {len(keep)} passes, each compared with the first."
        limits = base_lim + "Brighter also means wetter or rougher ground, crops, ships or metal; 5 months is short for construction."
    elif k == "forest":
        dc = agreement(hi | lo, valid, bbox, d0, dn, Z)
        out["independent_check"] = dc
        if dc.get("radar_flags_also_dist_pct") is not None:
            nums += [num("NISAR HV-drop pixels that OPERA DIST-ALERT calls new disturbance (chance)", f"{dc['radar_flags_also_dist_pct']} ({dc['chance_radar_flags_also_dist_pct']})", "%", src),
                     num("DIST-ALERT new disturbance that NISAR flags (chance)", f"{dc['dist_new_also_radar_pct']} ({dc['chance_dist_new_also_radar_pct']})", "%", src)]
            val = (quiet_txt + f" OPERA DIST-ALERT: {dc['radar_flags_also_dist_pct']} % of HV-drop pixels are new disturbance (chance {dc['chance_radar_flags_also_dist_pct']} %); "
                   f"NISAR flags {dc['dist_new_also_radar_pct']} % of DIST's new disturbance (chance {dc['chance_dist_new_also_radar_pct']} %).")
        elif dc.get("dist_new_px") is not None:
            val = quiet_txt + f" OPERA DIST-ALERT marks {dc['dist_new_share_of_seen_pct']} % of the box as new disturbance; NISAR flags none of it."
        else:
            val = quiet_txt + " OPERA DIST-ALERT: " + dc.get("result", "not run") + "."
        srcs.append({"name": "GIBS OPERA DIST-ALERT colormap", "url": "https://gibs.earthdata.nasa.gov/colormaps/v1.3/OPERA_Vegetation_Disturbance_Status.xml"})
        finding = f"HV (canopy echo) dropped by more than 4x the quiet wobble on {fk} km2 between {d0} and {dn} (quiet pair {qk} km2)."
        radar = f"{c['physics']} Same track {trk}; HV (green) drop vs the first pass."
        limits = base_lim + "DIST is optical and misses cloudy days."
    elif k == "ice":
        out["independent_check"] = "no independent product covers ice change here (OPERA DSWx/DIST do not map ice)"
        val = quiet_txt + " No independent product covers this ice change."
        finding = f"{fk} km2 changed by more than 4x the 12-day wobble between {d0} and {dn} ({round(float(hi.sum() * px), 2)} km2 brighter, {round(float(lo.sum() * px), 2)} km2 darker), vs {qk} km2 in the quiet pair."
        radar = f"{c['physics']} Same track {trk}; HH vs the first pass."
        limits = base_lim + "Melt, refreeze and wet snow change the echo without the front moving."
    else:
        out["independent_check"] = "none used"
        first_d = first["start"][:10]
        c["title"] = f"{c['place']}: radar backscatter change"
        c["what"] = f"Radar backscatter change over a {2 * HALF} km box since the first public NISAR pass ({first_d})."
        c["why"] = "Radar shows surface change, not its cause."
        val = quiet_txt
        finding = (f"Radar backscatter change since {first_d}: {fk} km2 changed by more than 4x the normal wobble on track {trk} "
                   f"({d0} to {dn}), vs {qk} km2 in a quiet pair. Radar shows surface change, not its cause.")
        radar = f"Same track {trk}; HH vs the first pass."
        limits = base_lim + "Rain, crops and season also change backscatter."
    out.update(title=c["title"], finding=finding, numbers=nums,
               sections=dict(what=c["what"], why=c["why"], radar=radar, validation=val, limits=limits, sources=srcs))
    return out


ORDER = ["id", "title", "place", "date", "bbox", "center", "zoom", "before", "after", "track", "finding", "sections", "numbers"]


def main():
    ids = sys.argv[1:] or list(P)
    for cid in ids:
        try:
            d = build(cid)
        except Exception as e:  # one bad place must not stop the rest
            print(cid, "| FAILED:", repr(e), flush=True)
            shutil.rmtree(CACHE, ignore_errors=True)
            if "too little common ground" not in str(e) and "no radar signal" not in str(e):
                continue
            c = P[cid]  # CMR has passes but GIBS serves no usable tiles: write an honest coverage-only case
            bbox = km_box(c["lon"], c["lat"], HALF)
            passes, urls = nisar_passes(bbox, ("2025-10-01T00:00:00Z", NOW + "T23:59:59Z"))
            d = dict(id=cid, title=c.get("title", c["place"]), place=c["place"], date=passes[-1]["start"][:10] if passes else NOW, bbox=bbox,
                     center=[c["lon"], c["lat"]], zoom=8, before=passes[0]["start"][:10] if passes else None, after=passes[-1]["start"][:10] if passes else None,
                     track=None, finding=f"NASA CMR lists {len(passes)} NISAR GCOV granules here ({passes[0]['start'][:10]} to {passes[-1]['start'][:10]}), but the NASA GIBS tiles for them are unusable here (no common ground, or the same picture on every pass), so no change is measured.",
                     sections=dict(what=c.get("what", ""), why=c.get("why", ""), radar=c.get("physics", ""),
                                   validation="Nothing measured, nothing to validate.", limits=str(e),
                                   sources=[{"name": "NASA CMR NISAR passes here", "url": cmr_link(bbox)}, {"name": "GIBS NISAR GCOV layer", "url": GIBS_NISAR}]),
                     numbers=[num("NISAR GCOV granules in CMR", len(passes), "granules", "NASA CMR"),
                              num("First public pass", passes[0]["start"][:10], "date", "NASA CMR")],
                     quality="screening", quality_note="coverage only: no GIBS tiles", independent_check="none", generated=NOW,
                     archive=dict(first_pass=passes[0]["start"], last_pass=passes[-1]["start"], granules=len(passes), cmr=urls))
        d = {**{k: d.get(k) for k in ORDER}, **{k: v for k, v in d.items() if k not in ORDER}}
        write_json(CASES / f"{cid}.json", d)
        idx = json.loads((CASES / "index.json").read_text()) if (CASES / "index.json").exists() else {"cases": []}
        if cid not in idx["cases"]:
            idx["cases"].append(cid)
        write_json(CASES / "index.json", idx)
        print(cid, "|", d["finding"], "|", json.dumps(d.get("independent_check"))[:300], flush=True)
        shutil.rmtree(CACHE, ignore_errors=True)  # disk is nearly full: tiles are re-fetched on a rebuild


if __name__ == "__main__":
    main()
