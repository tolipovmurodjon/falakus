"""Build data/headline_numbers.json and data/cases/*.json (+ data/cases/img/*.png). Every number comes from a repo file
or a live NASA API response (CMR, GIBS), and carries its source and script.

Usage: python tools/case_build.py            (all)
       python tools/case_build.py panama     (one case; headline numbers are rebuilt every time)
Needs network for CMR + GIBS (3 tries with backoff each). GIBS tiles are cached in ~/.cache/falakus-gibs.
"""
import json
import statistics
import sys
import urllib.parse
from datetime import datetime, timezone

import numpy as np
from PIL import Image

from case_change import screen
from case_common import (CASES, NISAR_COLLECTIONS, NISAR_LAYER, ROOT, cmr_hits, km_box, mosaic, nisar_passes, write_json)
from case_dist import agreement
from case_passes import best_pair, pairs

D = ROOT / "data"
IMG = CASES / "img"
REPO = "https://github.com/tolipovmurodjon/falakus/blob/main/"
GIBS_NISAR = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/NISAR_L2_Geocoded_Polarimetric_Covariance/default/{date}/GoogleMapsCompatible_Level13/{z}/{y}/{x}.png"
GIBS_DIST = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/OPERA_L3_DIST-ALERT-HLS_Color_Index/default/{date}/GoogleMapsCompatible_Level12/{z}/{y}/{x}.png"
SCREEN = "screening only: display-scaled GIBS tiles, not calibrated gamma0"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def J(p):
    return json.loads((D / p).read_text())


def N(value, unit, label, source, script, **kw):
    return dict(value=value, unit=unit, label=label, source=source, script=script, **kw)


def num(label, value, unit, source):
    return dict(label=label, value=value, unit=unit, source=source)


