# Data tour — what NISAR data really looks like, and how it becomes Falakus

Everything here was pulled live or measured from our own files on 15 Nov 2026. Read it top to bottom once and you
can answer "how?" questions from any judge.

---

## 1. One NISAR pass, from space to your screen
```
NISAR satellite (L-band radar, 24 cm)
   │  records echoes of its own microwave pulse, day or night, through cloud
   ▼
JPL processing → L2 GCOV product (one HDF5 file per frame, ~2 GB)
   │
   ▼
ASF DAAC (NASA's SAR archive) — stores the files
   │
   ├─► NASA CMR — the catalogue: "which passes cover this box?"   ← Falakus asks this for any place
   ├─► browse PNGs (quick-looks, public, no login)                ← our world mosaic (16,691 frames)
   ├─► NASA GIBS — the same data as ~15 m map tiles per date       ← Falakus' sharp zoom
   └─► the full HDF5 (Earthdata login)                             ← our measured numbers (Andijan)
```

## 2. A real catalogue record (NASA CMR, live)
Query: newest NISAR GCOV pass over the Andijan box (72.9–73.3 E, 40.6–40.9 N). **40 passes** found.

| Field | Value | What it means |
|---|---|---|
| GranuleUR | `NISAR_L2_PR_GCOV_033_092_D_068_2005_DHDH_A_20261018T140944_…` | The file's unique name (decoded below) |
| Time | 2026-10-18 14:09:44 → 14:10:19 UTC | 35 seconds of flight per frame |
| ASCENDING_DESCENDING | DESCENDING | Flying south (descending) |
| TRACK_NUMBER | 92 | Which orbit track; compare only the same track |
| FRAME_NUMBER | 68 | Which slice of that track |
| FREQUENCY_A_POLARIZATION | HH, HV | Two polarizations recorded |
| FREQUENCY_A / B bandwidth | 20 MHz / 5 MHz | Band A is the sharper one (we use A) |
| PRODUCT_TYPE | GCOV, "Geocoded Polarimetric Covariance" | Calibrated echo strength on a map grid |
| PROCESSING_CENTER | JPL | Made by NASA JPL |
| PRODUCT_VERSION | 1.0.11 | Provisional data (validated from 21 Oct 2026) |

**Filename anatomy:** `NISAR_L2_PR_GCOV_033_092_D_068_2005_DHDH_A_20261018T140944_20261018T141019_P05023_N_F_J_001`
- `L2` level 2 · `PR` provisional pipeline · `GCOV` product
- `033` cycle (each cycle is 12 days) · `092` track · `D` descending · `068` frame
- `2005` radar mode · `DHDH` dual polarization (HH + HV) · start / end time · processing version

**Files attached to each record:** the `.h5` (data), `…_NATIVE_A_HHHH.png` and `…_A_HVHV.png` (quick-looks),
`…_LATLON.png` (map-projected quick-look) and a thumbnail.
Real example: `docs/data-tour/browse_HHHH.png` (1948 × 1920 px, greyscale; one frame is about 240 km wide).

## 3. Inside the HDF5 file (what our code reads)
```
/science/LSAR/GCOV/grids/frequencyA/HHHH   ← echo power, horizontal send / horizontal receive (linear γ⁰)
/science/LSAR/GCOV/grids/frequencyA/HVHV   ← echo power, horizontal send / vertical receive
```
`tools/gcov_science.py` reads **only our box** over HTTPS (earthaccess + h5py range reads) instead of the whole
2 GB file. It converts each value to decibels (dB = 10·log₁₀ γ⁰) and saves 16-bit dB as `.npz`.

## 4. What the numbers look like (real pixels, Andijan, 30 Oct 2026, 15×15-pixel patches)
| Surface | HH | HV | HH − HV | Why |
|---|---|---|---|---|
| Calm water | **−21.4 dB** | −23.8 dB | 2.6 | Mirror bounce: almost nothing returns |
| Plants / fields | −6.2 dB | **−11.2 dB** | 5.1 | Leaves scatter the wave sideways: HV is strong |
| Town / rough ground | **+0.9 dB** | −13.2 dB | 14.2 | Double bounce off walls: very bright HH |

