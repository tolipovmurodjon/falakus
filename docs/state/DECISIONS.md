# Decisions (overnight autopilot, from 14 Nov 2026 evening)

Each line: what · why · the option not taken.

- Data = NASA's NISAR GCOV browse previews (PNG, rendered by NASA), not calibrated dB · no Earthdata login file on this laptop and the `pip install earthaccess` step was rejected by Boss, so I do not retry it · the calibrated .h5 path (waits for Boss's login in the morning).
- Time player range = 29 Oct 2025 (oldest GCOV in CMR) → today, one track/frame per place · mixing tracks fakes change (look angle) · showing every pass from all tracks.
- Change map = luminance difference of two previews of the SAME track/frame, labelled "from previews, not dB" · honest and computable tonight · a calibrated log-ratio (needs .h5).
- Optical layer = Esri World Imagery + EOX Sentinel-2 cloudless (no key) · judges need to know what they look at · Sentinel Hub (needs an account = wall).

## 14 Nov 2026, evening (after Boss's Earthdata login)
- Science mode = calibrated GCOV gamma0 boxes read over HTTPS (earthaccess + h5py), cut into static z10-14 tiles · the 1st decision above (previews only) is replaced now that Boss's login works · live per-tile streaming (measured 42-314 s per tile).
- Class map ("what is here") shown by default, raw HH/HV/ratio colours behind a switch · judges and the public cannot read raw SAR colours (Boss: "what is that yellow") · raw-only.
- Classes by fixed dB rules (water HH<-18 & HV<-24, built HH>-5, plants HV>-17, else bare) · checkable by anyone; Tashkent built share 35.8 % vs ~37 % city share · Otsu per box (it called Tashkent's city 508 km2 of "water").
- One fixed dB colour scale for all places and dates · per-image stretch fakes change · per-image percentile stretch.
- Events = NASA EONET + USGS M5+ since 17 Jun 2026 (936) · Boss asked for earthquakes; USGS needs no key · GDACS (later, if time).
- At most 2 NASA read lanes at once, 3 retries with pauses · 4+ parallel lanes were throttled (every read failed 17:30-19:50) and later the laptop ran out of memory · more lanes.
- Aral science box 40 km (not 80/100) · an 80 km box at 20 m is 4000x4000 x 2 bands and ran the laptop out of memory · full-basin box.
- Sentinel-1 no-login test: not done; the research agent stalled after 600 s and is not relaunched without Boss · Planetary Computer anonymous SAS token test is the next try.

## 14 Nov 22:00-23:00
- Front door = "drag to compare" with 3 curated cases (Boss's playbook v2 goal), not the world map. Not taken: keep the tour as the entry (judges have ~3 min; the tour needs 16 clicks).
- Aral baseline = RADARSAT-1 1997 ScanSAR (open, no login). Not taken: SAOCOM / RCM (need registration in Boss's name = wall).
- Langtang change = per-pixel anomaly vs its own pair-to-pair variability. Not taken: whole-box "km² changed by > 3 dB" (event pair 23.7 km² vs 22.8 km² for a no-event pair: indistinguishable, would be a false claim).
- False colour = R HH, G HV, B HH/HV (NISAR GCOV is dual-pol). Not taken: the UAVSAR R HH / G HV / B VV recipe (no VV in these products).
- Science lane paused at 83 MB free on D:; Boss frees D: himself (his answer). Not taken: writing to C: or downsampling.
