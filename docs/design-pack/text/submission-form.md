# Space Apps submission form: ready to paste (Falakus, "Dancing with the SARs")

All numbers are measured by our scripts (see `docs/state/handoff.md`). Do not change a number without rerunning its tool.

---

## Project Name
Falakus

## Summary (paste; 178 words, under 1,500 characters)
Falakus is a water-intelligence web app for Uzbekistan built on NASA-ISRO NISAR radar. The Fergana valley's 10.9 million people depend on reservoirs that camera satellites often cannot see. In winter, when spring water releases are planned, 15 of 24 Sentinel-2 photos of the Andijan reservoir were mostly cloud. NISAR's L-band radar sees through cloud and at night, every 12 days.

We read calibrated NISAR GCOV radar (HH and HV) straight from NASA's files. A gradient-boosting model learns what open water looks like to the radar, using clear-day photos as labels. It then maps the water on every pass. Tested on days it never saw, it beats the classic single-threshold method (map overlap 0.63 vs 0.59), and a shuffled-label control collapses (0.07). A second NASA satellite, the ICESat-2 laser, independently agrees: water level and lake area rise and fall together (rank correlation 0.95).

Falakus turns these numbers into plain-language briefings: what happened, why, and what comes next. There is a version for the water agency, for farmers and for families, plus a change map, a time series and a forecast.

## Project Demonstration (link)
The 7-slide deck: `docs/deck/falakus-7.html`, built by `tools/build_deck7.py`.
- Open it in Chrome, print to PDF (landscape, no margins), upload to Google Drive, and set "Anyone with the link: Viewer".
- Paste the full https link. Check it in a private window: it must open with no login.
- Before exporting, put the team name and the 6 member names in `TEAM` in `tools/build_deck7.py`, then rebuild.

## Project (link)
https://github.com/tolipovmurodjon/falakus (public, MIT). When the site is live, put **https://earth.instant.uz** first.

## Project Details (paste)
**What it does.** Falakus watches the water that Uzbekistan lives on, using NASA-ISRO NISAR radar, and explains each change in plain words. For each water body it shows:
- a map of open water on every NISAR pass, with a play button;
- a change map: water still there, and water that is gone;
- a briefing: what happened, why, and what comes next, with tabs for the water agency, farmers and families;
- how sure we are, with the outside check next to every number.

A time-lapse shows the Aral Sea and the Fergana valley's reservoir from 1985 to 2026. An explorer adds NASA's rain, fire, flood and storm layers worldwide.

**How it works.**
1. Data: calibrated NISAR L2 GCOV radar (HH and HV, 20 m, every 12 days) from NASA's ASF DAAC. We read only our box from each HDF5 file over HTTPS, not the 2 GB files.
2. Preprocessing: Lee speckle filter, decibels, local texture, and each pixel's season history (minimum, median, maximum). Ground steeper than 12° is masked with the Copernicus 30 m elevation model, because radar shadow on slopes looks like water.
3. Model: a gradient-boosting classifier (scikit-learn) on 10 radar features per pixel. The labels are Sentinel-2 photo water (NDWI) on clear days.
4. Testing: each photo day is scored by a model trained only on the other days (leave-one-date-out), with a shuffled-label control.
5. Outputs: water area per pass, a change map, a 3-month forecast, and the briefing text. Every number in a sentence is filled in by code from the measured files.

**Results, Andijan reservoir (Kara Darya, head of the Syr Darya), 2026.**
- Map overlap with clear-day photos the model never saw: IoU 0.63. Single-threshold rule: 0.59 with a water map, 0.30 without. Shuffled labels: 0.07. Typical area miss: 7.6 km².
- Clear-day photos show the lake fell from 42.1 to 21.1 km² (23 Jun → 19 Oct) as water was released for cotton and wheat. NISAR saw it on every pass, including the cloudy days.
- An independent check from a second NASA satellite: ICESat-2 laser water level vs lake area, Spearman ρ = 0.95 (n = 9).
- Polarization: HH shows water (calm water is a mirror for the radar). HV shows crops, because leaves and stems turn the pulse; 12.8 % of a Fergana field box lost its plant echo between July and October, mostly harvest. At the Aral, HH alone mistakes wet salt crust for water; requiring both HH and HV to be dark removes it.
- L-band vs C-band: same week in October, over the drained reservoir, Sentinel-1 C-band over-counted water by 21.9 km², NISAR L-band by 4.8 km².

