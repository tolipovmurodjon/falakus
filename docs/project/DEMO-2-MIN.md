# 2-minute demo: 5 tasks (explorer + briefing)

The challenge in one line: **use NISAR radar to track a surface change, over time, explain why, and make it useful to people.**
Every task below shows one part of that line. Start the demo at the Andijan reservoir, not the open Pacific.

| # | Time | Task (what you click) | What you say | Challenge line it proves |
|---|---|---|---|---|
| 1 | 0:00-0:20 | **The problem.** Explorer, Fergana valley, a cloudy day. Turn on true colour (MODIS / VIIRS): the ground is white cloud. | "Two-thirds of Earth is cloudy at any time. In winter, 15 of 24 photos of our reservoir were cloud. Cameras go blind exactly when water is planned." | Why it matters (Impact) |
| 2 | 0:20-0:45 | **NISAR sees through it.** Turn on NISAR mosaic and the 20 m calibrated HH layer over the same place. Point at the black lake. | "NISAR makes its own signal, so it sees through cloud and at night, every 12 days. Calm water is a mirror for radar, so it shows black." | Uses NISAR data (Relevance) · polarization HH |
| 3 | 0:45-1:10 | **Change over time.** Turn on the Andijan water layer; drag the date slider June to November. The lake shrinks. | "Our machine-learning model maps the water on every pass. Photos show the lake fell from 42 to 21 km2 as water went to cotton. Tested on days it never saw, it beats the standard method, 0.63 vs 0.59, and NASA's ICESat-2 laser agrees, 0.95." | Change at different time steps · ML · Validity |
| 4 | 1:10-1:35 | **Why it changed.** Turn on rain (IMERG), soil moisture (SMAP), events (floods, fires). Then the HV layer over the fields. | "Little rain all summer, fields drying, harvest in the HV channel field by field. The lake did not dry by itself: people released it for crops. In winter the river refills it." | Physical and human drivers · HV polarization · other sensors |
| 5 | 1:35-2:00 | **What comes next, and for whom.** Open the briefing (intel page). Then zoom out to the NISAR boxes over the whole world. | "Next month about 19.5 km2; the forecast beats a simple guess by 13 %. A farmer reads this in plain words. And the same tool runs anywhere NISAR flies." | Actionable insight · future NISAR uses · whole world |

## Layer map (what each explorer layer is for)
| Layer in the panel | Why it is there |
|---|---|
| NISAR boxes, NISAR mosaic, NISAR calibrated HH / HV (20 m) | The core NASA data: where NISAR looked, and the radar itself |
| Andijan water (ML) | Our model's output: water on every pass |
| True colour MODIS / VIIRS, Blue Marble | The camera view: shows the cloud problem |
| IMERG rain (day, 30 min), SMAP soil moisture, MODIS land temperature, snow | The "why": weather and ground drivers |
| Events (EONET: wildfires, floods, storms, volcanoes, dust, landslides, drought, snow) | Where change is happening worldwide right now |
| Tracks (ships) | A second radar power: metal shines on dark water, day or night |
| Coastlines | Orientation |

## Rules for the live demo
- Start with a saved link at the reservoir, all layers off except the ones for task 1.
- One layer change per sentence. Never show more than 3 layers at once.
- If a layer loads slowly, keep talking: the number is on the briefing page too.
- Do not claim: Sardoba, Rogun or Qosh Tepa numbers (the model failed the photo test there), an NDVI forecast (no tested number yet).
