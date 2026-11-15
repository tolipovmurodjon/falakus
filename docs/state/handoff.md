# START HERE (falakus, NASA Space Apps 2026 "Dancing with the SARs")

Deadline: Sun 15 Nov 2026 23:59 local. Team guide (story, status, rules): docs/TEAM.md. Decisions: docs/state/DECISIONS.md.
Repo: github.com/tolipovmurodjon/falakus (PUBLIC since 15 Nov 09:00, branch overnight → merged to main by PR).

## LATEST 15 Nov ~13:00 (pull this; main and overnight are the same)
**Start here:** `docs/design-pack/0-TODO-read-first.md` (files, steps to submit, what not to claim). The deck prompt for Claude Design is in `docs/design-pack/1-PROMPT-paste-this.md`. The form is in `docs/design-pack/text/submission-form.md`.

### The numbers we stand behind (Andijan reservoir; all measured, all in `docs/design-pack/text/key-numbers.json`)
| Claim | Number | Check |
|---|---|---|
| Learned water map vs photos on days it never saw | **IoU 0.63** (rule + map 0.59, rule alone 0.30, shuffled 0.07) | leave-one-date-out, 8 photo days |
| Typical area miss | **7.6 km²** (mostly wet mud in late summer) | same test |
| Laser check, second NASA satellite | **Spearman 0.95** (n = 9) | ICESat-2 ATL13 level vs area |
| Lake fall, clear-day photos | **42.1 → 21.1 km²** (23 Jun → 19 Oct 2026) | Sentinel-2 |
| Cloud blindness | **15 of 24** winter photos, 29 of 85 in 2025 | Sentinel-2 cloud mask |
| People who depend on it | **10.9 M**, 29 % of Uzbekistan | stat.uz, 1 Oct 2025 |
| C vs L band over drained mud | Sentinel-1 +21.9 km² vs NISAR +4.8 km² | same week, Oct 2026 |
| **Forecast v2** (10 years, 95 clear months) | 30 days ahead: ML **4.1 km²** miss vs 4.7 (best simple guess) = 13 % better. 3 months: ties the seasonal pattern (5.9 vs 5.3) | walk-forward, `tools/forecast_v2.py` |
| Forecast | Dec 2026 **19.5 km²** (13–26), typical 22.3 · Jan 24.7 (typical 27.1) · Feb 25.8 (typical 25.6) | `data/forecast/andijan_res_v2.json` |

### Do NOT claim
- Model at other places: Rogun IoU 0.02, Qosh Tepa 0.00. It does not transfer yet; those places are "next step".
- The old "30 % better forecast" (3-year model): use the v2 numbers above. `tools/water_intel.py` still reads the old forecast; switch it to `andijan_res_v2.json`.

### Status of each part
| Part | State |
|---|---|
| Deck | `docs/deck/falakus-7.html` works with the 7 official slides; needs the team name + 6 member names. Murodjon is rebuilding it in Claude Design. |
| Form text | Ready: `docs/project/submission-form.md`. |
| Website | Not yet one site: 5 pages. Merge, then deploy to earth.instant.uz. |
| Time-lapse | Aral baked only to 1987; play must take 10–15 s. |
| Explorer | Loads with 0 errors; live movement and event briefings not done. |
| Public project link | GitHub repo (public). |
| Submit | Before **23:59** Tashkent. |

## STATE 15 Nov ~11:00: handoff for Zaynobiddin (Murodjon works on the presentation)
Run the app: `python tools/nisar_tile_server.py --port 8765` → http://127.0.0.1:8765/
- `intel.html`: **new front door.** Water briefings per water body: map, plain-language "what happened / why / what next", tabs for farmer / water agency / family, and how sure we are. Works, with 0 console errors (Andijan). Boss: "too much on it, make it clean". NEXT: cut to headline + 3 short sections + one chart, one style.
- `timelapse.html`: Google Earth-style 1985–2026 Landsat summers + NISAR weeks (`tools/bake_timelapse.py`, frames in `data/timelapse/<place>/`). Boss: too slow; must play in 10–15 s, start at once, never stall. The builder agent was told this; check it.
- `explorer.html` (+ .js, .css): NASA Worldview-style layers (GIBS: MODIS, IMERG rain, fires, SMAP, snow) + EONET events + NISAR. Loads with 0 errors. The agent stalled before finishing "live movement" + plain-language event briefings. NEXT: test each layer, add those two.
- `dash.html`: first dashboard version (superseded by `intel.html`). `index.html`: the old classic map; Play bug fixed (the pulse rests while a chapter or the player is open).

