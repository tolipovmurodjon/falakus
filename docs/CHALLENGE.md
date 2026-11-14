# Challenge: "Dancing with the SARs" (NASA Space Apps 2026) — the spec, and how we cover each line

Deadline: Sun 15 Nov 2026, 23:59 Tashkent. Demo: video ≤ 30 s or ≤ 7 slides, English, public link, no login.
Status key: ✅ in the app and checked · 🟡 in the app, check or polish missing · ⛔ not yet.

## 1. Must (the objectives)
| # | the challenge asks | where it is in Falakus | state |
|---|---|---|---|
| 1 | Interactive app using NISAR radar data | web map + 3-chapter story, all from NISAR GCOV (calibrated HDF5 box reads) | ✅ |
| 2 | Track and visualise surface change (water, floods, crops, glaciers, quakes...) | reservoir water (Andijan), crop growth/harvest (Fergana RVI), Aral 1997 vs 2026, flood watch, Langtang landslide, Panama quake fringes | ✅ |
| 3 | Around the world, at different time steps | world map of 16,691 frames, time-lapse per place (every 12-day pass), flood watch on NASA EONET events worldwide | ✅ |
| 4 | Actionable insight for scientists, managers, educators, public | "reservoir area every 12 days through cloud" for basin water managers; plain-language "why it looks like this" | 🟡 name the user + decision on screen |
| 5 | Open-source, user-friendly | MIT licence, repo with TEAM.md; public link | 🟡 repo private, public link needs Murodjon's yes |
| 6 | Pick a study area, download NISAR data, present it interactively | Fergana valley water road, hometown | ✅ |
| 7 | Hypothesise the physical drivers | per stop: driver (cotton irrigation release, harvest, river diversion), physics (mirror water, volume scattering, double bounce) | ✅ |
| 8 | Which polarizations show the change; future NISAR uses | HH for water, HV/RVI for crops, HH/HV ratio colour; "next" line per stop | ✅ |

## 2. "You may consider" (Murodjon: treat as required)
| consideration | where | state |
|---|---|---|
| Different polarizations | HH / HV / false colour / Plants (HV) toggles in every view | ✅ |
| Different frequencies (other sensors) | Sentinel-1 C-band (multi-year series), RADARSAT-1 C-band 1997, ICEYE X-band 0.5 m (Bosphorus) vs NISAR L-band | 🟡 S1 3-year series running, chart not on screen yet |
| Several dates as a time series | NISAR 12-day passes (11 per place), all-tracks reader (~5-day looks), Sentinel-1 monthly Nov 2023 → Nov 2026 | 🟡 multi-year chart next |
| Ancillary data: population, vegetation type | ESA WorldCover (cropland, water zone); JRC surface water (flood watch) | ⛔ population layer (WorldPop / GHS-POP) missing |
| Human drivers (agriculture, industry) | reservoir release for cotton, harvest in RVI, Aral river diversion | ✅ |
| Storytelling through data visualisation | 3 chapters, charts radar vs photo, swipe sliders | ✅ |
| Personal / hometown context | Fergana valley, Uzbekistan team | 🟡 one personal line per chapter |
| Interactive summary (sliders, web maps) | swipe compare, compare anywhere, time-lapse | ✅ |

## 3. Resources tab (all of them)
| resource | used how | state |
|---|---|---|
| NASA Earthdata Search / CMR | granule search for every pass (tools/nisar_index.py, gcov_alltracks.py) | ✅ |
| ASF Data Search Vertex | same archive (ASF DAAC hosts the HDF5 we read) | ✅ |
| NISAR Data User Guide (ASF) | product layout HHHH/HVHV, provisional vs validated, QA | ✅ |
| Intro to Remote Sensing / Intro to SAR (Earthdata) | physics wording in "why it looks like this" | ✅ |
| NASA ARSET trainings | flood mapping method (threshold + change), RVI | ✅ method source |
| NISAR StoryMaps | floods, wildfires, subsidence, oil slicks, glaciers → our Explore topics | ✅ |
| NISAR Applications White Papers | water management, agriculture use cases → our "who uses it" lines | 🟡 cite on project page |
| UAVSAR Postcards | false-colour recipe (HH, HV, ratio) | ✅ |
| CSA RCM data | RCM is not open; named as the operational partner sensor | 🟡 named only |
| CSA SAR Python tutorial | Python + GDAL workflow pattern | ✅ |
| CSA RADARSAT-1 open archive | Aral 1997 scene (tools/rs1_fetch.py) | ✅ |
| CONAE SAOCOM catalogue | L-band like NISAR; needs a sign-up (one click profile) → not done in Murodjon's name | ⛔ needs Murodjon's sign-up |

## 4. Judging (NASA + Tashkent local round, same 5)
| criterion | local wording (summary) | our evidence | score now |
|---|---|---|---|
| Impact | big problem? helps many? | Fergana valley water, millions of people; flood watch worldwide | 7 |
| Creativity | new, not a small step? | 1997 ⇆ 2026 radar; radar ⇆ cloudy photo; 0.5 m check of our own detector | 8 |
| Validity | scientific? does what it says? | every number has an outside check: r = 0.83, held-out IoU 0.58; honest failures shown | 7 |
| Relevance | answers the challenge? complete? easy? | NISAR core; table above | 7 |
| Presentation | problem → solution → why it matters | story screen; deck + 30 s video still to rebuild | 5 |

## 5. Open items that lift the score most (in order)
1. Multi-year chart (Sentinel-1 2023-2026 + NISAR + Sentinel-2) in chapter 1, and its time-lapse.
2. Population layer (people living within 5 km of the water we map) for Impact.
3. Deck rebuilt to the 3 chapters, then the 30 s video.
4. RVI checked against Sentinel-2 NDVI (Validity for chapter 2).
5. Fresh judge round on the story path; fix the lowest line.
