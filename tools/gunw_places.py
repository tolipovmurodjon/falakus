"""GUNW availability at places famous for ground motion (subsidence): what NISAR interferograms exist, and one browse each.

For each place: list every GUNW pair over the point (CMR, provisional + validated), save the browse PNG of the
longest-interval pair (long intervals accumulate slow subsidence) to data/cases/gunw/<place>_<track><dir>_<ref>_<sec>.png,
and measure a fringe screen in a 25 km disc (coherent fraction, local fringe rate, net fringes across the disc).
Usage: python tools/gunw_places.py   -> data/cases/gunw/places_summary.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gunw_common import FRINGE_CM, PhaseFromColour, cmr_url, fetch, fringe_fields, georef, load_rgba, search  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/cases/gunw"
PLACES = {"mexico_city": (-99.13, 19.43), "tehran": (51.3, 35.6), "jakarta": (106.8, -6.2)}
BORDER = (47, 19, 55)


def screen(path, g, lon, lat):
    a = load_rgba(path)
    gr = georef(a[..., 3] > 0, g["polygon"])
    if not gr:
        return {"georef": None}
    H, W = a.shape[:2]
    c0, r0 = (lon - gr["ox"]) / gr["sx"], (lat - gr["oy"]) / gr["sy"]
    px_km = -gr["sy"] * 111.32
    rad = int(25 / px_km)
    ys, xs = np.mgrid[0:H, 0:W]
    disc = (xs - c0) ** 2 + (ys - r0) ** 2 <= rad ** 2
    ok = (a[..., 3] > 0) & ~np.all(a[..., :3] == BORDER, axis=-1)
    v = a[ok][:, :3]
    if len(v) < 2000:
        return {"georef": gr["ok"], "valid_in_disc": int((ok & disc).sum())}
    pfc = PhaseFromColour(v[np.random.default_rng(0).choice(len(v), min(len(v), 60000), replace=False)])
    ph = pfc(a[..., :3])
    gx, gy, coh = fringe_fields(ph, ok)
    c = disc & ok & (coh > 0.5)
    rate = np.hypot(gx, gy) / px_km
    return {"georef_ok": gr["ok"], "georef_residual_deg": round(gr["residual_deg"], 4), "point_in_image": bool(0 <= c0 < W and 0 <= r0 < H),
            "valid_frac_in_25km_disc": round(float((ok & disc).sum() / max(disc.sum(), 1)), 3),
            "coherent_frac_in_disc": round(float(c.sum() / max((ok & disc).sum(), 1)), 3),
            "median_fringe_rate_cyc_per_km_in_disc": round(float(np.median(rate[c])), 3) if c.sum() > 100 else None,
            "frame_median_fringe_rate": round(float(np.median(rate[ok & (coh > 0.5)])), 3) if (ok & (coh > 0.5)).sum() > 100 else None}


def main():
    out = {}
    for name, (lon, lat) in PLACES.items():
        bbox = (lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05)
        gs = [g for g in search(bbox, "2025-10-01", "2026-11-15") if g["browse"]]
        pairs = [{"track": g["track"], "dir": g["dir"], "frame": g["frame"], "ref": g["ref_date"], "sec": g["sec_date"], "days": g["days"],
                  "browse": g["browse"]} for g in gs]
        rec = {"lon": lon, "lat": lat, "cmr_query": cmr_url(bbox, "2025-10-01", "2026-11-15"), "n_pairs": len(pairs),
               "tracks": sorted({p["track"] + p["dir"] for p in pairs}),
               "first": min((p["ref"] for p in pairs), default=None), "last": max((p["sec"] for p in pairs), default=None),
               "intervals_days": sorted({p["days"] for p in pairs}), "pairs": pairs}
        if gs:
            # longest interval first; tie -> most recent
            pick = sorted(gs, key=lambda g: (-g["days"], g["sec_date"]), reverse=False)[0]
            recent = sorted(gs, key=lambda g: g["sec_date"])[-1]
            rec["saved"] = []
            for tag, g in (("long", pick), ("recent", recent)):
                fn = OUT / f"{name}_{g['track']}{g['dir']}_{g['ref'][:8]}_{g['sec'][:8]}.png"
                try:
                    fetch(g["browse"], fn)
                    s = screen(fn, g, lon, lat)
                    rec["saved"].append({"which": tag, "file": str(fn.relative_to(ROOT)), "granule": g["name"], "days": g["days"],
                                         "ref": g["ref_date"], "sec": g["sec_date"], "footprint": g["polygon"], **s})
                except Exception as e:
                    rec["saved"].append({"which": tag, "error": str(e)})
                if pick is recent:
                    break
        out[name] = rec
        print(name, rec["n_pairs"], rec["tracks"], rec["first"], rec["last"], rec["intervals_days"],
              json.dumps([{k: v for k, v in s.items() if k not in ("footprint", "granule")} for s in rec.get("saved", [])]))
    out["_note"] = f"1 fringe = {FRINGE_CM:.2f} cm LOS. Screening from browse images; 12-day pairs show only fast motion."
    (OUT / "places_summary.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
