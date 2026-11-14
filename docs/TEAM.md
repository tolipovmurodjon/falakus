# Falakus: team guide (read this first)

NASA Space Apps 2026 · challenge **Dancing with the SARs** · submission closes **Sun 15 Nov 2026, 23:59** (Tashkent).
Repo: `github.com/tolipovmurodjon/falakus` · work branch: `overnight` (do not push to `main`; open a pull request).

---

## 1. The story (decided 14 Nov, 23:30)

**One story, one screen: "Where the valley's water goes."**
The water starts in the Andijan reservoir, is used by the Fergana fields, and ends at the Aral Sea. NASA-ISRO NISAR radar watches all three every 12 days, through cloud and at night.

- The first screen shows only this story, as chapter tabs: **Andijan → Fergana → Aral**.
- Everything else we built goes behind one **"Explore the world"** button: the world map, ships, oil slicks, the airport, the Langtang landslide and the Panama quake. It is the "it scales" proof, not the pitch.
- Why: judges spend about 3 minutes. Many places and many topics mean they remember none. See the rules in section 6.

### The 60-second speech (draft; 🟡 = number still being measured)
| # | part | what we say | screen |
|---|---|---|---|
| 1 | Hook (0-10 s) | Half the valley's water flows out of one reservoir, Andijan. For months a year, clouds hide it from camera satellites. | Sentinel-2 photo, 🟡 % cloudy days |
| 2 | Twist (10-25 s) | NISAR sends its own 24 cm pulse. Calm water is a mirror, so it goes black. NISAR watched the Andijan reservoir drain from 50.5 km² (14 Jul) to 19.3 km² (6 Oct), the same trend as the cloud-free photos (r = 0.83). | drag photo ⇆ radar |
| 3 | Follow the water (25-40 s) | Downstream, the Fergana fields drink it. The cross-polarized echo (HV) rises as crops grow and drops at harvest. | heartbeat chart, field RVI 🟡 |
| 4 | Where it ends (40-50 s) | At the end of the river is the Aral Sea. Canada's 1997 radar shows open sea; NISAR in 2026 finds at most 0.93 km² of water in a 1,600 km² box. | 1997 ⇆ 2026 drag |
| 5 | Proof + close (50-60 s) | Every number is checked: on passes our rule never saw, the radar water map overlaps Sentinel-2 at IoU 0.58, and we show where it over-counts. Falakus lets water managers watch through any cloud. | proof badge, repo link |

