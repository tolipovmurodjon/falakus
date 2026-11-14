"""Bake the story's Sentinel-2 photos into local files, cut to each chapter's box, so the story never depends on a live
photo service (a timeout once showed the clear basemap on the 'Cloudy day' tab).
Writes data/waterroad/photo_<key>.png and data/waterroad/photos.json (date, scene cloud %, cloud % inside the box).
Usage: python tools/bake_photos.py
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nisar_tile_server import sentinel2_photo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
AJ = [73.02795, 40.68392, 73.24205, 40.84608]
FG = json.loads((ROOT / "data/science/fergana/frames.json").read_text())["bbox"]
JOBS = {"andijan_oct6": (AJ, "2026-10-04", "2026-10-08", True), "andijan_cloudy": (AJ, "2026-09-24", "2026-09-24", False),
        "andijan_midoct": (AJ, "2026-10-12", "2026-10-26", True), "fergana_oct": (FG, "2026-10-12", "2026-10-29", True)}
out = json.loads((ROOT / "data/waterroad/photos.json").read_text()) if (ROOT / "data/waterroad/photos.json").exists() else {}
for key, (b, a, z, clear) in JOBS.items():
    f = ROOT / "data/waterroad" / f"photo_{key}.png"
    if f.exists() and key in out:
        continue
    try:
        j = sentinel2_photo(*b, a, z, clear)
        box = j.get("box")
        if not box:
            print(key, "no scene"); continue
        f.write_bytes(urllib.request.urlopen(box["url"], timeout=180).read())
        out[key] = {k: v for k, v in box.items() if k != "url"}; out[key]["bbox"] = b
        print(key, out[key], f.stat().st_size // 1024, "KB", flush=True)
    except Exception as ex:
        print(key, "fail", str(ex)[:100])
(ROOT / "data/waterroad/photos.json").write_text(json.dumps(out, indent=1))