# ---------------------------------------------------------------- headline numbers
def headline():
    wc, wm = J("ml/water_clean.json"), J("ml/water_model.json")
    s, sm = wc["summary"], wm["summary"]
    ice = J("waterroad/andijan_res_icesat2.json")
    fc = J("forecast/andijan_res_v2.json")
    fz = J("ml/water_freq.json")
    pop = J("waterroad/population.json")["regions_2025"]
    aral = J("timelapse/aral/index.json")
    ho = {r["date"]: r for r in wm["held_out"]}
    dec = next(f for f in fc["forecast"] if f["month"] == "2026-12")
    hist_dec = [x["km2"] for x in fc["series"] if x["month"].endswith("-12") and x["month"] < "2026-12"]
    late = [r for r in wc["held_out"] if "2026-07-26" <= r["date"] <= "2026-09-12"]
    valley = pop["fergana"] + pop["andijan"] + pop["namangan"]
    fr = {f["year"]: f for f in aral["frames"]}
    a85, a26 = fr[1985]["water_km2"], fr[2026]["water_km2"]
    andi_box = [72.9, 40.6, 73.3, 40.9]
    first_and = [cmr_hits(andi_box, c) for c in NISAR_COLLECTIONS]
    glob = [cmr_hits(None, c) for c in NISAR_COLLECTIONS]
    earliest_and = min((x["first"] for x in first_and if x["first"]), key=lambda t: t[1])
    WC, WMS = "data/ml/water_clean.json", "tools/ml_water_clean.py"
    h = {
        "nested_iou": N(s["nested_iou"], "IoU", "Learned water map vs Sentinel-2 photos on 8 unseen days, speckle cut-off chosen without the scored day (nested)",
                        WC + " summary.nested_iou", WMS, ci_low=s["nested_iou_ci95"][0], ci_high=s["nested_iou_ci95"][1], ci_method=s["ci_method"],
                        cutoffs_chosen=s["nested_cutoffs_chosen"]),
        "raw_iou": N(s["raw_iou"], "IoU", "Same map with no speckle clean-up (8 unseen days)", WC + " summary.raw_iou", WMS,
                     ci_low=s["raw_iou_ci95"][0], ci_high=s["raw_iou_ci95"][1]),
        "old_iou_0_2": N(s["old_leaky_iou_at_0.2"], "IoU", "Old figure: 0.2 km2 cut-off picked after seeing these test days (leaky; do not quote as the score)",
                         WC + " summary.sensitivity_median_iou['0.2']", WMS),
        "speckle_sensitivity": N(s["sensitivity_median_iou"], "IoU by cut-off km2", "Median IoU on the 8 days for every cut-off (full sensitivity table)",
                                 WC + " summary.sensitivity_median_iou", WMS),
        "baseline_rule_iou": N(sm["rule_iou"], "IoU", "Baseline: single HH threshold (-16.75 dB) on the same 8 days", "data/ml/water_model.json summary.rule_iou", "tools/ml_water.py"),
        "baseline_rule_zone_iou": N(sm["rule_zone_iou"], "IoU", "Baseline: HH threshold inside a 1 km water zone, same 8 days", "data/ml/water_model.json summary.rule_zone_iou", "tools/ml_water.py"),
        "baseline_otsu_iou": N(None, "IoU", "Baseline: Otsu threshold on HH: NOT computed (calibrated HH npz for Andijan is not in the repo; needs re-download)",
                               "n/a", "n/a"),
        "recall": N(s["recall"], "fraction", "Share of photo water the radar map finds (median, 8 unseen days)", WC + " summary.recall", WMS),
        "shuffled_control_iou": N(sm["null_iou"], "IoU", "Same model trained on shuffled labels (must collapse)", "data/ml/water_model.json summary.null_iou", "tools/ml_water.py"),
        "icesat2_spearman": N(ice["spearman_r"], "rho", "ICESat-2 ATL13 water level vs lake area, rank correlation", "data/waterroad/andijan_res_icesat2.json spearman_r",
                              "tools/icesat2_levels.py", n=ice["n"]),
        "icesat2_n": N(ice["n"], "dates", "ICESat-2 dates paired with an area", "data/waterroad/andijan_res_icesat2.json n", "tools/icesat2_levels.py"),
        "area_error_nested": N(s["nested_area_mae_km2"], "km2", "Mean absolute area miss on the 8 unseen days (nested cut-off)", WC + " summary.nested_area_mae_km2", WMS),
        "area_error_raw": N(sm["ml_area_mae_km2"], "km2", "Mean absolute area miss, no clean-up", "data/ml/water_model.json summary.ml_area_mae_km2", "tools/ml_water.py"),
        "wet_mud_bias": N(round(statistics.mean(r["nested_area_err_km2"] for r in late), 2), "km2",
                          "Over-count on the drying-shore days 26 Jul-12 Sep (radar minus photo, nested cut-off; error maps put it on the wet-mud shore)",
                          WC + " held_out[].nested_area_err_km2 for " + ", ".join(r["date"] for r in late), WMS,
                          raw_model_extra_km2_median=statistics.median(ho[r["date"]]["extra_km2"] for r in late)),
        "lake_photo_23jun": N(ho["2026-06-20"]["photo_water_km2"], "km2", "Lake open water, Sentinel-2 photo 23 Jun 2026", "data/ml/water_model.json held_out[2026-06-20].photo_water_km2", "tools/ml_water.py"),
        "lake_photo_19oct": N(ho["2026-10-18"]["photo_water_km2"], "km2", "Lake open water, Sentinel-2 photo 19 Oct 2026", "data/ml/water_model.json held_out[2026-10-18].photo_water_km2", "tools/ml_water.py"),
        "always_wet_km2": N(fz["km2"]["every_pass"], "km2", f"Water on every one of {fz['passes']} NISAR passes", "data/ml/water_freq.json km2.every_pass", "tools/water_frequency.py"),
        "dried_once_km2": N(round(fz["km2"]["ever"] - fz["km2"]["every_pass"], 1), "km2", "Water on at least one pass but not all (ever minus every pass)",
                            "data/ml/water_freq.json km2.ever - km2.every_pass", "tools/water_frequency.py"),
        "forecast_dec": N(dec["km2"], "km2", "Dec 2026 lake area forecast", "data/forecast/andijan_res_v2.json forecast[2026-12].km2", "tools/forecast_v2.py",
                          band_low=dec["low"], band_high=dec["high"], band="8 in 10 (10th-90th percentile of its own walk-forward misses)"),
        "typical_dec": N(dec["typical"], "km2", f"Typical December: mean of the {len(hist_dec)} clear Decembers in the 2017-2025 photo record",
                         "data/forecast/andijan_res_v2.json forecast[2026-12].typical", "tools/forecast_v2.py", n_years=len(hist_dec), min=dec["min"], max=dec["max"]),
        "dec_anomaly": N(round(dec["km2"] - dec["typical"], 2), "km2", "Dec forecast minus typical December (typical lies inside the 8-in-10 band: below normal, not a significant anomaly)",
                         "derived: forecast_dec - typical_dec", "tools/case_build.py"),
        "forecast_mae_30d": N(fc["skill"]["h1"]["mae_km2"]["ridge"], "km2", "Forecast miss 30 days ahead (walk-forward)", "data/forecast/andijan_res_v2.json skill.h1.mae_km2.ridge",
                              "tools/forecast_v2.py", n_test=fc["skill"]["h1"]["n_test"]),
        "persistence_mae_30d": N(fc["skill"]["h1"]["mae_km2"]["persistence"], "km2", "Persistence (same as last month) miss, 30 days ahead",
                                 "data/forecast/andijan_res_v2.json skill.h1.mae_km2.persistence", "tools/forecast_v2.py"),
        "population_valley": N(round(valley / 1e6, 1), "million people", "Andijan + Fergana + Namangan regions (stat.uz, 1 Oct 2025)",
                               "data/waterroad/population.json regions_2025", "stat.uz press release"),
        "population_share": N(round(valley / pop["uzbekistan"] * 100, 1), "%", "Share of Uzbekistan's population", "data/waterroad/population.json regions_2025", "stat.uz press release"),
        "winter_cloud": N("15 of 24", "photos", "Sentinel-2 winter (Dec-Mar 2025) photos of the reservoir lost to cloud [unverified: no data file in repo; quoted from docs/state/handoff.md]",
                          "docs/state/handoff.md (measured 15 Nov; output not saved)", "none in repo"),
        "aral_1985_km2": N(fr[1985]["water_km2"], "km2", "Aral box open water, Landsat summer 1985 (44.7 % of pixels filled from 1986)",
                           "data/timelapse/aral/index.json frames[1985].water_km2", "tools/bake_timelapse.py"),
        "aral_2026_km2": N(a26, "km2", "Aral box open water, Landsat/Sentinel summer 2026", "data/timelapse/aral/index.json frames[2026].water_km2", "tools/bake_timelapse.py"),
        "aral_loss_pct": N(round((a85 - a26) / a85 * 100, 1), "%", "Open water lost in the Aral box, 1985 to 2026", "derived from the two numbers above", "tools/case_build.py"),
        "nisar_start_andijan": N(earliest_and[1][:10], "date", "First public NISAR GCOV pass over Andijan (bbox 72.9,40.6,73.3,40.9)",
                                 "NASA CMR: " + " | ".join(x["url"] for x in first_and), "tools/case_build.py", granule=earliest_and[0],
                                 granules={c: x["hits"] for c, x in zip(NISAR_COLLECTIONS, first_and)}),
        "nisar_start_global": N(glob[1]["first"][1][:10], "date", "First provisional NISAR GCOV granule anywhere", "NASA CMR: " + glob[1]["url"], "tools/case_build.py",
                                granule=glob[1]["first"][0]),
        "nisar_granules_provisional": N(glob[1]["hits"], "granules", f"NISAR GCOV provisional granules in CMR on {NOW}", "NASA CMR CMR-Hits header: " + glob[1]["url"], "tools/case_build.py"),
        "nisar_granules_validated": N(glob[0]["hits"], "granules", f"NISAR GCOV validated (V1) granules in CMR on {NOW}", "NASA CMR CMR-Hits header: " + glob[0]["url"], "tools/case_build.py",
                                      first=glob[0]["first"][1][:10]),
    }
    out = {"generated": NOW, "rule": "Every number the app or pitch uses. value + unit + label + source + script.", "numbers": h}
    write_json(D / "headline_numbers.json", out)
    return h


