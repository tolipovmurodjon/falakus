# Falakus: team guide for the 4 speakers

Read this twice before the pitch. Plain words first, then the radar term.
Learn tab (`web/learn.html`) has the pictures for every idea below.

Last checked: 15 Nov 2026, ~14:45 (branch v11). Anything marked **VERIFY** has not been confirmed. Do not say it on stage until someone confirms it.

---

## 1. The story in one breath

> **"NASA tells you where something happened. Falakus shows what changed: through cloud, smoke and night, anywhere NISAR flies, every 12 days."**

Every one of the four of us must be able to say this without notes.

The problem in 3 lines:
- Decisions about water, farms and disasters depend on **seeing change**.
- Cameras go blind exactly when it matters: cloud, smoke, night. Andijan on **24 Sep 2026: 100 % cloud**.
- Radar sees through all of that, but raw radar is unreadable grey static. **The gap is translation, and Falakus does it.**

---

## 2. What we built (v11) and what each part proves

| Part | What it does | What it proves |
|---|---|---|
| **Global pass finder** | Pick any place. NASA CMR lists every NISAR pass over it, and NASA GIBS shows the radar (about 15 m tiles). | It's real NISAR data, anywhere, with dates. No data of ours in the middle. |
| **Same-track before/after compare** | Two passes from the **same orbit track**, side by side. | We compare like with like. Only the ground changed, not the viewing angle. |
| **Any-place time-lapse** | Plays every pass for a place, with a progress bar. Skips frames that aren't ready. | A 12-day heartbeat, with no cloud gaps. |
| **Camera vs radar** | A same-day optical image on top of the radar, with a slider. | Shows the cloud advantage instead of just claiming it. |
| **Live hotspots** | NASA EONET events, USGS quakes, fires. | NASA tells us *where*. We check *what changed*. |
| **Case: Andijan water** | 11 calibrated 20 m passes, an ML water map, validation, forecast. | Depth: measurement + validation + limits. |
| **Case: Panama M7.7** (9 Oct 2026) | Interferogram of ground motion. | L-band's unique power: cm-scale motion. **VERIFY it loads before the pitch** (`data/motion/` is not in this checkout). |
| **Case: Langtang slopes** (Nepal) | Change test: each pixel against its own normal 12-day wobble. | A detector that needs no labels and has a false-alarm baseline. |
| **Case: Rondônia clearing** (Brazil) | Forest loss seen as a drop in HV (plant echo). | Volume scattering in action. **VERIFY the numbers on screen.** |
| **Case: Aral Sea** | Landsat 1985 to 2026 time-lapse, plus RADARSAT-1 1997 vs NISAR 2026. | The emotional hook: what water mismanagement looks like. |
| **Learn tab** | This physics, with real images. | We understand the data, not just display it. |

---

## 3. Radar physics in 2 minutes

**How it works.** NISAR sends its own microwave pulse (24 cm long) and records the echo. Because it brings its own "light", it works at **night**. Cloud droplets (about 10 µm) are tiny next to a 24 cm wave, so the wave **passes straight through cloud**. Radar doesn't detect clouds. It ignores them.

**What the echo depends on:** surface **roughness** and **wetness**, not colour.

| Surface | What the wave does | Looks |
|---|---|---|
| Calm water | Bounces away like a mirror (**specular reflection**) | **Black** |
| Wind-roughened water | Some energy comes back | Grey (it can fool us) |
| Plants, crops, forest | Scattered and twisted by leaves (**volume scattering**), strong in HV | **Green** in false colour |
| Towns, flooded forest | Ground to wall to sensor (**double bounce**) | **Very bright** |
| Bare rough soil, rubble | Rough surface sends more back | Bright |