**Where it is wrong (we show it).**
- In late summer the radar counts wet mud on the drying shore as water. The error maps on screen show this.
- A model trained at Andijan did not transfer to the Rogun gorge in the mountains. We say so and do not show Rogun numbers as fact.
- NISAR data before 21 Oct 2026 is provisional.

**Benefits and impact.**
- Basin water agencies get the reservoir's area every 12 days, through cloud, for winter and spring release plans.
- Farmers get a plain briefing on how full the lake is and what spring water to expect.
- The 10.9 million people in the valley's three regions (Andijan, Fergana, Namangan; 29 % of Uzbekistan) can see where their water goes.
- The same pipeline runs on any NISAR box. Next steps:
  - every big reservoir and canal on the Amu Darya and Syr Darya, including the Qosh Tepa canal upstream;
  - volume from area × ICESat-2 levels;
  - ALOS (2008) to NISAR (2026): 18 years of L-band radar.

**Tools.** Python (numpy, scipy, scikit-learn, h5py, earthaccess, Pillow), NASA CMR and Earthdata, Microsoft Planetary Computer STAC, JavaScript + MapLibre GL, HTML/CSS. Open source, MIT licence: every number can be rerun from `tools/`.

**What makes it creative.**
- Radar against radar across 29 years (Canada's RADARSAT-1 in 1997, NISAR in 2026).
- Two different satellites (radar and laser) checking each other.
- Every number shown next to its outside check and its failure case.
- Plain-language briefings in place of charts.

**Factors we considered.**
- Cost: only free and open data, and it runs on a laptop.
- Access: the briefings are in plain language and work on a phone.
- Honesty: provisional data is labelled, and failures are shown.

## Use of Super Intelligence (select)
Tick: **Code**, **Text/writing**. Do NOT tick images, video or audio (none generated).
Disclosure text, already on the project page and in the deck footer: "AI (Anthropic Claude) helped write code and draft text. The team ran, tested and fact-checked everything. No AI-generated images, video or audio; all imagery is real satellite data. No NASA logos."

## NASA Data (Link Text → Link Url)
| Link Text | Link Url |
|---|---|
| NISAR L2 GCOV radar (NASA-ISRO, ASF DAAC) | https://asf.alaska.edu/datasets/daac/nisar/ |
| NISAR L2 GUNW interferograms (ground motion) | https://asf.alaska.edu/datasets/daac/nisar/ |
| NASA Earthdata Search / CMR (granule search) | https://search.earthdata.nasa.gov/ |
| ICESat-2 ATL13 inland water surface height | https://nsidc.org/data/atl13 |
| NASA EONET natural events | https://eonet.gsfc.nasa.gov/ |
| NASA GIBS imagery (MODIS, VIIRS, GPM IMERG, SMAP) | https://nasa-gibs.github.io/gibs-api-docs/ |
| earthaccess (NASA Earthdata Python library) | https://github.com/nsidc/earthaccess |

## Space Agency Partner & Other Data (Link Text → Link Url)
| Link Text | Link Url |
|---|---|
| ESA Sentinel-2 L2A (photo water labels, 10-year record) | https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a |
| ESA Sentinel-1 RTC (C-band radar comparison) | https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc |
| ESA WorldCover 2021 (cropland and water zones) | https://esa-worldcover.org/ |
| Copernicus DEM GLO-30 (terrain mask) | https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-30 |
| USGS Landsat Collection 2 L2 (1985–2025 time-lapse) | https://planetarycomputer.microsoft.com/dataset/landsat-c2-l2 |
| CSA RADARSAT-1 open data (Aral 1997 radar) | https://www.asc-csa.gc.ca/eng/open-data/access-the-data.asp |
| ICEYE open data (0.5 m radar check) | https://www.iceye.com/sar-data/opendata |
| JRC Global Surface Water | https://global-surface-water.appspot.com/ |
| Microsoft Planetary Computer (STAC + data API) | https://planetarycomputer.microsoft.com/ |
| Statistics Agency of Uzbekistan, population 1 Oct 2025 | https://stat.uz/en/press-center/news-of-committee/62565-hududlar-kesimida-doimiy-aholi-soni-pp-3 |
| MapLibre GL JS (web map) | https://maplibre.org/ |
| Esri World Imagery (base map tiles) | https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9 |
| scikit-learn (model) | https://scikit-learn.org/ |
| Anthropic Claude (code and text help, disclosed) | https://www.anthropic.com/claude |
| Falakus source code (MIT) | https://github.com/tolipovmurodjon/falakus |

## Last steps
1. Tick both boxes (terms; original work).
2. Save Progress.
3. Open every link in a private window: none may ask for a login.
4. Submit for Judging before 23:59 Tashkent time.
