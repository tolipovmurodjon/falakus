# falakus — NASA Space Apps 2026, "Dancing with the SARs"

Team of 4 in Uzbekistan. Build an open-source interactive app that uses NISAR radar data to show how places change over time and why.

## Hard facts
- Submission closes **Sun 15 Nov 2026, 23:59 local time**. Demo = video ≤ 30 s or ≤ 7 slides, English, public link. Final project link must be public, no login.
- Judging, 1-5 each: Impact, Creativity, Validity, Relevance (NASA data must be core), Presentation.
- AI use must be disclosed on the project page: AI images carry a visible watermark, AI code/data is named in text. No NASA logos in generated content.

## What the challenge asks (the spec; every feature maps to a line here)
Must:
1. An interactive application using NISAR radar data.
2. Track and visualize one or more types of surface change (wetlands, floods, forest loss, fire, crops, soil moisture, glaciers, sea ice, earthquakes, subsidence).
3. At locations around the world, at different time steps.
4. Translate radar into actionable insight for scientists, resource managers, educators, decision-makers, the public.
5. Open-source and user-friendly.
6. Pick a study area, download NISAR data from the listed resources, present it in an interactive medium.
7. Hypothesize the physical drivers behind what you see (or don't see).
8. Say which polarizations highlight the changes, and what future NISAR applications are possible.
Encouraged: interactive change-detection maps · time-series animations · dashboards · different polarizations and frequencies (other sensors) · several dates as a time series · ancillary data (population, vegetation type) · optical images or GIS layers for context · human drivers (agriculture, industry) · storytelling · personal hometown context · image sliders and web maps.
Judging (1-5 each): Impact · Creativity · Validity · Relevance (NASA data as the core) · Presentation.

## Data (checked live 14 Nov 2026 via NASA CMR)
- NISAR L-band public since 20 Jul 2026, passes from 17 Jun 2026. Most products **provisional** (public beta); first **validated** GCOV from 21 Oct 2026.
- Main product `NISAR_L2_GCOV_PROVISIONAL_V1` (163,672 files, 0.5-5.7 GB each, 10-20 m pixels, HDF5 `/science/LSAR/GCOV/grids/frequencyA/HHHH`, `HVHV`). Others: GUNW (motion, 80 m), GOFF (offsets), L3 SME2 (soil moisture), UR_L2 (urgent response).
- Browse PNGs (HH, HV, colour) download **without login** from the `BROWSE` links in CMR granule metadata. Full `.h5` needs Earthdata Login.
- Time series rule: one track + frame + direction (A/D) per series. Check the QA report; drop partial/striped frames. HV over dry ground shows the noise floor, not plants.

## Story (team decision pending)
"Where did Central Asia's water go this summer?" Globe door (passes + urgent-response hotspots) → Rogun → Qosh Tepa → Fergana fields → Aral. Rogun feeds the Amu Darya (Uzbekistan, Turkmenistan), not Pakistan.

## Layout
- `tools/fetch_browse.py` — find granules over points via CMR, download browse PNGs.
- `tools/build_deck.py` — inline images, font and world outline into the deck.
- `docs/deck/deck.src.html` → `docs/deck/nisar-field-guide.html` (team brief, Eye Run style). Check with `python D:\30_library\taste\templates\slides-eye-run\render.py <deck>`.
