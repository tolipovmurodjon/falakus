"""Register a Sentinel-1 RTC (C-band) mosaic of the last 12 days at Microsoft Planetary Computer (anonymous)
and write its tile template to data/explorer/s1_mosaic.json for the Live Earth page (web/explorer.js).

PC mosaic ids expire 24 h after registering (the number in the id is the expiry time), so the page uses this
file only when it was registered less than 20 h ago; otherwise it registers a mosaic itself.
PC's register endpoint answers 504 about half the time, so this retries. Re-run every few hours (cron) to keep it fresh:
    python tools/s1_register.py
Tiles exist from zoom 8 (lower zooms answer 204, checked 2026-11-15).
"""
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "explorer" / "s1_mosaic.json"
PC = "https://planetarycomputer.microsoft.com/api/data/v1/mosaic/"


def main():
    end = datetime.now(timezone.utc).replace(microsecond=0)
    start = end - timedelta(days=12)
    z = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
    body = json.dumps({"collections": ["sentinel-1-rtc"], "filter-lang": "cql2-json",
                       "filter": {"op": "anyinteracts", "args": [{"property": "datetime"}, {"interval": [z(start), z(end)]}]},
                       "sortby": [{"field": "datetime", "direction": "desc"}]}).encode()
    for attempt in range(6):
        try:
            req = urllib.request.Request(PC + "register", data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as r:
                mid = json.load(r)["searchid"]
            break
        except Exception as e:
            print("register failed:", e)
            time.sleep(3 + attempt * 3)
    else:
        raise SystemExit("Planetary Computer did not register the mosaic")
    tiles = (f"{PC}{mid}/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}@1x"
             "?collection=sentinel-1-rtc&assets=vv&rescale=0,0.5&colormap_name=gray&format=png")
    OUT.write_text(json.dumps({"tiles": [tiles], "start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d"),
                               "minzoom": 8, "registered": z(end),
                               "attribution": "Copernicus Sentinel-1 RTC (ESA), via Microsoft Planetary Computer"}, indent=1))
    print("wrote", OUT, mid)


if __name__ == "__main__":
    main()
