"""Draw the 4-step picture of how tools/apron_count.py finds plane-sized objects (for the README and the app).
Usage: python tools/explain_apron.py   ->  docs/img/how-airport-objects-are-found.png"""
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import apron_count as ac

OUT = Path(__file__).resolve().parent.parent / "docs" / "img" / "how-airport-objects-are-found.png"
by = defaultdict(list); dirn = {}
for f in ac.search(ac.BBOX, 45):
    k = f["properties"]["datetime"][:13]; by[k].append(f["id"]); dirn[k] = f["properties"].get("sat:orbit_state", "?")
keys, stack = [], []
for k in sorted(by, reverse=True)[:8]:
    m = None
    for it in by[k]:
        try:
            v = ac.fetch(it, ac.BBOX, ac.W, ac.H)
        except Exception:
            continue
        m = v if m is None else np.where(np.isfinite(m), m, v)
    if m is not None and np.isfinite(m).mean() > 0.9:
        keys.append(k); stack.append(m)
stack = np.stack(stack)
apron = ac.apron_mask() & np.isfinite(stack).all(0); static = ac.static_mask(stack)
i = next(j for j, k in enumerate(keys) if dirn[k] == "ascending")
v = stack[i]; db = 10 * np.log10(np.nan_to_num(v, nan=1e-4))
objs = ac.detect(v, apron, static)
bright = (np.nan_to_num(v) > ac.BRIGHT) & apron
keep = bright & ~static
ys, xs = slice(120, 340), slice(80, 360)
outl = [np.array([ac.to_px(*p) for p in poly]) for poly in ac.APRONS.values()]

fig, ax = plt.subplots(1, 4, figsize=(17, 5.2), facecolor="white")
titles = ["1. The radar echo\nsmooth concrete = dark, metal = bright",
          "2. Keep only very bright pixels\n(echo stronger than 0 dB) on the aprons",
          f"3. Remove what is bright on most of\n{len(keys)} passes (buildings, masts) = blue",
          f"4. Touching pixels (3+) = one object\n{len(objs)} plane-sized objects, {keys[i][:10]}"]
for a, t in zip(ax, titles):
    a.imshow(db[ys, xs], cmap="gray", vmin=-22, vmax=3); a.set_title(t, fontsize=11.5, loc="left"); a.axis("off")
    for o in outl:
        a.plot(o[:, 0] - xs.start, o[:, 1] - ys.start, color="#E8A33D", lw=1.4)
red = np.zeros(db[ys, xs].shape + (4,))
red[bright[ys, xs]] = (0.91, 0.35, 0.05, 0.9); ax[1].imshow(red)
blue = np.zeros_like(red); blue[(static & apron)[ys, xs]] = (0.2, 0.35, 0.95, 0.8)
red2 = np.zeros_like(red); red2[keep[ys, xs]] = (0.91, 0.35, 0.05, 0.95)
ax[2].imshow(blue); ax[2].imshow(red2); ax[3].imshow(blue * 0.5)
for (r, c), s, _ in objs:
    ax[3].add_patch(plt.Circle((c - xs.start, r - ys.start), 6, fill=False, color="#7048E8", lw=2.2))
fig.text(0.01, 0.01, "Sentinel-1 C-band VV, ~9.5 m pixels, Tashkent airport. Orange = aprons traced from a Sentinel-2 photo. "
         "Not a plane count: trucks can make a blob.", fontsize=9, color="#4B5470")
plt.tight_layout(rect=(0, 0.04, 1, 1)); plt.savefig(OUT, dpi=110); print("saved", OUT, len(objs), "objects")
