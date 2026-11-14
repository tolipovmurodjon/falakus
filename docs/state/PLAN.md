# falakus — deep 5-phase plan (after phase 0)

## Context
Phase 0 works on localhost:8765: a world map of all 16,691 NISAR GCOV frames of one 12-day cycle (6-17 Oct 2026), radar streamed from NASA previews (~150 m), NASA EONET events (247+ incl. 125 floods), and a first time player + 10-stop tour (just written, not yet walked in Chrome). Boss: "it should not be just a map, it should give info": a judge or an ordinary person must understand **what changed, where, by how much, and why** within 5 minutes, starting in Uzbekistan (Aral, Amu Darya, Syr Darya, Karakalpakstan) and going worldwide, with cinematic animation, not dots.
Decisions (Boss, this turn): conflict stops = **humanitarian only** (one Gaza building-damage stop, sourced, no military sites) · summary text = **numbers first, Claude API on top** (needs a key Boss sets; no key → numbers-only text) · Boss **will log in to Earthdata** → calibrated dB path opens · hosting = **build local, export static, Boss picks host later**.

## The deeper version (4 expert questions)
1. **What a pro adds** (NASA OPERA / HydroSAR water scientist + a NYT graphics editor): turn pixels into a **ledger**: water km² per pass, % change, gained/lost-water map, each number traceable to a NISAR file, checked against an independent witness; the story leads with the number, the map proves it.
2. **Rawest material**: GCOV `.h5` HHHH/HVHV gamma0 + `mask` + `numberOfLooks` (calibrated, not the PNG preview); CMR granule metadata; NASA EONET/GDACS event geometry; Sentinel-2 L2A scenes for validation; the challenge text as the spec.
3. **Methods + tools**: earthaccess + h5py range reads of a box (no 2 GB downloads); dB = 10·log10; multi-date mean to cut speckle; water = HH below a threshold chosen by Otsu per place; change = log-ratio (dB after − dB before) with a noise-floor mask; one track/frame per series; static WebP/COG outputs; MapLibre; Claude (claude-haiku-5-5) only to phrase numbers already computed.
4. **Outside judges**: water-area agreement % vs Sentinel-2 NDWI on a clear day; event dates vs EONET/GDACS; tile + timelapse load times measured in the browser; a fresh checker agent scoring the challenge checklist from screenshots; a teammate who never saw radar answers 3 questions after 2 minutes.

## Top 10 flaws now (fix order)
1. Some passes 404 (NASA preview missing) → timelapse breaks; must drop bad passes server-side.
2. First play of a place streams 11× 3.5 MB from NASA (5-30 s) → judges see "Loading".
3. No numbers anywhere: no km², no %, no "what changed" sentence.
4. Change map = luminance diff of colour previews → can show fake change; not labelled strongly enough.
5. Events are dots; no animation, no link from event to radar evidence.
6. Tour stops never checked by eye (some may show nothing).
7. Uzbekistan water story (Aral / Amu Darya / Syr Darya / Rogun / Qosh Tepa) is not one connected story.
8. Three panels cover the map on 1440 px; phone (390 px) never tested.
9. No before/after swipe; no radar-vs-optical compare.
10. Localhost only; no export path for a public link; no project page text, video, AI-use note.

## Top 10 new ideas (in the plan below)
1. **Water ledger**: per-pass water km² chart for Aral east/west, Syr Darya delta, Rogun, Tuyamuyun; the line moves as the timelapse plays.
2. **"What changed here" intel card**: numbers → sentence ("Aral east basin: open water 412 → 318 km² from 24 Jun to 22 Oct, −23 %"), Claude polishes wording when a key exists.
3. **Swipe compare**: drag a bar: before | after radar, or radar | optical.
4. **Cinematic events**: storm tracks drawn over time with a moving eye icon, fire glow pulse, flood ripple; category icons, not dots.
5. **Global change hotspots**: compare the Jun and Oct world cycles, rank the 30 biggest-changing places on Earth, each clickable.
6. **River of Central Asia story**: glacier → Rogun → Qosh Tepa → fields → Aral, one scroll, numbers at each stop.
7. **Pixel probe**: tap → that pixel's brightness curve over all passes.
8. **Clouds can't stop it**: same day, Sentinel-2 photo (cloudy) vs NISAR (clear) side by side.
9. **Timelapse export**: one-click GIF/MP4 per place for the 30-s video and sharing.
10. **Humanitarian stop (Gaza)**: building-damage change framed like UN damage maps, sourced (UNOSAT), honest limits.

