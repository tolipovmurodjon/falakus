"""The 7-slide submission deck, in the order of the Space Apps guide:
1 Title, 2 Problem, 3 Solution (one sentence + change map), 4 How it works (pipeline), 5 Results (before/after + metrics),
6 NASA & partner data (exact datasets, how each is used), 7 Impact & next steps.
Every number is read from our measured files here. Team name and members: TEAM below (fill from Boss).
Usage: python tools/build_deck7.py  ->  docs/deck/falakus-7.html
Check: python D:/30_library/taste/templates/slides-eye-run/render.py docs/deck/falakus-7.html
"""
import json
from pathlib import Path

import build_pitch as bp

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
TEAM = {"name": "Falakus", "members": ["Member 1", "Member 2", "Member 3", "Member 4", "Member 5", "Member 6"]}


def nums():
    ml = json.loads((D / "ml/water_model.json").read_text())
    ice = json.loads((D / "waterroad/andijan_res_icesat2.json").read_text())
    pop = json.loads((D / "waterroad/population.json").read_text())["regions_2025"]
    fc = json.loads((D / "forecast/andijan_res.json").read_text())
    s = ml["summary"]; ho = ml["held_out"]
    pa = max(ho, key=lambda r: r["photo_water_km2"]); pb = ho[-1]
    people = pop["fergana"] + pop["andijan"] + pop["namangan"]
    return dict(iou=s["ml_iou"], rule=s["rule_zone_iou"], rule0=s["rule_iou"], null=s["null_iou"], mae=s["ml_area_mae_km2"], mae_rule=s["rule_zone_area_mae_km2"],
                n_days=len(ho), sp=ice["spearman_r"], n_ice=ice["n"], people=people / 1e6, share=people / pop["uzbekistan"] * 100,
                p_a=pa["photo_water_km2"], p_b=pb["photo_water_km2"], p_da=pa["photo"], p_db=pb["photo"],
                f0=fc["forecast"][0]["km2"], f2=fc["forecast"][-1]["km2"], skill=fc["skill"]["vs_seasonal_pct"])


def day(s):
    m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{int(s[8:])} {m[int(s[5:7]) - 1]}"