### ML and science measured today (all in data/, reproducible by tools/)
| what | tool | result |
|---|---|---|
| Learned water map (gradient boosting, 10 radar features) | `tools/ml_water.py` | Leave-one-date-out on 8 photo days: IoU **0.63** vs 0.59 rule + water map, 0.30 rule alone; null 0.07. Area miss 7.6 vs 8.8 km². Error maps `data/ml/water_err_<date>.png`: it adds 6–12 km² of wet mud and misses 1–6 km². |
| Same model at new places | `tools/ml_water_transfer.py rogun qoshtepa` | Copernicus DEM slope > 12° mask added (radar shadow). **Rogun: FAILS, IoU 0.02** (gorge, n = 3 photo days): do not show Rogun km² as fact. Qosh Tepa: was running (flat, mask 0 %). |
| Laser check | `tools/icesat2_levels.py` | ICESat-2 level vs area: Spearman **0.95**, Pearson 0.85, n = 9 |
| 10-year record | `tools/s2_history.py andijan_res 73.028 40.684 73.242 40.846` | Sentinel-2 monthly 2017→2026, resumable (was at 2018-12) |
| Forecast v2 | `tools/forecast_v2.py andijan_res` | Run AFTER s2_history finishes: walk-forward vs persistence / seasonal / climatology, 1 and 3 months ahead, band from its own misses |
| Briefings | `tools/water_intel.py` (`PYTHONIOENCODING=utf-8`) | `data/intel/<place>.json`; every number comes from files |
| Tuyamuyun radar | `tools/gcov_science.py tuyamuyun 61.40 41.22 --km 15` | Was downloading (2 passes); network flaps, rerun resumes |
| Population | `data/waterroad/population.json` | 10.9 M people in the 3 valley regions (stat.uz, 1 Oct 2025), 28.6 % of Uzbekistan |

### Deck
- `docs/deck/falakus-7.html` (`tools/build_deck7.py`): 7 slides in the guide's order: Title, Problem, Solution + change map, How it works, Results, Data, Impact. Pictures from `tools/make_deck_images.py` (`img/change_map.jpg`, `img/before_after.jpg`). **TODO: team name + 6 member names** in `TEAM` at the top of `build_deck7.py`. Murodjon owns the deck now.

### Submission checklist (from the official guide video)
- [ ] Project name + summary of 50–200 words (what we built, how it answers the challenge, why it matters): start from `docs/project/page.md`.
- [ ] Demo link: ≤ 7 slides (incl. title) OR video ≤ 30 s; public, no login (GitHub / Drive / YouTube). English (a video may use another language with English subtitles).
- [ ] Final project link: public, no login. Plan: GitHub Pages from `tools/export_static.py` → `dist/` → `gh-pages` branch, or the repo link.
- [ ] Details: what it does, how it works, benefits, impact, tools/languages, creativity, factors considered.
- [ ] SI (AI) use: tick the options. Code + text by Claude, disclosed in text. No AI images, so no watermark needed. No NASA logos.
- [ ] NASA data used (required): NISAR GCOV + GUNW (ASF DAAC), ICESat-2 ATL13, EONET, GIBS (MODIS, IMERG), CMR / Earthdata. Partner data: ESA Sentinel-1/2, WorldCover, Copernicus DEM, USGS Landsat, CSA RADARSAT-1, ICEYE, stat.uz.
- [ ] All members registered for the same local event and on the Members tab (max 6). No photos or video of anyone under 18.
- [ ] Tick terms + "work is original" → **Submit for judging before 23:59 Tashkent**. Only the last submission counts.

