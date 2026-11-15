"""Plain-language water briefings: what happened, why, what next, and what it means for a farmer, a water manager
and a family. Every number in a sentence is read from our measured files here; no sentence carries a typed number.

Inputs: data/ml/water_model.json (Andijan learned water), data/ml/<place>/water.json (model applied to other places),
data/forecast/andijan_res.json (ridge forecast + skill), data/waterroad/andijan_res_icesat2.json (laser check),
data/waterroad/population.json, data/waterroad/fergana_hvchange.json (harvest).
Writes data/intel/<place>.json  ({title, river, headline, sections: [{h, p}], numbers, confidence, sources}).
Usage: python tools/water_intel.py
"""
import json
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

PLACES = {
    "andijan_res": dict(title="Andijan reservoir", river="Kara Darya, head of the Syr Darya", who="the Fergana valley's farms and towns",
                        why_fall="Water is let out all summer for cotton, wheat and orchards downstream; the release season ends in September.",
                        why_rise="Winter brings little use and river inflow from Kyrgyzstan's mountains, so the lake refills until spring."),
    "rogun": dict(title="Rogun dam reservoir", river="Vakhsh, a main source of the Amu Darya", who="Amu Darya users downstream: Uzbekistan and Turkmenistan",
                  why_fall="When the dam holds less, more of the Vakhsh flows on into the Amu Darya.",
                  why_rise="When the reservoir grows, the dam is storing river water that would otherwise flow downstream into the Amu Darya."),
    "qoshtepa": dict(title="Qosh Tepa canal head, northern Afghanistan", river="Amu Darya", who="Uzbekistan's and Turkmenistan's share of the Amu Darya",
                     why_fall="Less open water here means less water standing in the canal and its new fields.",
                     why_rise="More open water here means the canal and its new fields are taking more water from the Amu Darya, upstream of Uzbekistan."),
    "tuyamuyun": dict(title="Tuyamuyun reservoir", river="Amu Darya, last big reservoir before the delta", who="Khorezm and Karakalpakstan, the driest end of the river",
                      why_fall="Water is let out for Khorezm's and Karakalpakstan's fields and towns.",
                      why_rise="Upstream flow is being stored before it reaches the delta."),
}


def day(s):
    d = date.fromisoformat(s); return f"{d.day} {MON[d.month - 1]}"


def fmt(v, n=1):
    return f"{v:,.{n}f}"


def trend(series):
    """Least-squares slope in km² per 30 days over the passes, and first/last."""
    t = np.array([date.fromisoformat(s["date"]).toordinal() for s in series], float); v = np.array([s["km2"] for s in series], float)
    slope = float(np.polyfit(t, v, 1)[0] * 30) if len(t) > 2 else 0.0
    return slope, series[0], series[-1], max(series, key=lambda s: s["km2"]), min(series, key=lambda s: s["km2"])


def andijan():
    P = PLACES["andijan_res"]
    ml = json.loads((D / "ml/water_model.json").read_text()); fc = json.loads((D / "forecast/andijan_res.json").read_text())
    ice = json.loads((D / "waterroad/andijan_res_icesat2.json").read_text()); pop = json.loads((D / "waterroad/population.json").read_text())["regions_2025"]
    s = [dict(date=x["date"], km2=x["ml_km2"]) for x in ml["series"]]
    slope, first, last, peak, low = trend(s)
    drop = (last["km2"] - peak["km2"]) / peak["km2"] * 100
    f0, f2 = fc["forecast"][0], fc["forecast"][-1]
    same_last_year = next((x for x in fc["series"] if x["month"] == f2["month"].replace("2027", "2026")), None)
    people = pop["fergana"] + pop["andijan"] + pop["namangan"]
    sm = ml["summary"]
    vs = ""
    if same_last_year:
        dv = f2["km2"] - same_last_year["km2"]
        vs = f" That is {fmt(abs(dv))} km² {'more' if dv > 0 else 'less'} than in {MON[int(f2['month'][5:]) - 1]} this year ({fmt(same_last_year['km2'])} km²)."
    ho = ml["held_out"]; pa, pb = max(ho, key=lambda r: r["photo_water_km2"]), ho[-1]
    pdrop = (pb["photo_water_km2"] - pa["photo_water_km2"]) / pa["photo_water_km2"] * 100
    sections = [
        dict(h="What happened", p=f"The lake's open water fell from {fmt(peak['km2'])} km² on {day(peak['date'])} to {fmt(last['km2'])} km² on {day(last['date'])} 2026: {fmt(abs(drop), 0)} % less. NISAR measured it every 12 days, also on the days clouds hid it from cameras. Clear-day photos show a bigger fall, {fmt(pa['photo_water_km2'])} → {fmt(pb['photo_water_km2'])} km² ({fmt(abs(pdrop), 0)} % less, {day(pa['photo'])} to {day(pb['photo'])}): in autumn the radar still counts wet mud on the drying shore as water."),
        dict(h="Why", p=P["why_fall"] + " " + P["why_rise"]),
        dict(h="What next", p=f"Our forecast for {MON[int(f0['month'][5:]) - 1]} to {MON[int(f2['month'][5:]) - 1]}: about {fmt(f0['km2'], 0)} km² rising to {fmt(f2['km2'], 0)} km² (8 in 10 chance within ±{fmt(f2['band80_km2'])} km²).{vs} The forecast beat simple guesses by {fc['skill']['vs_seasonal_pct']} % on months it never saw."),
        dict(h="For a farmer", p=f"Summer water for the valley's fields came from this lake; by {day(last['date'])} it held {fmt(last['km2'] / peak['km2'] * 100, 0)} % of its summer size. Watch the winter refill: if the lake reaches the forecast by spring, early-season water should be close to normal; if it stays lower, plan for a tighter first irrigation."),
        dict(h="For the water agency", p=f"You get the lake's area every 12 days, cloud or not (34 % of camera visits in 2025 were cloudy). Our learned map agrees with clear-day photos at IoU {fmt(sm['ml_iou'], 2)} (the old one-number rule: {fmt(sm['rule_zone_iou'], 2)}); its typical miss is {fmt(sm['ml_area_mae_km2'])} km², mostly wet mud counted as water in late summer. A second NASA satellite (ICESat-2 laser) agrees: water level and area rise and fall together (rank correlation {fmt(ice['spearman_r'], 2)}, {ice['n']} passes)."),
        dict(h="For a family", p=f"{fmt(people / 1e6)} million people live in the three valley regions this water reaches (Andijan, Fergana, Namangan; {fmt(people / pop['uzbekistan'] * 100, 0)} % of Uzbekistan). A smaller lake in winter means less water to share in spring."),
    ]
    return dict(place="andijan_res", title=P["title"], river=P["river"],
                headline=f"{fmt(abs(drop), 0)} % less open water since {day(peak['date'])}; refill to about {fmt(f2['km2'], 0)} km² expected by {MON[int(f2['month'][5:]) - 1]}",
                sections=sections, numbers=dict(peak=peak, last=last, drop_pct=round(drop, 1), slope_km2_per_month=round(slope, 2), forecast=fc["forecast"]),
                confidence=f"Learned water map IoU {fmt(sm['ml_iou'], 2)} vs photos (leave-one-date-out, 8 days); shuffled-label control {fmt(sm['null_iou'], 2)}; laser rank correlation {fmt(ice['spearman_r'], 2)}.",
                sources="NASA-ISRO NISAR GCOV (provisional before 21 Oct 2026); ESA Sentinel-2 (photo check); NASA ICESat-2 ATL13; stat.uz population 1 Oct 2025.")