# ---------------------------------------------------------------- radar change cases
def cmr_link(bbox, t0, t1):
    q = {"collection_concept_id": NISAR_COLLECTIONS[1], "bounding_box": ",".join(map(str, bbox)), "temporal": f"{t0},{t1}", "sort_key": "-start_date"}
    return "https://cmr.earthdata.nasa.gov/search/granules.json?" + urllib.parse.urlencode(q)


def pass_meta(p):
    return dict(id=p["id"], start=p["start"], track=p["track"], direction={"A": "ascending", "D": "descending"}[p["dir"]], frame=p["frame"],
                collection=p["collection"], incidence_deg=None, incidence_note="not in CMR granule metadata (UMM AdditionalAttributes)")


def change_case(cid, lon, lat, half_km, event_iso, z, ch, sign, dist=True, dates=None):
    bbox = km_box(lon, lat, half_km)
    pr = pairs(bbox, event_iso)
    out = dict(bbox=bbox, cmr=pr["cmr_urls"], tracks=[])
    best = best_pair(pr) if dates is None else dates
    if best is None:
        out["error"] = "no same-track pass on both sides of the event"
        return out
    for g in pr["groups"]:
        if not (g["prior"] and g["last_before"] and g["first_after"]):
            continue
        dd = dict(prior=g["prior"]["start"][:10], before=g["last_before"]["start"][:10], after=g["first_after"]["start"][:10])
        is_best = g["track"] == best["track"]
        png = IMG / f"{cid}_change.png" if is_best else None
        r, m = screen(bbox, dd, z, ch, png, sign=sign)
        r.update(track=g["track"], passes={k: pass_meta(g[n]) for k, n in (("prior", "prior"), ("before", "last_before"), ("after", "first_after"))})
        if png:
            r["png"] = f"data/cases/img/{cid}_change.png"
        if is_best and m is not None and dist:
            flag = m["hi"] | m["lo"]
            r["dist_check"] = agreement(flag, m["valid"], bbox, dd["before"], dd["after"], z)
        out["tracks"].append(r)
        print(cid, g["track"], dd, {k: r.get(k) for k in ("flag_km2", "quiet_flag_km2", "brighter_km2", "darker_km2", "valid_km2")}, flush=True)
    out["best"] = next((t for t in out["tracks"] if t["track"] == best["track"]), None)
    return out


def base(cid, title, place, date, bbox, zoom, before, after, track, finding, sections, numbers):
    W, S, E, Nn = bbox
    return {"id": cid, "title": title, "place": place, "date": date, "bbox": bbox, "center": [round((W + E) / 2, 4), round((S + Nn) / 2, 4)],
            "zoom": zoom, "before": before, "after": after, "track": track, "finding": finding, "sections": sections, "numbers": numbers}


