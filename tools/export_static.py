"""Static copy of the judge-facing pages for GitHub Pages (no Python server).

Fetches every page and data file from the running local server (http://127.0.0.1:8765) into dist/, keeping the same
paths, then rewrites root-absolute paths ("/waterroad/...") to relative ones ("waterroad/..."), because GitHub Pages
serves the site under /<repo>/. Server-only features (draw-a-box analysis, live series) are not in the copy; the
pages that need them say so.
Usage: python tools/export_static.py   (then push dist/ to the gh-pages branch)
"""
import json
import re
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BASE = "http://127.0.0.1:8765"
PREFIXES = ["waterroad", "forecast", "ml", "science", "timelapse", "explorer", "scitiles", "api", "floods", "s1series", "history", "hires", "motion"]


def get(path):
    for _ in range(3):
        try:
            return urllib.request.urlopen(BASE + path, timeout=60).read()
        except Exception as ex:
            err = ex
    print("  miss", path, str(err)[:60])
    return None


def save(path, body):
    f = DIST / path.lstrip("/").split("?")[0]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(body)


def relink(text):
    for p in PREFIXES:
        text = re.sub(r'(["`\'(])/' + p + r'/', r'\1' + p + '/', text)
    return text.replace('location.origin+"/scitiles', '"scitiles')


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    paths = set()
    pages = ["/dash.html", "/timelapse.html", "/explorer.html", "/explorer.js", "/explorer.css", "/index.html", "/stops.js"]
    for p in pages:
        b = get(p)
        if b is None:
            continue
        t = b.decode("utf8")
        save(p, relink(t).encode("utf8"))
        paths |= set(m.group(0) for m in re.finditer(r'/(?:' + "|".join(PREFIXES) + r')/[A-Za-z0-9_\-/]+\.(?:json|png|jpg|webp)', t))
    # dashboard data (dates come from the water series)
    wr = json.loads(get("/waterroad/andijan_res.json"))
    for ps in wr["passes"]:
        d = ps["date"]
        paths |= {f"/ml/water_pred_{d}.png", f"/waterroad/wl_andijan_res_{d}.png"} | {f"/science/andijan_res/img/{d}_{k}.webp" for k in ("hh", "hv", "rgb", "change")}
    paths |= {"/waterroad/andijan_res.json", "/forecast/andijan_res.json", "/ml/water_model.json", "/science/andijan_res/frames.json",
              "/waterroad/population.json", "/waterroad/photo_andijan_cloudy.jpg", "/api/events.json", "/api/science_boxes.json"}
    # time-lapse frames
    for place in ("aral", "andijan_res", "tashkent"):
        b = get(f"/timelapse/{place}/index.json")
        if not b:
            continue
        idx = json.loads(b); save(f"/timelapse/{place}/index.json", b)
        for fr in idx.get("frames", []):
            name = fr.get("file") or f"{fr.get('year')}.jpg"
            paths.add(f"/timelapse/{place}/{name}")
    n = 0
    for p in sorted(paths):
        if "{" in p:
            continue
        b = get(p)
        if b is not None:
            save(p, relink(b.decode("utf8")).encode("utf8") if p.endswith(".json") else b); n += 1
    (DIST / "index.html").exists() and shutil.copy(DIST / "dash.html", DIST / "start.html")
    (DIST / ".nojekyll").write_text("")
    size = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"dist/: {n} data files, {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