Rule of thumb: **HH below about −17 dB means water**; our first rule used −16.75 dB. The learned model goes
further: it combines 10 features (texture, HH − HV, each pixel's season history).

## 5. From file to dashboard (our pipeline, each step is a script)
| Step | Script | Output | Shown in the app as |
|---|---|---|---|
| 1. Read the box from each pass | `gcov_science.py` | `science/<place>/<date>.npz` (dB) | — |
| 2. Render images | `science_render.py` | `img/<date>_hh/hv/rgb/change.webp` | Radar, Colour, Change filters |
| 3. Learn water | `ml_water.py` | `water_pred_<date>.png`, `water_model.json` | Water (AI) |
| 4. Clean speckle (nested) | `ml_water_clean.py` | `water_clean_<date>.png`, score 0.80 | Water map + score |
| 5. How often wet | `water_frequency.py` | `water_freq.png` (19.1 km² always wet) | Heatmap |
| 6. Forecast | `forecast_v2.py` | `andijan_res_v2.json` | Chart band, Dec 19.5 km² |
| 7. Laser check | `icesat2_levels.py` | `andijan_res_icesat2.json` (ρ 0.95) | Validation card |
| 8. World mosaic | `nisar_tile_server.py` | tiles from 16,691 browse frames | Live Earth globe |
| 9. Any place, sharp | browser → CMR + GIBS | live | Pass list, compare, time-lapse |

## 6. The 11 passes as a table (Andijan reservoir)
| NISAR pass | Radar raw km² | Radar cleaned km² | Clear photo (date) km² |
|---|---|---|---|
| 20 Jun | 43.2 | 39.2 | 42.1 (23 Jun) |
| 2 Jul | 44.9 | 39.4 | — |
| 14 Jul | 45.1 | 38.5 | 40.2 (11 Jul) |
| 26 Jul | 42.2 | 35.0 | 32.0 (26 Jul) |
| 19 Aug | 30.3 | 21.9 | 20.1 (20 Aug) |
| 31 Aug | 28.5 | 19.8 | 19.0 (30 Aug) |
| 12 Sep | 29.7 | 20.5 | 18.8 (9 Sep) |
| 24 Sep | 24.7 | 19.5 | — (100 % cloud) |
| 6 Oct | 26.5 | 19.4 | 17.0 (4 Oct) |
| 18 Oct | 28.5 | 19.8 | 21.1 (19 Oct) |
| 30 Oct | 32.3 | 20.1 | — |

Read it like a judge would:
- The cleaned radar tracks the photos within about 2–3 km² once the speckle is removed.
- On 24 Sep the camera saw only cloud, and radar still measured the lake.
- **Caution:** the cleaned map uses the cut-off chosen on all 8 photo days (2 km²); the *score* 0.80 is nested.

## 7. GIBS tiles: what a judge sees when zooming
- **Real, measured:** about a third of NASA GIBS NISAR tiles at zoom 10–13 come back scrambled.
- **The finding:** the corruption is **random per request**. The same tile fetched 4 times gave ok / ok / scrambled / ok.
- **Our fix:** detect it (random transparency or grey static), retry the same tile, keep only clean copies, then cache them. That is why the zoom stays sharp.
- **How to say it to judges:** "We found a NASA-side data bug, and we handle it."

## 8. "Any place, any time?" — what each dataset can really cover
Checked live in NASA GIBS GetCapabilities and CMR (15 Nov 2026):

| Era | Dataset | Coverage | Any place? | In Falakus |
|---|---|---|---|---|
| 1985 → today | Landsat 5–9 (USGS), optical | global, every 16 days, summers cloud-free composite | yes, but **pre-baked per place** (Planetary Computer) | Time-lapse (Aral, Andijan, Tashkent) |
| 1995 → 2013 | RADARSAT-1 (CSA), C-band radar | **not systematic**: scenes only where ordered | only where scenes exist | "Radar to radar, 29 years" |
| 2000 → today | MODIS Terra (NASA), optical, ~250 m | global, daily | yes, instantly (GIBS) | Camera vs Radar |
| 2013 → today | HLS Landsat/Sentinel-2 (NASA), optical 30 m | global | yes, instantly (GIBS) | Optical comparison |
| 2014 → today | Sentinel-1 (ESA), C-band radar | global, 6–12 days; in GIBS from 10 Jan 2025 | yes, instantly (GIBS) | Sentinel-1 layer, time-lapse option |
| 29 Oct 2025 → today | **NISAR (NASA-ISRO), L-band radar** | global, 12 days (GIBS gap 27 Jul–10 Aug 2026; Fergana only from 18 Jun 2026) | **yes, instantly** (CMR + GIBS) | Core: passes, compare, time-lapse, cases |

So the honest answer to "any place, any time":
- **Any place, from late 2025 on:** yes, in NISAR radar.
- **Any place, from 2025 back to 2013/2000:** yes, with Sentinel-1 radar and optical layers.
- **Before that:** radar only where RADARSAT-1 happened to image a place; Landsat optical for everywhere, baked per place.

## 9. Why so many datasets — and why we keep them SEPARATE
We never blend them into one picture or one number. Each one has a **job**. Mixing sensors would mix their physics:
C-band and L-band see different things, and a camera sees colour, not echoes.

| Job | Dataset | Why it must stay separate |
|---|---|---|
| **The signal** we measure change with | NISAR L-band | It's the challenge's core; every Falakus number about change starts here |
| **The answer key** to train and test the model | Sentinel-2 / Landsat clear photos | Only used on clear days; a test must come from a different instrument than the one tested |
| **The independent judge** | ICESat-2 laser, OPERA DSWx / DIST-ALERT | They come from a different physics or a different team, so agreement means something |
| **The history** before NISAR existed | Sentinel-1 (2014→), RADARSAT-1 (1990s), Landsat (1985→) | Labelled by satellite on screen; comparing eras is "then vs now", never one series |
| **The frequency comparison** the challenge asks for | Sentinel-1 C-band vs NISAR L-band | Shown side by side to *show* the difference (C-band stops at leaves; L-band reaches the ground) |
| **The context** for where to look | USGS quakes, NASA EONET, FIRMS fires, population | They say *where* something happened; radar says *what changed* |

**One sentence for judges:** "Every dataset has one job. NISAR measures, photos grade it, the laser and OPERA
double-check it, and older satellites give the history, always labelled, never blended."

## 10. Audit: "Why does our data start in June 2026, not October 2025?" (CMR, measured 15 Nov 2026)
| Place | First public NISAR GCOV pass | Oct 2025–Jan 2026 | Feb–May 2026 | Jun–Nov 2026 |
|---|---|---|---|---|
| California | 1 Nov 2025 | 28 | 38 | 50 |
| India (Delhi) | 17 Nov 2025 | 18 | 28 | 46 |
| Nepal (Langtang) | 28 Nov 2025 | 6 | 10 | 31 |
| Andijan | 18 Jun 2026 | 0 | 0 | 45 |
| Tashkent | 20 Jun 2026 | 0 | 0 | 63 |
| Amazon (Rondônia) | 18 Jun 2026 | 0 | 0 | 55 |
| Panama | 16 Jun 2026 | 0 | 0 | 76 |
| Netherlands | 19 Jun 2026 | 0 | 0 | 40 |

**Reason:** NASA's public archive. Before mid-June 2026 it covers only some regions (the US, India, Nepal); from
mid-June 2026 it covers the whole land surface. It isn't our code.
**Fix in Falakus:** for any period before NISAR data exists at a place, the time-lapse fills in Sentinel-1 radar
(GIBS from Jan 2025), shown as a separate, labelled segment ("NISAR public data here starts <date>").
**Say it:** "NASA's archive opens region by region; it went global in June 2026. Before that we show Sentinel-1, clearly labelled."