Deck: 7 slides, one per speech part plus "the challenge" and "who acts". Build with `python tools/build_pitch.py`, then check with `python D:/30_library/taste/templates/slides-eye-run/render.py docs/deck/pitch.html` (that template lives on Murodjon's laptop).

---

## 2. Status (honest, 15 Nov ~01:00)

| part | state |
|---|---|
| Calibrated NISAR reader (HDF5 box reads, no full downloads) | ✅ `tools/gcov_science.py` |
| **Andijan reservoir water vs Sentinel-2** | ✅ `tools/water_road.py andijan_res`: NISAR **50.5 → 19.3 km²** (14 Jul → 6 Oct) vs Sentinel-2 **40 → 17 km²**; areas agree **r = 0.83** (R² 0.69, 8 passes); map overlap on held-out passes **IoU 0.49-0.71, median 0.58**; radar counts **~8.6 km² too much water**, likely smooth mud left as the lake drains (not yet verified) |
| How the water rule works | filtered HH < −16.75 dB, learned on ONE pass (20 Jun) and tested on the 7 later passes it never saw; only inside the lake basin (ESA WorldCover water + 1 km, like NASA's OPERA water product). HV is not used: over calm water it sits at NISAR's noise floor (~−23 dB) |
| **Old bug, fixed** | the first "Andijan" box sat WEST of the reservoir. Its "1.5-19 km² reservoir water" was wrong; the real reservoir is box `andijan_res` (73.135 E, 40.765 N, 18 km) |
| Fergana fields, Aral through the same check | ⏳ next |
| Aral 1997 (RADARSAT-1) vs 2026 (NISAR) | ✅ in the app (Compare → Aral) |
| 0.5 m check of the 10 m ship detector | ✅ Radar finds → Bosphorus. ICEYE 0.5 m image, taken 5 h after the Sentinel-1 pass: **5 of 12** of our dots sit on a ship you can see, 1 on a breakwater (false), 6 on empty water (probably ships that moved on), 5 small boats missed |
| Before/after swipe, compare anywhere (any layer on either side) | ✅ |
| Fixed-rule land classes | ⚠️ call 40 % of Tashkent's buildings "plants" (walls turned away from the radar). Now opt-in, with that error printed; the map shows the measured radar by default |
| World map placement | ⚠️ off by 0.5-4 km. Fix: NASA's own `_LATLON.kml` box per preview (`tools/fetch_kml_boxes.py`, 600 of 16,691 fetched, resumable; the server already uses them) |
| Judge score (fresh agent, playing the app) | 6.0 / 10 (round 3). Fixed since: wrong Panama metre count removed, physics wording, anomaly method stated |
| Still open from the judge | case → tour freeze; phone layout; trim the Sentinel-2 photo to the radar box with cloud % inside the box; draw the analysis box |
| Single story screen | ⏳ next |
| 30 s video, public link | ⏳ (the public link needs Murodjon's yes) |

Full decision log: `docs/state/DECISIONS.md`. Rounds: `docs/state/overnight.md`. Plan: `docs/state/PLAN.md`.

## 3. Run it on your machine

```bash
git clone git@github.com:tolipovmurodjon/falakus.git && cd falakus && git checkout overnight
pip install earthaccess h5py numpy scipy pillow scikit-learn matplotlib rasterio
```

The `data/` folder is **not in git** (it is several GB). Rebuild what you need:

```bash
# 1) world map index + small previews (no login, ~15 min)
python tools/nisar_index.py data/index.json
python tools/fetch_previews.py data/index.json data/thumb --kind thumb
# 2) start the app
python tools/nisar_tile_server.py --port 8765        # open http://127.0.0.1:8765
```

Calibrated 20 m science data needs a free **NASA Earthdata Login** (https://urs.earthdata.nasa.gov). Log in once in Python with `import earthaccess; earthaccess.login(persist=True)`. It saves your own credentials locally; never commit them.

```bash
python tools/gcov_science.py andijan_res 73.135 40.765 --km 9   # read every pass over a box
python tools/water_road.py andijan_res                         # water km2, RVI, IoU vs Sentinel-2
python tools/science_render.py andijan_res 73.135 40.765 --km 9 && python tools/science_pyramid.py andijan_res
python tools/rs1_fetch.py data/history/aral 59.7 45.0 60.3 45.6 # RADARSAT-1 1997 (no login)
```

Rules for the data scripts:
- At most **2 parallel reads from NASA**. More gets throttled: every read failed for 2 hours on 14 Nov.
- After **every** edit to `web/index.html`, run the parse check. A duplicate `const` once blanked the whole page.
  ```
  node -e "const h=require('fs').readFileSync('web/index.html','utf8');new Function(h.match(/<script>([\s\S]*)<\/script>\s*<\/body>/)[1])"
  ```

---

## 4. Where things are

| path | what |
|---|---|
| `web/index.html` | the whole app (MapLibre GL 5). Sections: compare cases (`CASES`), compare anywhere (`FC`), tour, player, science mode, finds |
| `web/stops.js` | tour stop texts |
| `tools/nisar_tile_server.py` | local server: tiles, science, jobs, Sentinel-1/2 endpoints (`/api/s1.json`, `/api/s2.json`) |
| `tools/gcov_science.py` | calibrated NISAR box reader |
| `tools/water_road.py` | the story pipeline (Lee filter, water, RVI, IoU vs Sentinel-2) |
| `tools/ml_landcover.py` | Random Forest land cover, tested on unseen places vs ESA WorldCover |
| `tools/gunw_read.py` | interferograms (ground motion) |
| `tools/ship_count.py`, `slick_find.py`, `apron_count.py` | Sentinel-1 detectors (Explore) |
| `tools/rs1_fetch.py` | RADARSAT-1 1990s scenes |
| `tools/build_pitch.py` | the deck |
| `docs/project/page.md` | text for the Space Apps project page (has the AI-use note) |
| `docs/project/video-storyboard.md` | 30 s video plan |
| `docs/state/` | decisions, rounds, logs, screenshots |

---

## 5. Next steps, in order
1. Finish `water_road.py` on the real reservoir, then Fergana fields, then Aral. Put the real numbers into the speech (replace every 🟡).
2. Build the **single story screen**: photo ⇆ NISAR swipe; tabs Andijan / Fergana / Aral; a heartbeat chart under it (one point per 12-day pass); click a field to see HV dB, RVI and water yes/no.
3. Move everything else behind "Explore the world".
4. Fix the judge's open problems: case → tour freeze, phone layout (case buttons off screen), Sentinel-2 photo trimmed to the radar box with cloud % inside the box, draw the analysis box on the map.
5. A fresh judge plays the 3-minute path. Fix the lowest score. Repeat until 9/10.
6. Record the 30 s video. Prepare the public link (Murodjon decides where).

---

## 6. Our rules (from `D:\Brain\rules\hackathon-scalpel-not-encyclopedia.md`)
- **A scalpel, not an encyclopedia:** one place, one crisis, one screen, built backwards from a 60-second speech.
- **Only measured numbers.** Every number on screen comes from a script and has an outside check next to it. Never put an invented or "target" number in the pitch (banned on 14 Nov: "1.4 cm drop", "88 % accuracy").
- **Line it up before you compare.** Check geo-registration first; the world map was 4.3 km off.
- **Physics first, ML second.** Name the physical signal: roughness, dielectric constant, double bounce, phase. Test ML on a place it never saw.
- **Control beats claim.** A quiet pair shows that a change is not noise.
- **The maker never grades itself.** A fresh judge plays the real app.
- **Facts about the data:** NISAR GCOV here is dual-pol (HH + HV, no VV). Data before 21 Oct 2026 is provisional. Permanent gap: 27 Jul - 10 Aug 2026. HV over dry ground is the noise floor, not plants. Building walls turned away from the radar give a strong HV too, so "high HV = plants" is wrong in cities (40 % of Tashkent's buildings were mislabelled).
- **Walls:** no money; no sign-ups in someone else's name; never commit secrets (`.netrc`, `.env`, tokens); never push to `main`; no NASA logos in generated images; disclose AI use on the project page.
