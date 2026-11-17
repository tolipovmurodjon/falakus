// Precompute "Falakus explains" for the demo places, so the panel opens instantly on stage.
// For each place: NASA CMR lists the NISAR GCOV passes over the box (granule start date = GIBS tile date), then
// headless Chrome opens web/explain-test.html with that studio, runs FalakusExplain.run() (the exact browser code)
// and we save { id, ts, studio, facts, overlays } to data/cases/explain/<id>.json (+ copy in web/cases/explain) plus an index.json for lookup.
// usage: node tools/explain_cache.mjs [placeId ...]   (needs the local server on :8765 serving web/)
import { spawn } from "node:child_process";
import { writeFileSync, readFileSync, copyFileSync, rmSync, mkdirSync, mkdtempSync, existsSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "data/cases/explain");          // source of truth: tools/sync_web_data.py mirrors data/cases -> web/cases
const WEB = join(ROOT, "web/cases/explain");           // written too, so the page works before the next sync
const SERVER = process.env.FALAKUS_SERVER || "http://127.0.0.1:8765";
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const COLLS = ["C2854338529-ASF", "C3622241360-ASF"];          // NISAR L2 GCOV provisional + validated
const PLACES = {
  andijan:    { bbox: [72.98, 40.68, 73.25, 40.86], from: "2026-06-01", to: "2026-11-15" },
  panama_m77: { bbox: [-80.91, 7.46, -80.61, 7.76], from: "2026-09-01", to: "2026-11-15" },   // M7.7, 9 Oct 2026: passes before and after
  aral:       { bbox: [59.55, 45.0, 60.05, 45.4], from: "2026-06-01", to: "2026-11-15" },
  dubai:      { bbox: [55.0, 24.98, 55.3, 25.2], from: "2026-06-01", to: "2026-11-15" },
  jakobshavn: { bbox: [-50.1, 69.1, -49.4, 69.3], from: "2026-06-01", to: "2026-11-15" },
  deadsea:    { bbox: [35.35, 31.3, 35.6, 31.6], from: "2026-06-01", to: "2026-11-15" }
};
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function frames(p) {
  const out = new Map();
  for (const c of COLLS) {
    const u = `https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=${c}&bounding_box=${p.bbox.join(",")}&temporal=${p.from}T00:00:00Z,${p.to}T23:59:59Z&sort_key=start_date&page_size=200`;
    let j; for (let n = 0; n < 4 && !j; n++) { try { j = await (await fetch(u)).json() } catch (e) { if (n === 3) throw e; await sleep(2000 * (n + 1)) } }
    for (const e of j.feed.entry || []) {
      const f = e.title.split("_");                                   // NISAR_L2_PR_GCOV_<cycle>_<track>_<A|D>_<frame>_...
      const date = e.time_start.slice(0, 10), key = date + f[5] + f[6];
      if (!out.has(key)) out.set(key, { date, sensor: "NISAR", track: f[5], dir: f[6], layerId: "nisar-" + date });
    }
  }
  return [...out.values()].sort((a, b) => a.date < b.date ? -1 : 1);
}

async function runInChrome(url, expr, timeoutMs = 300000) {
  const port = 9800 + Math.floor(Math.random() * 150), prof = mkdtempSync(join(tmpdir(), "fx-"));
  const ch = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`, "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-first-run", "--window-size=1200,800", "about:blank"], { stdio: "ignore" });
  try {
    let wsUrl;
    for (let i = 0; i < 50 && !wsUrl; i++) { try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); wsUrl = (l.find(t => t.type === "page") || {}).webSocketDebuggerUrl } catch { } if (!wsUrl) await sleep(200) }
    const ws = new WebSocket(wsUrl); await new Promise(r => ws.onopen = r);
    let id = 0; const pend = new Map();
    ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id) } };
    const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })) });
    await send("Page.enable"); await send("Runtime.enable"); await send("Page.navigate", { url }); await sleep(3000);
    for (let i = 0; i < 40; i++) { const t = await send("Runtime.evaluate", { expression: "typeof FalakusExplain", returnByValue: true }); if (t.result?.result?.value === "object") break; await sleep(500) }
    const r = await Promise.race([send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }), sleep(timeoutMs).then(() => ({ timeout: true }))]);
    ws.close();
    if (r.timeout) throw new Error("timeout");
    if (r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || "eval error");
    return r.result.result.value;
  } finally { ch.kill(); await sleep(500); try { rmSync(prof, { recursive: true, force: true }) } catch { } }
}

mkdirSync(OUT, { recursive: true }); mkdirSync(WEB, { recursive: true });
const ids = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(PLACES);
const idxPath = join(OUT, "index.json");
const index = existsSync(idxPath) ? JSON.parse(readFileSync(idxPath, "utf8")) : [];
for (const id of ids) {
  const p = PLACES[id]; if (!p) { console.log(id, "unknown place"); continue }
  const fr = await frames(p);
  if (fr.length < 2) { console.log(id, `only ${fr.length} NISAR passes in CMR, skipped`); continue }
  const studio = { placeId: id, bbox: p.bbox, sensor: "NISAR", frames: fr };
  const url = `${SERVER}/explain-test.html?studio=${encodeURIComponent(JSON.stringify(studio))}`;
  const t0 = Date.now();
  let res;
  try {
    res = await runInChrome(url, `FalakusExplain.run(window.FALAKUS_STUDIO).then(f => f ? JSON.stringify({ facts: f, overlays: FalakusExplain.overlays }) : null)`);
  } catch (e) { console.log(id, "failed:", e.message); continue }
  if (!res) { console.log(id, "analysis returned nothing (no usable radar in box?)"); continue }
  const { facts, overlays } = JSON.parse(res);
  const doc = { id, ts: new Date().toISOString(), studio, facts, overlays };
  const file = join(OUT, id + ".json"); writeFileSync(file, JSON.stringify(doc)); copyFileSync(file, join(WEB, id + ".json"));
  const entry = { id, bbox: p.bbox, sensor: "NISAR", from: facts.frames[0], to: facts.frames[facts.frames.length - 1], track: facts.track, dir: facts.dir, passes: facts.frames.length, ts: doc.ts };
  const k = index.findIndex(e => e.id === id); if (k >= 0) index[k] = entry; else index.push(entry);
  writeFileSync(idxPath, JSON.stringify(index, null, 1)); copyFileSync(idxPath, join(WEB, "index.json"));
  console.log(`${id}: ${facts.frames.length} passes (track ${facts.track} ${facts.dir}) ${facts.frames[0]}..${entry.to} · ${(statSync(file).size / 1024).toFixed(0)} KB · ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  console.log("   " + facts.narrative[0].t.replace(/<[^>]+>/g, ""));
}