def track_label(t):
    return t["track"][:3] + t["track"][3]


def panama():
    ev = "2026-10-09T17:56:00Z"
    r = change_case("panama", -80.769, 7.587, 20, ev, 11, "HH", 0)
    b = r["best"]
    src = "data/cases/panama.json radar (tools/case_build.py)"
    others = [t for t in r["tracks"] if t is not b]
    dc = b.get("dist_check", {})
    gunw = ("https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C2854335566-ASF&bounding_box="
            + ",".join(map(str, r["bbox"])) + "&temporal=2026-09-20T00:00:00Z,2026-10-31T00:00:00Z")
    nums = [num("Radar-flagged area (HH change > 4x quiet wobble)", b["flag_km2"], "km2", src),
            num("Same test on a quiet pair (false-alarm baseline)", b["quiet_flag_km2"], "km2", src),
            num("Of which brighter", b["brighter_km2"], "km2", src), num("Of which darker", b["darker_km2"], "km2", src),
            num("Box seen on all 3 dates", b["valid_km2"], "km2", src),
            num("Hours from quake to the after pass", round((datetime.fromisoformat(b["passes"]["after"]["start"].replace("Z", "+00:00"))
                                                             - datetime.fromisoformat(ev.replace("Z", "+00:00"))).total_seconds() / 3600, 1), "h", "NASA CMR granule start time")]
    for t in others:
        nums.append(num(f"Check on track {t['track']} ({t['dates']['before']} -> {t['dates']['after']}): flagged / quiet", f"{t.get('flag_km2')} / {t.get('quiet_flag_km2')}", "km2", src))
    if dc.get("radar_flags_also_dist_pct") is not None:
        nums.append(num("Radar flags that OPERA DIST-ALERT also flags (chance level)", f"{dc['radar_flags_also_dist_pct']} ({dc['chance_radar_flags_also_dist_pct']})", "%", src))
        nums.append(num("DIST-ALERT new disturbance that radar also flags (chance level)", f"{dc['dist_new_also_radar_pct']} ({dc['chance_dist_new_also_radar_pct']})", "%", src))
    d = base("panama", "Panama M7.7: what changed at the surface", "Herrera / Azuero, Panama", "2026-10-09", r["bbox"], 10,
             b["dates"]["before"], b["dates"]["after"], track_label(b),
             f"{b['flag_km2']} km2 changed more than 4x the normal radar wobble six hours after the quake (quiet pair {b['quiet_flag_km2']} km2), but later passes on other tracks flag far less, so most of it may be short-lived (e.g. wet ground): screening candidates, not confirmed damage.",
             {"what": "A magnitude 7.7 earthquake struck at 17:56 UTC on 9 Oct 2026 (USGS us6000u18k). NISAR flew over the same spot about six hours later.",
              "why": "Strong shaking can loosen slopes and damage ground cover, and both change how the surface returns radar. Rain does the same thing, so every flagged patch is a candidate to check.",
              "radar": f"We compared passes on the same track and direction ({track_label(b)}): {b['dates']['before']} and {b['dates']['after']}. A pixel is flagged only if its HH change is more than 4 times the normal 12-day wobble, measured on {b['dates']['prior']} to {b['dates']['before']}. Ground motion needs GUNW interferometry: next step (a GUNW pair for these dates is in CMR).",
              "validation": (f"Quiet pair: {b['quiet_flag_km2']} km2. Other tracks after the quake: " + "; ".join(f"{t['track']} {t.get('flag_km2')} vs quiet {t.get('quiet_flag_km2')} km2" for t in others if t.get('flag_km2') is not None)
                             + (f". OPERA DIST-ALERT does not support it: {dc.get('radar_flags_also_dist_pct')} % of radar flags agree, below the {dc.get('chance_radar_flags_also_dist_pct')} % expected by chance." if dc.get("radar_flags_also_dist_pct") is not None and dc["radar_flags_also_dist_pct"] <= dc["chance_radar_flags_also_dist_pct"]
                                else f". OPERA DIST-ALERT: {dc.get('radar_flags_also_dist_pct')} % of radar flags agree (chance {dc.get('chance_radar_flags_also_dist_pct')} %)." if dc.get("radar_flags_also_dist_pct") is not None else ". OPERA DIST-ALERT: " + dc.get("result", "not run") + ".")),
              "limits": "Display-scaled GIBS radar, not calibrated dB; screening only. Rain-wetted soil and crops also brighten HH. No field report confirms these patches.",
              "sources": [{"name": "USGS event us6000u18k", "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us6000u18k"},
                          {"name": "NASA CMR pass search (NISAR GCOV)", "url": cmr_link(r["bbox"], "2026-08-01T00:00:00Z", "2026-11-15T00:00:00Z")},
                          {"name": "NASA CMR GUNW pairs (interferograms)", "url": gunw},
                          {"name": "GIBS NISAR GCOV layer", "url": GIBS_NISAR},
                          {"name": "GIBS OPERA DIST-ALERT layer", "url": GIBS_DIST},
                          {"name": "Change test script", "url": REPO + "tools/case_change.py"},
                          {"name": "Case builder", "url": REPO + "tools/case_build.py"}]}, nums)
    d.update(quality="screening", quality_note=SCREEN, image={"png": b.get("png"), "bbox": r["bbox"], "legend": "orange = brighter, blue = darker, faint white = compared"},
             radar=r, gunw={"exists_in_cmr": True, "query": gunw, "processed": False, "note": "Ground motion needs GUNW interferometry: next step."})
    return d


