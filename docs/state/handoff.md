# START HERE (falakus, NASA Space Apps 2026 "Dancing with the SARs")

Deadline: Sun 15 Nov 2026 23:59 local. Plan: docs/state/PLAN.md (approved 14 Nov evening). Decisions: docs/state/DECISIONS.md.

## Running
- Server: `cd D:/10_projects/falakus && python -I tools/nisar_tile_server.py --port 8765` → http://127.0.0.1:8765
- Data: data/index.json (16,691 GCOV frames, 6-17 Oct 2026), data/thumb (all 16,691 small previews), data/full (big previews, cache), data/eonet_v2.json.
- Prewarm tour: `python -I tools/prewarm.py`

## State at handoff (updated 14 Nov ~16:50, context 60 % save)
- Server: tools/nisar_tile_server.py: world mosaic (all 16,691 frames, disk tile cache data/tilecache), /api/series (provisional+validated, no Beta, partial frames rejected), /api/frame?band=hh|hv (fixed scale), /api/diff, /api/stats (preview water km2 + HV), /api/science/<stop>.json (calibrated, when present), /api/events (EONET cache data/eonet_v2.json).
- Page web/index.html: intro, 10-stop tour (web/stops.js) in a right panel, time player with NASA/HH/HV views, Before|after swipe, Change map, measured card with sparklines, drawn event icons + animated storm tracks, nav/geolocate/fullscreen.
- Science mode: tools/gcov_science.py ready (earthaccess 0.19 + h5py installed; run with plain `python`, not -I). Boss is logged in to Earthdata in Chrome; ASF access already granted. WAITING: Boss runs earthaccess interactive login in his own PowerShell (writes the netrc). Never type his password or tokens.
- QA: docs/state/qa/round-1.md. Aral preview estimate: water 51.1 -> 4.5 km2 (-91 %), unconfirmed until calibrated.

## Science mode (updated 14 Nov ~20:05)
- Calibrated GCOV boxes: tools/gcov_science.py (retries x3, saves UTM meta, water = fixed rule HH<-18 & HV<-24, `--stats-only` recomputes from disk). Renders: tools/science_render.py (time-series images), tools/science_pyramid.py (z10-14 tiles in data/scitiles/{class,raw} + boxes.json). Colours/classes: tools/sar_colors.py (fixed dB scales; classes water/built/plants/bare; Tashkent built 35.8 % vs ~37 % real).
- "What happened here?": /api/analyze?w,s,e,n -> background job (tools/analyze_area.py, <=25 km box, <=4 passes) -> /api/job/<id>.json; UI = popup button + "Draw an area" in the brand panel; result panel on the right.
- Live per-tile streaming was tried and dropped: 42-314 s per tile.
- Events: EONET 372 + USGS M5+ since 17 Jun = 1,308 (data/usgs_quakes.json). Ocean popups say NISAR does not image open ocean.
- 16 tour stops (web/stops.js) incl. Andijan, Qosh Tepa, Kyzylorda, Fedchenko, Langtang (USGS-confirmed 26 Aug), Kumamoto M6.8; new fields use/next.
- Lanes running: logs docs/state/logs/science.log (lane A, 10 stops) and science_b.log (lane B, 6 new stops). Max 2 NASA lanes + 2 analysis jobs: more got throttled (all reads failed 17:30-19:50).
- Critic report (fresh Opus, 2.9/5): top fix = public static link; validity fixes done (legend, HV dB, range headline, Otsu removed).

## Next 3 steps
1. Verify the Charvak area analysis in Chrome; then static export (tools/export_static.py) for a public link (Boss says yes before publishing).
2. ESA WorldCover agreement % for the classes (no-login COG) -> DECISIONS.md.
3. Fresh critic round 2; Sentinel-2 cloud contrast (Nepal), wind test for Aral.