### The 10 words (say the plain word, then the term)
1. **Backscatter**: the share of the pulse that comes back. A bright pixel means a strong echo.
2. **Polarisation (HH / HV)**: the direction the wave wiggles. HH = sent horizontal, received horizontal. HV = sent horizontal, received vertical, which comes mostly from plants.
3. **Specular reflection**: a mirror bounce, which makes calm water black.
4. **Volume scattering**: leaves bounce and twist the pulse, so HV is strong.
5. **Double bounce**: ground to wall (or trunk) and straight back. Towns and flooded forest look very bright.
6. **Speckle**: radar's grainy salt-and-pepper look. *"One radar pixel lies; a pixel compared with its own history doesn't."*
7. **dB (decibel)**: a log scale for the echo. **3 dB = half or double** the echo.
8. **GCOV / GUNW**: NISAR products. GCOV = calibrated echo strength on a map grid, 20 m (**our main data**). GUNW = interferogram, i.e. ground motion from phase.
9. **Coherence**: how alike two passes' echoes are (0 to 1). High means the phase can be trusted. A drop can mean damage.
10. **Ascending / descending**: the satellite heading north or south. We compare passes from the **same track**.

Bonus terms if a judge pushes: **layover / shadow** (mountains fold over or go dark), **line of sight** (motion is measured toward or away from the satellite), **incidence angle**.

### L-band (NISAR) vs C-band (Sentinel-1)
- NISAR L-band **24 cm**. Sentinel-1 C-band **5.6 cm**.
- The longer wave gets past leaves to stems and soil. So it **sees floods under forest**, follows crop structure, and **stays coherent over vegetation**, which ground-motion maps need.
- Our measured example: over the drained shore at Andijan, **same week, Oct 2026**, Sentinel-1 over-counted water by **21.9 km²** and NISAR by **4.8 km²**.

### Ground motion (only with GUNW)
- One colour cycle (fringe) = half the wavelength = **≈ 11.9 cm** of motion along the line of sight (L-band). C-band ≈ 2.8 cm.
- **GCOV has no phase.** Never say "deformation" about a GCOV case (Langtang). Say "**surface disruption**".

---

## 4. Every number: source, and what to say if challenged

**Rule: say only numbers that are on screen at that moment.** The single source of truth is `data/headline_numbers.json`. When it exists, it wins over this table. It **did not exist yet** at 14:45, so the values below come from the files named.

| Number | Meaning | Source | If challenged |
|---|---|---|---|
| **Water IoU on unseen days** | Overlap of our radar water map with the Sentinel-2 photo, scored only on days the model never saw (leave-one-date-out, 8 photo days) | `data/ml/water_clean.json` → `summary`; `tools/ml_water_clean.py` | See the warning below. |
| Raw model IoU **0.63** | The same test, before speckle clean-up | `water_clean.json` `raw_iou` 0.627 | "Before clean-up it's 0.63. Clean-up only drops tiny blobs and uses no labels." |
| Recall **94 %** | It finds 94 % of the real water | `water_clean.json` `recall` 0.936 | Errors are mostly extra, not missed: wet mud. |
| Shuffled-label control **0.07** | The same model trained on scrambled answers | `docs/design-pack/text/key-numbers.json` 0.067 | "If it had learned noise, this would score high. It collapses." |
| ICESat-2 **Spearman 0.95, n = 9** | Laser water level vs our area, rank agreement | `key-numbers.json`; `tools/icesat2_levels.py` | "n = 9 is small. It's a sanity check from a second NASA satellite, not the main proof." |
| **42.1 → 21.1 km²** | Lake area 23 Jun → 19 Oct 2026, clear-day photos | handoff; Sentinel-2 | "That's the normal summer irrigation drawdown. The insight is the anomaly vs normal." |
| **19.5 km²** Dec forecast (13–26), typical **22.3** | Below-normal winter | `data/forecast/andijan_res_v2.json` | "30 days ahead the ML beats the best simple guess, 4.1 vs 4.7 km². At 3 months it ties, so beyond that we show the range." |
| **19.1 km²** always wet, **23.4** dried at least once | Water-frequency heatmap, 11 passes | `data/ml/water_freq.json` (`every_pass` 19.1; `most`+`few` = 23.4) | Built from the raw learned maps, one per pass. |
| **21.9 vs 4.8 km²** | Water over-count on drained mud, S1 vs NISAR, same week | handoff | Single comparison. Say "in our test", not "always". |
| **10.9 M** people, 29 % of Uzbekistan | Andijan, Fergana, Namangan regions | stat.uz, 1 Oct 2025 | |
| **15 of 24** | Winter Sentinel-2 photos lost to cloud, Dec–Mar 2025 | `key-numbers.json` | |
| **Langtang 0.9 km²** flagged vs **0.0–0.2** in quiet pairs | Slope disruption vs the false-alarm baseline | Playbook, from site | **VERIFY** against the v11 case file. |
| **Panama: 11.9 cm per fringe**, pair **2 Oct → 14 Oct 2026**, GUNW, ~100 cm LOS | Ground motion | handoff (`tools/gunw_read.py panama_m77`) | **VERIFY**: files not in this checkout. Read the motion off our own image, never guess. |
| **Data dates** | NISAR over Fergana from **18 Jun 2026**; global from **29 Oct 2025**; provisional before **21 Oct 2026**; gap **27 Jul–10 Aug 2026** | CMR query (master prompt 1.1–1.2) | "That's NASA's archive, not our choice." |
| **−81 %** Aral open water 1985 → 2026 | Landsat, in our box | KNOW-BEFORE-PITCH | Not NISAR. Say "Landsat". |

