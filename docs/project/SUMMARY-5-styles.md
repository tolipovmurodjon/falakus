# Summary: 5 styles (each 50–200 words, no em dashes, only measured or sourced numbers). Pick one, paste it.

## A · News lede (problem first, then the fix)
About two-thirds of Earth is under cloud at any moment (NASA), and half of every day is night. The changes that shape people's lives, like shrinking reservoirs, floods, harvests and sinking ground, often happen where satellite cameras cannot see.

Falakus makes them visible with NISAR, the new NASA-ISRO radar satellite. NISAR sends its own signal and sees through cloud and darkness, everywhere on Earth, every 12 days. On its images, calm water turns black. Crops glow as leaves twist the radar wave. Ground motion of a few centimetres shows up after an earthquake.

We proved it at home. In Uzbekistan, 10.9 million people rely on reservoirs that cameras lost to cloud in 15 of 24 winter photos. Our machine-learning model maps that water through cloud, and NASA's ICESat-2 laser confirms it: the lake's level and area rise and fall together (correlation 0.95).

Anyone can explore NISAR worldwide, NASA flood and fire events, and a time-lapse since 1985. For our reservoir, a plain briefing says what changed, why, and what comes next.

## B · One person's question (story)
Every winter, a farmer in Uzbekistan's Fergana valley asks one question: will there be enough water this spring? The answer sits in a reservoir that satellite cameras often cannot see. In 2025, 15 of 24 winter photos of it were lost to cloud. The same blind spot hides floods under storms and fields after dark, all over the world.

Falakus answers with NISAR, the new NASA-ISRO radar satellite. Radar makes its own signal, so it sees through cloud and at night, every 12 days. Our machine-learning model learned what water looks like to the radar and maps the reservoir on every pass. NASA's ICESat-2 laser checks it independently, and the two agree (correlation 0.95).

The farmer gets a plain answer: the lake fell by half this summer, and here is what to expect next month. The same tool shows harvests field by field, ground motion after earthquakes, ships at night, and NASA's flood and fire events anywhere on Earth. It is free and open for 10.9 million people in the valley, and for everyone else.

## C · Scientific abstract (numbers first, for science judges)
Optical satellites miss surface change under cloud and at night. Falakus uses NISAR L-band radar (NASA-ISRO), which sees through both, to track and explain change every 12 days.

At the Andijan reservoir, which serves 10.9 million people in Uzbekistan's Fergana valley, 15 of 24 winter Sentinel-2 photos (2025) were cloud-covered. We trained a gradient-boosting model on calibrated NISAR HH/HV backscatter, labelled by clear-day photos. Tested on dates it never saw, it reached a map overlap of 0.63, against 0.59 for the standard threshold method. A shuffled-label control fell to 0.07. NASA ICESat-2 laser water levels track the mapped area independently (Spearman 0.95). A forecast trained on 10 years of monthly water beats simple baselines 30 days ahead.

Polarization tells processes apart: HH separates water, and HV reveals crop growth and harvest. Interferometric phase measures centimetre ground motion. The open web app adds global NISAR coverage, NASA flood and fire events, and a Landsat time-lapse since 1985, with plain-language briefings.

## D · "What only radar sees" (structured, easy to scan)
Most of Earth's important changes happen under cloud or in the dark, where satellite cameras see nothing. About two-thirds of the planet is cloudy at any moment (NASA).

NISAR, the new NASA-ISRO radar satellite, sees through both, everywhere, every 12 days. Falakus turns its images into answers anyone can read:
Water: calm water is a mirror for radar, so reservoirs and floods stay visible under storm clouds.
Crops: leaves twist the radar wave, so harvests show field by field.
Ground: the radar's timing reveals movement of a few centimetres after earthquakes.
Ships: metal hulls shine on dark water, day or night.

We tested it where it matters to us. In Uzbekistan, 10.9 million people depend on reservoirs that cameras lost to cloud in 15 of 24 winter photos. Our machine-learning model maps that water on every pass. A second NASA satellite, the ICESat-2 laser, confirms it (correlation 0.95).

Explore it worldwide. For our reservoir, read a plain briefing: what changed, why, and what comes next.

## E · Short and inspiring (for the "Most Inspirational" and "Storytelling" awards)
Clouds cover two-thirds of our planet at any moment (NASA). Night covers half of every day. Underneath, the world keeps changing. Rivers shrink, floods rise, fields are harvested and ground shifts. Most of it goes unseen until it is too late.

NISAR, the new NASA-ISRO radar satellite, sees through it all. Falakus gives its vision to everyone.

We began at home, in Uzbekistan, where 10.9 million people depend on reservoirs that cameras lost to cloud in 15 of 24 winter photos. We taught a machine-learning model to see water in radar. NASA's ICESat-2 laser checked our work, and the two agree (correlation 0.95). We watched a reservoir give half its water to the fields in one summer, and we can now say what comes next.

Then we opened it to the world: every NISAR pass, NASA flood and fire events, and a time-lapse since 1985. Each change comes with words anyone can understand.

## My pick
**D**: it is the clearest for a judge with no radar background, it names the problem in the first line, and it shows four things only radar sees. Second choice: **B** (story), for the Storytelling award.
