"""Check NASA EONET event points against the country in the event title, and repair swapped coordinates.

Found 15 Nov 2026: many GDACS flood polygons in the EONET v3 feed list [lat, lon] instead of GeoJSON's [lon, lat]
("Flood in Poland" at lon 53.1, lat 17.9 is in Yemen; swapped it is 53.1 N, 17.9 E, in Poland).
Rule: keep a point inside its country's box (1.5 deg margin); if only the swapped point fits, swap it and mark
coords="swapped_fixed"; if neither fits, mark coords="unverified" so it is never measured or shown as fact.
Country boxes are approximate [W, S, E, N] extents.
"""
import re

BOX = {
    "Albania": (19, 39.6, 21.1, 42.7), "Algeria": (-8.7, 19, 12, 37.1), "Angola": (11.6, -18.1, 24.1, -4.4), "Argentina": (-73.6, -55.1, -53.6, -21.8),
    "Australia": (112.9, -43.7, 153.7, -10.6), "Bangladesh": (88, 20.6, 92.7, 26.7), "Bhutan": (88.7, 26.7, 92.1, 28.4), "Brazil": (-74, -33.8, -34.8, 5.3),
    "Bulgaria": (22.3, 41.2, 28.6, 44.2), "Cambodia": (102.3, 10.4, 107.7, 14.7), "Canada": (-141, 41.7, -52.6, 83.1), "Central African Republic": (14.4, 2.2, 27.5, 11.1),
    "Chad": (13.5, 7.4, 24, 23.5), "Chile": (-75.7, -56, -66.4, -17.5), "China": (73.5, 18.2, 134.8, 53.6), "Colombia": (-79, -4.2, -66.9, 12.5),
    "Costa Rica": (-85.95, 8, -82.5, 11.2), "Cote d'Ivoire": (-8.6, 4.3, -2.5, 10.7), "Croatia": (13.5, 42.4, 19.5, 46.6), "Cyprus": (32.2, 34.5, 34.6, 35.7),
    "Democratic Republic of Congo": (12.2, -13.5, 31.3, 5.4), "Dominican Republic": (-72, 17.5, -68.3, 20), "Ecuador": (-92.1, -5, -75.2, 1.5), "Egypt": (24.7, 22, 36.9, 31.7),
    "El Salvador": (-90.1, 13.1, -87.7, 14.5), "France": (-5.2, 41.3, 9.6, 51.1), "Germany": (5.9, 47.3, 15, 55.1), "Ghana": (-3.3, 4.7, 1.2, 11.2),
    "Guatemala": (-92.3, 13.7, -88.2, 17.8), "Guinea": (-15.1, 7.2, -7.6, 12.7), "Honduras": (-89.4, 13, -83.1, 16.5), "Iceland": (-24.5, 63.3, -13.5, 66.6),
    "India": (68.1, 6.7, 97.4, 35.5), "India, Nepal": (68.1, 6.7, 97.4, 35.5), "Indonesia": (95, -11, 141, 6), "Iraq": (38.8, 29.1, 48.6, 37.4), "Ireland": (-10.5, 51.4, -6, 55.4),
    "Islamic Republic of Iran": (44, 25, 63.3, 39.8), "Israel": (34.2, 29.5, 35.9, 33.3), "Italy": (6.6, 36.6, 18.5, 47.1), "Japan": (122.9, 24, 153.9, 45.6),
    "Jordan": (34.9, 29.2, 39.3, 33.4), "Kenya": (33.9, -4.7, 41.9, 5), "Libya": (9.3, 19.5, 25.2, 33.2), "Malaysia": (99.6, 0.8, 119.3, 7.4), "Maldives": (72.6, -0.7, 73.8, 7.1),
    "Mali": (-12.2, 10.2, 4.3, 25), "Mauritania": (-17.1, 14.7, -4.8, 27.3), "Mexico": (-118.4, 14.5, -86.7, 32.7), "Morocco": (-17.1, 21, -1, 35.9),
    "Myanmar": (92.2, 9.8, 101.2, 28.5), "Nepal": (80, 26.3, 88.2, 30.5), "Nicaragua": (-87.7, 10.7, -82.6, 15), "Nigeria": (2.7, 4.2, 14.7, 13.9),
    "Panama": (-83.1, 7.2, -77.2, 9.7), "Paraguay": (-62.7, -27.6, -54.3, -19.3), "Peru": (-81.4, -18.4, -68.7, -0.03), "Philippines": (116.9, 4.6, 126.6, 21.1),
    "Poland": (14.1, 49, 24.2, 54.9), "Portugal": (-31.3, 32.6, -6.2, 42.2), "Romania": (20.2, 43.6, 29.7, 48.3), "Senegal": (-17.6, 12.3, -11.3, 16.7),
    "Slovenia": (13.4, 45.4, 16.6, 46.9), "Somalia": (40.9, -1.7, 51.4, 12), "South Africa": (16.4, -34.9, 32.9, -22.1), "South Korea": (124.6, 33.1, 131.9, 38.6),
    "Spain": (-18.2, 27.6, 4.4, 43.8), "Sri Lanka": (79.6, 5.9, 81.9, 9.9), "Syria": (35.7, 32.3, 42.4, 37.3), "Thailand": (97.3, 5.6, 105.7, 20.5),
    "Tunisia": (7.5, 30.2, 11.6, 37.4), "Turkiye": (25.6, 35.8, 44.8, 42.1), "Uganda": (29.5, -1.5, 35, 4.3), "Ukraine": (22.1, 44.3, 40.2, 52.4),
    "Uruguay": (-58.5, -35, -53.1, -30.1), "Venezuela": (-73.4, 0.6, -59.8, 12.2), "Vietnam": (102.1, 8.4, 109.5, 23.4),
}
M = 1.5


def country(title):
    t = re.sub(r"^(Flood|Floods) in ", "", title or "")
    t = re.sub(r"\s+\d+$", "", t).replace("&#039;", "'")
    if re.match(r"^T.{1,3}rkiye$", t):
        t = "Turkiye"
    return t if t in BOX else None


def inside(c, lon, lat):
    w, s, e, n = BOX[c]
    return w - M <= lon <= e + M and s - M <= lat <= n + M


def fix(ev):
    """Return a copy of the event with checked coordinates and a 'coords' status."""
    e = dict(ev); c = country(e.get("title"))
    if not c or e.get("lon") is None:
        e["coords"] = "unchecked"; return e
    lon, lat = e["lon"], e["lat"]
    if inside(c, lon, lat):
        e["coords"] = "ok"
    elif abs(lon) <= 90 and inside(c, lat, lon):
        e["lon"], e["lat"], e["coords"] = lat, lon, "swapped_fixed"
        if e.get("track"):
            e["track"] = [[p[1], p[0]] for p in e["track"]]
    else:
        e["coords"] = "unverified"
    return e


if __name__ == "__main__":
    import collections
    import json
    from pathlib import Path
    d = json.loads((Path(__file__).resolve().parent.parent / "data/eonet_v2.json").read_text())
    ev = d.get("events", d) if isinstance(d, dict) else d
    fx = [fix(e) for e in ev]
    print(collections.Counter(e["coords"] for e in fx))
    print("floods:", collections.Counter(e["coords"] for e in fx if "lood" in str(e.get("category", ""))))
    for e in fx:
        if e["coords"] == "unverified":
            print("  unverified:", e["title"][:40], round(e["lon"], 2), round(e["lat"], 2))
