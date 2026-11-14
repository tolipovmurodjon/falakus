"""Build the 10-slide pitch deck (Eye Run style) from the template and our real app screenshots.

Usage: python tools/build_pitch.py   ->  docs/deck/pitch.html   (check: python D:/30_library/taste/templates/slides-eye-run/render.py docs/deck/pitch.html)
Images live in docs/deck/img/ (copied from the app's own screenshots). Every number on the slides comes from our data files.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path("D:/30_library/taste/templates/slides-eye-run/template.html")

CSS = """<style>
.shot{border-radius:18px;overflow:hidden;box-shadow:0 14px 34px -18px rgba(15,22,48,.45);border:1px solid rgba(255,255,255,.9);background:#fff}
.shot img{display:block;width:100%;height:100%;object-fit:cover}
.cap{font:400 11px/1.4 var(--mono);color:var(--ink-3);margin-top:8px}
.tile{padding:14px;border-radius:20px;display:grid;grid-template-rows:140px auto auto auto;gap:7px}
.tile .shot{height:140px}
.tile b{font:400 21px/1 var(--mono);color:var(--mint)}
.tile h4{margin:0;font-size:15px;font-weight:800}
.tile p{font-size:12.5px;line-height:1.4;color:var(--ink-2)}
.t30{list-style:none;margin:0;padding:0;display:grid;gap:5px}
.t30 li{display:grid;grid-template-columns:26px 1fr auto;gap:6px;font-size:13px;line-height:1.3;align-items:baseline}
.t30 li i{font:400 11px/1 var(--mono);color:var(--ink-3);font-style:normal}
.t30 li s{text-decoration:none;font:400 10px/1 var(--mono);padding:3px 6px;border-radius:99px;background:rgba(15,22,48,.06);color:var(--ink-2)}
.t30 li s.on{background:var(--mint-s);color:var(--mint)}
</style>
"""

# (thing, how radar sees it, built in the app?)
TOP30 = {
    "Water": [
        ("Open water extent", "calm water = mirror, darkest pixel", True),
        ("Reservoir filling and emptying", "water area every 12 days", True),
        ("Floods under cloud", "dark new water after a storm", False),
        ("Flooded forest and towns", "water + trunk or wall = double bounce, very bright", False),
        ("Rice paddies flooded", "standing water, then plants grow through", True),
        ("Shrinking lakes and seas", "shoreline moves over years", True),
        ("Rivers changing course", "dark channel moves between passes", False),
        ("Wetlands by season", "HH bright when flooded vegetation", False),
        ("Lake ice on and off", "ice is rough and bright, water dark", False),
        ("Sea ice edge", "ice texture vs open sea", False),
    ],
    "Land and plants": [
        ("Crop growth stage", "HV rises as stems and leaves grow", True),
        ("Harvest date", "HV drops the week a field is cut", False),
        ("Forest loss and logging", "HV drops when trees are gone", False),
        ("Burn scars through smoke", "canopy lost, HV and texture change", True),
        ("Forest biomass", "24 cm L-band reaches trunks", False),
        ("Soil moisture", "wet soil = higher dielectric = brighter", False),
        ("Irrigated vs dry fields", "watered fields stay bright", False),
        ("Moving sand dunes", "bright dune faces shift", False),
        ("Wet vs dry snow", "melt water absorbs the pulse", False),
        ("Glacier flow speed", "pixel offsets between passes (GOFF)", False),
    ],
    "Built, ground and sea": [
        ("City growth", "new walls = new double bounce", True),
        ("New construction", "a bright spot that was not there", False),
        ("Building damage after a quake", "coherence lost between passes", False),
        ("Earthquake ground motion", "interferogram, cm per colour band", True),
        ("Sinking ground from pumping", "slow phase change over months", False),
        ("Landslides", "debris texture changes, anomaly test", True),
        ("Volcanoes and lava flows", "new rough lava, ground swelling", True),
        ("Dams and embankments", "mm motion of the structure", False),
        ("Ships at sea, day and night", "steel hull = bright point on dark sea", True),
        ("Oil-slick candidates", "oil calms waves = dark streak", True),
    ],
}

HIRES = [
    ("Each aircraft, by its shape", "wings, tail, engines visible at 0.5 m: count and type, not just 'plane-sized'"),
    ("Ship length, type and wake", "tanker vs container ship; the wake shows direction and speed"),
    ("Cars and trucks", "parking lots, border queues, mine haul trucks"),
    ("Shipping containers in ports", "stacks and empty yards: trade activity"),
    ("Damage, building by building", "a collapsed roof, not a 20 m pixel"),
    ("Oil tank fill level", "floating roof shadow inside the tank"),
    ("Rail cars and bridges", "trains on sidings, bridge spans"),
    ("Mine pits and stockpiles", "volumes change from pass to pass"),
    ("Construction step by step", "foundations, cranes, floors"),
    ("Small boats and fishing fleets", "too small for 10 m pixels"),
]


def top30_html():
    cols = []
    n = 0
    for group, rows in TOP30.items():
        items = []
        for thing, how, built in rows:
            n += 1
            tag = '<s class="on">in app</s>' if built else "<s>possible</s>"
            items.append(f'<li><i>{n:02d}</i><span><b style="font-weight:600">{thing}</b><br><span class="muted" style="font-size:11.5px">{how}</span></span>{tag}</li>')
        cols.append(f'<div class="glass" style="padding:16px 18px"><p class="lab">{group}</p><ul class="t30">{"".join(items)}</ul></div>')
    built = sum(b for rows in TOP30.values() for *_, b in rows)
    return "".join(cols), built


SLIDES = []

SLIDES.append("""
 <div style="position:absolute;left:56px;top:56px;width:470px;display:grid;gap:20px">
  <p class="eyebrow">Falakus · NASA Space Apps 2026 · Dancing with the SARs</p>
  <h1>Clouds and night blind every camera. Radar keeps watching.</h1>
  <p class="muted" style="font-size:17px">On 31 Aug 2026, five days after a rock-ice avalanche in Langtang, Nepal, the Sentinel-2 camera saw cloud. NASA-ISRO NISAR saw the valley.</p>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
   <div class="kpi warn"><b>89 %</b><span>cloud in the camera photo, 31 Aug</span></div>
   <div class="kpi"><b>16,691</b><span>NISAR radar frames on our world map</span></div>
   <div class="kpi"><b>29 y</b><span>of radar history, 1997 to 2026</span></div>
  </div>
 </div>
 <div style="position:absolute;left:560px;right:52px;top:56px;height:520px">
  <div class="shot" style="height:470px"><img src="img/langtang-cloud.jpg" alt="NISAR radar of Langtang on the left, cloudy Sentinel-2 photo on the right, same day"></div>
  <p class="cap">Our app, live: drag the white bar. Left NISAR radar, right the camera, same day.</p>
 </div>
""")

SLIDES.append("""${F("01 · the challenge","What NASA asked, and how Falakus answers")}
 <div class="glass" style="position:absolute;left:52px;right:52px;top:150px;padding:20px 26px">
 <table><thead><tr><th>the challenge asks</th><th>Falakus</th></tr></thead><tbody>
  <tr><td><b>An interactive app on NISAR radar data</b></td><td>a world map of 16,691 NISAR frames plus calibrated 10–20 m boxes read straight from NASA's files</td></tr>
  <tr><td><b>Track surface change at places around the world, over time</b></td><td>a drag-to-compare swipe, a time player over every pass, 16 tour stops, and "click anywhere"</td></tr>
  <tr><td><b>Turn radar into actionable insight</b></td><td>one number and one plain sentence per place, plus who acts on it</td></tr>
  <tr><td><b>Explain the physical drivers</b></td><td>"why it looks like this": mirror water, double bounce, volume scattering, phase</td></tr>
  <tr><td><b>Which polarization shows the change</b></td><td>a switch between HH, HV and false colour on every swipe</td></tr>
  <tr><td><b>Other sensors, history, context</b></td><td>RADARSAT-1 (1997), Sentinel-1 (C-band), Sentinel-2 photos, USGS quakes, NASA EONET events</td></tr>
  <tr><td><b>Open source, easy to use</b></td><td>MIT-licensed repo, every number reproducible from a script</td></tr>
 </tbody></table></div>
""")

SLIDES.append("""${F("02 · drag to compare","A sea that is gone, in one drag")}
 <div style="position:absolute;left:52px;top:150px;width:700px;height:440px">
  <div class="shot" style="height:400px"><img src="img/aral.jpg" alt="Aral Sea: RADARSAT-1 radar 1997 left, NISAR radar 2026 right"></div>
  <p class="cap">Left: Canada's RADARSAT-1, 16 Jul 1997 (open archive). Right: NISAR, Oct 2026. Same place, both radar.</p>
 </div>
 <div style="position:absolute;left:780px;right:52px;top:150px;display:grid;gap:12px">
  <div class="glass mint-card" style="padding:22px"><b style="font:400 42px/1 var(--mono)">&le; 0.93 km&sup2;</b><p style="margin-top:10px;font-size:14.5px">of open water left in a 1,600 km&sup2; box of the eastern basin, in every NISAR pass from June to October 2026. In 1997 it was open sea.</p></div>
  <div class="glass" style="padding:18px 20px"><p class="lab">Why 1997 and 2026 compare fairly</p><p style="font-size:14px">Both satellites bring their own pulse, so cloud and sunlight do not matter. Calm water is a mirror (dark); dry seabed and salt crust are rough (bright).</p></div>
  <div class="glass" style="padding:18px 20px"><p class="lab">Our home story</p><p style="font-size:14px">Upstream cotton and rice took the Amu Darya's water. The tour follows it: Rogun, the Qosh Tepa canal, the Fergana fields, the Aral.</p></div>
 </div>
""")

SLIDES.append("""${F("03 · a disaster, the next pass","Where the valley changed, while cameras saw cloud")}
 <div style="position:absolute;left:52px;top:150px;width:700px;height:440px">
  <div class="shot" style="height:400px"><img src="img/langtang-change.jpg" alt="Langtang: NISAR before and after the collapse, changed pixels marked"></div>
  <p class="cap">NISAR 19 Aug (before) and 31 Aug (after the 26 Aug collapse). Orange = brighter, violet = darker.</p>
 </div>
 <div style="position:absolute;left:780px;right:52px;top:150px;display:grid;gap:12px">
  <div class="kpi"><b style="color:var(--mint)">0.9 km&sup2;</b><span>changed more than 4&times; its own normal 12-day wobble across the collapse</span></div>
  <div class="kpi"><b>0.0&ndash;0.2 km&sup2;</b><span>same test on the summer pairs before it: the control</span></div>
  <div class="glass" style="padding:18px 20px"><p class="lab">The expert move</p><p style="font-size:14px">Counting every pixel that changed by 3 dB could not tell this pair from a quiet one (23.7 vs 22.8 km&sup2;). So each pixel is judged against its own history: a time-series anomaly test.</p></div>
 </div>
""")

SLIDES.append("""${F("04 · the physics in three lines","Why the radar looks like this")}
 <div style="position:absolute;left:52px;right:52px;top:160px;display:grid;grid-template-columns:1fr 1fr 1.25fr;gap:14px">
  <div class="glass" style="padding:24px;display:grid;gap:12px;align-content:start"><span class="chip c-blue">surface</span><h3>Calm water is a mirror</h3><p class="muted" style="font-size:15px">The 24 cm pulse bounces away, so lakes and floods are the darkest thing on the map. Wet soil has a higher dielectric constant, so it is brighter than dry soil.</p></div>
  <div class="glass" style="padding:24px;display:grid;gap:12px;align-content:start"><span class="chip c-amber">double bounce &middot; volume</span><h3>Walls shine, leaves glow in HV</h3><p class="muted" style="font-size:15px">A wall and a street make a corner that sends the pulse straight back (HH bright). Leaves and branches scatter it and turn it sideways (HV). Cut or burned forest goes dark in HV.</p></div>
  <div class="glass" style="padding:18px;display:grid;gap:10px;align-content:start"><span class="chip c-violet">phase &middot; interferometry</span><div class="shot" style="height:200px"><img src="img/panama.jpg" alt="Panama control pair vs quake pair"></div><p style="font-size:14px">Each rainbow band = <b>11.9 cm</b>. Panama M7.7: about <b>1 m</b> of ground motion. Left: the control pair with no quake.</p></div>
 </div>
""")

SLIDES.append("""${F("05 · 30 things radar finds at 10&ndash;20 m","Free, global, every 12 days, through cloud and night")}
 <div style="position:absolute;left:52px;right:52px;top:140px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px">TOP30</div>
 <p class="cap" style="position:absolute;left:52px;bottom:70px">NISAR L-band (24 cm) and Sentinel-1 C-band (5.6 cm). "in app" = shown with real data in Falakus today (BUILT of 30).</p>
""")

SLIDES.append("""${F("06 · zoom from 10 m to 0.5 m","What free commercial radar adds")}
 <div style="position:absolute;left:52px;top:150px;width:640px" class="glass"><div style="padding:18px 22px">
  <p class="lab">Umbra · Capella · ICEYE open data (CC-BY 4.0, 0.25&ndash;1 m)</p>
  <ul class="t30" style="gap:7px">HIRES</ul></div></div>
 <div style="position:absolute;left:716px;right:52px;top:150px;display:grid;gap:12px">
  <div class="glass mint-card" style="padding:22px"><b style="font:400 40px/1 var(--mono)">400&times;</b><p style="margin-top:10px;font-size:14.5px">more pixels per km&sup2; at 0.5 m than at 10 m. A plane becomes a shape instead of one bright dot.</p></div>
  <div class="glass" style="padding:18px 20px"><p class="lab">How we use it</p><p style="font-size:14px">As proof: where a free 0.5 m scene overlaps our sites, it shows whether our 10 m ship and plane detectors found the real objects.</p></div>
  <div class="glass" style="padding:18px 20px"><p class="lab">Honest limit</p><p style="font-size:14px">The companies pick the sites, not us. For any place on Earth, NISAR and Sentinel-1 at 10&ndash;20 m stay the free global layer.</p></div>
 </div>
""")

SLIDES.append("""${F("07 · detectors and machine learning","Each one checked, none placed by hand")}
 <div style="position:absolute;left:52px;right:52px;top:150px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
  <div class="glass tile"><div class="shot"><img src="img/ships.jpg" alt="Ship watch Singapore"></div><b>601&ndash;650</b><h4>Ships, day and night</h4><p>Steel hulls are bright points on a dark sea. Singapore per calm pass; 7 chokepoints including Hormuz at night.</p></div>
  <div class="glass tile"><div class="shot"><img src="img/slick.png" alt="Baku slick candidates"></div><b>91 km&sup2;</b><h4>Oil-slick candidates</h4><p>Oil calms waves, so slicks are dark streaks: a 21 km plume from Neft Da&#351;lar&#305;, 23 Oct. Labelled candidates, not proof.</p></div>
  <div class="glass tile"><div class="shot"><img src="img/airport.png" alt="Airport detection steps"></div><b>12</b><h4>Plane-sized objects</h4><p>Tashkent airport: bright metal on smooth concrete, minus anything bright on most passes.</p></div>
  <div class="glass tile"><div class="shot"><img src="img/tashkent.jpg" alt="ML land cover"></div><b>66 % vs 36 %</b><h4>ML land cover</h4><p>A Random Forest on NISAR time series, tested on a place it never saw against ESA WorldCover. Beats fixed rules at 3 of 4 places.</p></div>
 </div>
""")

SLIDES.append("""${F("08 · how we know it is right","Every number has an outside check")}
 <div class="glass" style="position:absolute;left:52px;right:52px;top:150px;padding:22px 26px">
 <table><thead><tr><th>claim</th><th>outside check</th><th>result</th></tr></thead><tbody>
  <tr><td><b>Tashkent built-up share</b></td><td>fixed dB rule vs the city's known footprint</td><td>35.8 % vs about 37 %</td></tr>
  <tr><td><b>The ground moved at Panama</b></td><td>a control pair on the same orbit track, no quake</td><td>straight bands (air) vs bunched bands (fault)</td></tr>
  <tr><td><b>Land cover by ML</b></td><td>ESA WorldCover 10 m, leave-one-place-out</td><td>Fergana 66 %, Tashkent 60 %, Andijan 58 % (rules: 36 / 48 / 26 %)</td></tr>
  <tr><td><b>Where the ML fails</b></td><td>the same test on the Aral seabed</td><td>0 %: it never saw desert in training. Shown, not hidden</td></tr>
  <tr><td><b>Radar through cloud</b></td><td>Sentinel-2 photo on the day of the NISAR pass</td><td>89 % cloud (Langtang, 31 Aug)</td></tr>
  <tr><td><b>Data status</b></td><td>NASA's own labels</td><td>NISAR provisional before 21 Oct 2026; data gap 27 Jul&ndash;10 Aug</td></tr>
 </tbody></table></div>
""")

SLIDES.append("""${F("09 · who acts on it","From a radar echo to a decision")}
 <div style="position:absolute;left:52px;right:52px;top:150px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 28px/1 var(--mono);color:var(--mint)">1.5&ndash;19 km&sup2;</b><h3>Water managers</h3><p class="muted" style="font-size:14px">Open water in the Andijan reservoir over 11 passes, through cloud, every 12 days, for Uzbekistan's and Kyrgyzstan's water agencies.</p></div>
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 28px/1 var(--mono);color:var(--mint)">next pass</b><h3>Rescue teams</h3><p class="muted" style="font-size:14px">Where a valley changed after a landslide or quake, while cameras see cloud. Click anywhere and get a 20 m analysis in minutes.</p></div>
  <div class="glass" style="padding:22px;display:grid;gap:8px;align-content:start"><b style="font:400 28px/1 var(--mono);color:var(--mint)">day + night</b><h3>Ports and coast guards</h3><p class="muted" style="font-size:14px">Ship queues at chokepoints and slick candidates at sea, every pass: a reason to send a boat.</p></div>
 </div>
 <div class="glass mint-card" style="position:absolute;left:52px;right:52px;top:420px;padding:20px 26px;display:grid;grid-template-columns:1fr auto;gap:20px;align-items:center">
  <p style="font-size:17px">Falakus is open source: any place on Earth, NISAR's 10&ndash;20 m radar, an honest number and a plain sentence.</p>
  <p style="font:400 13px/1.4 var(--mono)">github.com/tolipovmurodjon/falakus</p>
 </div>
""")


def main():
    t = TEMPLATE.read_text(encoding="utf-8")
    head = t[: t.index('<main class="stage"')].replace("<style>", CSS + "<style>", 1)
    tail = t[t.index('const stage=document.getElementById("stage");'):]
    tail = tail[: tail.index('document.getElementById("copy").onclick')]
    cols, built = top30_html()
    hires = "".join(f'<li><i>{i + 1:02d}</i><span><b style="font-weight:600">{a}</b><br><span class="muted" style="font-size:11.5px">{b}</span></span></li>'
                    for i, (a, b) in enumerate(HIRES))
    body = []
    for s in SLIDES:
        s = s.replace("TOP30", cols).replace("BUILT", str(built)).replace("HIRES", hires)
        body.append("S.push(`" + s + "`);")
    html = (head + '<main class="stage" id="stage" aria-roledescription="slide deck"></main>\n<script>\nconst S=[];\n'
            'const F=(n,t)=>`<p class="eyebrow">${n}</p><h2 style="margin-top:12px">${t}</h2>`;\n'
            + "\n".join(body) + "\n" + tail + "</script>\n<title>Falakus Pitch</title>\n"
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;800&display=swap">\n')
    out = ROOT / "docs" / "deck" / "pitch.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out, len(SLIDES), "slides,", built, "of 30 in the app")


if __name__ == "__main__":
    main()