def langtang():
    ev = "2026-08-26T02:52:00Z"  # 08:37 Nepal time as reported; USGS confirms the date (26 Aug, morning local time)
    r = change_case("langtang", 85.5, 28.2, 20, ev, 11, "HH", 0)
    b = r["best"]
    src = "data/cases/langtang.json radar (tools/case_build.py)"
    dc = b.get("dist_check", {})
    nums = [num("Radar-flagged area (HH change > 4x quiet wobble)", b["flag_km2"], "km2", src),
            num("Same test on a quiet pair (false-alarm baseline)", b["quiet_flag_km2"], "km2", src),
            num("Of which brighter", b["brighter_km2"], "km2", src), num("Of which darker", b["darker_km2"], "km2", src),
            num("Box seen on all 3 dates", b["valid_km2"], "km2", src)]
    for t in r["tracks"]:
        if t is not b:
            nums.append(num(f"Check on track {t['track']} ({t['dates']['before']} -> {t['dates']['after']}): flagged / quiet", f"{t.get('flag_km2')} / {t.get('quiet_flag_km2')}", "km2", src))
    d = base("langtang", "Langtang: slope change after the 26 Aug 2026 collapse", "Langtang valley, Rasuwa, Nepal", "2026-08-26", r["bbox"], 10,
             b["dates"]["before"], b["dates"]["after"], track_label(b),
             f"Monsoon-season slope change screening: {b['flag_km2']} km2 changed more than 4x the normal radar wobble between {b['dates']['before']} and {b['dates']['after']} (quiet pair {b['quiet_flag_km2']} km2), spread over many slopes, so it cannot be pinned to the collapse alone.",
             {"what": "On the morning of 26 Aug 2026 a slope failure involving a glacier in Langtang National Park sent a debris flow and flood about 100 km downstream (USGS).",
              "why": "Debris, scoured valley floors and new mud change surface roughness and wetness, so radar echo changes even under monsoon cloud.",
              "radar": f"Same track and direction ({track_label(b)}): {b['dates']['before']} vs {b['dates']['after']}, flagged if the HH change exceeds 4x the wobble of {b['dates']['prior']} to {b['dates']['before']}.",
              "validation": (f"Quiet pair: {b['quiet_flag_km2']} km2. Other tracks: " + "; ".join(f"{t['track']} {t.get('flag_km2')} vs quiet {t.get('quiet_flag_km2')} km2" for t in r["tracks"] if t is not b) + f". OPERA DIST-ALERT: {dc.get('radar_flags_also_dist_pct')} % of radar flags agree (chance {dc.get('chance_radar_flags_also_dist_pct')} %)."
                             if dc.get("radar_flags_also_dist_pct") is not None else f"Quiet pair: {b['quiet_flag_km2']} km2. OPERA DIST-ALERT: " + dc.get("result", "not run") + "."),
              "limits": "Display-scaled GIBS radar, not calibrated dB; screening only. Steep mountains cause layover and shadow; snow and monsoon wetness also change HH. The quiet pair on this track spans 24 days (GIBS has no NISAR 27 Jul-10 Aug).",
              "sources": [{"name": "USGS Landslide Hazards: 2026 Nepal debris avalanche and flash flood", "url": "https://www.usgs.gov/programs/landslide-hazards/science/2026-nepal-debris-avalanche-and-flash-flood"},
                          {"name": "NASA CMR pass search (NISAR GCOV)", "url": cmr_link(r["bbox"], "2026-06-01T00:00:00Z", "2026-11-15T00:00:00Z")},
                          {"name": "GIBS NISAR GCOV layer", "url": GIBS_NISAR},
                          {"name": "Change test script", "url": REPO + "tools/case_change.py"}]}, nums)
    d.update(quality="screening", quality_note=SCREEN, image={"png": b.get("png"), "bbox": r["bbox"], "legend": "orange = brighter, blue = darker, faint white = compared"},
             radar=r, event_verification={"date": "2026-08-26", "verified_by": "USGS Landslide Hazards Program page (date, 'Wednesday morning local time')",
                                          "time_utc_used": ev, "time_note": "08:37 local time is from press reports, not USGS"})
    return d


