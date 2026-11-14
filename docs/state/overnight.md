# Overnight log (falakus)

## Round 1 (14 Nov, 16:30-20:30)
Checker: fresh Opus critic (not shown my reasoning). Score ~2.9/5 overall (≈5.8/10).

| Bar line | score /10 | evidence |
|---|---|---|
| 1 time player | 8 | Aral 10 passes 24 Jun-22 Oct, crossfade, date on screen |
| 2 whole world, fast | 6 | preview tiles capped at z10 (no wasted requests); science tiles static; first visit to a new place still slow |
| 3 tour 8-10 places | 7 | 16 stops; 6 new ones not yet eye-checked |
| 4 change map | 6 | swipe + diff; legend now honest (preview vs dB) |
| 5 optical context | 7 | Esri photo + Sentinel-2 cloudless + swipe |
| 6 Sentinel-1 | 1 | not tested (agent stalled) |
| 7 events | 7 | 1,308 events, drawn icons, storm tracks animate, ocean popups honest |
| 8 explain radar | 7 | how-to card + "what radar sees that a camera can't" (8 powers) |
| 9 honesty + rules | 5 | provisional labels; AI-use note drafted in docs/project/page.md (not yet on the page) |
| 10 pitch material | 3 | deck from phase 0; storyboard drafted in docs/project/video-storyboard.md |

What changed (files): tools/gcov_science.py, tools/science_render.py, tools/science_pyramid.py, tools/sar_colors.py, tools/analyze_area.py, tools/utm_convert.py, tools/nisar_tile_server.py, web/index.html, web/stops.js. Commit 86f0416.
Stopped at 20:30: laptop out of memory, Claude Code stopped the server and both science lanes. Waiting for Boss's "restart". Screenshots for round 1 are in C:\Users\Murodjon\AppData\Local\Temp\claude-chrome-screenshots-34bIVD\ (copy into docs/state/overnight/round-1/ next round).

Lowest line next: 6 (Sentinel-1), then 10 (pitch), then 9 (AI note on the page).

## Round 3 (14 Nov ~22:00-23:00)
Checker round 2b (fresh judge play-test in Chrome): **6/10** (Impact 6, Creativity 8, Validity 5, Relevance 6, Presentation 5). Page was black for a few minutes before (duplicate const), fixed + parse-check rule in CLAUDE.md.
Built (lowest lines first: Presentation + Validity):
- Compare front door (web/index.html "Compare" block): top bar with 3 one-click cases, swipe left image vs right map layer, colour switcher (HH / false colour / HV), number + physics + sources per slide.
  - Langtang: NISAR 19 Aug vs 31 Aug with per-pixel anomaly map (|change| > 4x the pixel's own pair-to-pair std, 5x5 multilook): 0.9 km² vs 0.0-0.2 km² for summer pairs; same-day Sentinel-2 = 89 % cloud.
  - Aral: CSA RADARSAT-1 16 Jul 1997 (tools/rs1_fetch.py, EODMS STAC + open AWS bucket, GCP warp) vs NISAR Oct 2026.
  - Panama: GUNW control pair vs co-event pair.
- /api/s2.json (Sentinel-2 photo tiles for any box + dates, with per-scene cloud %), /history route.
- Critic fixes: settings not hidden/covered, radar fades past z11, play-here flies, BETA passes filtered, km² axes from 0, rice box moved to Shieli (WorldCover 27 % cropland vs 7.5 % at the city), English titles.
- Repo: github.com/tolipovmurodjon/falakus (private, branch overnight), README with figures, MIT.
Screenshots: docs/state/overnight/round-3/. Checker round 3 running.
