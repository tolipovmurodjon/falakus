"""Inline real NISAR browse pictures, the world outline and the mono font into the deck.

Usage: python build_deck.py <browse dir> <land-110m.json> <font.woff2> <deck.src.html> <out.html>
Every {{KEY}} in the source becomes a data: URI (or raw JSON for {{LAND}}).
"""
import base64
import io
import sys
from pathlib import Path

from PIL import Image

browse, land, font, src, out = map(Path, sys.argv[1:6])


def jpeg(name, width, quality=82):
    im = Image.open(browse / name).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def png(name):
    return "data:image/png;base64," + base64.b64encode((browse / name).read_bytes()).decode()


def series(prefix):
    files = sorted(browse.glob(f"{prefix}__*_LATLON_thumbnail.png"))
    items = [f'["{f.name.split("__")[1]}","{png(f.name)}"]' for f in files]
    return "[" + ",".join(items) + "]"


keys = {
    "HERO": jpeg("aral_latlon.png", 760),
    "HH": jpeg("aral_pols__2026-10-17__10737_P05023_N_F_J_001_NATIVE_A_HHHH.png", 560),
    "HV": jpeg("aral_pols__2026-10-17__10737_P05023_N_F_J_001_NATIVE_A_HVHV.png", 560),
    "GUNW": jpeg("tashkent_gunw__2026-06-20__60702T002455_P05023_N_F_J_001_LATLON.png", 620),
    "GOFF": jpeg("fedchenko_goff__2026-06-20__60702T002421_P05023_N_F_J_001_LATLON.png", 560),
    "S_ARAL_EAST": series("aral_east"),
    "S_ARAL_WEST": series("aral_west"),
    "S_ROGUN": series("rogun"),
    "S_QOSH": series("qoshtepa"),
    "S_FERGANA": series("fergana"),
    "FONT": "data:font/woff2;base64," + base64.b64encode(font.read_bytes()).decode(),
    "LAND": land.read_text(),
}

html = src.read_text(encoding="utf-8")
for k, v in keys.items():
    html = html.replace("{{" + k + "}}", v)
missing = [k for k in keys if "{{" + k + "}}" in html]
out.write_text(html, encoding="utf-8")
print(f"wrote {out} {out.stat().st_size/1e6:.2f} MB; unresolved: {missing or 'none'}")
