"""Deck pictures made from our measured files (no generated imagery).

change_map.jpg: NISAR HH on 18 Oct 2026 in grey; blue = water on both 14 Jul and 18 Oct (learned water map);
  amber = water on 14 Jul that is gone by 18 Oct (released for the fields).
before_after.jpg: NISAR HH 14 Jul | 18 Oct 2026, same box, labelled.
Usage: python tools/make_deck_images.py  ->  docs/deck/img/
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCI = ROOT / "data/science/andijan_res/img"
ML = ROOT / "data/ml"
OUT = ROOT / "docs/deck/img"
A, B = "2026-07-14", "2026-10-18"


def font(n):
    for f in ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


def grey(d):
    im = Image.open(SCI / f"{d}_hh.webp").convert("RGBA")
    g = np.asarray(im.convert("L"), np.float32)
    return np.stack([g] * 3, -1)


def mask(d, size):
    m = np.asarray(Image.open(ML / f"water_pred_{d}.png").resize(size, Image.NEAREST))[..., 3] > 0
    return m


def label(img, text, xy, size=30):
    dr = ImageDraw.Draw(img); f = font(size)
    x, y = xy; w = dr.textlength(text, font=f)
    dr.rounded_rectangle([x - 10, y - 6, x + w + 10, y + size + 10], 8, fill=(255, 255, 255))
    dr.text((x, y), text, font=f, fill=(20, 18, 13))


def main():
    base = grey(B); H, W = base.shape[:2]
    a, b = mask(A, (W, H)), mask(B, (W, H))
    out = base * 0.85
    out[a & b] = out[a & b] * 0.25 + np.array([47, 111, 209]) * 0.75
    out[a & ~b] = out[a & ~b] * 0.2 + np.array([234, 140, 20]) * 0.8
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    label(img, "blue: still water   amber: water gone 14 Jul -> 18 Oct", (20, H - 56), 26)
    img.save(OUT / "change_map.jpg", quality=86)
    l, r = Image.fromarray(grey(A).astype(np.uint8)), Image.fromarray(base.astype(np.uint8))
    ba = Image.new("RGB", (W * 2 + 16, H), (246, 243, 237)); ba.paste(l, (0, 0)); ba.paste(r, (W + 16, 0))
    label(ba, "NISAR HH  14 Jul 2026", (20, 20)); label(ba, "NISAR HH  18 Oct 2026", (W + 36, 20))
    ba.save(OUT / "before_after.jpg", quality=86)
    print("wrote change_map.jpg, before_after.jpg", int(a.sum()), int(b.sum()))


if __name__ == "__main__":
    main()
