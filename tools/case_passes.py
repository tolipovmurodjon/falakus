"""Find same-track NISAR pass pairs around an event time, from NASA CMR (both GCOV collections).

For each (track, direction) that covers the box: the last pass that STARTS before the event, the first pass that
starts after it, and the pass before the last one (for a quiet reference pair). Comparing only within one
track + direction keeps the viewing geometry identical, so a difference is the ground, not the orbit.

Usage: python tools/case_passes.py LON LAT HALF_KM EVENT_ISO [DAYS]
  e.g. python tools/case_passes.py -80.769 7.587 20 2026-10-09T17:56:00Z
"""
import json
import sys
from datetime import datetime, timedelta, timezone

from case_common import km_box, nisar_passes


def iso(t):
    return datetime.fromisoformat(t.replace("Z", "+00:00"))


def pairs(bbox, event_iso, days=75):
    ev = iso(event_iso)
    t0 = (ev - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t1 = min(ev + timedelta(days=days), datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    passes, urls = nisar_passes(bbox, (t0, t1))
    groups = {}
    for p in passes:
        groups.setdefault(p["track"] + p["dir"], []).append(p)
    out = []
    for key, ps in groups.items():
        # one entry per date (a track can have 2 frames over the box on one date)
        bydate = {}
        for p in ps:
            bydate.setdefault(p["start"][:10], p)
        ps = sorted(bydate.values(), key=lambda p: p["start"])
        before = [p for p in ps if iso(p["start"]) < ev]
        after = [p for p in ps if iso(p["start"]) > ev]
        out.append(dict(track=key, n_passes=len(ps), dates=[p["start"][:10] for p in ps],
                        last_before=before[-1] if before else None, prior=before[-2] if len(before) > 1 else None,
                        first_after=after[0] if after else None, second_after=after[1] if len(after) > 1 else None))
    out.sort(key=lambda g: (g["last_before"] is None or g["first_after"] is None, -g["n_passes"]))
    return dict(bbox=bbox, event=event_iso, window=[t0, t1], cmr_urls=urls, n_granules=len(passes), groups=out)


def best_pair(res):
    """Track with a before AND after pass (and a prior pass for the quiet pair if possible): the first look after
    the event wins, then the shortest before/after gap."""
    ok = [g for g in res["groups"] if g["last_before"] and g["first_after"]]
    if not ok:
        return None
    ev = iso(res["event"])
    return min(ok, key=lambda g: (g["prior"] is None, iso(g["first_after"]["start"]) - ev,
                                  iso(g["first_after"]["start"]) - iso(g["last_before"]["start"])))


if __name__ == "__main__":
    lon, lat, half = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    ev = sys.argv[4]
    days = int(sys.argv[5]) if len(sys.argv) > 5 else 75
    r = pairs(km_box(lon, lat, half), ev, days)
    for g in r["groups"]:
        lb, fa = g["last_before"], g["first_after"]
        print(g["track"], g["n_passes"], "before", lb and lb["start"], "after", fa and fa["start"], "prior", g["prior"] and g["prior"]["start"])
    b = best_pair(r)
    print("BEST", json.dumps(b and {k: b[k] for k in ("track", "last_before", "first_after", "prior")}, indent=1))
