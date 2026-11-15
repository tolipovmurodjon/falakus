# Prompt for Claude Design: rebuild the Falakus 7-slide deck (paste everything below the line)

Attach these images from the repo (real satellite data, ours):
- `docs/deck/img/change_map.jpg`: hero change map (NISAR radar, blue = still water, amber = water gone 14 Jul → 18 Oct 2026)
- `docs/deck/img/before_after.jpg`: NISAR HH radar, 14 Jul vs 18 Oct 2026, same box
- `docs/deck/img/cloudy.jpg`: the 24 Sep 2026 photo, fully cloud covered (if you want it on slide 2)
- Optional screenshots of our app: `intel.html`, `timelapse.html` (Aral 1985 → 2026), `explorer.html`

---

Make a 7-slide 16:9 presentation deck for a NASA Space Apps Challenge 2026 submission. It must be in English, with exactly 7 slides including the title. The judges have no background in radar and spend about 3 minutes on it. Give each slide one idea, put the big number first, keep words few, and use readable type: titles of 36 pt or more, body of 16 pt or more.

**Look.**
- Clean, editorial, calm: like a NASA Earth Observatory feature crossed with an Apple keynote.
- Background: warm off-white paper #F6F3ED. Ink: #14120D. One accent, deep teal #17515F. Water blue #2F6FD1, warning amber #EA8C14 (only for "water lost" and cloud).
- A grotesk sans for titles (Inter Tight, 800 weight) and a monospace for numbers.
- White cards with one soft shadow. Big real satellite images.
- No stock photos, no icons drawn as emoji, no NASA logos or NASA insignia, no people's photos.

**Slide 1 · Title**
- Falakus
- Tagline: "Water intelligence for Uzbekistan from NASA-ISRO NISAR radar: what changed, why, and what comes next, through cloud and at night."
- Team Falakus · Tashkent, Uzbekistan
- Members: [NAME 1], [NAME 2], [NAME 3], [NAME 4], [NAME 5], [NAME 6]
- Challenge: "Dancing with the SARs"
- Image: change_map.jpg, large on the right, captioned "Andijan reservoir, NISAR radar: amber = water released between 14 Jul and 18 Oct 2026."

**Slide 2 · Problem: "Without radar, the valley's water is planned half-blind"**
Three cards:
- **10.9 million** people in the Fergana valley's three regions (29 % of Uzbekistan) depend on reservoirs like Andijan on the Kara Darya, head of the Syr Darya.
- **15 of 24** winter photos lost to cloud. Sentinel-2, Dec–Mar 2025: the months when spring releases are planned.
- **Undetected:** how fast a reservoir is drawn down, when upstream canals take more water, when fields are harvested.

**Slide 3 · Solution**
- One sentence: "Falakus turns every 12-day NISAR radar pass into a checked water map and a plain-language briefing for water agencies, farmers and families."
- Hero image: change_map.jpg.
- A small quote card: "Clear-day photos show the lake fell from 42.1 to 21.1 km² (23 Jun → 19 Oct) as water went to the fields. Forecast: about 26 km² by February, close to a typical February (25.6 km²)."

**Slide 4 · How it works (pipeline diagram, 4 boxes with arrows)**
1. **NISAR GCOV, ASF DAAC:** calibrated HH and HV radar, 20 m, every 12 days. We read only our box from NASA's files.
2. **Preprocessing:** speckle filter, decibels, texture, each pixel's season history, and a terrain mask (Copernicus DEM) against radar shadow.
3. **Model:** gradient boosting on 10 radar features, labelled by clear-day Sentinel-2 photos, tested on days it never saw.
4. **Output:** water map per pass, change map, 3-month forecast, plain-language briefing.

Small line under it: "Outside checks: Sentinel-2 photos, NASA ICESat-2 laser levels, Sentinel-1 C-band radar."

**Slide 5 · Results: "NISAR sees the release, and two independent checks agree"**
- Image: before_after.jpg (NISAR HH, 14 Jul | 18 Oct 2026; calm water is black).
- Metric 1: **IoU 0.63**. The learned water map vs clear-day photos on 8 days it never saw. Classic one-threshold rule: 0.59. Shuffled-label control: 0.07.
- Metric 2: **ρ = 0.95**. NASA ICESat-2 laser water level vs lake area, 9 passes: a second satellite and different physics show the same rise and fall.

**Slide 6 · NASA & partner data: exactly what we used, and for what (table)**

| Dataset | How we used it |
|---|---|
| NISAR L2 GCOV (NASA-ISRO, ASF DAAC) | core radar, HH/HV every 12 days: water, crops, change |
| NISAR L2 GUNW | ground motion from radar phase |
| ICESat-2 ATL13 (NASA) | laser water levels: independent check |
| NASA EONET + GIBS | floods, fires, storms, IMERG rain for context |
| Sentinel-2 L2A (ESA) | photo water labels; 10-year monthly record |
| Sentinel-1 RTC (ESA) | C-band vs L-band comparison |
| Copernicus DEM, ESA WorldCover | terrain mask; cropland and water zones |
| Landsat 5–9 (USGS), RADARSAT-1 (CSA) | 1985–2025 time-lapse; 1997 Aral radar |
| Statistics Agency of Uzbekistan | population depending on the water |

**Slide 7 · Impact & next steps**
Who uses it:
- **Basin water agencies:** reservoir area every 12 days through cloud.
- **Farmers:** a plain briefing on how full the lake is and what spring water to expect.
- **Families and teachers:** 10.9 million people can see where their water goes.

Next:
1. Every reservoir and canal on the Amu Darya and Syr Darya, including the Qosh Tepa canal.
2. Volume: area × ICESat-2 levels.
3. ALOS 2008 → NISAR 2026: 18 years of L-band radar.
4. NISAR soil moisture and ground motion.

Footer: "Open source, MIT · github.com/tolipovmurodjon/falakus · AI use: Claude helped write code and text; the team checked every number. No AI-generated images."

Rules: do not invent or round numbers differently; keep every number exactly as written above. Keep each slide readable in 10 seconds.
