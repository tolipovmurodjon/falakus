# START HERE (falakus, NASA Space Apps 2026 "Dancing with the SARs")

Deadline: Sun 15 Nov 2026 23:59 local. Team guide (story, status, rules): docs/TEAM.md. Decisions: docs/state/DECISIONS.md.
Repo: github.com/tolipovmurodjon/falakus (private, branch overnight, Zaynobiddin33 invited).

## State 15 Nov ~01:30
- STORY (Boss): one screen "Where the valley's water goes": Andijan reservoir -> Fergana -> Aral; rest behind "Explore". Only measured numbers.
- Water pipeline tools/water_road.py (Lee, HH<T fit on ONE pass, held-out IoU vs Sentinel-2, WorldCover water+1 km zone):
  - andijan_res (real reservoir 73.135E 40.765N): NISAR 50->19 km2 vs S2 40->17, r=0.83, held-out IoU median 0.58, +8.6 km2 over-count.
  - fergana: IoU 0.05-0.17 (canals narrower than 20 m pixels). aral: FAILS (salt flats look like water, IoU ~0) -> show Aral only via 1997 vs 2026 RADARSAT, not water km2.
  - OLD andijan stop text is WRONG (box west of reservoir) -> rewrite web/stops.js andijan before demo.
- Flood watch tools/flood_watch.py running in background (40 EONET floods, log docs/state/logs/floods.log, out data/floods/). First: Iran 0 km2 new water, 32 km2 brighter, S2 clear -> 'brighter' = wetter soil OR flooded vegetation candidates (label honestly).
- 0.5 m check (Radar finds -> Bosphorus): 5/12 S1 dots on visible ships.
- Server box (AWS i-0854c64194a77b2a6, us-east-2) RUNNING as c7i.4xlarge (16 CPU, no GPU, ~$0.71/h; GPU capacity refused). User zaynobiddin added (key on Desktop\zaynobiddin-gpu-access, tested login, no sudo, /srv/falakus shared). Boss stops it himself.
- KML exact preview boxes: tools/fetch_kml_boxes.py paused at 600/16691 (resumable); server uses them when present.
- Judge round 3: 6.0/10. Open: case->tour freeze, phone layout, S2 trimmed to box + cloud % in box, draw analysis box.

## Done since
- Story screen live: top bar 1 Andijan reservoir / 2 Fergana fields / 3 Aral Sea + Explore menu; chapter 1 auto-opens on first visit; chart radar vs Sentinel-2 km2. Task board: docs/state/PLAN.md (bottom).

## Next steps
0. Check ch.2 Fergana + ch.3 Aral in Chrome; draw the Aral box; wire Explore -> Flood watch (x-floods button has no handler yet).
1. When flood_watch finishes: look at 3 PNGs by eye, add "Flood watch" list+map in Explore (label: new open water vs wetter/flooded-vegetation candidates; S2 check).
2. Build the one-screen story (Andijan reservoir chart r=0.83 + photo/radar swipe; Fergana HV/RVI heartbeat; Aral 1997 vs 2026).
3. Rewrite Andijan stop text; fix judge open problems; fresh judge; deck + 30 s video; public link needs Boss yes.

## State (updated 14 Nov ~22:15, context 60 % save)
- Server: python tools/nisar_tile_server.py --port 8765 (plain python, not -I). Memory-safe caches. World radar = grayscale HH (data/tilecache_hh).
- Science: tools/gcov_science.py (16-bit npz, resume, retries) -> science_render.py -> science_pyramid.py (data/scitiles/{class,raw,water,built,plants}). Done: tashkent, aral (40 km), andijan, fergana, langtang (29 passes, pyramid may be pending). Lane log docs/state/logs/science.log; remaining rogun, qoshtepa, kyzylorda, nepal, kumamoto, fedchenko, iowa, lava, delta, rondonia, fire.
- Colour law (expert review): grey = radar; blue = calm water; amber = very bright/built; green = plants; no paint = other; orange/violet = brighter/darker.
- Features: 16 stops in 2 chapters (Water road, World) with hero numbers; draw-a-box 20 m analysis (/api/analyze); Sentinel-1 C-band switch (/api/s1.json, PC mosaic, no login); Ship watch (tools/ship_count.py, data/ships/<choke>.json, rough-sea passes flagged); Radar finds (Baku slicks tools/slick_find.py, Tashkent apron tools/apron_count.py); last-radar-look chip (/api/lastlook.json); USGS quakes; Layers button; phone layout (web/phone-preview.html).
- Checker: round 1 ~5.8, round 2 6.1/10 (lowest: pitch 4, optical 5, explain 5, S1 6, speed 6). Logs docs/state/overnight.md, screenshots docs/state/overnight/round-2.
- Disk D: almost full (~550 MB free; not our files). Keep outputs small.
- GUNW (ground motion): tools/gunw_read.py written; Kumamoto pair 20260721->20260814 returned 403 Forbidden from ASF CloudFront (needs check: maybe GUNW requires separate EULA/app approval). NISAR permanent gap 2026-07-27..08-10.
- Europe holes in world map: CMR has ~350 frames/cycle over 0-40E,45-60N; index kept 280; partial frames rejected in load_preview. Fix candidate: place partial frames by full footprint (test first).

## Added ~23:00
- Ground motion WORKS: tools/gunw_read.py panama_m77 (pair 20261002->20261014, 80 m, ~100 cm LOS, fringes.png/los.png in data/motion/). Kumamoto file 403 (that file only; Rogun GUNW opens). In Radar finds.
- ML: tools/ml_landcover.py (RF on NISAR time-series features vs ESA WorldCover via PC, leave-one-place-out). First run: ML beats rules at tashkent 0.60 vs 0.48, andijan 0.58 vs 0.26, fergana 0.66 vs 0.36; aral 0.00 (98 % bare, model calls dry seabed water/crops: needs bare examples), langtang 0.24 (mountains). Results data/ml/landcover_results.json. Next: more places as lane finishes, add pooled score, show in app.
- Map settings panel; theme-aware measured card; page broke once from duplicate const (parse check rule in CLAUDE.md).
- Cache data/full cleared with Boss's yes (2 GB). Science lane running again (tashkent missing passes first).

## Next steps
1. Verify Radar finds in Chrome (slick + apron), commit.
2. GUNW 403: test another pair / check ASF EULA; if blocked, write in DECISIONS and show wrapped phase from a pair that works.
3. Europe holes: partial-frame placement test, then rebuild world tiles.
4. Checker round 3; pitch deck (7 slides) + record 30 s video; static export (Boss yes before publishing).