def rondonia():
    lon, lat = -63.545, -9.709  # densest OPERA DIST-ALERT block in the z7 tile over (-63, -10) on 2026-10-21 (see notes)
    bbox = km_box(lon, lat, 15)
    pr = pairs(bbox, "2026-10-01T00:00:00Z", 90)
    g = next(x for x in pr["groups"] if x["track"] == "068D")
    byd = {p: p for p in g["dates"]}
    dd = dict(prior="2026-08-17", before="2026-08-29", after="2026-10-28")
    assert all(v in byd for v in dd.values()), g["dates"]
    r, m = screen(bbox, dd, 12, "HV", IMG / "rondonia_change.png", sign=-1)
    r["png"] = "data/cases/img/rondonia_change.png"
    dc = agreement(m["hi"] | m["lo"], m["valid"], bbox, dd["before"], dd["after"], 12) if m else {}
    r["dist_check"] = dc
    print("rondonia", {k: r.get(k) for k in ("flag_km2", "quiet_flag_km2", "valid_km2")}, dc, flush=True)
    src = "data/cases/rondonia.json radar (tools/case_build.py)"
    nums = [num("Radar HV drop > 4x quiet wobble", r["flag_km2"], "km2", src),
            num("Same test on a quiet pair (false-alarm baseline)", r["quiet_flag_km2"], "km2", src),
            num("Box seen on all 3 dates", r["valid_km2"], "km2", src)]
    if dc.get("radar_flags_also_dist_pct") is not None:
        nums += [num("NISAR HV-drop pixels that DIST-ALERT also flags as new (chance level)", f"{dc['radar_flags_also_dist_pct']} ({dc['chance_radar_flags_also_dist_pct']})", "%", src),
                 num("DIST-ALERT new disturbance that NISAR also flags (chance level)", f"{dc['dist_new_also_radar_pct']} ({dc['chance_dist_new_also_radar_pct']})", "%", src),
                 num("DIST-ALERT pixels seen cloud-free on both sides", dc["seen_by_both_pct"], "%", src)]
    if not r["flag_km2"]:
        agree = (f"The radar test flagged nothing: the quiet-pair HV wobble in GIBS display values is large (sigma {r['quiet_sigma']}), so a 4x threshold is {r['threshold']} units. "
                 f"OPERA DIST-ALERT marks {dc.get('dist_new_share_of_seen_pct')} % of the box as new disturbance in the same window, so agreement is 0 %: this method misses it.")
    else:
     agree = (f"{dc['radar_flags_also_dist_pct']} % of NISAR HV-drop pixels are new OPERA DIST-ALERT disturbance (chance {dc['chance_radar_flags_also_dist_pct']} %); "
             f"{dc['dist_new_also_radar_pct']} % of DIST's new disturbance is flagged by NISAR (chance {dc['chance_dist_new_also_radar_pct']} %).") if dc.get("radar_flags_also_dist_pct") is not None else "OPERA DIST-ALERT: " + dc.get("result", "not run") + "."
    d = base("rondonia", "Rondonia: forest clearing seen as a drop in HV", "Rondonia, Brazil (Amazon)", dd["after"], bbox, 11, dd["before"], dd["after"], "068D",
             (f"{r['flag_km2']} km2 lost HV echo between {dd['before']} and {dd['after']} vs {r['quiet_flag_km2']} km2 in a quiet pair; checked against NASA OPERA DIST-ALERT." if r["flag_km2"] else
              f"Negative result: OPERA DIST-ALERT shows new disturbance on {dc.get('dist_new_share_of_seen_pct')} % of the box, but the 4x-wobble HV test on display-scaled GIBS tiles flags none of it. Calibrated GCOV HV is needed here."),
             {"what": "Forest in Rondonia is cleared and burned in the dry season. The box is where OPERA DIST-ALERT showed the most vegetation disturbance in late Oct 2026.",
              "why": "L-band HV is volume scattering from branches and trunks; when the canopy is cut, HV drops by several dB, through smoke and cloud.",
              "radar": f"Same track 068 descending, {dd['before']} vs {dd['after']} (about 2 months). A pixel is flagged when its HV (green channel) falls more than 4x the 12-day wobble of {dd['prior']} to {dd['before']}.",
              "validation": agree,
              "limits": "Display-scaled GIBS radar, not calibrated dB; screening only. The quiet pair spans 12 days but the event pair 60 days, so seasonal drying also lowers HV. DIST is optical and misses cloudy days.",
              "sources": [{"name": "NASA CMR pass search (NISAR GCOV)", "url": cmr_link(bbox, "2026-07-01T00:00:00Z", "2026-11-15T00:00:00Z")},
                          {"name": "GIBS NISAR GCOV layer", "url": GIBS_NISAR},
                          {"name": "GIBS OPERA DIST-ALERT layer + colormap", "url": "https://gibs.earthdata.nasa.gov/colormaps/v1.3/OPERA_Vegetation_Disturbance_Status.xml"},
                          {"name": "Agreement script", "url": REPO + "tools/case_dist.py"}]}, nums)
    d.update(quality="screening", quality_note=SCREEN, image={"png": r["png"], "bbox": bbox, "legend": "blue = HV dropped, faint white = compared"}, radar=r,
             box_choice="densest 16x16-pixel block of OPERA DIST-ALERT disturbance in GIBS z7 tile over (-63,-10) on 2026-10-21")
    return d


