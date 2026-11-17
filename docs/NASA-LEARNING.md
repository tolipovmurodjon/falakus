# NASA-LEARNING: what NASA itself says about SAR and NISAR

A study guide for the four of us before judging. Everything here comes from NASA's own pages, read on **2026-11-15**, and each fact gives its page URL. If a judge asks "where does that come from?", the answer is in this file.

Images that go with this guide are in `deck-v11/nasa_learn/` (credits and slide suggestions in `deck-v11/nasa_learn/CREDITS.md`).

**Contents**
1. Earth Observation Data Basics (remote sensing)
2. SAR page: bands, polarization, scattering, InSAR
3. NISAR mission specs and data products
4. The five NISAR StoryMaps
5. Societal benefits: the 26 white papers
6. **26 NASA use-cases × Falakus** (what we cover, what we missed)
7. How Falakus maps onto NASA's own framing
8. All 15 challenge resources: what each is, how Falakus uses it, gap

---

## 1. Earth Observation Data Basics

Source: https://www.earthdata.nasa.gov/learn/earth-observation-data-basics. The old `/remote-sensing` URL now loads this same hub.

- **Remote sensing is "acquiring information from a distance".** NASA uses instruments on satellites and aircraft that "detect and record reflected or emitted energy".
- **Active vs passive.** "Active instruments emit energy and collect data based on changes in the return signal." "Passive instruments detect energy emitted from the natural environment." SAR is active and a camera is passive. That is the whole "flashlight vs camera" line in our pitch.
- **Four kinds of resolution:** radiometric, spatial, spectral and temporal. "Resolution can vary depending on the platform's orbit and instrument design." For NISAR: spatial is 3–10 m, temporal is 12-day repeat (about 6 days with ascending and descending passes combined). See §3.
- **SAR in one sentence (hub card):** SAR "enables high resolution imagery to be created night or day, regardless of weather conditions", and "over time, can detect even minute changes on Earth's surface."
- **NISAR named on the hub as the reason for new technology.** "Innovations in artificial intelligence, climate models, and cloud computing are improving the ways users work with Earth science data, especially massive datasets like those expected from NISAR." This supports our cloud-read approach (box reads, no 2 GB downloads) and our ML land cover.
- **Earthdata Login.** NASA data are "openly available without restriction, [but] an Earthdata Login is required to download data". This matches our README: the world map works with no login, science mode needs one.
- **Processing levels run from 0 (raw) to 4 (model output).** GCOV and GUNW are Level 2 (see §3).

### SAR image-interpretation rules of thumb (sub-page)

Source: https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/sar/image-interpretation

- "Regions of calm water and other smooth surfaces appear black". "Wind-roughened water can backscatter brightly." This is exactly the wind caveat on our water and ship counts.
- "Rough surfaces appear brighter … A rough surface backscatters even more brightly when it is wet."
- "Surface variations near the size of the radar's wavelength cause strong backscattering." Short wavelengths scatter off leaves and clods; long wavelengths scatter off trunks and boulders.
- **Slopes:** layover (mountains "look as if they have fallen over toward the sensor") and shadow. Both are fixed by terrain and radiometric correction, which is already applied in GCOV.
- **Buildings act as corner reflectors.** They show as "bright spots … a bright dot or a cross". This is the physics behind our "city that shines" stop and our airport objects.

---

## 2. The SAR page

Source: https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/sar

### Why SAR sees through clouds and at night
- SAR is **active**: "an instrument sends out a pulse of energy and then records the amount of that energy reflected back". It does not need sunlight.
- Radar uses "longer wavelengths at the centimeter to meter scale, which enables them to create imagery of landforms that might be covered with clouds or under a dense canopy of trees." Cloud droplets are far smaller than 24 cm, so the wave passes straight through.

### What's "synthetic" about it
- Resolution depends on wavelength ÷ antenna length. For C-band (5 cm) at 10 m resolution "you would need a radar antenna about 4,250 m long (That's over 47 football fields!)".
- The fix: "a sequence of acquisitions from a shorter antenna are combined to simulate a much larger antenna". Figure: `earthdata-synthetic-aperture-geometry.jpg`.
- Geometry words: **slant range** vs **ground range**; **azimuth** = along-track; **range** = across-track; **look angle** vs **incidence angle**; **layover** and **shadow** in hilly terrain.

### The band table (memorise X, C, S, L, P)

| band | frequency | wavelength | what NASA says it is for / what it penetrates |
|---|---|---|---|
| Ka, K, Ku | 12–40 GHz | 0.8–2.4 cm | "Rarely used" |
| **X** | 8–12 GHz | 2.4–3.8 cm | High-res SAR: urban monitoring, ice and snow. "**little penetration into vegetation cover; fast coherence decay in vegetated areas**" |
| **C** | 4–8 GHz | 3.8–7.5 cm | "**SAR Workhorse**": global mapping, change detection, "low to moderate penetration, higher coherence"; ice, ocean, maritime navigation. *(Sentinel-1, RADARSAT-1, RCM)* |
| **S** | 2–4 GHz | 7.5–15 cm | "Increasing use … agriculture monitoring (**NISAR will carry an S-band channel**; [extends] C-band applications to higher vegetation density)" |
| **L** | 1–2 GHz | 15–30 cm | "geophysical monitoring, biomass and vegetation mapping, **high penetration**, interferometric SAR [InSAR]" *(NISAR L-SAR, ALOS, SAOCOM)* |
| **P** | 0.3–1 GHz | 30–100 cm | "Biomass, vegetation mapping … Experimental" (ESA BIOMASS) |

- **Penetration in one sentence:** X-band (about 3 cm) "mostly interacts with leaves at the top of the tree canopy". L-band (about 23 cm) "penetrate[s] more deeply … allows for more interaction … with large branches and tree trunks." Figure: `earthdata-wavelength-penetration-forest-x-c-l-p.jpg`.
- Wavelength also controls penetration into **soil, ice and dry sand**. NASA cites SAR "space archaeology" finding buried structures under desert sand.

