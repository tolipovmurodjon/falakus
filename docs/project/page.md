# Falakus: watching Central Asia's water and the world's changes with NASA-ISRO NISAR radar

**Challenge:** Dancing with the SARs (NASA Space Apps 2026) · **Team:** 4, Tashkent, Uzbekistan

## What it does
Falakus is an open web map that plays every NISAR radar pass over a place as a time-lapse, from the archive start to this week.
It starts at home: the Aral Sea, the Andijan reservoir, the Fergana fields, Rogun and the Qosh Tepa canal upstream, Kyzylorda's rice.
Then it goes worldwide: the 26 Aug 2026 Langtang collapse in Nepal, the Kumamoto M6.8 earthquake, a monsoon flood, a savanna fire, corn and lava and a delta.

At each stop you see:
- what changed, as numbers measured from calibrated radar (km² of water, built-up land, plants and bare ground);
- why it changed (the physical driver);
- which polarization shows it (HH or HV);
- who could act on it;
- what NISAR could do next;
- one honest limit.

Anyone can click any point on land, or draw a box, and get the same analysis at NISAR's native 10–20 m in about five minutes.

## Why radar
NISAR brings its own microwave pulse (L-band, 24 cm), so it sees through cloud and at night.
- Calm water sends the pulse away, so it shows dark.
- Walls and ground form corners, so cities shine.
- Leaves and stems scatter the pulse sideways (HV).
- Wet snow absorbs it.

That is why radar can watch a flooded valley the day after a disaster, while optical satellites see only cloud.

## NASA data used (the core)
- **NISAR L2 GCOV** (provisional and validated V1), from the ASF DAAC via NASA CMR and Earthdata Cloud. Two uses:
  - the world mosaic of one 12-day cycle: 16,691 frames, NASA browse previews;
  - calibrated gamma0 HH and HV in dB for the science boxes, read straight from the HDF5 files.
- **NASA EONET** natural events (fires, floods, storms, sea ice).

Other open data:
- USGS earthquakes M5+ since 17 Jun 2026.
- Esri World Imagery and EOX Sentinel-2 cloudless 2023 for optical context.

## How we measure
- dB = 10·log10(gamma0). One fixed colour and class scale is used for every place and date.
- Water = HH < −18 dB and HV < −24 dB.
- Built-up = HH > −5 dB.
- Plants = HV > −17 dB.
- Bare ground = everything else.
- Change = HH(last) − HH(first) beyond ±3 dB.
- Each time series uses one orbit track and frame only, because mixing tracks fakes change.
- Check: Tashkent's built-up share comes out at 35.8 % of a 30 × 30 km box, against about 37 % from the city's area.

## Honest limits
- Most NISAR data is provisional (public beta); validated products start 21 Oct 2026.
- Classes come from simple dB rules, not a trained model:
  - wind can roughen water;
  - steep mountains cause radar shadow and layover.
- The world mosaic uses NASA's preview images (~150 m). Only the science boxes are calibrated at 10–20 m.

## Use of AI (disclosure)
- **Code:** AI (Anthropic Claude) helped write the data tools, the server and the web page. The team reviewed, ran and tested all of it.
- **Text:** AI helped draft the stop texts and this page. The team checked the facts against NASA, USGS and ESA sources.
- **Images:** no AI-generated images are used. All imagery is real satellite data. No NASA logos are used.

## Open source
Code: the team will add the public repository link before submission (MIT licence).