> **Warning: the water IoU number is changing today.**
> The old headline **0.78** used a 0.2 km² clean-up cut-off that was picked by looking at the same test days. That is test-set tuning (leakage), and an expert judge will catch it.
> `tools/ml_water_clean.py` is being re-run with a **nested** choice: for each test day, the cut-off is chosen on the other 7 days. At 14:45 the file read **nested IoU 0.796, area miss 2.48 km²**. That is uncommitted and may still change.
> **Say whatever `headline_numbers.json` says.** If asked "how did you pick the cut-off?": *"Without the day being scored. For each test day we chose it on the other seven days. With no clean-up at all it's 0.63, and we publish the full table."*

Also do NOT claim:
- The model works at other places. **Rogun IoU 0.02, Qosh Tepa 0.00, Sardoba 0.39.** Transfer is "next step".
- The old "30 % better forecast". Use v2: 4.1 vs 4.7 km², 13 % better at 30 days.
- "Predicts" fires or floods. We **map** change; we do not predict it.
- "Deformation" from GCOV.
- **GIBS colours.** The master prompt says GIBS tiles are R = B = HH, G = HV. In the tiles I sampled, R ≠ B (mean R 46, G 68, B 26). Say "NASA's colour composite; green = strong HV" and don't recite the channel mapping for GIBS. Our own false colour (Andijan) *is* R = HH, G = HV, B = HH/HV.

---

## 5. Architecture (data in → processing → web)

```
NISAR (L-band, 12 days) → JPL processing → L2 GCOV (calibrated, 20 m)
   → ASF DAAC (files) + NASA CMR (pass catalogue, any bbox)
   → NASA GIBS (global map tiles, ~15 m)
   → Falakus in the browser (MapLibre): pass finder, compare, time-lapse, change, hotspots → you

Our science path (Andijan, full files):
GCOV HDF5 (~2 GB/pass) → HH, HV to dB → Lee speckle filter (7×7) → terrain mask (Copernicus DEM, slope > 12°)
   → 10 features per pixel → HistGradientBoosting (water / not water)
   → validation: Sentinel-2 photos (leave-one-date-out), shuffled-label control, ICESat-2 ATL13 laser
   → images + JSON → the site
```