### Polarization: HH, HV, VV, VH
- The first letter is **transmit** and the second is **receive**. H = horizontal, V = vertical. "VH" means sent vertical, received horizontal. HV and VH are **cross-pol**; HH and VV are **co-pol**.
- "Examining the signal strength from these different polarizations carries information about the structure of the imaged surface."

### The three scattering mechanisms

| mechanism | caused by | strongest in | looks like |
|---|---|---|---|
| **Rough-surface** scattering | "bare soil or water" | **VV** | medium grey; brighter if rougher or wetter |
| **Specular** (mirror) reflection | calm water, smooth tarmac, oil-smoothed sea | (the energy goes away from the radar) | **black** |
| **Volume** scattering | "leaves and branches in a forest canopy" | **cross-pol VH / HV** | bright in HV |
| **Double-bounce** | "buildings, tree trunks, or inundated vegetation" | **HH** | **very bright** |

- Caption, verbatim: "Strong scattering in HH indicates a predominance of double-bounce scattering (e.g., stemmy vegetation, human-created structures), while strong VV relates to rough surface scattering (e.g., bare ground, water)". Figure: `earthdata-scattering-mechanisms-polarization.jpg`.
- **The mix depends on wavelength.** C-band gets "mostly roughness scattering mixed with a limited amount of volume scattering" in a forest. L-band and P-band get "strongly enhanced volume scattering as well as increasing amounts of double-bounce … tree trunks."
- **Specular vs surface**, from the Floods StoryMap: "Specular / Surface Scattering: occurs when there is a smooth surface, such as open water … the signal scatters away from the radar, and as a result, open water appears dark."

### Speckle
- Speckle is not noise. It "arises because the spatial resolution … is not sufficient to resolve individual scatterers". It "can be reproduced if the acquisition conditions are identical, while noise is random." It "is removed by **multi-looking**." Pixel size is **not** the same as resolution.

### InSAR basics
- "InSAR uses the **phase** information recorded by the instrument to measure the distance from the instrument to the target." With two passes at different times, the change in distance gives ground motion that is "very accurate (up to the centimeter level)".
- **One fringe = half a wavelength.** The pulse travels there and back, so a full colour cycle is λ/2 of line-of-sight motion:
  - Earthdata's Okmok figure (ERS-2, C-band 5.6 cm): "**Each color cycle represents 2.8 cm**", which is 5.6 ÷ 2.
  - NISAR L-band 23.8–24 cm gives **about 11.9–12 cm per fringe**. That is our README number.
  - Good judge check: the same physics gives different numbers on different satellites.
- **Coherence** is how similar the two echoes are; you need it before you can trust a fringe. Earthdata's band table says X-band has "fast coherence decay in vegetated areas" and C-band has "higher coherence". The glacier StoryMap says L-band "maintains better correlation when images are collected at different times". NISAR's interferogram products carry a "normalized interferometric correlation" layer (§3).
- From the Glacial Motion and Subsidence StoryMaps: "Each fringe cycle represents a certain range of change and the number of fringe cycles can be counted to determine displacement." **Phase unwrapping** turns the repeating rainbow into continuous centimetres. GUNW is *unwrapped*; RIFG is *wrapped*.
- **Too-fast motion breaks InSAR**, for example fast glaciers. Then you use **speckle or offset tracking**, which compares image patterns rather than phase. NISAR's product for that is **GOFF**. (Glacial Motion StoryMap: "InSAR is limited in cases of fast m[otion]".)
- Pre-processing NASA lists for raw SAR: apply orbit file, radiometric calibration, de-bursting, multilooking, speckle filtering, terrain correction. **NISAR GCOV arrives with these done** (radiometric and terrain corrected).
- Free tools on the page: ESA SNAP, ISCE (JPL), HyP3 (ASF), SNAPHU (unwrapping), MapReady, PolSARpro, GMTSAR, pyroSAR.
- Earthdata on NISAR: "the joint NASA/ISRO … (NISAR) platform, which will collect L-band and S-band SAR data. **All data will be free and openly available to the public.**"

---

## 3. NISAR: specs and data products

Sources:
- https://science.nasa.gov/mission/nisar/about-the-satellite
- https://nisar.jpl.nasa.gov/mission/quick-facts/
- https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/nisar

| spec | value | source |
|---|---|---|
| Launch | **30 July 2025**, GSLV Mk II, Satish Dhawan Space Centre, India | quick-facts |
| Science operations began | **early January 2026**; 3-year NASA primary mission | quick-facts |
| Orbit | 747 km, 98.4°, Sun-synchronous dawn-dusk; orbit held to < 500 m | quick-facts, about-the-satellite |
| Repeat | **12-day exact repeat**; ascending + descending gives "sampling Earth on average every 6 days" | quick-facts |
| Wavelengths | **L-band 24 cm** (NASA/JPL; StoryMaps say 23.8 cm) + **S-band 9.4 cm** (ISRO; white papers round to "10 cm") | quick-facts, about-the-satellite |
| Where each band images | L-band **global**; S-band over India and cal/val sites | quick-facts |
| Swath | "greater than 150 miles (**240 km**)"; L-SAR "capable of **242-kilometer** swaths" (SweepSAR scan-on-receive) | about-the-satellite |
| Resolution | 3–10 m depending on mode; 7 m along-track, 2–8 m cross-track | quick-facts, about-the-satellite |
| Antenna | **12 m (39 ft) reflector** on a 9 m boom, "the largest radar antenna NASA has sent to space" | about-the-satellite; Kamchatka article |
| Data volume | "up to **26 terabits (Tb) per day**". That is terabits; ÷ 8 ≈ 3.25 TB/day raw. Do not say "26 TB". | about-the-satellite |
| Downlink | 3.5 Gbps Ka-band | about-the-satellite |
| Access | Free and open. L-band from **ASF DAAC** (Vertex, asf_search, Earthdata Search); S-band via ISRO Bhoonidhi | quick-facts, Earthdata |
| Releases | Feb 2026: >100,000 *pre-calibration* L1–L3 products. "Full global release of calibrated NISAR data products is scheduled for **July 2026**." | Earthdata |
| Latency (2017 white papers) | "1–2 days after observation, and within hours in response to disasters". The Venezuela article (2026): Urgent Response delivers in **12–24 h**. | white papers; EO article |