### What is left, in order (Boss, 15 Nov 11:30)
0. **Domain:** the finished site will be served at **earth.instant.uz**, the public link judges open. Everything must work there cold, with no localhost paths (use relative URLs, see `tools/export_static.py`).
1. **One website, not separate HTML pages.** Today each part is its own page (`intel.html`, `timelapse.html`, `explorer.html`, `index.html`, `dash.html`) with its own look and nav. Make one site:
   - one shared header and nav, and one style (Falak tokens: paper #F6F3ED, ink #14120D, teal #17515F);
   - `index.html` = the briefings front door; the time-lapse and explorer as sections or tabs;
   - the old classic map moves to `app.html`;
   - every page loads cold with 0 console errors, at 1440 and 390 px.
2. Briefings page: cut it down (Boss: "too much"): headline, 3 short sections, one chart.
3. Time-lapse: the whole play in 10–15 s, starting at once.
4. Explorer: check every layer loads; add live movement and plain-language event briefings.
5. Network: NASA, GitHub and Planetary Computer drop out from here; every tool retries. Check the public link from another network or phone.
6. Public link: `python tools/export_static.py` → push `dist/` to a `gh-pages` branch → enable Pages (`gh api -X POST repos/tolipovmurodjon/falakus/pages -f source[branch]=gh-pages -f source[path]=/`). Test logged out.
7. Deck: team name + 6 names in `tools/build_deck7.py` (TEAM), rebuild, export to PDF, upload publicly.
8. Fill the form: see `docs/project/submission-rules.md` (every field, our drafts, the disqualifiers). Submit before 23:59.

### Walls
ALOS 2008 still needs the ASF app approval in Murodjon's Earthdata account (`tools/alos_series.py`, command below). Laptop RAM is about 0.8 GB free: one heavy job at a time.

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

## WALL for Boss (2 min, his account)
- ALOS PALSAR (L-band like NISAR, 2006-2011, 28 scenes over the reservoir incl. HH+HV Jun/Aug/Oct 2008) returns 401 "Pre authorization required".
  Fix: log in at https://urs.earthdata.nasa.gov -> Applications -> Authorized Apps -> approve "Alaska Satellite Facility Data Access"; then open https://search.asf.alaska.edu once and accept the ALOS terms. Then run: python tools/alos_series.py andijan_res 73.135 40.765 73.0279 40.6839 73.2421 40.8461

## STATE 15 Nov ~03:00 (judge 4: 5.0 -> 5: 7.0 -> 6: 6.5 after it found the EONET lat/lon swap)
STOPPED by low laptop memory (restart only when Boss says / memory is free):
- app server:   python tools/nisar_tile_server.py --port 8765
- laser check:  python -u tools/icesat2_levels.py > docs/state/logs/icesat2.log   (works when NASA reachable; 10 Jan 2025 = 847.99 m, 335 segments)
- flood rescan: python -u tools/flood_watch.py --max 125 > docs/state/logs/floods4.log   (uses tools/event_coords.py; 46 old swapped results already discarded)
- cloud photo:  python tools/bake_cloud_photo.py   (textured 24 Sep cloud from raw B04/B03/B02)
Network to NASA/GitHub/Planetary Computer flaps (Google fine): retry, push when up.
Done tonight since round 4: baked story photos (offline-safe, JPEG), cloudy tab real cloud, shoreline overlay in time-lapse, Aral 1,598->1 km2 (photos) + NISAR HH+HV <= 0.93 km2 (polarization finding), Fergana harvest map (12.8 % lost plant echo), forecast skill 30 % + honest 80 % band, 30 s video docs/video/falakus-30s.mp4 (tools/make_video.py), 7-slide deck docs/deck/story.html, project page text docs/project/page.md, EONET coordinate check, player fixes.
NEXT: 1) restart server, re-run the 4 jobs above; 2) pair laser levels with areas (icesat2 json) -> chapter 1 line + deck row if r holds; 3) recapture video shot s2 with the textured cloud, rebuild video; 4) judge round 7 (app + deck + video); 5) public link needs Boss's yes; ALOS needs Boss's ASF authorization.

## Done 15 Nov 01:00-02:00 (see git log)
- Judge round 4 = 5.0/10 (fresh website-design-auditor). Fixed: phone nav row, front-door line, Explore menu closes (now a dropdown card), calm Play mode, dated headline, flood list sorted + no layer leak, settings reachable on phone, zoom cap + sharp 20 m pixels in all radar views, photo cut to exactly the box at native 10 m + cloud % inside the box.
- New: cloudy-day slide (24 Sep 2026, photo 100 % cloud vs NISAR), time-lapse frame info (water/crops + plain HH/HV lesson), data timeline panel, ML forecast slide (ridge, walk-forward 2026: MAE 2.3 km2 vs 3.3 seasonal / 4.3 persistence; Dec-Feb 22.6/26.9/29.4 km2), 7-slide story deck docs/deck/story.html (tools/build_story_pitch.py), Falak design system tokens from Zaynobiddin's static.zip (warm paper, #17515F, one shadow).
- Measured: Sentinel-1 2023-2026 monthly (median IoU 0.79, autumn mud over-count), all-tracks NISAR 42 passes r 0.82 vs photo, RVI vs NDVI r 0.578 (n 11), cloudy camera visits 2025: 29/85 (34 %), Dec-Mar 15/24.
- Zaynobiddin will send his latest design repo; old Zaynobiddin33/Falak is outdated (mock data) -> do not use.

## Next steps
- A. Put '42 NISAR looks, all orbits, r 0.82' into chapter 1 text. B. Aral chapter: lead with a measured number (judge #8). C. Fergana: show HV change map so the change is visible (judge #7). D. Fresh judge round 5. E. 30 s video storyboard + record. F. Deck: add forecast + cloudy slide numbers.
-1. RUNNING: tools/s1_series.py andijan_res (Sentinel-1 monthly Nov 2023-Nov 2026, log docs/state/logs/s1series.log, out data/s1series/andijan_res/*.png + andijan_res.json). When done: serve /s1series/ route, add a 3-year chart (S1 monthly water km2 + NISAR 12-day + S2 points) and a multi-year time-lapse button to story ch.1 (Boss: 'timelapse for all time, 1-2 years, like Google Earth'). Case->tour freeze NOT reproduced (0 errors). Time-lapse button per chapter added (NISAR passes).
0. DONE: ch.2 colour, Aral box outline, Flood watch view, Andijan stop rewritten (id andijan_res). NEXT: judge bug case->tour freeze (closeCase must leave no hooks), phone 390 px check, then fresh judge round 4 (Opus agent, Chrome, own tab) -> fix lowest.
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
