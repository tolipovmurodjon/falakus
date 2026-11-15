# Falakus: what is in this folder, and everything left to do (15 Nov, deadline 23:59 Tashkent)

## This folder
| File | What it is |
|---|---|
| `1-PROMPT-paste-this.md` | Paste into Claude Design to build the 7-slide deck (every number is exact) |
| `images/change_map.jpg` | HERO: NISAR radar change map of the Andijan reservoir (blue = still water, amber = water gone 14 Jul → 18 Oct 2026) |
| `images/before_after.jpg` | NISAR HH radar, 14 Jul vs 18 Oct 2026 |
| `images/cloudy.jpg` + `nisar-cloudy-day-24sep-hh.webp` | Same day, 24 Sep 2026: photo 100 % cloud vs radar sees the lake |
| `images/aral.jpg`, `aral-landsat-1985/86/87.jpg` | Aral Sea: radar 1997 vs 2026, and Landsat summers from 1985 |
| `images/fergana-harvest.jpg` | Fields that lost plant echo (harvest) vs gained it, Jul → Oct |
| `images/andijan.jpg`, `forecast.jpg` | Old app screenshots (reservoir chapter, forecast) |
| `reference-html/falakus-7.html` | Our current 7-slide deck (open in Chrome, arrow keys) |
| `reference-html/intel.html`, `timelapse.html` | App pages, for the look only (they need our server for data) |
| `text/key-numbers.json` | Every number for slides and form, from our measured files |
| `text/submission-form.md` | Every form field written and ready to paste, with all links |
| `text/submission-rules.md` | Official rules: form fields, disqualifiers, judging, awards, 30 s demo script |
| `text/page.md` | Long project description |

## To do, in order
1. **Team name + 6 member names** → slide 1 (Claude Design prompt: [NAME 1..6]).
2. **Deck in Claude Design** → export PDF → Google Drive, "Anyone with the link: Viewer" → paste the link as Project Demonstration. Check it in a private window.
3. **Form**: paste from `text/submission-form.md` (summary, details, SI = code + text, NASA data links, partner links).
4. **Project link**: https://github.com/tolipovmurodjon/falakus (public) now; https://earth.instant.uz first once the site is live there.
5. **Website (friends)**: one site, not 5 pages: one header, one style, briefings as the front door, time-lapse and explorer as tabs. Then deploy to earth.instant.uz with no localhost paths. Details in `docs/state/handoff.md`.
6. **Time-lapse**: the full play in 10–15 s (still too slow). The Aral frames are baked only to 1987 so far.
7. Tick both boxes → Save Progress → **Submit for Judging before 23:59**.

## Do NOT claim (measured failures)
- The water model trained at Andijan **does not transfer**: Rogun gorge IoU 0.02 (3 photo days), Qosh Tepa 0.00 (1 photo day). Show only Andijan numbers as results; call other places "next step".
- The radar over-counts wet mud in late summer: say so, and use the photo numbers (42.1 → 21.1 km²) for the fall.
- NISAR data before 21 Oct 2026 is provisional.