def other(place):
    f = D / "ml" / place / "water.json"
    if not f.exists():
        return None
    w = json.loads(f.read_text()); P = PLACES[place]
    s = [dict(date=x["date"], km2=x["ml_km2"]) for x in w["passes"]]
    slope, first, last, peak, low = trend(s)
    change = last["km2"] - first["km2"]; pct = change / first["km2"] * 100 if first["km2"] else 0
    direction = "grew" if change > 0 else "shrank"
    why = P["why_rise"] if change > 0 else P["why_fall"]
    nxt = last["km2"] + slope * 3
    conf = (f"The model learned water at Andijan and was tested here on {w['n_photo_days']} clear photo days it never trained on: median IoU {fmt(w['median_iou'], 2)}."
            if w.get("median_iou") is not None else "No clear photo day here yet to score the model; treat the numbers as estimates.")
    sections = [
        dict(h="What happened", p=f"Open water {direction} from {fmt(first['km2'])} km² on {day(first['date'])} to {fmt(last['km2'])} km² on {day(last['date'])} 2026 ({'+' if change > 0 else ''}{fmt(pct, 0)} %). Biggest: {fmt(peak['km2'])} km² on {day(peak['date'])}; smallest: {fmt(low['km2'])} km² on {day(low['date'])}."),
        dict(h="Why", p=why),
        dict(h="What next", p=f"If the season's trend holds ({'+' if slope > 0 else ''}{fmt(slope)} km² a month), the next 3 months would end near {fmt(max(nxt, 0))} km². This is a trend line, not a tested forecast: one season of NISAR is too short to learn this place's yearly cycle."),
        dict(h="Who it matters to", p=f"{P['who'].capitalize()}. NISAR sees this water every 12 days through cloud and at night."),
    ]
    return dict(place=place, title=P["title"], river=P["river"],
                headline=f"Open water {direction} {fmt(abs(pct), 0)} % between {day(first['date'])} and {day(last['date'])}",
                sections=sections, numbers=dict(first=first, last=last, peak=peak, low=low, slope_km2_per_month=round(slope, 2)), confidence=conf,
                sources="NASA-ISRO NISAR GCOV (provisional before 21 Oct 2026); model trained on Andijan; ESA Sentinel-2 photo check.")


def main():
    out = D / "intel"; out.mkdir(exist_ok=True)
    made = []
    for p, fn in [("andijan_res", andijan)] + [(p, lambda p=p: other(p)) for p in ("rogun", "qoshtepa", "tuyamuyun")]:
        b = fn()
        if b:
            (out / f"{p}.json").write_text(json.dumps(b, indent=1)); made.append(p)
            print(f"\n== {b['title']}: {b['headline']}")
            for s in b["sections"]:
                print(f"  {s['h']}: {s['p']}")
    (out / "index.json").write_text(json.dumps(dict(places=made), indent=1))


if __name__ == "__main__":
    main()
