"""Build the 7-slide story pitch (Eye Run style): the problem, why cameras fail, the 3 chapters, the proof, who acts, why us.

Every number comes from our data files or a printed measurement (see docs/CHALLENGE.md and docs/TEAM.md).
Usage: python tools/build_story_pitch.py  ->  docs/deck/story.html
Check: python D:/30_library/taste/templates/slides-eye-run/render.py docs/deck/story.html
"""
import json
from pathlib import Path

import build_pitch as bp

ROOT = Path(__file__).resolve().parent.parent


def nums():
    a = json.loads((ROOT / "data/waterroad/andijan_res.json").read_text())["passes"]
    f = json.loads((ROOT / "data/waterroad/fergana.json").read_text())["passes"]
    fl = json.loads((ROOT / "data/floods/index.json").read_text())
    by = {p["date"]: p for p in a}  # dated, photo-checked passes; 24 Sep (no photo, wind-roughened lake) is not used as the low point
    return {"aj_max": by["2026-07-14"]["water_km2"], "aj_min": by["2026-10-06"]["water_km2"], "aj_refill": by["2026-10-30"]["water_km2"],
            "rvi0": max(p["rvi_crop"] for p in f), "rvi1": f[-1]["rvi_crop"], "fl_n": len(fl), "fl_map": sum(r["status"] == "mapped" for r in fl)}


