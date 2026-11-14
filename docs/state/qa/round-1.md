# QA round 1 (14 Nov 2026, evening) — played in Chrome at 1536x674

## What works (checked by playing it)
- World mosaic: all 16,691 frames visible at zoom 2-5; Tashkent radar lines up with the city on the photo.
- Tour: info panel on the right, map stays visible; timelapse plays (Aral: 10 passes, 24 Jun -> 22 Oct).
- HH view (from the preview's red channel) is readable; before | after slider works with date tags.
- Measured card at Aral: open water 51.1 -> 4.5 km2 (-91 %) in a 30x30 km box, 2 sparklines.

## Bugs found and fixed this round
1. CARTO basemap returned "API KEY REQUIRED" -> Esri light gray.
2. Panels with `hidden` still showed (CSS display won) -> `[hidden]{display:none!important}`.
3. Beta files (not for science) entered the timelapse -> removed.
4. Partial NASA frames were stretched into the wrong place -> rejected (<70 % fill).
5. Per-image contrast in HH/HV views faked change -> one fixed scale.

## Usability scores (1-10)
first open 6 · tour panel 7 · player 7 · HH/HV views 7 · before|after 7 · events 5 · Rogun stop 3 · phone 4 (not re-tested)

## Top 5 to fix next
1. Rogun stop unreadable (mountains) -> zoomed to the reservoir + HH hint; needs eye check.
2. Numbers come from previews (uncalibrated) -> calibrated dB after Boss's Earthdata login.
3. Event markers are plain dots; no link from an event to its radar evidence beyond the popup.
4. First visit still waits 5-40 s on a new place (NASA preview download) -> prewarm more places + show a progress bar.
5. Phone layout (390 px) not tested since the redesign.

## 5 new ideas for next round
1. Central Asia river story: Pamir -> Rogun -> Qosh Tepa -> Amu Darya delta -> Aral, numbers at each stop.
2. "Clouds can't stop it": a cloudy Sentinel-2 day next to the NISAR pass of the same day.
3. Draw a box -> water km2 and change for that box (same engine as the measured card).
4. Global hotspots: rank the 30 most-changed places between two 12-day cycles.
5. One-click GIF export of any timelapse for the 30-s video.