## Boss's round-2 notes (this turn) → where they land
- "Current UI is trash, make loading faster" → P1 first: speed budget (first map < 2 s, any tile < 1 s after first view, a place's timelapse first frame < 2 s), plus a UI rebuild: clear zoom +/- and locate buttons, one search box (place names), panels that collapse, phone-first.
- "Click anywhere → show what happened, with all info" → P2 "What happened here" card for ANY point: passes found, dates, change % (water / brightness / HV), nearby EONET events, the sentence, and the timelapse, in one click.
- "I can draw" → P2 draw a box or polygon on the map → same analysis for that area (area km², water km² per pass, change map clipped to it).
- "Use labs for the text, not paid generation" → text = our numbers in sentences; the polish step calls Boss's labs proxy if it answers (checked at build time, no key typed by me), else stays numbers-only.
- "Whole world: Uzbekistan → Central Asia → Russia, Ukraine, Iran; big ships moving over time" → P4: regional stories (Central Asia water, Caspian coast, Black Sea and Persian Gulf ports); **ships** = bright points on dark harbour water counted per NISAR pass (NISAR images coasts, not open ocean) + Global Fishing Watch radar vessel detections if Boss signs up for its free token. Conflict framing stays humanitarian-only (his earlier pick).
- "Can we get 1 m resolution?" → NISAR cannot: its finest product is ~10 m (GCOV 10-20 m). The door: **Umbra and Capella open SAR data** (free, CC BY 4.0, ~0.25-1 m, on public AWS buckets, no login) at a few sites → "zoom from NISAR 10 m to 0.5 m" moment. P4 checks which open scenes overlap our stops.

## Phases (each: build → Chrome judge walk at 1440 + 390 px → fresh checker agent → fix lowest)
**P1 Truth + speed** (tools/nisar_tile_server.py, tools/prewarm.py, web/index.html)
- Series endpoint drops passes whose preview fails or is partial (QA: valid-pixel share < 60 %); cache series JSON on disk.
- Precompute every tour stop's frames + diffs to `data/cache/` (prewarm.py), serve static; target: tour step plays < 2 s.
- Done = prewarm prints 0 fails for 10 stops; timelapse first frame < 2 s measured in Chrome.

**P2 Intel engine** (new tools/place_stats.py; server `/api/stats`; web intel card)
- Earthdata login (Boss) → `tools/gcov_subset.py`: earthaccess + h5py read a box of HHHH/HVHV per pass → dB arrays (cache .npy).
- Water km² per pass (Otsu on HH dB, noise mask), HV mean for crops, log-ratio change map (calibrated) → replaces preview diff where available; preview-based fallback labelled.
- Intel card: numbers + template sentence; `/api/summary` calls Claude (claude-haiku-5-5) only if ANTHROPIC_API_KEY is set (load the `claude-api` skill before writing it).
- Validation: Sentinel-2 NDWI for one clear date at Aral east → agreement %.
- Done = Aral, Rogun, Fergana, Nepal show a chart + sentence; agreement % printed in DECISIONS.md.

**P3 Cinematic UX** (web/)
- Swipe compare (before/after, radar/optical), animated EONET events (icons, track drawing, fire glow), pixel probe, Central Asia river story, panel layout redesign (collapsible, phone-first), GIF export.
- Done = checker scores Presentation + Creativity ≥ 9; 390 px screenshots have no overlap.

**P4 World change + more data**
- Global hotspots (Jun vs Oct world mosaic diff, ranked list); Sentinel-1 no-login test (PC GRD, AWS RTC Indigo) 30 min cap; Gaza humanitarian stop with UNOSAT source.
- Done = hotspot list of 30 places clickable; S1 outcome written.

**P5 Ship**
- Static export (prebuilt tiles for z0-8 + stop caches) ready for any host (Boss picks, says yes before publishing); README + project page text + AI-use note; Eye Run deck update (render.py check); 30-s video storyboard + recorded screen capture.
- Done = fresh checker ≥ 9/10 twice in a row (the active /goal), screenshots in docs/state/overnight/.

## Walls
No money, no sign-ups in Boss's name (he types logins), nothing published or pushed, never delete data, no R2, never read secret files; Claude key only via env var Boss sets.

## Usability QA after every build (Boss, this turn)
Every build ends with an in-depth play test in Chrome, as a judge and as an ordinary user: first 5 minutes cold, every button, every tour stop, wrong taps, slow network, phone width. Output each time: `docs/state/qa/round-N.md` = what worked, every bug with a screenshot, a 1-10 usability score per screen, and 5+ concrete suggestions; the top suggestions go into the next build. Boss gets a short version in chat.

## Verification (every round)
Server up → Chrome on localhost: intro → tour stops 1-10 → play, change map, swipe → event "play the radar here" → tap anywhere; screenshots 1440 + 390 into `docs/state/overnight/round-N/`; prewarm.py timings; one fresh Opus checker agent scores the challenge checklist (CLAUDE.md "What the challenge asks") with evidence; log in `docs/state/overnight.md`; local git commit every 2 rounds.