def slides(n):
    S = []
    S.append(f"""
 <div style="position:absolute;left:56px;top:56px;width:500px;display:grid;gap:20px">
  <p class="eyebrow">Falakus · NASA Space Apps 2026 · Dancing with the SARs</p>
  <h1>The Fergana valley drinks from one reservoir. Cameras lose sight of it every winter.</h1>
  <p class="muted" style="font-size:17px">We built a free, open tool that measures the water every 12 days with NASA-ISRO NISAR radar, through cloud and at night, and checks every number against photos.</p>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
   <div class="kpi warn"><b>34 %</b><span>of 2025 camera visits to the reservoir were mostly cloud (63 % in Dec&ndash;Mar)</span></div>
   <div class="kpi"><b>{n['aj_max']:.1f} &rarr; {n['aj_min']:.1f} km&sup2;</b><span>reservoir water NISAR measured, 14 Jul &rarr; 6 Oct 2026</span></div>
   <div class="kpi"><b>r = 0.83</b><span>radar vs cloud-free photos</span></div>
  </div>
 </div>
 <div style="position:absolute;left:590px;right:52px;top:56px;height:520px">
  <div class="shot" style="height:470px"><img src="img/andijan.jpg" alt="Falakus chapter 1: NISAR radar of the Andijan reservoir left, Sentinel-2 photo right, chart of water area below the text"></div>
  <p class="cap">Our app, first screen: drag the white bar, radar &#8644; photo. The chart is radar water vs photo water, every pass.</p>
 </div>""")
    S.append("""${F("01 · the problem","Water decisions are made half-blind")}
 <div style="position:absolute;left:52px;right:52px;top:150px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 30px/1 var(--mono);color:var(--mint)">1 reservoir</b><h3>feeds the valley</h3><p class="muted" style="font-size:14px">The Andijan reservoir on the Kara Darya stores spring water and releases it June&ndash;September for cotton and wheat in the Fergana valley, Uzbekistan's most crowded region.</p></div>
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 30px/1 var(--mono);color:#C2410C">1 in 3</b><h3>camera visits lost to cloud</h3><p class="muted" style="font-size:14px">Sentinel-2, 2025: 29 of 85 visits were mostly cloud, 15 of 24 in Dec&ndash;Mar, exactly when the spring water budget is planned.</p></div>
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 30px/1 var(--mono);color:var(--mint)">Aral</b><h3>where the water ends</h3><p class="muted" style="font-size:14px">The same rivers once filled the Aral Sea. Canada's 1997 radar shows open sea; today the eastern basin is dry.</p></div>
 </div>
 <div class="glass mint-card" style="position:absolute;left:52px;right:52px;top:430px;padding:20px 26px"><p style="font-size:17px"><b>Not another dashboard.</b> A dashboard shows a picture. Falakus gives a basin water manager one checked number every 12 days, says how sure it is, and shows the photo it was checked against.</p></div>""")
    S.append(f"""${{F("02 · the water road","Three chapters, one river, one radar")}}
 <div style="position:absolute;left:52px;right:52px;top:150px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px">
  <div class="glass tile"><div class="shot"><img src="img/andijan.jpg" alt="reservoir chapter"></div><b>{n['aj_max']:.1f} &rarr; {n['aj_min']:.1f} km&sup2;</b><h4>1 · Source: Andijan reservoir</h4><p>Calm water is a mirror for the radar pulse, so it is black. NISAR counts the black area every pass; photos agree (r = 0.83). By 30 Oct it is refilling: {n['aj_refill']:.0f} km&sup2;.</p></div>
  <div class="glass tile"><div class="shot"><img src="img/fergana-harvest.jpg" alt="Fergana harvest map: fields whose plant echo fell (red) or rose (green)"></div><b>12.8 % harvested</b><h4>2 · Use: Fergana fields</h4><p>HV is the echo turned sideways by leaves and stems. From 2 Jul to 30 Oct it fell in 12.8 % of the box: fields cut for harvest, seen field by field.</p></div>
  <div class="glass tile"><div class="shot"><img src="img/aral.jpg" alt="Aral 1997 vs 2026"></div><b>1,598 &rarr; 1 km&sup2;</b><h4>3 · End: Aral Sea</h4><p>Water in one 40 &times; 40 km box: all sea in 1997 (Landsat-5), at most 1.1 km&sup2; in 2026 (Sentinel-2). Canada's 1997 radar next to NISAR.</p></div>
 </div>""")
    S.append("""${F("03 · how we know it is right","Every number has an outside check, and we show where we fail")}
 <div class="glass" style="position:absolute;left:52px;right:52px;top:150px;padding:20px 26px">
 <table><thead><tr><th>claim</th><th>outside check</th><th>result</th></tr></thead><tbody>
  <tr><td><b>Reservoir water area</b></td><td>Sentinel-2 photo water (NDWI) on clear days, 8 passes</td><td>areas track each other r = 0.83; radar over-counts ~8.6 km&sup2; in late summer (wet mud)</td></tr>
  <tr><td><b>The water rule is not tuned to the answer</b></td><td>cut-off learned on ONE pass, tested on 7 it never saw</td><td>map overlap IoU 0.49&ndash;0.71, median 0.58</td></tr>
  <tr><td><b>Forecast, Dec &ndash; Feb</b></td><td>ML model tested on every 2026 month it never saw</td><td>miss 2.3 km&sup2; vs 3.3 (same as last year) and 4.3 (same as last month)</td></tr>
  <tr><td><b>Crop signal</b></td><td>Sentinel-2 plant index (NDVI) on the same fields, 11 passes</td><td>r = 0.58: same rise and fall, weaker in midsummer</td></tr>
  <tr><td><b>Ships found by our 10 m detector</b></td><td>a 0.5 m ICEYE radar image of the Bosphorus, 5 h later</td><td>5 of 12 dots on ships you can see; 1 false (breakwater)</td></tr>
  <tr><td><b>Where it fails (shown, not hidden)</b></td><td>same water rule on the Aral salt flats and Fergana canals</td><td>salt crust is as smooth as water; canals are narrower than a 20 m pixel</td></tr>
  <tr><td><b>Data status</b></td><td>NASA's own labels</td><td>NISAR provisional before 21 Oct 2026; data gap 27 Jul&ndash;10 Aug</td></tr>
 </tbody></table></div>""")
    S.append(f"""${{F("04 · it scales","The same engine, anywhere on Earth")}}
 <div style="position:absolute;left:52px;top:150px;width:640px">
  <div class="shot" style="height:380px"><img src="img/floods.jpg" alt="Flood watch: NASA EONET floods checked with NISAR before and after"></div>
  <p class="cap">Flood watch: NASA's EONET flood list, each event checked with the NISAR pass before and after it.</p>
 </div>
 <div style="position:absolute;left:720px;right:52px;top:150px;display:grid;gap:12px">
  <div class="glass mint-card" style="padding:20px"><b style="font:400 38px/1 var(--mono)">{n['fl_n']}</b><p style="margin-top:8px;font-size:14px">NASA flood events checked so far; {n['fl_map']} had a NISAR pass on both sides. Blue = new open water, magenta = brighter (flooded plants or wet soil, a candidate).</p></div>
  <div class="glass" style="padding:18px 20px"><p class="lab">Also in Explore</p><p style="font-size:14px">16,691 NISAR frames on a world map · compare any two layers anywhere · Langtang landslide under cloud · Panama quake fringes with a control pair · ships and oil-slick candidates.</p></div>
 </div>""")
    S.append("""${F("05 · who acts on it","From a radar echo to a decision")}
 <div style="position:absolute;left:52px;right:52px;top:150px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 26px/1 var(--mono);color:var(--mint)">every 12 days</b><h3>Basin water managers</h3><p class="muted" style="font-size:14px">How fast stored water is being spent, cloud or not, with the photo check beside it.</p></div>
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 26px/1 var(--mono);color:var(--mint)">harvest week</b><h3>Farm and food agencies</h3><p class="muted" style="font-size:14px">The HV crop signal shows when fields are full and when they are cut, across the whole valley.</p></div>
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 26px/1 var(--mono);color:var(--mint)">next pass</b><h3>Teachers and the public</h3><p class="muted" style="font-size:14px">Every screen explains HH, HV and the mirror effect in plain words, so a 10-year-old can read the radar.</p></div>
 </div>
 <div class="glass" style="position:absolute;left:52px;right:52px;top:420px;padding:18px 24px"><p style="font-size:15px"><b>What NISAR makes possible next:</b> volume from area plus a shoreline height model; Toktogul and Rogun upstream for the whole Syr Darya and Amu Darya chain; centimetre ground motion of dams with interferometry.</p></div>""")
    S.append("""${F("06 · why us","Our valley, our water, NASA's radar")}
 <div style="position:absolute;left:52px;right:52px;top:150px;display:grid;grid-template-columns:1.1fr 1fr;gap:14px">
  <div class="glass" style="padding:24px;display:grid;gap:12px;align-content:start">
   <p style="font-size:16px">We are a team of four from Uzbekistan. The Fergana valley is home; the Aral is our country's best-known loss. We built the tool we wanted for our own region, then made it work for any place on Earth.</p>
   <p class="muted" style="font-size:14px">Reads NASA's calibrated NISAR files directly (box reads, no 2 GB downloads) · Lee speckle filter · water from HH, crops from HV · Sentinel-1, RADARSAT-1 and ICEYE for other frequencies and other years · ESA WorldCover and JRC water for context.</p>
  </div>
  <div class="glass mint-card" style="padding:24px;display:grid;gap:10px;align-content:start">
   <p class="lab">Open, and honest by design</p>
   <p style="font-size:15px">MIT licence. Every number comes from a script anyone can rerun, and every claim sits next to its outside check, including the places where radar is fooled.</p>
   <p style="font:400 13px/1.4 var(--mono)">github.com/tolipovmurodjon/falakus</p>
  </div>
 </div>""")
    return S


def main():
    t = bp.TEMPLATE.read_text(encoding="utf-8")
    head = t[: t.index('<main class="stage"')].replace("<style>", bp.CSS + "<style>", 1)
    tail = t[t.index('const stage=document.getElementById("stage");'):]
    tail = tail[: tail.index('document.getElementById("copy").onclick')]
    body = ["S.push(`" + s + "`);" for s in slides(nums())]
    html = (head + '<main class="stage" id="stage" aria-roledescription="slide deck"></main>\n<script>\nconst S=[];\n'
            'const F=(n,t)=>`<p class="eyebrow">${n}</p><h2 style="margin-top:12px">${t}</h2>`;\n'
            + "\n".join(body) + "\n" + tail + "</script>\n<title>Falakus Story Pitch</title>\n"
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;800&display=swap">\n')
    out = ROOT / "docs" / "deck" / "story.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out, len(body), "slides")


if __name__ == "__main__":
    main()
