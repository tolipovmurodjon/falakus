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

## State (updated 14 Nov ~22:15, context 60 % save)
- Server: python tools/nisar_tile_server.py --port 8765 (plain python, not -I). Memory-safe caches. World radar = grayscale HH (data/tilecache_hh).
- Science: tools/gcov_science.py (16-bit npz, resume, retries) -> science_render.py -> science_pyramid.py (data/scitiles/{class,raw,water,built,plants}). Done: tashkent, aral (40 km), andijan, fergana, langtang (29 passes, pyramid may be pending). Lane log docs/state/logs/science.log; remaining rogun, qoshtepa, kyzylorda, nepal, kumamoto, fedchenko, iowa, lava, delta, rondonia, fire.
- Colour law (expert review): grey = radar; blue = calm water; amber = very bright/built; green = plants; no paint = other; orange/violet = brighter/darker.
- Features: 16 stops in 2 chapters (Water road, World) with hero numbers; draw-a-box 20 m analysis (/api/analyze); Sentinel-1 C-band switch (/api/s1.json, PC mosaic, no login); Ship watch (tools/ship_count.py, data/ships/<choke>.json, rough-sea passes flagged); Radar finds (Baku slicks tools/slick_find.py, Tashkent apron tools/apron_count.py); last-radar-look chip (/api/lastlook.json); USGS quakes; Layers button; phone layout (web/phone-preview.html).
- Checker: round 1 ~5.8, round 2 6.1/10 (lowest: pitch 4, optical 5, explain 5, S1 6, speed 6). Logs docs/state/overnight.md, screenshots docs/state/overnight/round-2.
- Disk D: almost full (~550 MB free; not our files). Keep outputs small.
- GUNW (ground motion): tools/gunw_read.py written; Kumamoto pair 20260721->20260814 returned 403 Forbidden from ASF CloudFront (needs check: maybe GUNW requires separate EULA/app approval). NISAR permanent gap 2026-07-27..08-10.
- Europe holes in world map: CMR has ~350 frames/cycle over 0-40E,45-60N; index kept 280; partial frames rejected in load_preview. Fix candidate: place partial frames by full footprint (test first).

## Next steps
1. Verify Radar finds in Chrome (slick + apron), commit.
2. GUNW 403: test another pair / check ASF EULA; if blocked, write in DECISIONS and show wrapped phase from a pair that works.
3. Europe holes: partial-frame placement test, then rebuild world tiles.
4. Checker round 3; pitch deck (7 slides) + record 30 s video; static export (Boss yes before publishing).
