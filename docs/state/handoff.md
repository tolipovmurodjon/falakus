# START HERE (falakus, NASA Space Apps 2026 "Dancing with the SARs")

Deadline: Sun 15 Nov 2026 23:59 local. Plan: docs/state/PLAN.md (approved 14 Nov evening). Decisions: docs/state/DECISIONS.md.

## Running
- Server: `cd D:/10_projects/falakus && python -I tools/nisar_tile_server.py --port 8765` → http://127.0.0.1:8765
- Data: data/index.json (16,691 GCOV frames, 6-17 Oct 2026), data/thumb (all 16,691 small previews), data/full (big previews, cache), data/eonet_v2.json.
- Prewarm tour: `python -I tools/prewarm.py`

## State at handoff
- Phase 0 done: world map, events list, time player + 10-stop tour (web/index.html, web/stops.js) written, NOT yet walked in Chrome.
- Known bug: some passes 404 / partial frames get stretched → P1 fix in load_preview (reject partial frames) + client skips failed frames.
- Boss will log in to Earthdata himself (earthaccess) → P2 calibrated dB. No ANTHROPIC_API_KEY set; text = numbers first; "labs" proxy for polish if reachable.
- Walls: no money, no sign-ups, nothing published/pushed, never delete data, no R2, no secrets.

## Next 3 steps
1. P1: reject partial/failed passes, prewarm 10 stops to 0 fails, first frame < 2 s.
2. Walk the tour in Chrome (1440 + 390 px), write docs/state/qa/round-1.md (bugs, scores, 5+ suggestions).
3. Rebuild UI per QA (zoom buttons, search, collapsible panels), then P2 intel card.