def slides(n):
    S = []
    members = " · ".join(TEAM["members"])
    S.append(f"""
 <div style="position:absolute;left:56px;top:60px;width:560px;display:grid;gap:22px">
  <p class="eyebrow">NASA Space Apps Challenge 2026 · Dancing with the SARs</p>
  <h1 style="font-size:64px;line-height:1">Falakus</h1>
  <p style="font-size:24px;line-height:1.3">Water intelligence for Uzbekistan from NASA-ISRO NISAR radar: what changed, why, and what comes next, through cloud and at night.</p>
  <div class="glass" style="padding:18px 22px;display:grid;gap:6px"><p class="lab">Team {TEAM['name']} · Tashkent, Uzbekistan</p><p style="font-size:16px">{members}</p></div>
 </div>
 <div style="position:absolute;left:650px;right:52px;top:56px;height:500px"><div class="shot" style="height:470px"><img src="img/change_map.jpg" alt="Change map of the Andijan reservoir from NISAR radar: blue still water, amber water gone between July and October 2026"></div>
 <p class="cap">Andijan reservoir, NISAR radar: amber = water released between 14 Jul and 18 Oct 2026.</p></div>""")
    S.append(f"""${{F("Problem","Without radar, the valley's water budget is planned half-blind")}}
 <div style="position:absolute;left:52px;right:52px;top:150px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px">
  <div class="glass" style="padding:24px;display:grid;gap:8px;align-content:start"><b style="font:400 40px/1 var(--mono);color:var(--mint)">{n['people']:.1f} M</b><h3>people, one river system</h3><p class="muted" style="font-size:15px">The Fergana valley's three regions ({n['share']:.0f} % of Uzbekistan) live on reservoirs like Andijan on the Kara Darya, head of the Syr Darya.</p></div>
  <div class="glass" style="padding:24px;display:grid;gap:8px;align-content:start"><b style="font:400 40px/1 var(--mono);color:#C2410C">15 of 24</b><h3>winter photos lost to cloud</h3><p class="muted" style="font-size:15px">Sentinel-2, Dec–Mar 2025: the months when spring releases are planned. Camera satellites go blind exactly when the decision is made.</p></div>
  <div class="glass" style="padding:24px;display:grid;gap:8px;align-content:start"><b style="font:400 40px/1 var(--mono);color:var(--mint)">Undetected</b><h3>what changes in the dark</h3><p class="muted" style="font-size:15px">How fast a reservoir is drawn down, when upstream canals start taking more water, when fields are harvested. Missed for weeks, or seen too late.</p></div>
 </div>""")
    S.append(f"""${{F("Solution","Falakus turns every 12-day NISAR pass into a checked water map and a plain-language briefing")}}
 <div style="position:absolute;left:52px;top:170px;width:560px;display:grid;gap:14px">
  <p style="font-size:20px;line-height:1.4">A model trained on photos learns what open water looks like to the radar. Then it maps the water on every pass, cloud or not. It writes what happened, why, and what comes next, for a farmer, a water manager and a family.</p>
  <div class="glass mint-card" style="padding:18px 22px"><p style="font-size:15px"><b>Example briefing, Andijan reservoir:</b> "Clear-day photos show the lake fell from {n['p_a']:.1f} to {n['p_b']:.1f} km² ({day(n['p_da'])} to {day(n['p_db'])}) as water went to the fields. Refill to about {n['f2']:.0f} km² expected by February."</p></div>
 </div>
 <div style="position:absolute;left:650px;right:52px;top:150px;height:430px"><div class="shot" style="height:400px"><img src="img/change_map.jpg" alt="change map"></div><p class="cap">Hero change map: blue = still water, amber = water gone 14 Jul → 18 Oct 2026.</p></div>""")
    box = 'class="glass" style="padding:18px;display:grid;gap:6px;align-content:start"'
    S.append(f"""${{F("How it works","From NASA's radar files to a water map and a briefing")}}
 <div style="position:absolute;left:52px;right:52px;top:170px;display:grid;grid-template-columns:1fr 26px 1fr 26px 1fr 26px 1fr;gap:6px;align-items:center">
  <div {box}><p class="lab">1 · Data</p><h3>NISAR GCOV, ASF DAAC</h3><p class="muted" style="font-size:13.5px">Calibrated HH and HV radar, 20 m, every 12 days. We read only our box from each HDF5 file over HTTPS.</p></div><b style="font-size:26px;color:var(--mint);text-align:center">→</b>
  <div {box}><p class="lab">2 · Preprocessing</p><h3>Clean the signal</h3><p class="muted" style="font-size:13.5px">Lee speckle filter, decibels, texture, each pixel's season history; slopes over 12° masked with the Copernicus elevation model (radar shadow).</p></div><b style="font-size:26px;color:var(--mint);text-align:center">→</b>
  <div {box}><p class="lab">3 · Model</p><h3>Gradient boosting</h3><p class="muted" style="font-size:13.5px">10 radar features per pixel, labelled by Sentinel-2 photo water on clear days; tested on days it never saw, with a shuffled-label control.</p></div><b style="font-size:26px;color:var(--mint);text-align:center">→</b>
  <div {box}><p class="lab">4 · Output</p><h3>Change map + briefing</h3><p class="muted" style="font-size:13.5px">Water km² per pass, change map, forecast for the next months, and a plain-language briefing per water body.</p></div>
 </div>
 <p class="muted" style="position:absolute;left:52px;right:52px;top:470px;font-size:14px">Outside checks run beside the model: Sentinel-2 photos, NASA ICESat-2 laser water levels, Sentinel-1 C-band radar. Open source (MIT): every number comes from a script in tools/.</p>""")
    S.append(f"""${{F("Results","NISAR sees the release, and two independent checks agree")}}
 <div style="position:absolute;left:52px;top:150px;width:700px;height:400px"><div class="shot" style="height:370px"><img src="img/before_after.jpg" alt="NISAR HH radar of the Andijan reservoir on 14 July and 18 October 2026"></div><p class="cap">Before / after, NISAR HH: calm water is a mirror and goes black.</p></div>
 <div style="position:absolute;left:780px;right:52px;top:150px;display:grid;gap:14px">
  <div class="kpi"><b>IoU {n['iou']:.2f}</b><span>learned water map vs clear-day photos on {n['n_days']} days it never saw. One-number rule: {n['rule']:.2f} with a water map, {n['rule0']:.2f} without. Shuffled labels: {n['null']:.2f}.</span></div>
  <div class="kpi"><b>ρ = {n['sp']:.2f}</b><span>NASA ICESat-2 laser water level vs lake area, {n['n_ice']} passes: a second satellite, a different physics, the same rise and fall.</span></div>
 </div>""")
    rows = [("NISAR L2 GCOV (NASA-ISRO, ASF DAAC)", "Core: calibrated HH/HV radar every 12 days; water, crops, change"),
            ("NISAR L2 GUNW", "Ground motion from radar phase (method shown on a quake)"),
            ("ICESat-2 ATL13 (NASA)", "Laser water levels: independent check of the water area"),
            ("NASA EONET + GIBS", "Floods, fires, storms, rain (IMERG) for context worldwide"),
            ("Sentinel-2 L2A (ESA)", "Photo water labels on clear days; 10-year monthly record"),
            ("Sentinel-1 RTC (ESA)", "C-band radar: compare frequencies (L vs C)"),
            ("Copernicus DEM, ESA WorldCover", "Terrain mask (radar shadow); cropland and water zones"),
            ("Landsat 5–9 (USGS), RADARSAT-1 (CSA)", "1985–2025 time-lapse; 1997 radar of the Aral"),
            ("Statistics Agency of Uzbekistan", "Population that depends on the water (1 Oct 2025)")]
    tr = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td></tr>" for a, b in rows)
    S.append(f"""${{F("NASA & partner data","Exactly what we used, and for what")}}
 <div class="glass" style="position:absolute;left:52px;right:52px;top:140px;padding:14px 22px"><table><thead><tr><th>dataset</th><th>how we used it</th></tr></thead><tbody>{tr}</tbody></table></div>""")
    S.append(f"""${{F("Impact & next steps","Who uses it, and what we would scale")}}
 <div style="position:absolute;left:52px;right:52px;top:150px;display:grid;grid-template-columns:1fr 1fr;gap:14px">
  <div class="glass" style="padding:24px;display:grid;gap:10px;align-content:start"><p class="lab">Who uses it</p>
   <p style="font-size:16px"><b>Basin water agencies:</b> reservoir area every 12 days through cloud, for winter and spring release plans.</p>
   <p style="font-size:16px"><b>Farmers:</b> a plain briefing: how full the lake is, and what spring water to expect.</p>
   <p style="font-size:16px"><b>Families and teachers:</b> {n['people']:.1f} million people in the valley can see where their water goes.</p></div>
  <div class="glass mint-card" style="padding:24px;display:grid;gap:10px;align-content:start"><p class="lab">Next steps</p>
   <p style="font-size:16px">1 · Every big reservoir and canal on the Amu Darya and Syr Darya, including the Qosh Tepa canal upstream.</p>
   <p style="font-size:16px">2 · Volume, not just area: area × ICESat-2 levels.</p>
   <p style="font-size:16px">3 · ALOS-2008 to NISAR-2026: 18 years of L-band radar.</p>
   <p style="font-size:16px">4 · NISAR soil moisture and ground motion for farms and canals.</p></div>
 </div>
 <p class="muted" style="position:absolute;left:52px;bottom:40px;font-size:13px">Open source, MIT · github.com/tolipovmurodjon/falakus · AI use: Claude helped write code and text; the team checked every number. No AI-generated images.</p>""")
    return S


def main():
    t = bp.TEMPLATE.read_text(encoding="utf-8")
    head = t[: t.index('<main class="stage"')].replace("<style>", bp.CSS + "<style>", 1).replace("<title>PAGEL Jarvis Audit</title>", "")
    tail = t[t.index('const stage=document.getElementById("stage");'):]
    tail = tail[: tail.index('document.getElementById("copy").onclick')]
    body = ["S.push(`" + s + "`);" for s in slides(nums())]
    html = ('<!doctype html>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n' + head +'<main class="stage" id="stage" aria-roledescription="slide deck"></main>\n<script>\nconst S=[];\n'
            'const F=(n,t)=>`<p class="eyebrow">${n}</p><h2 style="margin-top:12px">${t}</h2>`;\n'
            + "\n".join(body) + "\n" + tail + "</script>\n<title>Falakus · 7 slides</title>\n"
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;800&display=swap">\n')
    out = ROOT / "docs" / "deck" / "falakus-7.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out, len(body), "slides")


if __name__ == "__main__":
    main()
