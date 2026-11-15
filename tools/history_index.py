"""Write data/cases/history/index.json (then-vs-now pairs) from the *_meta.json / *_series.json that
tools/history_build.py wrote. what_changed sentences are written by a person who looked at both images
(kept here, next to the ids, so they can be re-checked against the pictures)."""
import json
from pathlib import Path

H = Path(__file__).resolve().parent.parent / "data" / "cases" / "history"

PLACES = {
    "aral": dict(place="Aral Sea, east basin of the Large Aral (Uzbekistan/Kazakhstan)", series=True),
    "andijan": dict(place="Andijan reservoir (Kampirravot), Uzbekistan/Kyrgyzstan border"),
    "tashkent": dict(place="Tashkent, Uzbekistan"),
    "urmia": dict(place="Lake Urmia, north-central lake and causeway (Iran)", series=True),
}
WHAT = json.loads((H / "what_changed.json").read_text())
BAND = ("RADARSAT-1 is C-band (5.6 cm wavelength), NISAR is L-band (24 cm): L-band sees deeper into vegetation and "
        "dry soil, so brightness differences are partly the sensor, not the ground. Water stays dark in both.")


def main():
    items = []
    for pid, cfg in PLACES.items():
        f = H / (f"{pid}_series.json" if cfg.get("series") else f"{pid}_meta.json")
        if not f.exists():
            print("missing", f.name)
            continue
        m = json.loads(f.read_text())
        rs1 = [fr for fr in m["frames"] if fr["sensor"].startswith("RADARSAT")]
        now = [fr for fr in m["frames"] if fr["sensor"].startswith("NISAR")][-1]
        then = max(rs1, key=lambda fr: (fr["coverage_pct"] >= 95, -int(fr["date"][:4])))  # earliest full frame
        items.append({
            "id": pid, "place": cfg["place"], "bbox": m["bbox"],
            "then": {"date": then["date"], "file": then["file"], "sensor": "RADARSAT-1 (CSA), C-band HH",
                     "note": "relative dB, uncalibrated", "beam": then["beam"], "scenes": then["scenes"]},
            "now": {"date": now["date"], "file": now["file"], "sensor": "NISAR (NASA-ISRO), L-band, NASA GIBS",
                    "granules": now["granules"], "coverage_pct": now["coverage_pct"]},
            "what_changed": WHAT[pid],
            "band_note": BAND,
            "series": f"{pid}_series.json" if cfg.get("series") else None,
            "sources": [
                {"name": "CSA RADARSAT-1 open archive (NRCan EODMS STAC, Open Government Licence - Canada)",
                 "url": "https://www.eodms-sgdot.nrcan-rncan.gc.ca/search/search?collections=Radarsat-1-L1-COG"},
                {"name": "NISAR L2 GCOV via NASA GIBS (layer NISAR_L2_Geocoded_Polarimetric_Covariance)",
                 "url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/NISAR_L2_Geocoded_Polarimetric_Covariance/default/"
                        f"{now['date']}/GoogleMapsCompatible_Level13/{{z}}/{{y}}/{{x}}.png"},
                {"name": "NASA CMR granule search (pass dates)", "url": "https://cmr.earthdata.nasa.gov/search/granules.json"
                 f"?collection_concept_id=C2854338529-ASF&bounding_box={','.join(map(str, m['bbox']))}"},
            ],
        })
    (H / "index.json").write_text(json.dumps({"items": items}, indent=1, ensure_ascii=False))
    print("wrote index.json with", len(items), "items")
    for pid, cfg in PLACES.items():  # series files: slim to the requested shape, keep extras
        if cfg.get("series") and (H / f"{pid}_series.json").exists():
            m = json.loads((H / f"{pid}_series.json").read_text())
            m["place"] = cfg["place"]
            (H / f"{pid}_series.json").write_text(json.dumps(m, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
