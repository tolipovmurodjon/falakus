# Falakus: where the Fergana valley's water goes, seen by NASA-ISRO NISAR radar

**Challenge:** Dancing with the SARs (NASA Space Apps 2026) · **Team:** 4, Tashkent, Uzbekistan
**Demo:** 30 s video `docs/video/falakus-30s.mp4` · 7-slide deck `docs/deck/story.html` · app (link added at submission)

## The problem
The Fergana valley, Uzbekistan's most crowded region, drinks from one reservoir on the Kara Darya: Andijan.
Water managers plan its release in winter and spring, exactly when camera satellites lose sight of it.
In 2025, 29 of 85 Sentinel-2 visits to the reservoir (34 %) were mostly cloud, and 15 of 24 in December to March.

## What Falakus does
One screen, three chapters, following the water. Every number is measured by our scripts and shown next to its outside check.

1. **Source: the Andijan reservoir.** NISAR measured its open water falling from **50.5 km² (14 Jul)** to **19.3 km² (6 Oct)** as it was released for cotton. Cloud-free Sentinel-2 photos show the same fall (r = 0.83). On **24 Sep 2026 the photo was 100 % cloud; NISAR still saw the whole lake.** A small ML model forecasts the next 3 months (Dec–Feb: about 23 → 29 km², 80 % band ±3.5–6 km²).
2. **Use: the Fergana fields.** NISAR's HV echo (the pulse turned sideways by leaves and stems) shows the season field by field: between 2 Jul and 30 Oct, **12.8 %** of a 30 × 30 km box lost its plant echo (mostly harvest) and 9.4 % gained it.
3. **End of the line: the Aral Sea.** The valley's Syr Darya ends in the North Aral; the Amu Darya fed the South Aral. In a 40 × 40 km box of the South Aral's eastern basin, all **1,598 km²** were sea in summer 1997 (Landsat-5); in 2026 at most **1.1 km²** is water (Sentinel-2). Canada's 1997 RADARSAT-1 radar sits next to NISAR in a drag-to-compare slider.

Behind **Explore the world**: a world map of 16,691 NISAR frames, compare-anywhere (any two layers, any place), NASA EONET flood watch, the Langtang landslide under cloud, Panama quake fringes with a control pair, ships and oil-slick candidates.

## Why radar sees it
NISAR sends its own 24 cm L-band pulse, so cloud and night do not stop it.
- **HH** (sent flat, back flat): calm water is a mirror and goes black; rough ground and walls come back bright.
- **HV** (sent flat, back turned): only leaves, stems and branches turn the pulse, so HV rises as crops grow and falls at harvest.
- In autumn, C-band Sentinel-1 counts drained wet mud as water far more than L-band NISAR does (same week, Oct 2026: +21.9 km² vs +4.8 km² over the photo).

## How we know it is right
| claim | outside check | result |
|---|---|---|
| Reservoir water area | Sentinel-2 photo water (NDWI) on clear days | r = 0.83 over 8 passes; radar over-counts 8.6 km² on average in late summer (wet mud) |
| The water rule is not tuned to the answer | cut-off learned on ONE pass, tested on 7 it never saw | map overlap IoU 0.49–0.71, median 0.58 |
| More looks | all NISAR orbits crossing the lake (mixed viewing angles, a check only) | 42 looks in 4.5 months, r = 0.82 against 30 photo days |
| Forecast | every 2026 month, never seen in training | miss 2.3 km² vs 3.3 (same month last year) and 4.3 (last month): 30 % better |
| Crop signal | Sentinel-2 NDVI on the same cropland | r = 0.58 over 11 passes |
| Ship detector (Explore) | ICEYE 0.5 m radar, Bosphorus | 5 of 12 dots on visible ships |
| Where it fails, shown | Aral salt crust, Fergana canals, flood points | salt is as smooth as water; canals are narrower than a 20 m pixel; most EONET flood points show no new water |

## Data used
NASA (core): **NISAR L2 GCOV** (provisional and validated, ASF DAAC via CMR and Earthdata Cloud; calibrated gamma0 HH and HV read straight from the HDF5), NISAR GUNW (quake fringes), NASA EONET events, NASA ICESat-2 ATL13 (independent laser water levels, in progress).
Other open data: ESA Sentinel-1 RTC and Sentinel-2 L2A, ESA WorldCover, JRC Global Surface Water, USGS Landsat-5 (via Microsoft Planetary Computer); CSA RADARSAT-1 open archive; ICEYE open data (CC BY 4.0); USGS earthquakes.

## Methods
Lee speckle filter (7 × 7) · water = HH below a cut-off learned on one pass and tested on the rest · only inside the lake basin (WorldCover water + 1 km), which keeps hill shadows out · radar vegetation index RVI = 4·HV/(HH+HV) · HV change maps at 100 m · one orbit track per time series · ridge-regression forecast tested walk-forward against two baselines · tools in `tools/` reproduce every number.

## Honest limits
- NISAR data before 21 Oct 2026 is provisional (public beta); there is a permanent gap 27 Jul – 10 Aug 2026; over the valley the calibrated record starts 18 Jun 2026.
- Wind roughens the lake and lowers the radar's water count (24 Sep); wet mud raises it (late summer).
- "Lost plant echo" is mostly harvest, but drying soil or stopped watering also lower HV.
- The forecast learns from only 2 years.

## Use of AI (disclosure)
- **Code:** AI (Anthropic Claude) helped write the data tools, the server and the web page. The team reviewed, ran and tested them.
- **Text:** AI helped draft the chapter texts, this page and the deck. Every number comes from our scripts; the team checked facts against NASA, ESA, USGS and CSA sources.
- **Images and video:** no AI-generated images. All imagery is real satellite data; the video is made from screenshots of the app. No NASA logos.

## Open source
MIT licence. Repository link added at submission.
