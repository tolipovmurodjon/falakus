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

## Science mode (live since ~17:00)
- Boss's earthaccess login is saved (netrc). tools/gcov_science.py reads calibrated GCOV boxes (padded to the exact box); tools/science_render.py makes data/science/<stop>/img/<date>_{rgb,hh,hv,change}.webp + frames.json; the page plays them automatically for tour stops.
- Resolution facts: Uzbekistan (Tashkent, Aral, Fergana) = 20 m only (mode 2005); Nepal, Iowa, Krasheninnikov, Mississippi delta = 10 m (mode 4005); Rogun mixed. 1 m only via Umbra/Capella open data (not checked yet).
- Background run btgpkveoe: all 10 stops, log docs/state/logs/science.log ("=== ALL DONE" at the end). Aral box = 59.4, 45.1, +-50 km.
- Map maxZoom 18; world radar dims only while the playing box is on screen.

## Next 3 steps
1. After "done": `python tools/gcov_science.py aral 60.3 45.4`, then rogun 69.79 38.69, fergana 71.8 40.6, nepal 84.63 27.99; compare calibrated vs preview numbers; write the result in DECISIONS.md.
2. Chrome QA round 2 at 1440 + 390 px (phone untested), Rogun eye check, docs/state/qa/round-2.md.
3. Fresh checker agent on the challenge checklist; then P3: Central Asia river story, draw-a-box analysis, GIF export.