- **Global viewing runs in the browser.** Passes come straight from NASA CMR (CORS), and tiles straight from NASA GIBS. There's no server of ours in that path.
- **Measuring runs in Python** (numpy, scipy, scikit-learn, Pillow) on our machine. Its outputs are committed as images and JSON.
- **The 10 features:** filtered HH, HV, HH−HV; HH texture 5×5 and 11×11; HV texture 5×5; the pixel's season min / median / max HH; this pass minus the season median.
- **GIBS guard:** each tile is decoded and checked. Scrambled tiles are rejected, so the map shows the parent tile instead.
- Code: GitHub (public). Live: earth.instant.uz / falakai.uz. **VERIFY which URL is final.**

---

## 6. Honest limits (say these before a judge does)

- **Wet mud reads as water.** A drained shore is smooth and wet. This is our main error in late summer.
- **Speckle.** Single pixels are noisy. We filter, drop tiny blobs, and compare each pixel with its own history.
- **Mountains:** layover and shadow. We mask steep slopes. This is also why the model fails at Rogun (gorge).
- **GCOV has no phase**, so ground motion needs GUNW.
- **Young data.** Provisional before 21 Oct 2026. Fergana only from 18 Jun 2026.
- **GIBS scrambled tiles** at zoom 11–13. We detect and skip them. Mention it in Q&A as proof that we inspect the data.
- **Trained on one reservoir.** Transfer to new places is next.
- **Wind-roughened water** looks grey, not black (the 24 Sep pass).

---

## 7. Judge Q&A (answers ≤ 20 s)

| Question | Answer | Who |
|---|---|---|
| Is this real NISAR data? | "Yes. NASA's catalogue lists the exact passes over your view, and NASA GIBS serves the tiles. Every frame shows its date, track and direction." | Speaker |
| How do you know the water map is right? | "We scored it only on days it never saw, against Sentinel-2 photos: [IoU from headline file]. Scrambled labels score 0.07. A second NASA satellite, ICESat-2's laser, agrees: Spearman 0.95." | Science |
| How did you pick the clean-up cut-off? | "Without the day being scored: chosen on the other seven days each time. With no clean-up it's 0.63, and we publish the full table." | Science |
| n = 9 is tiny. | "Agreed. It's a sanity check, not the proof. The main test is the held-out photo score." | Science |
| Isn't −50 % just the irrigation cycle? | "Yes. That's why we compare against ten years of normal. This December is forecast at 19.5 km² against a typical 22.3. The anomaly is the insight." | Science |
| Why not Sentinel-1? | "C-band, 5.6 cm, stops at the leaves. NISAR's 24 cm reaches stems and soil: floods under canopy, coherence over forest. On drained mud, Sentinel-1 over-counted by 21.9 km², NISAR by 4.8." | Science |
| Why only 5 months over Uzbekistan? | "NASA has nothing public over Fergana before 18 June 2026. Globally NISAR starts in October 2025. Every new pass lands automatically." | Speaker |
| Can it detect earthquakes? | "From GCOV we map surface disruption. Centimetre motion needs the GUNW interferogram, as in Panama: one colour band is 11.9 cm." | Science |
| How did you get the Panama motion? | "A NISAR GUNW pair, [dates on screen], 12 days apart around the 9 October quake. Each fringe is half the 24 cm wave." **Fill in from the screen.** | Science |
| Does it work elsewhere? | "Viewing and change detection work anywhere NISAR flies. The water model is trained on Andijan only. At Rogun it fails, and we say so." | Speaker |
| Who would use it? | "The basin water agency planning winter releases, and responders sizing a disaster when no camera can see." | Speaker |
| What breaks? | "Wet mud, wind-roughened water, mountains, and NASA's tiles at high zoom are sometimes corrupt. We detect and skip those." | Science |
| Where did you use AI? | "Claude helped write code and short texts. Every number comes from our measured files, and the code is public." | Speaker |

If you don't know: *"Good question. Here's what we measured: …"* or *"We haven't tested that; it's next."* Never bluff.

---

## 8. 2-minute demo click path (DRAFT: finalise once the v11 UI lands)

