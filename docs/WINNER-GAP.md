# What stops a judge from saying "winner" in one look — and the fix

A judge spends about 10 seconds on the first screen. They mark a winner when three things happen at once:
- they **see real NISAR data, sharp**;
- they **understand what changed** without reading;
- they **trust it**: a source, a date and a check are visible.

| # | Blocker today (v8 live) | What a judge thinks | Fix in v11 | Status |
|---|---|---|---|---|
| 1 | World radar goes blurry when zooming in | "Is this even data?" | NASA GIBS ~15 m tiles for the exact pass date, with a scrambled-tile guard | building |
| 2 | No pass date or track on screen | "Unknown acquisition = unusable" | Status bar: "Newest NISAR pass here: date · UTC · track · A/D" | building |
| 3 | Only Andijan is analysed | "One local demo, not global" | Any place: search, draw a box, list every pass, same-track before/after, time-lapse with progress | building |
| 4 | Dead buttons (Panama, Flood, Langtang) | "Broken demo" | Old app retired; cases rebuilt from real data with honest limits | building |
| 5 | The headline was the normal seasonal drop | Water expert: "that's just the season" | Anomaly vs the 10-year normal (Dec 19.5 vs typical 22.3) | done (cases) |
| 6 | Score 0.78 tuned on test days | ML judge: "leakage" | Nested choice gives 0.80 honest; raw 0.63; range 0.74–0.80 | done |
| 7 | Too much clutter (684 quake dots, many layers) | "Noise" | Icons only for M6+ and NASA events; at most 3 panels | building |
| 8 | "Why only 5 months?" | Doubt | CMR answer on the Learn page: nothing over Fergana before 18 Jun 2026; global from 29 Oct 2025 | done |
| 9 | Recommended partner data barely shown | "Did they use the resources?" | RADARSAT-1 (CSA) 1990s vs NISAR 2026, radar to radar; dataset registry mapped to the challenge list | building |
| 10 | No visible independent check on global cases | "Just pictures" | OPERA DIST-ALERT / DSWx agreement % for each case | building |
| 11 | Slides told, didn't show | "Text slides" | v11 deck: real NASA imagery, one idea per slide | done (draft) |
| 12 | Team can't answer deep questions | Lost credibility in Q&A | JUDGE-QA.md (≈40 questions), TEAM-GUIDE.md, Learn page | done |

## Still out of reach without an Earthdata login (say this honestly if asked)
- Calibrated γ⁰ numbers for the global cases (Panama, Langtang) from the raw GCOV HDF5. Today these are tile-based "screening only" numbers.
- ALOS PALSAR (L-band, 2006–2011) history. The tool `tools/alos_series.py` exists; it needs the JAXA authorization in Earthdata.

## The one-look test (gate before showing anyone)
A person who has never seen Falakus opens localhost cold. Within 10 seconds they must be able to say:
1. "This is radar from NISAR."
2. The date of the image.
3. What changed and how they know.

If any of the three fails, it isn't done.