> **Release timeline, resolved** (ASF guide, https://nisar-docs.asf.alaska.edu/availability-overview):
>
> | date | release | data covered |
> |---|---|---|
> | 23 Jan 2026 | 25 sample products | |
> | 27 Feb 2026 | **BETA** (uncalibrated), >100,000 files, >500 TB | |
> | 20 Jul 2026 | **PROVISIONAL** (CRID P05023) | acquisitions 17 Jun to about 23 Oct 2026 |
> | 6 Nov 2026 | **VALIDATED** (CRID P05036) | acquisitions from 21 Oct 2026 |
>
> - Reprocessing of older data is due in 2027.
> - Earthdata's "calibrated release scheduled for July 2026" is the PROVISIONAL release, and our README's "validated from 21 Oct" is correct.
> - **This matters for us:** our world map (6–17 Oct) and both Panama pairs are **PROVISIONAL**. Say so on screen.

### The product ladder (Earthdata NISAR page, quoting the ASF NISAR Data User Guide)

| level | product | what it is | Falakus? |
|---|---|---|---|
| L0 | **RRSD** | raw radar signal | no |
| L1 | **RSLC** | focused single-look complex: amplitude + phase, radar geometry | no |
| L1 | **RIFG** | wrapped interferogram + "normalized interferometric correlation" (coherence) | no |
| L1 | **RUNW** | unwrapped interferogram, radar geometry, 80 m | no |
| L1 | **ROFF** | pixel offsets from "incoherent speckle tracking", mainly cryosphere | no |
| L2 | **GSLC** | geocoded SLC (UTM, polar stereographic at the poles); amplitude + phase; "can be combined … to generate interferograms and change maps" | no (NASA used it for Hubbard Glacier) |
| L2 | **GCOV** | geocoded polarimetric covariance: "calibrated backscatter … gamma-0 power … corrected for both radiometric and terrain distortions", comparable to RTC/NRB | **yes**: world map, time player, HH/HV, science mode |
| L2 | **GOFF** | geocoded pixel offsets, "primarily … cryosphere": Antarctica, Greenland, selected mountain glaciers | no |
| L2 | **GUNW** | geocoded unwrapped interferogram, UTM, **80 m** posting | **yes**: Panama M7.7 + control pair |
| L3 | **SME2** | soil moisture, 200 m grid (400 m over the Sahara) | no (gap) |

### First NISAR results NASA has published (2025–2026), good for the "it's real" slide
- **"Hummingbird" (Aug 2025):** L-band image of ice flowing around Nunatak Zaterjavshijsja, East Antarctica, with crevasses as green lines. NASA/JPL-Caltech, PIA26617. https://science.nasa.gov/photojournal/nisars-l-band-radar-reveals-hummingbird-in-antarctica/
- **Hubbard Glacier, Alaska:** M7.0 quake on 6 Dec 2025. NISAR GSLC images from 26 Nov and 8 Dec show debris from landslides and avalanches, "more than 700 potential landslides and snow avalanches" per a USGS preliminary analysis. Ice over 700 m thick ruled out standard interferograms, so backscatter roughness was the evidence. https://science.nasa.gov/earth/earth-observatory/landslide-and-avalanche-debris-litter-hubbard-glacier/
- **Krasheninnikov volcano, Kamchatka:** erupted after the M8.8 quake of 30 Jul 2025, its first eruption in about 5 centuries. NISAR made a 17-frame time-lapse from Dec 2025 to Aug 2026, with about 10 m pixels. "Lava appears brighter because it reflects microwaves more strongly." Two passes per 12 days. **This is our own tour stop "New land from lava".** https://www.nasa.gov/missions/nisar/us-india-satellite-captures-time-lapse-video-of-volcanic-eruption/
- **Venezuela, 24 Jun 2026:** M7.2 foreshock, then M7.5 mainshock less than a minute later. NISAR InSAR shows up to 60 cm of westward motion near Caracas and La Guaira. NISAR looks about 40° off nadir, so it sees both horizontal and vertical motion. This was the **first use of NISAR's Urgent Response system** for a big quake, and USGS used it to refine its fault model. https://science.nasa.gov/earth/earth-observatory/where-venezuelas-earthquakes-shifted-the-ground/

---

## 4. The five NISAR StoryMaps

Index pages: https://science.nasa.gov/mission/nisar/arcgis-storymaps/ (and nisar.jpl.nasa.gov/applications/arcgis-storymaps/). The StoryMaps were made by the NISAR applications team and are citable as Peacock, An, Pinto & Lou (2024), *NISAR ArcGIS StoryMaps*, doi:10.5281/zenodo.10818833. The ArcGIS pages are JavaScript-heavy, so we read their content through the ArcGIS REST JSON.

| StoryMap | the case | key NASA claims | polarization or technique |
|---|---|---|---|
| **Floods** https://storymaps.arcgis.com/stories/c00d7691b8004b20a14f28df710d05fd | Hurricane Florence 2018, Pee Dee River, South Carolina: UAVSAR flew 5 times between 17 and 23 Sep; Napo River (Amazon) | "radar brightness is highest over flooded forests and tall vegetation, while short vegetation and open water will appear dark". Water under trees "can be very bright" (double bounce). Threshold the backscatter to classify, with "the lowest backscatter values … open water", but "the threshold will vary" by site. | **HH** is best for floods. HV is "more suitable for volume scattering" (vegetation). |
| **Wildfires** https://storymaps.arcgis.com/stories/4724cd32c4064b9eb5ebe300c1385d07 | 2019 Rainbow Fire (Alaska); 2017 La Tuna Fire (Los Angeles, 29 km²); UAVSAR time series 2009–2020; RGB composite of 2010/2017/2020 | "Burned areas will appear darker post-fire". An "HV Ratio (Pre-Fire HV/Post-Fire HV)" is compared with Landsat dNBR. Pre-fire HV indicates **fuel load**. Radar works through smoke and at night. | **HV** (volume scattering ≈ biomass) |
| **Oil Slicks** https://storymaps.arcgis.com/stories/bda9a0fb909946918579830747a3a2a9 | Deepwater Horizon (UAVSAR, 22–23 Jun 2010; 4 million barrels); ALOS L-band vs MERIS optical | "oil slicks appear as darker areas … oil suppresses the ocean's capillary waves". In optical images sunglint can make oil brighter *or* darker; radar is consistent. | VV is the usual choice for oil, but "only **HH and HV** polarizations will be available from NISAR for the ocean and coastal waters" |
| **Glacial Motion** https://storymaps.arcgis.com/stories/7c674de4e9024a219249627500d2449b | Andes (UAVSAR 2013 and 2014: 4–8 cm vs >60 cm motion in 2 days); Iceland (Minchew 2015); Wrangell–St Elias (PALSAR offset tracking) | InSAR plus **speckle or offset tracking** for fast ice. L-band "maintains better correlation", and SAR can measure velocity at depth. | InSAR + offsets (GOFF) |
| **Land Subsidence** https://storymaps.arcgis.com/stories/109e602e748346f3be8dc89124619828 | California Aqueduct "subsidence bowl" from June 2013 to Nov 2017 (UAVSAR; Jones et al. 2020): "**over 40 inches**" in places; Belridge oil field | Groundwater pumping compacts the aquifer and the land sinks, sometimes permanently. InSAR is "much less costly than … GPS surveys collected point by point". L-band works better in vegetated areas. | InSAR (GUNW) |

All five StoryMaps repeat the same teaching core: active microwaves, clouds and night don't matter, L-band penetrates canopy, the HH/HV/VV/VH table, and the four scattering types. We teach the same core, which is a good sign.

---

## 5. Societal benefits: the 26 white papers

Source: https://science.nasa.gov/mission/nisar/societal-benefits/ (also nisar.jpl.nasa.gov/applications/societal-benefit/). These are 2-page NASA/JPL application briefs, mostly from 2017 (permafrost and soil moisture 2019; earthquake 2022; snow hydrology 2023). They grew out of the 2014 and 2015 NISAR Applications Workshops.

**The application areas NASA uses**, grouped:
- **Hazards and solid Earth:** earthquakes, volcanoes, landslides, sinkholes, induced seismicity, damage mapping, Texas and Florida hazards
- **Water:** floods, flood forecasting, soil moisture, drought and groundwater, underground reservoirs
- **Infrastructure:** levees and dams, subsidence
- **Cryosphere:** ice sheets, glaciers, sea ice, permafrost, snow hydrology
- **Ecosystems and food:** forest resources, timber and disturbance, fire management, food security, coastal land loss
- **Oceans:** oil spills, marine hazards

**The boilerplate every 2017 paper repeats.** Quote it to judges:
> NISAR "will provide all-weather, day/night imaging of nearly the entire land and ice masses of the Earth repeated 4-6 times per month … at resolutions of 5-10 meters … Products are expected to be available 1-2 days after observation, and within hours in response to disasters."

**Strong numbers to quote:**
- **Floods:** "18 major flood events hit Texas, Louisiana, Oklahoma, and Arkansas in 2015 and 2016". NISAR maps flooding "twice every 12 days", "even flooding hidden beneath forest canopies".
- **Earthquakes:** "about $5.3B annually" in the US (FEMA, 2008). Ridgecrest 2019 motion was detected over about 60 × 40 km.
- **Damage mapping:** a radar damage proxy map made **3 days** after the Christchurch quake matched the government map released **8 months** later.
- **Subsidence:** the Washington Monument has sunk about 2 inches. Subsidence "often goes unnoticed until the damage is done".
- **Sinkholes:** "Forty percent of the U.S. is prone to naturally occurring sinkholes". At Bayou Corne, InSAR saw motion "at least 30 days" before the collapse.
- **Landslides:** "Globally, between 2000 and 3000 people are killed by landslides every year."
- **Coastal:** Mississippi delta land loss is "equivalent to losing 1 football field every hour".
- **Ice:** "a loss of 1% of the volume of water in the ice sheets would raise sea level by more than 2 feet".
- **Mountain glaciers:** they hold "only 0.5% of Earth's land ice by volume" but give "nearly half of the contribution to global sea level rise from land ice".
- **Fire:** the US Forest Service share spent on firefighting rose from 16% (1995) to 52% (2015).
- **Food:** ">11% of the Earth's land surface (1.5 billion hectares) is used for farming".
- **Soil moisture:** NISAR gives field-scale maps at **200 m** every 6–12 days, compared with about 25 km from current missions.
- **Induced seismicity:** Oklahoma M3+ quakes rose "from an average of 21 … per year … 1973 to 2008, up to 659 in 2014".

---

## 6. 26 NASA use-cases × Falakus

**How to read this table:**
- **"NISAR product"** is our reading of the paper's wording, mapped onto today's product names. The 2017 papers predate the names GCOV, GUNW and GOFF.
- **Measurement types:** "backscatter" = GCOV-type; "InSAR" = GUNW-type; "offsets" = GOFF-type; GSLC = complex image (phase + amplitude).
- **"Users"** are the agencies the paper names.

| # | NASA use-case (white paper) | NISAR measurement | users named | one key fact (quoted) | what Falakus already shows | gap / what we could add next |
|---|---|---|---|---|---|---|
| 1 | Mountain Glaciers & Snow Hydrology (2023) | **offsets** (glacier velocity) + **backscatter** change (snow-melt facies) | mountain communities, India (no agency) | glaciers are "0.5% of Earth's land ice by volume" but "nearly half" of land-ice sea-level rise | **Fedchenko glacier** stop (source of the Amu Darya), GCOV time player | **Wet-snow and melt-onset map** from the HV/HH drop in GCOV over the Pamir (doable with our data). GOFF velocity exists only for selected mountain glaciers; check whether Fedchenko is covered. |
| 2 | Earthquake! Tracking Location and Impact (2022) | **InSAR** (GUNW) | FEMA (cost figure); Ridgecrest via JPL ARIA | US quakes cost "about $5.3B annually" | **GUNW Panama M7.7 interferogram + pre-quake control pair**; Kumamoto stop; USGS M5+ events layer | Add the **Venezuela 2026** NISAR case; combine ascending and descending passes to separate horizontal from vertical motion; count fringes to cm on screen. |
| 3 | Soil Moisture & Water Resources (2019) | **backscatter** → L3 soil moisture (SME2) | USDA, USGS (credits); WHO stats | NISAR maps soil moisture "at the spatial scale of individual farm fields", 200 m every 6–12 days | indirectly: the wet-soil-is-brighter rule in our physics table | **Gap: we don't load SME2.** Add a soil-moisture layer for Fergana/Kyzylorda. It fits our water story. |
| 4 | Damage Mapping (2019) | **coherence / backscatter change** (damage proxy map, from SLC pairs) | rescue operations, insurers (no agency named) | DPM made **3 days** after Christchurch matched the government map from **8 months** later | **change map** in the time player; Langtang landslide **changed pixels** (89% cloud on the optical side); "What happened here?" | **Coherence-loss damage map** from GSLC/RIFG pairs. Our change map uses amplitude only. |
| 5 | Changes in Permafrost (2019) | **InSAR** (seasonal heave and subsidence) + backscatter | none (planners, residents) | permafrost underlies "approximately 15% of the Earth's terrestrial surface" | not covered | A Siberian or Alaskan GUNW pair showing thaw subsidence (the Anaktuvuk fire case). |
| 6 | Sinkholes & Cavern Collapse (2017) | **InSAR** (fraction-of-24 cm motion) | none named; USGS and National Cave/Karst Institute credits | "Forty percent of the U.S. is prone to naturally occurring sinkholes"; precursor motion "at least 30 days" before collapse | not covered | InSAR time series over a salt or karst area. A strong "early warning" story but needs many GUNW pairs. |
| 7 | Volcanic Hazards (2017) | **InSAR** (inflation) + **backscatter** (lava, ash extent) | USGS, Smithsonian GVP, CDC | Three Sisters: "about 20 million cubic meters of magma about 5 km beneath the ground" | **Krasheninnikov stop "New land from lava"**: GCOV brightness of the new lava field. **NASA published the same volcano as a NISAR time-lapse.** | Add the GUNW deformation pair for Krasheninnikov; cite NASA's time-lapse next to ours. |
| 8 | Landslides (2017) | **InSAR** (slow creep) | USGS (credits) | "between 2000 and 3000 people are killed by landslides every year" | **Langtang 26 Aug collapse**: backscatter change through cloud | We show the *sudden* failure. NASA's emphasis is *slow creep before* failure (InSAR over months). |
| 9 | Floods (2017) | **backscatter** (HH; open water dark, flooded forest bright) | FEMA, NOAA, USGS | maps flooding "twice every 12 days … Even flooding hidden beneath forest canopies will be visible" | **water map** (HH < −18 dB & HV < −24 dB), **before/after swipe**, Narayani monsoon flood stop, Shieli rice, EONET floods | **We only classify open water (dark).** Add a "**flooded vegetation**" class (very bright HH from double bounce with high HH/HV), which is exactly NASA's Pee Dee and Farmerville point. |
| 10 | Induced Seismicity (2017) | **InSAR** | USGS, USBR, National Academies | Oklahoma M3+ "from an average of 21 … per year … up to 659 in 2014" | not covered | Low priority for Central Asia. |
| 11 | Hazards in Texas (2017) | **InSAR** (Houston subsidence) + **backscatter** (hurricanes, floods) | NOAA, FEMA, Texas A&M Forest Service (credits) | Houston drawdown "about 50 mm/year" | EONET storms and floods (global) | No US-specific layer; not needed for our pitch. |
| 12 | Coastal Land Loss (2017) | **backscatter / polarimetry** (vegetation type, canopy height) | US FWS, CA DWR, USGS (credits); land managers | Mississippi delta: "losing 1 football field every hour" | **Mississippi River Delta stop** ("A delta that floods and grows"); Aral Sea shoreline | Quantify land gained or lost per pass (km²) the way we do for the Aral. |
| 13 | Oil Spills (2017) | **backscatter** (oil damps capillary waves, so it is dark) | NOAA (STAR, OR&R), DHS, International Charter | Deepwater Horizon: "210 million gallons … over 86 days"; "Coastlines will be imaged by NISAR every six days" | **oil-slick candidates off Baku** (Sentinel-1; > 6 dB darker, elongated, platforms masked) | Run the same detector on **NISAR HH** coastal frames (NASA notes NISAR gives only HH/HV over oceans). Low-wind look-alikes are the same caveat NASA gives. |
| 14 | Ice Sheets, Glaciers & Oceans (2017) | **offsets / velocity** ("radar speed gun") + grounding line (InSAR) | none (planners) | 1% of ice-sheet volume = "more than 2 feet" of sea level; Jakobshavn sped up "nearly threefold" | not covered beyond Fedchenko | A GOFF velocity tile (Greenland or Antarctica) or the NASA "hummingbird" image as a showcase. |
| 15 | Marine Hazards (2017) | **backscatter** (brightness rises with wind → wind speed; ice/water edge) | NOAA, US National Ice Center | ocean wind at "500 m resolution" | **ship watch** at 7 chokepoints; wind-bright passes greyed out | Turn our "wind made the sea bright" flag into a **wind-speed estimate**. That makes a weakness into a product. |
| 16 | Sea Ice (2017) | **offsets** (ice motion) + backscatter (ice age and type) | US Coast Guard, Navy | "NISAR will image most of the sea ice areas … twice a week" | not covered (Aral winter ice not shown) | Optional: Caspian or Aral winter ice extent from GCOV. |
| 17 | Fire Management (2017) | **polarimetric backscatter change + InSAR coherence change** | NICC, USFS WFAS, USFS RSAC | firefighting rose from 16% to 52% of the USFS budget, 1995→2015 | **"After the fire"** stop (Northern Territory); **HV toggle**; EONET fires | Add NASA's **HV ratio (pre/post)** burn map and a pre-fire **HV fuel-load** note, straight from the Wildfires StoryMap. |
| 18 | Food Security (2017) | **multi-pol and multi-frequency backscatter time series** (crop type and stage) | UN FAO | ">11% of the Earth's land surface … used for farming" | **cotton calendar** (Fergana), **Iowa corn harvest**, **Shieli rice**; **ML land cover** (Random Forest on the NISAR time series) | Crop-**type** classes (cotton vs wheat vs rice) from the seasonal HV curve. Our ML currently does water / built / plants. |
| 19 | Forest Resources (2017) | **backscatter → biomass and volume** | Secretary of Agriculture (RPA Act), USGS | maps forests "at 25 m resolution multiple times per year" | **Rondônia "forest edge"**, HV = plants class | An HV → above-ground-biomass estimate (t/ha) with an honest error bar. |
| 20 | Timber & Forest Disturbance (2017) | **multi-date backscatter change** | timber industry, resource managers (USDA, NPS credits) | timber has "more than 30,000 applications" | Rondônia deforestation through the time player | Date each clearing (first pass with an HV drop), like NASA's 3-date RGB. |
| 21 | Flood Forecasting (2017) | **InSAR over flooded vegetation** (water-level change, a "virtual stream gauge") | NOAA AHPS, US Army Corps of Engineers | centimetre-level water-level change measured "24 hours apart" (SIR-C, Purus) | not covered | Ambitious: GUNW over the Amu Darya delta wetlands for water-level change. |
| 22 | Hazards in Florida (2017) | **InSAR** (sinkholes, Everglades water levels) + backscatter (hurricane winds) | National Hurricane Center, SE Florida Climate Compact | sinkholes cost "$200 million per year" in Central Florida | not covered | Not needed. |
| 23 | Drought & Groundwater Withdrawal (2017) | **InSAR** (aquifer subsidence) | US Drought Monitor, CA DWR | aqueduct sections sank "more than 12″" | **Aral Sea, Rogun, Qosh Tepa, Andijan reservoir**: water *extent* over time | **Gap: no groundwater subsidence.** A GUNW stack over an irrigated Central Asian basin would link our water story to NASA's aqueduct story. |
| 24 | Oil, Gas & Water Underground Reservoirs (2017) | **InSAR** (uplift and subsidence over managed reservoirs) | USGS, operators, insurers | NISAR data "almost 3 times more frequently" than the examples | not covered | Optional: Caspian oilfields near Baku, combined with our slick stop. |
| 25 | Levees & Dams (2017) | **InSAR** (embankment motion) + backscatter (seepage via soil moisture) | CA DWR, USACE (credits) | "tens of thousands of miles of levees and hundreds of dams" | **Rogun dam** and **Andijan reservoir** stops (water extent only) | **Dam-body InSAR** at Rogun or Nurek. It would move us from "how much water" to "is the dam safe". |
| 26 | Subsidence (2017) | **InSAR** (repeat images "for several years") | ASF (data access) | Washington Monument "~2″" since construction; New Orleans hot spots | not covered (our GUNW is a quake) | A subsidence map for **Tashkent** or another Central Asian city would be the single biggest add for NASA alignment. |

**Coverage in one line:** we directly cover **10 of 26**: floods, damage, landslides (sudden), volcano, oil, fire, food, forest, timber, and coastal/delta. We partly cover **5**: earthquake, glaciers/snow, marine, drought (extent only), dams (extent only). **11** are open, and most of them are **InSAR deformation** (subsidence, sinkholes, permafrost, induced seismicity, reservoirs, flood forecasting).

**The pattern:** we are strong on **GCOV backscatter** and thin on **GUNW time series** and **GOFF**. That is the honest "next step" answer for judges.

---

## 7. How Falakus maps onto NASA's own framing

| Falakus feature | NASA's framing it matches | NASA source |
|---|---|---|
| "Camera vs flashlight", works through cloud and at night | active vs passive; "night or day, regardless of weather" | Earthdata basics + SAR page |
| Physics table (water dark, city bright, HV plants, wet soil brighter) | the 3 scattering mechanisms + image-interpretation rules | Earthdata SAR + image-interpretation pages; Floods StoryMap |
| **HH / HV toggle** | "HH … surface and double bounce; HV … volume" | Floods + Wildfires StoryMaps |
| **Water map** (dB thresholds) | "a range of backscatter values associated with different classes … threshold will vary" | Floods StoryMap |
| **Before/after swipe, time player** | Pee Dee 17 vs 23 Sep swipe; Hubbard 26 Nov vs 8 Dec; Kamchatka time-lapse | Floods StoryMap; NASA EO; NASA article |
| **Change map / "What happened here?"** | damage proxy maps; multi-temporal HV composites | Damage Mapping white paper; Wildfires StoryMap |
| **GUNW Panama interferogram + control pair** | InSAR phase → cm; fringes = λ/2; NISAR Venezuela InSAR | Earthdata SAR; Glacial Motion and Subsidence StoryMaps; NASA EO |
| **L-band vs C-band switch** | band table: C = workhorse, L = penetration and coherence | Earthdata SAR |
| **Ship watch, airport objects** | "buildings, bridges … behave as corner reflectors"; marine hazards | image-interpretation page; Marine Hazards white paper |
| **Oil-slick candidates** | "oil slicks appear as darker areas … suppresses capillary waves" | Oil Slicks StoryMap; Oil Spills white paper |
| **ML land cover** | "AI … especially massive datasets like those expected from NISAR" | Earthdata basics hub |
| **Central Asia water road** (Aral, Rogun, Qosh Tepa) | water resources, drought, levees and dams, food security | white papers 3, 18, 23, 25 |
| **Krasheninnikov, Mississippi Delta, Fedchenko, Langtang** | NASA's own NISAR stories and white-paper cases at the same or similar places | NASA Kamchatka article; Coastal, Snow-Hydrology and Landslide papers |
| **Honest-limits section** | NASA's own caveats: "threshold will vary", wind look-alikes for oil, UR maps "preliminary until reprocessed" | Floods and Oil StoryMaps; Venezuela EO article |

**The one-liner for judges:** *"Falakus takes NASA's own SAR curriculum, from scattering and polarization to change detection and InSAR, and runs it live on real NISAR GCOV and GUNW data, for the place we live: Central Asia's water."*

---

## 8. All 15 challenge resources: what each is, how Falakus uses it, gap

Challenge page: https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/. We checked it on 2026-11-15.

**It lists 13 entries, not 15.** That is 9 NASA, 3 CSA, and CONAE as one entry with two links (catalogue + registration), so **14 URLs**. There is no separate NISAR mission page or sample-data link. The page says "More resources may be added". All pages loaded.

| # | resource | what it is | key facts | how Falakus uses it | gap / next |
|---|---|---|---|---|---|
| 1 | **Earthdata Search** https://search.earthdata.nasa.gov/search | NASA's search, compare and download portal for all Earth science data (>10,000 collections) | Search `nisar_` for NISAR. VALIDATED collections are named `NISAR_L2_GCOV_V1` / `NISAR_L2_GUNW_V1`; older ones carry `_PROVISIONAL_` / `_BETA_`. CMR today: 18,588 VALIDATED GCOV and 140 VALIDATED GUNW granules. (Notes from https://nisar-docs.asf.alaska.edu/earthdata-search; the app itself is JavaScript.) | We skip the web app and query the same **CMR API** directly (`tools/nisar_index.py`, `gunw_read.py`), downloading with `earthaccess` | Add a per-frame "open in Earthdata Search" link so judges can verify any frame |
| 2 | **ASF Vertex** https://search.asf.alaska.edu/ | ASF DAAC's SAR search tool | NISAR filters: product type, **Production vs Urgent Response**, maturity, freq A/B polarisation, orbit direction, coverage. L-band only (S-band is on ISRO Bhoonidhi). | Mentioned only; discovery runs through CMR | Deep-link each frame; mention **Urgent Response** (12–24 h) in the disaster pitch |
| 3 | **NISAR Data User Guide** https://nisar-docs.asf.alaska.edu/ | ASF's official product documentation | See the GCOV and GUNW notes below this table | Science mode reads GCOV HH/HV; `gunw_read.py` reads `unwrappedPhase` + `coherenceMagnitude`, with LOS = −φ·λ/4π and coherence > 0.3 | **Apply `ionospherePhaseScreen` and mask with `connectedComponents` on Panama**; label maturity + CRID on every layer |
| 4 | **Intro to Remote Sensing** https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/remote-sensing (redirects to the hub; read via the `/remote-sensing-resolution` and `/remote-sensing/active-instruments` sub-pages) | NASA primer | **Four resolutions:** radiometric (bits), spatial (pixel), spectral (bands), temporal (revisit). Trade-off: "difficult to combine all of the desirable features into one remote instrument". **Active** sensors (radar, lidar, scatterometer…) send a pulse and are mostly microwave, so they work through the atmosphere "under most conditions". | The "flashlight vs camera" opener (README §1) | A small "resolution card" per layer (NISAR 10–20 m / 12 d vs S-1 10 m vs RADARSAT-1 ScanSAR vs S-2) |
| 5 | **Intro to SAR** https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/sar | NASA SAR primer | All of §2 above | Physics table, L vs C switch, HH/HV toggle, InSAR explainer | Cite it on the "how it works" slide |
| 6 | **ARSET trainings** https://appliedsciences.nasa.gov/get-involved/training (now redirects to https://www.earthdata.nasa.gov/data/projects/arset; the list is at /learn/trainings) | NASA Applied Remote Sensing Training | SAR/NISAR courses: *Introduction to SAR* (2017); *When Fields Flood: standing water & inundated vegetation* (2020, 2022); ***Harnessing NISAR*** (2–16 Jul 2026); ***Monitoring Surface Water with SAR*** (20 & 27 Oct 2026: NISAR amplitude flood mapping in QGIS + OPERA DSWx); ***Identifying Disaster Extent and Risk Using NISAR Surface Displacement*** (12 & 19 Nov 2026, Fielding & Podest, JPL: InSAR error sources). Paths are under `www.earthdata.nasa.gov/learn/trainings/…`. | `docs/CHALLENGE.md` takes the flood threshold + change method and RVI from ARSET | Cite the Nov 2026 InSAR course for our ionosphere and error answer; validate our water and motion against **OPERA DSWx / DISP** |
| 7 | **NISAR StoryMaps** https://nisar.jpl.nasa.gov/applications/arcgis-storymaps/ (redirects to science.nasa.gov) | 5 teaching StoryMaps | See §4 | The same 5 themes are our Explore topics (floods, fire, oil, glaciers, subsidence) | Subsidence and glacier velocity are the two we can't yet show |
| 8 | **White papers** https://nisar.jpl.nasa.gov/applications/societal-benefit/ (redirects to science.nasa.gov) | 26 two-page application briefs (the page has 28 PDF links; the other 2 are the 2014 and 2015 workshop reports) | See §5–6 | See §6: 10 covered, 5 partly | See §6 |
| 9 | **UAVSAR Postcards** https://uavsar.jpl.nasa.gov/education/postcards.html | JPL education page: 2 infographics + 17 printable postcards (updated 2017) | Topics: Gabon, **Central Valley subsidence** (>7 in, 2013–15), LA and SF Bay polarimetry, El Mayor–Cucapah M7.2 interferogram, Kilauea, Chilean glacier InSAR, **Pacaya-Samiria flooded forest** (red/pink = inundated vegetation), volcanoes (Tungurahua, Kyushu, Aleutians), Vatnajökull, Hofsjökull. Polarimetric cards use R=HH, G=HV, B=VV. Licence: only the JPL Image Policy footer link. | Our false colour (R HH, G HV, B HH/HV) adapts the postcard recipe, because NISAR dual-pol has no VV (`science_render.py`) | **Flooded-vegetation class**, the postcard theme our classes miss; a UAVSAR-vs-NISAR comparison card |
| 10 | **CSA RCM** https://donnees-data.asc-csa.gc.ca/en/dataset/rcm | Canada's 3-satellite RADARSAT Constellation (C-band) | Daily revisit of Canada, daily access to 90% of the world, Arctic up to 4×/day. Uses: ice, wind, oil, ships, disasters. Catalogue licence is OGL-Canada, but products have per-product user licences with exceptions. Access via EODMS; open samples at `donnees-data.asc-csa.gc.ca/users/OpenData_DonneesOuvertes/pub/RCM/` (Newfoundland, Lake Superior, Montreal, Nairobi, …). | Not used (EODMS registration would be in the team lead's name) | An open RCM sample next to Ship watch: a third band and a third agency, no login |
| 11 | **CSA SAR Python tutorial** https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial | Bilingual **beginner plotting guide** (MIT licence, © CSA 2022) | Option 1: QGIS (load raster + vector). Option 2: one notebook, `BC Wildfire raster plot.ipynb`: read a GeoTIFF with rasterio, plot a Natural Earth shapefile with geopandas, overlay with CRS conversion, cartopy map. Data: RCM-3 BC wildfire scene. **No** calibration, speckle filter, terrain correction or change detection. | Not used; our steps start where it ends (rasterio/CRS reading ≈ our `gcov_science.py` box reads + `utm_convert.py`) | Nothing to adopt. In the pitch: "the CSA tutorial plots a radar image; Falakus calibrates, classifies, detects and measures motion" |
| 12 | **CSA RADARSAT-1** https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1 | Canada's first EO satellite, 1995–2013, C-band 5.3 GHz (about 5.6 cm) | Whole Canadian archive under **Open Government Licence – Canada**. Access: EODMS (TIFF) or AWS bucket `radarsat-r1-l1-cog` (COG). Since Dec 2025, a free NRCan processing service for never-processed raw data. | **Aral Sea 1997 baseline** (`tools/rs1_fetch.py`, EODMS STAC + COG) | Build a multi-year Aral series (1995–2013), not one date; print the OGL-Canada attribution on the slider |
| 13 | **SAOCOM (CONAE)** https://catalogos.conae.gov.ar/catalogo/catalogoSatSaocomInfo.html + registration https://www.argentina.gob.ar/noticias/la-informacion-saocom-cada-vez-mas-accesible | Argentina's **L-band** polarimetric pair, 1A/1B (about 23.5 cm, close to NISAR). Specs are from secondary sources, not CONAE's pages. | Catalogue browsing is open. Downloads need CONAE registration + a signed licence. Since Feb 2023, anyone can get **archive over Argentina only**. Free test products (L1A/1C/1D, single to quad-pol) are non-commercial, credited "Producto SAOCOM® - ©CONAE - (year)". | Not used (registration would be in the team lead's name) | A "two L-band missions" card: a SAOCOM quad-pol test scene beside a NISAR GCOV of the same Argentine area. No registration needed. |
| 14–15 | (*NISAR mission page / NISAR sample data*) | **Not on the challenge page today.** We cover them anyway from science.nasa.gov/mission/nisar and nisar-docs (§3). | | | |

### NISAR Data User Guide: GCOV and GUNW details

From https://nisar-docs.asf.alaska.edu/gcov/, /gunw/ and the GUNW product spec (Rev E, Nov 2024).

**GCOV**
- **Values:** gamma-0 **power** (linear; dB = 10·log10), terrain-corrected (area-based, Copernicus DEM).
- **HDF5 paths:** `/science/LSAR/GCOV/grids/frequencyA|B/{HHHH, HVHV, VVVV, VHVH, …}`. The diagonal terms are real-valued; the off-diagonal terms are complex and appear only in quad-pol.
- **Extra layers:** `numberOfLooks`, `mask`, `rtcGammaToSigmaFactor`.
- **Posting:** frequency A is **10 m or 20 m** (bandwidth-dependent); frequency B is **80 m**. B is mainly for ionosphere correction, but it makes small quick-look files.
- **Polarisation codes:** SH, SV, **DH (HH/HV)**, DV (VV/VH), CL/CR, QP. Quad-pol has gap stripes by design.

**GUNW**
- **Pairs:** co-pol only (HH or VV), frequency A, **12-day nearest-neighbour pairs**.
- **`unwrappedInterferogram/{pol}/`:** `unwrappedPhase` (Float32, radians, **80 m**), `coherenceMagnitude`, `connectedComponents`, **`ionospherePhaseScreen` + `ionospherePhaseScreenUncertainty`** (split-spectrum estimate, *included but not applied*).
- **`wrappedInterferogram/{pol}/`:** at 20 m.
- **`pixelOffsets/{pol}/`:** along-track and slant-range offsets.
- **Metadata cubes:** hydrostatic and wet troposphere, solid-earth tide, LOS unit vectors, incidence angle, perpendicular baseline. None are removed from the phase.

**Both products**
- **CRS:** UTM WGS84 (EPSG 326xx/327xx) between 60°N and 60°S; EPSG 3413 north of that; EPSG 3031 south. L3 soil moisture uses EASE-Grid 2.0 (EPSG 6933).
- **Sizes** (CMR): GCOV 1.6–7.2 GB per `.h5`, GUNW 1.2–2.0 GB.
- **Naming example:** `NISAR_L2_PR_GUNW_032_141_D_085_033_2000_SH_<4 timestamps>_P05036_N_P_J_001.h5`. PR/UR/OD = production, urgent response, on-demand. The CRID is the processing version.

**The judge question to pre-empt:** *"Are the Panama fringes ionosphere?"* Answer with **both** our control pair **and** the product's own `ionospherePhaseScreen`. Panama is at about 9°N, where the ionosphere is strongest. NASA's Nov 2026 ARSET InSAR course lists the ionosphere among L-band InSAR error sources.

### Priority adds that NASA's own material points to
1. Ionosphere screen + connected-components mask on Panama; label PROVISIONAL vs VALIDATED.
2. **Flooded-vegetation class** (bright HH, double bounce). It appears in the Floods StoryMap, the Floods white paper, the UAVSAR postcards and ARSET "When Fields Flood".
3. **One subsidence or dam InSAR case in Central Asia.** This covers the white papers on subsidence, drought & groundwater, and levees & dams.
4. **HV ratio burn map** (Wildfires StoryMap) and **SME2 soil moisture** layer.
5. RADARSAT-1 multi-year Aral series; per-frame Earthdata / Vertex links.