def andijan(h):
    wc = J("ml/water_clean.json")
    ser = wc["series"]
    fc = J("forecast/andijan_res_v2.json")
    nov = next(x for x in fc["series"] if x["month"] == "2026-11")
    nov_hist = [x["km2"] for x in fc["series"] if x["month"].endswith("-11") and x["month"] < "2026-11"]
    bbox = [round(v, 4) for v in J("ml/water_model.json")["bbox"]]
    H = "data/headline_numbers.json "
    nums = [num("Radar water, first pass (20 Jun 2026)", ser[0]["km2"], "km2", "data/ml/water_clean.json series[0] (final map)"),
            num("Radar water, last pass (30 Oct 2026)", ser[-1]["km2"], "km2", "data/ml/water_clean.json series[-1] (final map)"),
            num("Radar water on the 100 % cloud day (24 Sep 2026)", next(x["km2"] for x in ser if x["date"] == "2026-09-24"), "km2", "data/ml/water_clean.json series"),
            num("Dec 2026 forecast", h["forecast_dec"]["value"], "km2", H + "forecast_dec"),
            num("Dec 8-in-10 band", f"{h['forecast_dec']['band_low']}-{h['forecast_dec']['band_high']}", "km2", H + "forecast_dec"),
            num(f"Typical December (n = {h['typical_dec']['n_years']} years)", h["typical_dec"]["value"], "km2", H + "typical_dec"),
            num("Nov 2026 photo vs typical November", f"{nov['km2']} vs {round(statistics.mean(nov_hist), 2)} (n = {len(nov_hist)}, range {min(nov_hist)}-{max(nov_hist)})", "km2", "data/forecast/andijan_res_v2.json series"),
            num("Water map IoU on unseen days (nested)", h["nested_iou"]["value"], "IoU", H + "nested_iou"),
            num("95 % CI", f"{h['nested_iou']['ci_low']}-{h['nested_iou']['ci_high']}", "IoU", H + "nested_iou"),
            num("No clean-up", h["raw_iou"]["value"], "IoU", H + "raw_iou"),
            num("Baseline: one HH threshold", h["baseline_rule_iou"]["value"], "IoU", H + "baseline_rule_iou"),
            num("Shuffled-label control", h["shuffled_control_iou"]["value"], "IoU", H + "shuffled_control_iou"),
            num("ICESat-2 level vs area", f"{h['icesat2_spearman']['value']} (n = {h['icesat2_n']['value']})", "Spearman rho", H + "icesat2_spearman"),
            num("Wet-mud over-count, late summer", h["wet_mud_bias"]["value"], "km2", H + "wet_mud_bias")]
    d = base("andijan", "Andijan reservoir: radar water every 12 days vs the 10-year normal", "Andijan reservoir, Fergana valley, Uzbekistan", ser[-1]["date"], bbox, 11,
             ser[0]["date"], ser[-1]["date"], None,
             f"December is forecast at {h['forecast_dec']['value']} km2 (8 in 10: {h['forecast_dec']['band_low']}-{h['forecast_dec']['band_high']}) vs a typical {h['typical_dec']['value']} km2: below normal, but inside the band.",
             {"what": f"NISAR measured the lake on {len(ser)} passes from {ser[0]['date']} to {ser[-1]['date']}, including the 24 Sep day the camera saw only cloud. The summer drop is the normal irrigation cycle; the question is whether this year is unusual.",
              "why": "The reservoir feeds the Fergana valley's fields; how much water is left for winter and spring decides the first irrigation releases.",
              "radar": "Calm water is a mirror: it sends the L-band pulse away, so it looks dark in HH. A learned model on 10 radar features maps water at 40 m on every pass.",
              "validation": f"On 8 photo days it never saw, the map matches Sentinel-2 at IoU {h['nested_iou']['value']} (95 % CI {h['nested_iou']['ci_low']}-{h['nested_iou']['ci_high']}); shuffled labels score {h['shuffled_control_iou']['value']}. ICESat-2 laser levels track the area (rho {h['icesat2_spearman']['value']}, n = {h['icesat2_n']['value']}).",
              "limits": f"Wet mud on the drying shore reads as water (+{h['wet_mud_bias']['value']} km2 in late summer). The typical December rests on only {h['typical_dec']['n_years']} clear years. The model fails at other places so far.",
              "sources": [{"name": "Water map score (nested cut-off)", "url": REPO + "tools/ml_water_clean.py"}, {"name": "Learned water model", "url": REPO + "tools/ml_water.py"},
                          {"name": "Forecast v2", "url": REPO + "tools/forecast_v2.py"}, {"name": "ICESat-2 ATL13 check", "url": REPO + "tools/icesat2_levels.py"},
                          {"name": "NASA CMR NISAR passes over Andijan", "url": h["nisar_start_andijan"]["source"].split(" | ")[0].replace("NASA CMR: ", "")}]}, nums)
    d.update(quality="calibrated", quality_note="NISAR GCOV gamma0 dB from the HDF5 files (tools/gcov_science.py), 40 m", anomaly={
        "dec_forecast_km2": h["forecast_dec"]["value"], "band": [h["forecast_dec"]["band_low"], h["forecast_dec"]["band_high"]],
        "typical_dec_km2": h["typical_dec"]["value"], "anomaly_km2": h["dec_anomaly"]["value"], "typical_inside_band": h["forecast_dec"]["band_low"] <= h["typical_dec"]["value"] <= h["forecast_dec"]["band_high"],
        "latest_month": "2026-11", "latest_km2": nov["km2"], "typical_nov_km2": round(statistics.mean(nov_hist), 2), "nov_years": len(nov_hist)},
        independent_check="Sentinel-2 photos (ESA) and ICESat-2 ATL13 (NASA), neither made by us. OPERA DSWx not run for this case.",
        series=ser)
    return d


