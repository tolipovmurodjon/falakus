# Decisions (overnight autopilot, from 14 Nov 2026 evening)

Each line: what · why · the option not taken.

- Data = NASA's NISAR GCOV browse previews (PNG, rendered by NASA), not calibrated dB · no Earthdata login file on this laptop and the `pip install earthaccess` step was rejected by Boss, so I do not retry it · the calibrated .h5 path (waits for Boss's login in the morning).
- Time player range = 29 Oct 2025 (oldest GCOV in CMR) → today, one track/frame per place · mixing tracks fakes change (look angle) · showing every pass from all tracks.
- Change map = luminance difference of two previews of the SAME track/frame, labelled "from previews, not dB" · honest and computable tonight · a calibrated log-ratio (needs .h5).
- Optical layer = Esri World Imagery + EOX Sentinel-2 cloudless (no key) · judges need to know what they look at · Sentinel Hub (needs an account = wall).