| Time | Screen (Driver clicks) | Speaker says |
|---|---|---|
| 0:00–0:12 | Time-lapse → Aral, playing | "In 1986 this was the Aral Sea. *(pause)* It died because of how Central Asia manages its rivers. Those rivers start in the Fergana valley: ten point nine million people." |
| 0:12–0:30 | Case: Andijan → Camera vs radar, 24 Sep | "Water managers plan from satellite photos. Twenty-fourth of September: a hundred percent cloud. *(pause)* That's when cameras go blind." |
| 0:30–0:50 | Slide the camera off → radar | "NISAR sends its own 24-centimetre microwave. Calm water is a mirror: black. Leaves twist it: green. Cloud is invisible to it." |
| 0:50–1:12 | Andijan: play the passes, point at the chart and the validation badge | "Every twelve days, through cloud, we measure the reservoir. Tested on days it never saw: [IoU]. NASA's laser agrees. *(pause)* Against ten years of normal, this winter runs low." |
| 1:12–1:27 | Panama M7.7 (only if it loads) | "Ninth of October, magnitude 7.7. Two NISAR passes. Every rainbow band is twelve centimetres of ground motion." |
| 1:27–1:40 | Pass finder → any place → same-track compare | "And it works anywhere. Pick a place, NASA lists the passes, we compare the same track before and after." |
| 1:40–1:50 | Live hotspots globe, 3 s | "NASA tells you where. Falakus shows what changed." |
| 1:50–2:00 | Title | "Through cloud, smoke and night, every twelve days. *(2 s pause)* Thank you." |

**Fallback:** if Panama doesn't load, drop that row. Give Andijan +8 s and the pass finder +7 s.
**Rules:** one rehearsed path, all tabs pre-opened and pre-loaded, no typing on stage. Keep a 60 s backup recording on the desktop. Browser at 125 %, notifications off, hotspot ready. Move the cursor slowly and only to what the Speaker names.

---

## 9. Roles and delivery

| Role | Job |
|---|---|
| **Speaker** | Talks the whole time. Owns the story, impact and "who uses it". |
| **Driver** | Clicks the demo and says nothing. Switches to the backup video if anything lags more than 3 s. The Speaker keeps talking. |
| **Science** | Answers physics and validation in Q&A (section 7, "Science" rows). |
| **Timer + recovery** | Holds up 60 s and 30 s cards. Watches the clock. Calls the fallback. |

Delivery rules:
- **130 words/min.** Sentences of 15 words or fewer. Lower your pitch at the end of a sentence.
- **Pause 1 s** after every number and after "100 % cloud". Silence = confidence. No "uh", "so", "basically", "kind of", "we tried to", "hopefully".
- Open: plant your feet, look at the judges, 2 s of silence, then the first line. Don't open with team intros (they're on the slide).
- One sentence = one judge. Rotate eye contact. Look at the screen only to point.
- Open palms at waist height. Stand beside the screen, never in front of the projector. Move only at a section change.
- Physics word + plain word: "specular reflection: water acts as a mirror".
- End: last line, 2 s pause, "Thank you", stay still. Let the judge speak first.
- Rehearse **10 full timed runs**; the last 3 in front of someone new. Watch one recording muted.

---

## 10. Red flags (each one loses points)

1. Demoing anything that shows 0, a spinner or an error.
2. Two different numbers for the same thing. **Use only `headline_numbers.json`.**
3. "AI detects…" without saying how it was tested.
4. Overclaiming: "predicts", "detects earthquakes" from GCOV, "global water model".
5. Quoting 0.78 as the clean IoU (it was test-tuned). Quote the headline file.
6. Reading slides; more than 12 words on a slide.
7. Team intros in the first 20 s.
8. Ten features shallow instead of 2–3 deep.
9. Running over 2:00.
10. Arguing with a judge. Say "Good point. Here's what we measured."
11. NASA logos or mission patches anywhere.
12. Private or broken links. Test every link in incognito.