def aral(h):
    a = J("timelapse/aral/index.json")
    bbox = a["bbox"]
    t0 = "2026-10-01T00:00:00Z"
    passes, urls = nisar_passes(bbox, (t0, NOW + "T23:59:59Z"))
    dates = sorted({p["start"][:10] for p in passes}, reverse=True)
    best = None
    for dte in dates[:12]:
        im, info = mosaic(*NISAR_LAYER, dte, bbox, 8)
        v = float((im[..., 3] == 255).mean())
        if best is None or v > best[1]:
            best = (dte, v, im, info)
        if v > 0.6:
            break
    dte, v, im, info = best
    Image.fromarray(im).save(IMG / "aral_nisar.png", optimize=True)
    trk = sorted({p["track"] + p["dir"] for p in passes if p["start"][:10] == dte})
    print("aral", dte, round(v, 3), trk, flush=True)
    H = "data/headline_numbers.json "
    nums = [num("Open water 1985 (Landsat)", h["aral_1985_km2"]["value"], "km2", H + "aral_1985_km2"),
            num("Open water 2026 (Landsat/Sentinel-2)", h["aral_2026_km2"]["value"], "km2", H + "aral_2026_km2"),
            num("Lost since 1985", h["aral_loss_pct"]["value"], "%", H + "aral_loss_pct"),
            num("NISAR GIBS pass shown", dte, "date", "NASA CMR + GIBS"),
            num("Share of the box covered by that day's NISAR tiles", round(v * 100, 1), "%", "data/cases/aral.json image")]
    d = base("aral", "Aral Sea: 41 years of shrinking, and today's radar", "Aral Sea, Kazakhstan / Uzbekistan", dte, bbox, 7, "1985-07-28", dte, trk[0] if len(trk) == 1 else None,
             f"Open water in the box fell from {h['aral_1985_km2']['value']:,} km2 (1985) to {h['aral_2026_km2']['value']:,} km2 (2026), {h['aral_loss_pct']['value']} % less (Landsat).",
             {"what": "The Aral Sea shrank as its rivers were diverted to irrigation; the summer Landsat photos show it year by year.",
              "why": "The same rivers feed the Fergana valley, so upstream water use reaches all the way here.",
              "radar": "On the NISAR pass, calm open water is dark and wet salt crust and rough ground are bright. We show the radar; we do not measure water area from it here.",
              "validation": "Water areas are from Landsat (MNDWI > 0 on clear pixels), not from NISAR. Salt flats can look like water to radar, so no radar water number is claimed.",
              "limits": "The 1985 frame borrows 44.7 % of its pixels from 1986 (cloud fill). GIBS radar is display-scaled, not calibrated dB.",
              "sources": [{"name": "Time-lapse baker (Landsat C2 L2, Planetary Computer)", "url": REPO + "tools/bake_timelapse.py"},
                          {"name": "NASA CMR NISAR passes over the Aral box", "url": urls[1]}, {"name": "GIBS NISAR GCOV layer", "url": GIBS_NISAR}]}, nums)
    d.update(quality="screening", quality_note="Landsat numbers are measured; NISAR is shown only (display-scaled GIBS)",
             image={"png": "data/cases/img/aral_nisar.png", "bbox": bbox, "date": dte, "zoom": 8, "tiles": info["tiles"]},
             independent_check="no independent product used: no change is claimed from NISAR here")
    return d


def main():
    want = set(sys.argv[1:]) or {"andijan", "panama", "langtang", "rondonia", "aral"}
    IMG.mkdir(parents=True, exist_ok=True)
    h = headline()
    print("headline numbers:", len(h), flush=True)
    order = ["andijan", "panama", "langtang", "rondonia", "aral"]
    for cid in order:
        if cid not in want:
            continue
        d = {"andijan": lambda: andijan(h), "panama": panama, "langtang": langtang, "rondonia": rondonia, "aral": lambda: aral(h)}[cid]()
        d["generated"] = NOW
        write_json(CASES / f"{cid}.json", d)
    have = [c for c in order if (CASES / f"{c}.json").exists()]
    prev = json.loads((CASES / "index.json").read_text())["cases"] if (CASES / "index.json").exists() else []
    write_json(CASES / "index.json", {"cases": have + [c for c in prev if c not in have]})  # keep world cases (tools/case_world.py)


if __name__ == "__main__":
    main()
