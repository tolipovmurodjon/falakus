# Falakus v11 — deeper, not bigger

For each role: (1) what a top professional would do that we did not ask for, (2) the rawest material they would
start from, (3) their methods and tools, (4) what — other than us — proves the result is right.

---

## Role 1 · Radar scientist (the change detection)

1. **What a pro would add**
   - Measure only on **calibrated γ⁰**, never on display PNGs.
   - Compare **same track, same look direction, same incidence**.
   - Separate the **seasonal cycle from the anomaly**.
   - Attach an **uncertainty** to every change area.
   - Read NASA's own **layover/shadow mask** and the **number of looks** before trusting a pixel.
2. **Rawest material**
   - The NISAR **L2 GCOV HDF5** itself: `HHHH`, `HVHV` covariance terms, `rtcGammaToSigmaFactor`, `layoverShadowMask`, `numberOfLooks`, incidence angle.
   - For motion, **GUNW** (unwrapped phase + coherence); for damage, **GSLC** to form coherence.
   - Not GIBS tiles and not ASF browse images. Those are pictures.
3. **Methods and tools**
   - Read the files with `earthaccess` + `h5py`/`xarray`; geometry with `rasterio`.
   - Multi-temporal (Quegan) speckle filter.
   - **Log-ratio** change with a threshold from each pixel's own quiet-pair variability (our "4× normal wobble").
   - The **omnibus Wishart test** (Conradsen et al.) for polarimetric change.
   - Coherence loss for damage; GUNW + MintPy for cm motion; CFAR for bright targets.
4. **Independent proof**
   - **NASA OPERA DSWx-S1/HLS** for water, **OPERA DIST-ALERT** for vegetation loss.
   - **USGS ShakeMap** and landslide inventories for quakes.
   - **ICESat-2 / SWOT** water heights.
   - Sentinel-2 clear photos, and news or field reports.

## Role 2 · ML engineer (the water model)

1. **What a pro would add**
   - **Nested** choice of every threshold (done: the cut-off is now nested).
   - **Spatial-block** cross-validation, because neighbouring pixels leak.
   - **Bootstrap confidence intervals** over dates.
   - Baselines a reviewer expects: Otsu threshold, and OPERA DSWx as an off-the-shelf product.
   - **Error analysis** by class: wet mud, wind-roughened water, shadow.
2. **Rawest material**
   - γ⁰ in dB on the native 20 m grid.
   - Labels from Sentinel-2 **SCL + NDWI**, not a pre-made water map.
   - The per-date error maps.
3. **Methods and tools**
   - scikit-learn `GroupKFold` (groups = dates and spatial blocks), `HistGradientBoosting`.
   - Permutation importance.
   - `scipy.stats.bootstrap`.
   - A confusion matrix per surface type.
4. **Independent proof**
   - Agreement with **OPERA DSWx-S1**, a NASA product we did not train on.
   - ICESat-2 heights.
   - A held-out **second reservoir**, honestly reported even when it fails (Sardoba 0.39, Rogun 0.02).

## Role 3 · Geospatial web engineer (the platform)

1. **What a pro would add**
   - **Performance budgets**: first paint under 2 s, tile from cache under 300 ms.
   - **Offline demo cache** (Service Worker / Cache API) for the 5–10 demo places.
   - Automated **end-to-end tests** on every change.
   - **Observability**: a tile-error counter.
   - Graceful fallbacks, so the screen never goes blank.
2. **Rawest material**
   - **GIBS WMTS GetCapabilities** for layer ids, dates and max zoom, not hard-coded URLs.
   - **CMR UMM-G** granule metadata: track, direction, footprint polygon, time.
   - The actual tile bytes, to detect scrambled tiles.
3. **Methods and tools**
   - MapLibre GL (self-hosted).
   - Playwright/CDP checks, Lighthouse.
   - PMTiles or a titiler on COGs for true 20 m.
   - CDN with immutable cache.
4. **Independent proof**
   - Lighthouse scores.
   - A **cold start on a phone over a different network**.
   - A **judge agent** that never saw the code, plus a person outside the team using it unguided.

## Role 4 · Pitch and science communication

1. **What a pro would add**
   - One **hero moment** (camera = cloud, radar = lake), shown, not told.
   - A real **user quote**, e.g. a water agency or emergency ministry staff member: "we plan releases from…".
   - The limit stated before a judge finds it.
   - Ten timed rehearsals.
2. **Rawest material**
   - The **official judging rubric** and the challenge text, line by line.
   - Real users' words.
   - Our own raw before/after images.
   - Not a summary of our features.
3. **Methods and tools**
   - Problem → promise → proof storyboard.
   - ≤12 words per slide.
   - 130 words per minute.
   - Watch a recording with the sound off to check body language.
   - A Q&A bank with 20-second answers.
4. **Independent proof**
   - A cold listener can repeat the story in one sentence.
   - A judge-agent rubric score of 9 or more on all 5 criteria.
   - A timed run under 2:00, three times in a row.

---

## The rewritten prompt (what we are actually asking for)

> Build Falakus v11 the way a radar scientist, an ML reviewer, a geospatial engineer and a science communicator
> would sign off on it. **Every number** comes from calibrated NISAR GCOV γ⁰ (HDF5), never from display tiles,
> unless it is labelled "screening only". It carries an uncertainty and a source, and is cross-checked against at
> least one independent NASA product (OPERA DSWx / DIST-ALERT, ICESat-2, USGS). Compare only same-track,
> same-direction pass pairs. Separate the seasonal cycle from the anomaly. Choose every threshold without the data
> it is scored on (nested), report confidence intervals over dates, and state the failures.
> The platform finds every NISAR pass for any place or drawn box from NASA CMR metadata. It shows 15 m GIBS radar
> with the pass date, track and direction. It works instantly offline for 8 pre-cached world places, and never shows
> a blank or boxed-in map. It passes automated end-to-end tests, a phone cold-start and a blind judge score of 9 or
> more on all five criteria.
> The pitch leads with one shown moment (camera sees cloud, NISAR sees the lake), uses ≤12 words per slide, states
> limits first, and is checked by an outsider retelling it in one sentence. Maker never checks itself; a separate
> checker signs off each part.

## What this changes right now
- **Science agent:**
  - Panama, Langtang and Rondônia numbers from GIBS tiles are labelled **"screening only"**.
  - Every case is cross-checked against OPERA DSWx or DIST-ALERT, with an agreement % reported.
  - Bootstrap CI for the water IoU.
- **Calibrated γ⁰ for the cases:** this needs an **Earthdata login**; the team's earlier `.netrc` is not on this laptop. If a team member runs `earthaccess.login(persist=True)`, we read the real GCOV HDF5 for Panama and Langtang. Otherwise screening only, and we say so.
- **Platform agent:** GetCapabilities-driven layer dates, Cache-API warm-up of the demo places, tile-error counter.
- **Checker:** a blind judge agent plus a separate code/claims checker after each maker finishes.
