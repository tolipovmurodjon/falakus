/* Falakus explains — deterministic radar change analysis + templated plain language.
   API:   window.FalakusExplain = { open(), close(), run(studio), facts }
   Input: window.FALAKUS_STUDIO = { bbox:[W,S,E,N], sensor, frames:[{date, sensor, track, dir, layerId}] }
          (also listens for the `falakus:studio` document event). Map: window.map || window.FALAKUS_MAP.
   Everything runs in the browser on NASA GIBS display tiles. No model writes any sentence: every sentence is a
   template filled with a number this file measured, and each carries its source. Optional "Ask" box POSTs
   {question, facts} to window.FALAKUS_LLM_ENDPOINT only if the page sets it (a server proxy); never an LLM directly. */
(() => {
  "use strict";
  if (window.FalakusExplain) return;
  const SCRIPT_SRC = document.currentScript && document.currentScript.src;

  /* ---------------- config ---------------- */
  const SENSORS = {
    "NISAR": { layer: "NISAR_L2_Geocoded_Polarimetric_Covariance", set: "GoogleMapsCompatible_Level13", max: 13, label: "NISAR L-band", product: "NISAR GCOV" },
    "Sentinel-1": { layer: "OPERA_L2_Radiometric_Terrain_Corrected_SAR_Sentinel-1", set: "GoogleMapsCompatible_Level12", max: 12, label: "Sentinel-1 C-band", product: "OPERA RTC-S1" }
  };
  const K_SIGMA = 4, MIN_ABS = 10, MAX_TILES = 64, MAX_FRAMES = 24, MIN_BLOB_PX = 12, EVENT_PAD = 0.5, TILE_BUDGET = 120;   // GIBS answers ~3 s per tile; keep a run near a minute
  const C_DARK = [0, 114, 178], C_BRIGHT = [230, 159, 0], C_UNUSUAL = [204, 121, 167];       // Okabe-Ito: blue, orange, pink
  const ZONE_COLS = ["#0072B2", "#56B4E9", "#009E73", "#E69F00", "#CC79A7", "#F0E442"];
  const EARTH = 40075016.686;
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  const $ = s => document.querySelector(s);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const tick = () => new Promise(r => setTimeout(r, 0));
  const dD = (d, y = true) => { const [Y, M, D] = d.split("-").map(Number); return `${D} ${MON[M - 1]}${y ? " " + Y : ""}` };
  const km = v => v >= 100 ? v.toFixed(0) : v >= 10 ? v.toFixed(1) : v >= 1 ? v.toFixed(1) : v.toFixed(2);
  const normSensor = s => /sentinel|s1|opera/i.test(s || "") ? "Sentinel-1" : "NISAR";
  const normDir = d => /^a/i.test(d || "") ? "ascending" : /^d/i.test(d || "") ? "descending" : "";
  const getMap = () => { const m = window.map || window.FALAKUS_MAP; return m && typeof m.addSource === "function" ? m : null };

  /* ---------------- styles ---------------- */
  function injectStyle() {
    if ($("#fx-style")) return;
    if (![...document.querySelectorAll("link")].some(l => /Fira\+Sans/.test(l.href))) {
      const l = document.createElement("link"); l.rel = "stylesheet";
      l.href = "https://fonts.googleapis.com/css2?family=Fira+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap";
      document.head.appendChild(l);
    }
    const s = document.createElement("style"); s.id = "fx-style";
    s.textContent = `
#fx-panel{--bg:#0D1B2E;--bg2:#13253D;--ink:#F2F5FA;--mute:#8A9BB4;--acc:#1C5BD9;--line:rgba(242,245,250,.10);
 position:fixed;top:12px;right:12px;bottom:12px;width:min(420px,calc(100vw - 24px));z-index:1000;background:var(--bg);color:var(--ink);
 font:14px/1.5 "Fira Sans",system-ui,sans-serif;border:1px solid var(--line);border-radius:14px;box-shadow:0 18px 50px rgba(0,0,0,.45);
 display:flex;flex-direction:column;overflow:hidden}
#fx-panel *{box-sizing:border-box}
#fx-panel .fx-h{padding:14px 16px 10px;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:flex-start}
#fx-panel .fx-h b{font-size:16px;font-weight:600;display:block}
#fx-panel .fx-h small{color:var(--mute);font-size:12px;display:block;line-height:1.35}
#fx-panel .fx-x{margin-left:auto;background:none;border:0;color:var(--mute);font-size:22px;line-height:1;cursor:pointer;padding:2px 6px;border-radius:6px}
#fx-panel .fx-x:hover{color:var(--ink);background:var(--bg2)}
#fx-panel .fx-body{overflow:auto;padding:12px 16px 16px;flex:1}
#fx-panel .fx-prog{height:4px;background:var(--bg2);border-radius:2px;overflow:hidden;margin:4px 0 6px}
#fx-panel .fx-prog i{display:block;height:100%;width:0;background:var(--acc);transition:width .2s}
#fx-panel .fx-st{color:var(--mute);font:12px/1.4 "JetBrains Mono",monospace}
#fx-panel .fx-say{margin:10px 0 0;padding:0;list-style:none;counter-reset:s}
#fx-panel .fx-say li{margin:0 0 10px;padding-left:2px}
#fx-panel .fx-say .src{display:block;color:var(--mute);font:11px/1.35 "JetBrains Mono",monospace;margin-top:2px}
#fx-panel .num{font-family:"JetBrains Mono",monospace;font-weight:500;color:#fff}
#fx-panel h4{margin:16px 0 6px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--mute);font-weight:500}
#fx-panel .fx-seg{display:flex;background:var(--bg2);border-radius:9px;padding:3px;gap:3px;margin-top:14px}
#fx-panel .fx-seg button{flex:1;border:0;background:none;color:var(--mute);font:500 13px "Fira Sans",sans-serif;padding:7px 4px;border-radius:7px;cursor:pointer}
#fx-panel .fx-seg button[aria-pressed=true]{background:var(--acc);color:#fff}
#fx-panel .fx-seg button:disabled{opacity:.4;cursor:default}
#fx-panel .fx-leg{margin-top:10px;font-size:13px}
#fx-panel .fx-leg div{display:flex;align-items:center;gap:8px;margin:4px 0}
#fx-panel .sw{width:14px;height:14px;border-radius:3px;flex:none}
#fx-panel .fx-leg .note{color:var(--mute);font-size:12px;display:block}
#fx-panel label.tg{display:flex;gap:8px;align-items:center;color:var(--mute);font-size:13px;margin-top:8px;cursor:pointer}
#fx-panel .fx-hs{display:flex;flex-direction:column;gap:6px}
#fx-panel .fx-hs button{all:unset;display:flex;gap:10px;align-items:center;padding:7px 9px;border-radius:8px;background:var(--bg2);cursor:pointer;font-size:13px}
#fx-panel .fx-hs button:hover,#fx-panel .fx-hs button:focus-visible{outline:1px solid var(--acc)}
#fx-panel .fx-hs .dt{display:block;color:var(--mute);font-size:12px}
.fx-pin{width:24px;height:24px;border-radius:50%;background:#0D1B2E;color:#fff;border:2px solid #fff;font:600 12px/20px "Fira Sans",sans-serif;text-align:center;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.5)}
.fx-pin.dark{border-color:rgb(${C_DARK})}.fx-pin.bright{border-color:rgb(${C_BRIGHT})}
#fx-panel details{margin-top:14px;border-top:1px solid var(--line);padding-top:10px}
#fx-panel summary{cursor:pointer;color:var(--ink);font-weight:500}
#fx-panel details ul{padding-left:18px;color:var(--mute);font-size:13px;margin:8px 0 0}
#fx-panel .fx-ask{display:flex;gap:6px;margin-top:6px}
#fx-panel .fx-ask input{flex:1;min-width:0;background:var(--bg2);border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:8px 10px;font:13px "Fira Sans",sans-serif}
#fx-panel .fx-ask button,#fx-panel .chip{background:var(--acc);border:0;color:#fff;border-radius:8px;padding:7px 11px;font:500 13px "Fira Sans",sans-serif;cursor:pointer}
#fx-panel .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
#fx-panel .chip{background:var(--bg2);color:var(--ink);border:1px solid var(--line);padding:5px 9px;font-size:12px}
#fx-panel .fx-ans{margin-top:8px;font-size:13px;background:var(--bg2);border-radius:8px;padding:8px 10px}
#fx-panel .fx-ans:empty{display:none}
#fx-panel .spark{display:block;width:100%;height:70px}
#fx-panel .err{color:#FFB4A8}
#fx-panel .fx-cached{display:flex;gap:8px;align-items:center;justify-content:space-between;background:var(--bg2);border:1px solid var(--line);border-radius:8px;padding:7px 10px;font-size:12px;color:var(--mute);margin-top:8px}
#fx-panel .fx-cached button{background:var(--acc);border:0;color:#fff;border-radius:7px;padding:5px 10px;font:500 12px "Fira Sans",sans-serif;cursor:pointer;flex:none}
@media (max-width:720px){#fx-panel{top:auto;left:0;right:0;bottom:0;width:100%;max-height:62vh;border-radius:16px 16px 0 0}}
`;
    document.head.appendChild(s);
  }

  /* ---------------- GIBS tile fetch with scramble guard ----------------
     GIBS returns ~1/3 of NISAR z11-13 tiles scrambled per request (semi-transparent noise or grey static). Same detector as
     home.js: reject, retry the same URL with ?r=n up to 5 times. Good tiles go to the shared Cache API store. */
  const CACHE_NAME = "falakus-gibs-v1";
  const cacheP = (async () => { try { return "caches" in self ? await caches.open(CACHE_NAME) : null } catch (e) { return null } })();
  const STATS = { ok: 0, scrambled: 0, retries: 0, failed: 0, empty: 0, parentFill: 0 };
  const PARENT = new Map();
  async function decode(buf) {
    const bmp = await createImageBitmap(new Blob([buf]));
    const c = new OffscreenCanvas(bmp.width, bmp.height), x = c.getContext("2d", { willReadFrequently: true }); x.drawImage(bmp, 0, 0);
    return x.getImageData(0, 0, bmp.width, bmp.height);
  }
  function scrambled(im, colour, bytes) {
    const a = im.data, W = im.width, N = a.length / 4;
    let zero = 0, mid = 0, op = 0, sat = 0, mx = 0, gh = 0, gv = 0, nh = 0;
    const L = i => a[i] + a[i + 1] + a[i + 2];
    for (let i = 0, p = 0; i < a.length; i += 4, p++) {
      const al = a[i + 3]; if (al <= 8) { zero++; continue } if (al < 247) mid++;
      op++; const hi = Math.max(a[i], a[i + 1], a[i + 2]); sat += hi - Math.min(a[i], a[i + 1], a[i + 2]); mx += hi;
      if ((p & 1) === 0 && p % W < W - 1 && i + W * 4 + 3 < a.length && a[i + 7] > 8 && a[i + W * 4 + 3] > 8) { gh += Math.abs(L(i) - L(i + 4)); gv += Math.abs(L(i) - L(i + W * 4)); nh++ }
    }
    if (zero / N > 0.98) return bytes > 5000;
    if (mid / N > 0.25) return true;
    if (op > 500 && mx / op < 4) return true;
    if (colour && op > 500 && sat / op < 12) return true;          // grey static (real NISAR tiles are colour)
    if (nh > 800 && gv > 1.45 * gh + 50) return true;              // horizontal streaks / big neighbour jumps
    return false;
  }
  async function getTile(url, colour, signal, tries = 5) {
    const c = await cacheP;
    if (c) { try { const h = await c.match(url); if (h) { const b = await h.arrayBuffer(); return b.byteLength < 400 ? null : await decode(b) } } catch (e) { } }
    for (let n = 0; n <= tries; n++) {
      if (signal && signal.aborted) throw new DOMException("aborted", "AbortError");
      if (n) { STATS.retries++; await new Promise(r => setTimeout(r, Math.min(800, 100 * 2 ** (n - 1)))) }
      let r; try { r = await fetch(n ? url + "?r=" + (Date.now() % 1e7 + n * 7919 + Math.floor(Math.random() * 1e6)) : url, { signal }) } catch (e) { if (e.name === "AbortError") throw e; continue }
      if (r.status >= 500) continue;
      if (!r.ok) { STATS.empty++; return null }
      const buf = await r.arrayBuffer();
      if (buf.byteLength < 400) { STATS.empty++; return null }
      let im; try { im = await decode(buf) } catch (e) { continue }
      if (scrambled(im, colour, buf.byteLength)) { STATS.scrambled++; continue }
      STATS.ok++;
      if (c) c.put(url, new Response(buf, { headers: { "content-type": "image/png" } })).catch(() => { });
      return im;
    }
    return FAIL;
  }
  const FAIL = { fail: true };
  async function pool(jobs, n, onDone) { let i = 0; const run = async () => { while (i < jobs.length) { const j = i++; await jobs[j](); onDone() } }; await Promise.all(Array.from({ length: Math.min(n, jobs.length) }, run)) }

  /* ---------------- Web Mercator grid ---------------- */
  const lon2px = (lon, z) => (lon + 180) / 360 * 256 * 2 ** z;
  const lat2px = (lat, z) => { const s = Math.sin(lat * Math.PI / 180); return (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * 256 * 2 ** z };
  const px2lon = (x, z) => x / (256 * 2 ** z) * 360 - 180;
  const px2lat = (y, z) => { const n = Math.PI - 2 * Math.PI * y / (256 * 2 ** z); return 180 / Math.PI * Math.atan(Math.sinh(n)) };
  function makeGrid(bbox, maxZ, nFrames = 1) {
    const [W, S, E, N] = bbox;
    let z = maxZ, g;
    for (; z >= 1; z--) {
      const x0 = Math.floor(lon2px(W, z)), x1 = Math.ceil(lon2px(E, z)), y0 = Math.floor(lat2px(N, z)), y1 = Math.ceil(lat2px(S, z));
      const tiles = (Math.floor((x1 - 1) / 256) - Math.floor(x0 / 256) + 1) * (Math.floor((y1 - 1) / 256) - Math.floor(y0 / 256) + 1);
      g = { z, x0, y0, W: x1 - x0, H: y1 - y0, tiles };
      if (Math.max(g.W, g.H) <= 1024 && tiles <= MAX_TILES && (tiles * nFrames <= TILE_BUDGET || Math.max(g.W, g.H) <= 400)) break;
    }
    const s = EARTH / (256 * 2 ** g.z);
    g.rowKm2 = new Float64Array(g.H);
    for (let r = 0; r < g.H; r++) { const c = Math.cos(px2lat(g.y0 + r + 0.5, g.z) * Math.PI / 180); g.rowKm2[r] = (s * c) ** 2 / 1e6 }
    g.pxM = s * Math.cos((S + N) / 2 * Math.PI / 180);
    g.corners = [[px2lon(g.x0, g.z), px2lat(g.y0, g.z)], [px2lon(g.x0 + g.W, g.z), px2lat(g.y0, g.z)], [px2lon(g.x0 + g.W, g.z), px2lat(g.y0 + g.H, g.z)], [px2lon(g.x0, g.z), px2lat(g.y0 + g.H, g.z)]];
    g.ll = (x, y) => [px2lon(g.x0 + x + 0.5, g.z), px2lat(g.y0 + y + 0.5, g.z)];
    return g;
  }
  function mosaicJobs(sensor, date, g, colour, signal) {
    const cfg = SENSORS[sensor], rgba = new Uint8ClampedArray(g.W * g.H * 4);
    const jobs = [];
    for (let ty = Math.floor(g.y0 / 256); ty <= Math.floor((g.y0 + g.H - 1) / 256); ty++)
      for (let tx = Math.floor(g.x0 / 256); tx <= Math.floor((g.x0 + g.W - 1) / 256); tx++)
        jobs.push(async () => {
          const url = `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${cfg.layer}/default/${date}/${cfg.set}/${g.z}/${ty}/${tx}.png`;
          let im = await getTile(url, colour, signal);
          if (im === FAIL) {                      // some tiles stay scrambled on every request: fill from the parent tile (1-2 levels up)
            for (let up = 1; up <= 2 && im === FAIL; up++) {
              const pz = g.z - up, px = tx >> up, py = ty >> up, pu = url.replace(`/${g.z}/${ty}/${tx}.png`, `/${pz}/${py}/${px}.png`);
              if (!PARENT.has(pu)) PARENT.set(pu, getTile(pu, colour, signal, 3));
              const pim = await PARENT.get(pu); if (!pim || pim === FAIL) { if (!pim) im = null; continue }
              const sz = 256 >> up, ox = (tx - (px << up)) * sz, oy = (ty - (py << up)) * sz, out = new ImageData(256, 256), f = 1 << up;
              for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) { const s = ((oy + (y / f | 0)) * 256 + ox + (x / f | 0)) * 4, t = (y * 256 + x) * 4; for (let k = 0; k < 4; k++) out.data[t + k] = pim.data[s + k] }
              im = out; STATS.parentFill++;
            }
          }
          if (im === FAIL) { STATS.failed++; return }
          if (!im) return;
          const ox = tx * 256 - g.x0, oy = ty * 256 - g.y0, d = im.data;
          for (let y = 0; y < 256; y++) {
            const gy = oy + y; if (gy < 0 || gy >= g.H) continue;
            for (let x = 0; x < 256; x++) { const gx = ox + x; if (gx < 0 || gx >= g.W) continue; const s = (y * 256 + x) * 4, t = (gy * g.W + gx) * 4; rgba[t] = d[s]; rgba[t + 1] = d[s + 1]; rgba[t + 2] = d[s + 2]; rgba[t + 3] = d[s + 3] }
          }
        });
    return { rgba, jobs };
  }

  /* ---------------- per-frame features ---------------- */
  // 5x5 box mean over valid pixels only (speckle suppression), via integral images; result rounded to Uint8, valid if >=13/25 valid.
  function smooth5(src, valid, W, H, out, outValid) {
    const I = new Float64Array((W + 1) * (H + 1)), C = new Float64Array((W + 1) * (H + 1));
    for (let y = 0; y < H; y++) { let rs = 0, rc = 0; for (let x = 0; x < W; x++) { const p = y * W + x; if (valid[p]) { rs += src[p]; rc++ } const q = (y + 1) * (W + 1) + x + 1; I[q] = I[q - W - 1] + rs; C[q] = C[q - W - 1] + rc } }
    for (let y = 0; y < H; y++) {
      const ya = Math.max(0, y - 2), yb = Math.min(H, y + 3);
      for (let x = 0; x < W; x++) {
        const xa = Math.max(0, x - 2), xb = Math.min(W, x + 3), A = ya * (W + 1), B = yb * (W + 1);
        const c = C[B + xb] - C[B + xa] - C[A + xb] + C[A + xa], p = y * W + x;
        if (c >= 13 && valid[p]) { out[p] = Math.round((I[B + xb] - I[B + xa] - I[A + xb] + I[A + xa]) / c); outValid[p] = 1 } else { out[p] = 0; outValid[p] = 0 }
      }
    }
  }
  function frameFeatures(rgba, g) {
    const N = g.W * g.H, valid = new Uint8Array(N), L = new Uint8Array(N), G = new Uint8Array(N), R = new Uint8Array(N);
    let nv = 0, sR = 0, sG = 0, sRG = 0;
    for (let p = 0, i = 0; p < N; p++, i += 4) if (rgba[i + 3] > 8) { valid[p] = 1; nv++; R[p] = rgba[i]; G[p] = rgba[i + 1]; L[p] = Math.round((rgba[i] + rgba[i + 1] + rgba[i + 2]) / 3); sR += rgba[i]; sG += rgba[i + 1]; sRG += Math.abs(rgba[i] - rgba[i + 1]) }
    const sL = new Uint8Array(N), sGv = new Uint8Array(N), sv = new Uint8Array(N), sv2 = new Uint8Array(N);
    smooth5(L, valid, g.W, g.H, sL, sv); smooth5(G, valid, g.W, g.H, sGv, sv2);
    return { valid: sv, L: sL, G: sGv, validPct: nv / N * 100, meanHH: nv ? sR / nv : 0, meanHV: nv ? sG / nv : 0, grey: nv ? sRG / nv < 2 : true };
  }
  function otsu(L, mask) {
    const h = new Float64Array(256); let n = 0;
    for (let p = 0; p < L.length; p++) if (mask[p]) { h[L[p]]++; n++ }
    let sum = 0; for (let i = 0; i < 256; i++) sum += i * h[i];
    let wB = 0, sB = 0, best = 0, thr = 40;
    for (let t = 0; t < 256; t++) { wB += h[t]; if (!wB) continue; const wF = n - wB; if (!wF) break; sB += t * h[t]; const mB = sB / wB, mF = (sum - sB) / wF, v = wB * wF * (mB - mF) ** 2; if (v > best) { best = v; thr = t } }
    return thr;
  }
  /* Water threshold. Display-scaled NISAR tiles put calm water at the colour-map floor, so water forms a small, separate
     peak at the dark end of the smoothed-brightness histogram, while land fills one wide hump. Otsu over the whole histogram
     splits that hump instead, so we cut at the valley right after the darkest peak, and use Otsu only when there is no such peak. */
  function waterThr(L, mask) {
    const h = new Float64Array(256); let n = 0;
    for (let p = 0; p < L.length; p++) if (mask[p]) { h[L[p]]++; n++ }
    const s = Array.from(h, (v, i) => (h[i - 1] || 0) + v + (h[i + 1] || 0));
    let lo = 0; while (lo < 255 && s[lo] < n * 0.0005) lo++;
    for (let i = lo + 1; i < Math.min(200, lo + 60); i++) {
      if (s[i] >= s[i - 1] && s[i] > s[i + 1] && s[i] > n * 0.004) {             // darkest real peak
        let v = i; for (let j = i + 1; j < i + 25 && j < 255; j++) { if (s[j] < s[v]) v = j; if (s[j] > s[v] * 1.25 && j > v + 1) break }
        if (s[v] < s[i] * 0.85 && v > i) return { thr: v + 1, how: "valley after the darkest peak" };   // the valley level itself counts as water
        break;
      }
    }
    return { thr: otsu(L, mask), how: "Otsu split" };
  }
  function dilate(m, W, H, r) {                       // square max filter, radius r (separable)
    const t = new Uint8Array(m.length);
    for (let y = 0; y < H; y++) { let last = -1e9; for (let x = 0; x < W; x++) { if (m[y * W + x]) last = x; t[y * W + x] = x - last <= r ? 1 : 0 } last = 1e9; for (let x = W - 1; x >= 0; x--) { if (m[y * W + x]) last = x; if (last - x <= r) t[y * W + x] = 1 } }
    for (let x = 0; x < W; x++) { let last = -1e9; for (let y = 0; y < H; y++) { if (t[y * W + x]) last = y; m[y * W + x] = y - last <= r ? 1 : 0 } last = 1e9; for (let y = H - 1; y >= 0; y--) { if (t[y * W + x]) last = y; if (last - y <= r) m[y * W + x] = 1 } }
  }
  function localStd(L, v, W, H, r) {
    const I = new Float64Array((W + 1) * (H + 1)), I2 = new Float64Array(I.length), C = new Float64Array(I.length), out = new Float32Array(W * H);
    for (let y = 0; y < H; y++) { let a = 0, b = 0, c = 0; for (let x = 0; x < W; x++) { const p = y * W + x; if (v[p]) { a += L[p]; b += L[p] * L[p]; c++ } const q = (y + 1) * (W + 1) + x + 1; I[q] = I[q - W - 1] + a; I2[q] = I2[q - W - 1] + b; C[q] = C[q - W - 1] + c } }
    for (let y = 0; y < H; y++) { const ya = Math.max(0, y - r) * (W + 1), yb = Math.min(H, y + r + 1) * (W + 1); for (let x = 0; x < W; x++) { const xa = Math.max(0, x - r), xb = Math.min(W, x + r + 1), f = (A, i) => A[yb + xb] - A[yb + xa] - A[ya + xb] + A[ya + xa]; const c = f(C), m = c ? f(I) / c : 0; out[y * W + x] = c > 1 ? Math.sqrt(Math.max(0, f(I2) / c - m * m)) : 0 } }
    return out;
  }
  function pctl(a, v, q) { const h = new Float64Array(512); let n = 0; for (let p = 0; p < a.length; p++) if (v[p]) { h[Math.min(511, a[p] * 4 | 0)]++; n++ } let c = 0; for (let i = 0; i < 512; i++) { c += h[i]; if (c >= q * n) return i / 4 } return 128 }
  // robust diff threshold from a histogram: median and MAD of (b - a)
  function diffStats(a, b, mask) {
    const h = new Float64Array(511); let n = 0;
    for (let p = 0; p < a.length; p++) if (mask[p]) { h[b[p] - a[p] + 255]++; n++ }
    const q = f => { let c = 0; for (let i = 0; i < 511; i++) { c += h[i]; if (c >= f * n) return i - 255 } return 0 };
    const med = q(0.5); const h2 = new Float64Array(256);
    for (let i = 0; i < 511; i++) if (h[i]) h2[Math.min(255, Math.abs(i - 255 - med))] += h[i];
    let c = 0, mad = 0; for (let i = 0; i < 256; i++) { c += h2[i]; if (c >= 0.5 * n) { mad = i; break } }
    const sigma = Math.max(1, 1.4826 * mad);
    return { med, mad, sigma, thr: Math.max(MIN_ABS, K_SIGMA * sigma), n };
  }
  // connected components (8-neighbour) on a label array of {0, 1, 2}; drops blobs < MIN_BLOB_PX
  function blobs(cls, g) {
    const N = g.W * g.H, lab = new Int32Array(N), out = [], st = new Int32Array(N); let id = 0;
    for (let p0 = 0; p0 < N; p0++) {
      if (!cls[p0] || lab[p0]) continue;
      const k = cls[p0]; id++; let sp = 0; st[sp++] = p0; lab[p0] = id;
      const b = { id, kind: k, px: [], area: 0, sx: 0, sy: 0, minx: 1e9, miny: 1e9, maxx: -1, maxy: -1 };
      while (sp) {
        const p = st[--sp], x = p % g.W, y = (p / g.W) | 0; b.px.push(p); b.area += g.rowKm2[y]; b.sx += x; b.sy += y;
        if (x < b.minx) b.minx = x; if (x > b.maxx) b.maxx = x; if (y < b.miny) b.miny = y; if (y > b.maxy) b.maxy = y;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= g.W || yy >= g.H) continue; const q = yy * g.W + xx; if (cls[q] === k && !lab[q]) { lab[q] = id; st[sp++] = q } }
      }
      if (b.px.length >= MIN_BLOB_PX) out.push(b); else for (const p of b.px) cls[p] = 0;
    }
    return out;
  }
  function overlay(g, paint) {
    const c = document.createElement("canvas"); c.width = g.W; c.height = g.H;
    const x = c.getContext("2d"), im = x.createImageData(g.W, g.H); paint(im.data); x.putImageData(im, 0, 0);
    return c.toDataURL("image/png");
  }

  /* ---------------- ML 1: unusual change vs each pixel's own normal ---------------- */
  function unusual(fr, common, g, stepMed) {
    const n = fr.length, N = g.W * g.H, steps = n - 1, d = new Float32Array(steps);
    const flag = new Uint8Array(N), stepOf = new Int16Array(N).fill(-1), base = new Uint8Array(N), perStep = new Float64Array(steps);
    let area = 0, baseArea = 0;
    for (let p = 0; p < N; p++) {
      if (!common[p]) continue;
      for (let t = 0; t < steps; t++) d[t] = fr[t + 1].L[p] - fr[t].L[p] - stepMed[t];   // remove scene-wide shift (wind, moisture, stretch)
      const a = Array.from(d, Math.abs).sort((u, v) => u - v);
      const normal = Math.max(2, steps % 2 ? a[(steps - 1) >> 1] : (a[steps / 2 - 1] + a[steps / 2]) / 2);
      let bt = 0; for (let t = 1; t < steps; t++) if (Math.abs(d[t]) > Math.abs(d[bt])) bt = t;
      const r = p / g.W | 0;
      if (Math.abs(d[bt]) > 4 * normal && Math.abs(d[bt]) >= MIN_ABS) { flag[p] = d[bt] < 0 ? 1 : 2; stepOf[p] = bt }
      if (Math.abs(d[0]) > 4 * normal && Math.abs(d[0]) >= MIN_ABS) { base[p] = 1; baseArea += g.rowKm2[r] }
    }
    const kept = blobs(flag, g);                       // same speckle rule as the change map
    for (const b of kept) for (const p of b.px) { const r = p / g.W | 0; area += g.rowKm2[r]; perStep[stepOf[p]] += g.rowKm2[r] }
    let top = 0; for (let t = 1; t < steps; t++) if (perStep[t] > perStep[top]) top = t;
    const img = overlay(g, a => { for (let p = 0; p < N; p++) if (flag[p]) { const c = C_UNUSUAL; a[p * 4] = c[0]; a[p * 4 + 1] = c[1]; a[p * 4 + 2] = c[2]; a[p * 4 + 3] = 215 } });
    return { area, baseArea, topStep: top, topStepArea: perStep[top], perStep: Array.from(perStep), img, fromDate: fr[top].date, toDate: fr[top + 1].date, baseFrom: fr[0].date, baseTo: fr[1].date };
  }

  /* ---------------- ML 2: radar fingerprint zones (k-means on time profiles) ---------------- */
  function zones(fr, common, g, darkThr, stepMed) {
    const n = fr.length, D = 2 * n, N = g.W * g.H, idx = [];
    for (let p = 0; p < N; p++) if (common[p]) idx.push(p);
    if (idx.length < 500) return null;
    const useG = !fr[0].grey;
    // scene-wide shift per pass (cumulative median step) is removed, so zones group by how a pixel behaves, not by the pass stretch
    const off = [0]; for (let t = 0; t < n - 1; t++) off.push(off[t] + stepMed[t]);
    // features: level (mean brightness, mean plant signal), weighted ×n so level is not drowned by speckle in the shape dims, + shape (deviation of each pass from the pixel's own mean)
    // + water persistence (share of passes below the water threshold), which separates calm water from dark fields and shadow
    const nLev = useG ? 3 : 2, dims = nLev + (useG ? D : n), wL = n, raw = new Float32Array(dims);
    const prof = p => { let mL = 0, mG = 0, wet = 0; for (let t = 0; t < n; t++) { mL += fr[t].L[p] - off[t]; mG += fr[t].G[p]; if (fr[t].L[p] < darkThr) wet++ } mL /= n; mG /= n;
      raw[0] = mL; raw[1] = wet / n; let j = 2; if (useG) raw[j++] = mG; for (let t = 0; t < n; t++) raw[j++] = fr[t].L[p] - off[t] - mL; if (useG) for (let t = 0; t < n; t++) raw[j++] = fr[t].G[p] - mG; return raw };
    const mu = new Float64Array(dims), sd = new Float64Array(dims); let m = 0;
    const acc = new Float64Array(dims), acc2 = new Float64Array(dims);
    for (let i = 0; i < idx.length; i += 7) { const r = prof(idx[i]); m++; for (let j = 0; j < dims; j++) { acc[j] += r[j]; acc2[j] += r[j] * r[j] } }
    for (let j = 0; j < nLev; j++) { mu[j] = acc[j] / m; sd[j] = Math.sqrt(Math.max(j === 1 ? 0.01 : 1, acc2[j] / m - mu[j] ** 2)) / wL }
    const pooled = (a, b) => { let v = 0; for (let j = a; j < b; j++) v += acc2[j] / m; return Math.sqrt(Math.max(1, v / (b - a))) };
    const sdL = pooled(nLev, nLev + n), sdG = useG ? pooled(nLev + n, dims) : 1;
    for (let j = nLev; j < dims; j++) { mu[j] = 0; sd[j] = j < nLev + n ? sdL : sdG }
    const feat = (p, j) => (j === 0 ? prof(p) : raw)[j];
    // deterministic PRNG so the same box gives the same zones
    let seed = 20261115; const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
    const S = Math.min(20000, idx.length), sample = new Float32Array(S * dims);
    for (let i = 0; i < S; i++) { const p = idx[Math.floor(rnd() * idx.length)]; for (let j = 0; j < dims; j++) sample[i * dims + j] = (feat(p, j) - mu[j]) / sd[j] }
    const k = idx.length > 40000 ? 6 : idx.length > 10000 ? 5 : 4, cen = new Float64Array(k * dims);
    const dist = (arr, o, c) => { let s = 0; for (let j = 0; j < dims; j++) { const e = arr[o + j] - cen[c * dims + j]; s += e * e } return s };
    // k-means++ init
    let f = Math.floor(rnd() * S); for (let j = 0; j < dims; j++) cen[j] = sample[f * dims + j];
    const dmin = new Float64Array(S).fill(Infinity);
    for (let c = 1; c < k; c++) {
      let tot = 0; for (let i = 0; i < S; i++) { dmin[i] = Math.min(dmin[i], dist(sample, i * dims, c - 1)); tot += dmin[i] }
      let r = rnd() * tot, pick = S - 1; for (let i = 0; i < S; i++) { r -= dmin[i]; if (r <= 0) { pick = i; break } }
      for (let j = 0; j < dims; j++) cen[c * dims + j] = sample[pick * dims + j];
    }
    const as = new Int8Array(S);
    for (let it = 0; it < 10; it++) {
      for (let i = 0; i < S; i++) { let b = 0, bd = Infinity; for (let c = 0; c < k; c++) { const v = dist(sample, i * dims, c); if (v < bd) { bd = v; b = c } } as[i] = b }
      const acc = new Float64Array(k * dims), cnt = new Float64Array(k);
      for (let i = 0; i < S; i++) { cnt[as[i]]++; for (let j = 0; j < dims; j++) acc[as[i] * dims + j] += sample[i * dims + j] }
      for (let c = 0; c < k; c++) if (cnt[c]) for (let j = 0; j < dims; j++) cen[c * dims + j] = acc[c * dims + j] / cnt[c];
    }
    // assign every pixel; collect raw-unit centroid curves and areas
    const lab = new Int8Array(N).fill(-1), area = new Float64Array(k), cntA = new Float64Array(k), curve = new Float64Array(k * D), v = new Float32Array(dims);
    for (const p of idx) {
      for (let j = 0; j < dims; j++) v[j] = (feat(p, j) - mu[j]) / sd[j];
      let b = 0, bd = Infinity; for (let c = 0; c < k; c++) { const dd = dist(v, 0, c); if (dd < bd) { bd = dd; b = c } }
      lab[p] = b; area[b] += g.rowKm2[p / g.W | 0]; cntA[b]++;
      for (let j = 0; j < n; j++) { curve[b * D + j] += fr[j].L[p] - off[j]; curve[b * D + n + j] += fr[j].G[p] }
    }
    let zs = [];
    for (let c = 0; c < k; c++) {
      if (!cntA[c]) continue;
      const Lc = [], Gc = []; for (let j = 0; j < n; j++) { Lc.push(curve[c * D + j] / cntA[c]); Gc.push(curve[c * D + n + j] / cntA[c]) }
      zs.push({ c, area: area[c], L: Lc, G: Gc, meanL: Lc.reduce((a, b) => a + b, 0) / n, ...labelZone(Lc, Gc, darkThr, useG) });
    }
    zs.sort((a, b) => a.meanL - b.meanL);
    zs.forEach((z, i) => z.col = ZONE_COLS[i % ZONE_COLS.length]);
    const colOf = new Array(k); zs.forEach(z => colOf[z.c] = z.col.match(/\w\w/g).map(h => parseInt(h, 16)));
    const img = overlay(g, a => { for (let p = 0; p < N; p++) if (lab[p] >= 0) { const c = colOf[lab[p]]; a[p * 4] = c[0]; a[p * 4 + 1] = c[1]; a[p * 4 + 2] = c[2]; a[p * 4 + 3] = 170 } });
    return { k, zones: zs, img, sample: S, dims, useG };
  }
  function labelZone(L, G, thr, useG) {
    const n = L.length, a = (arr, i, j) => arr.slice(i, j).reduce((s, x) => s + x, 0) / Math.max(1, j - i);
    const third = Math.max(1, Math.round(n / 3));
    const L0 = a(L, 0, third), L1 = a(L, n - third, n), Lmax = Math.max(...L), Lmean = a(L, 0, n);
    const G0 = a(G, 0, third), G1 = a(G, n - third, n), Gmax = Math.max(...G), Gmean = a(G, 0, n), gi = G.indexOf(Gmax);
    const darkN = L.filter(v => v < thr + 1).length;
    if (darkN >= 0.8 * n) return { label: "dark all season", meaning: "likely open water" };
    if (L0 < thr + 3 && L1 >= thr + 5 && L1 - L0 > 5) return { label: "dark, then brighter", meaning: "likely shore exposed as water dropped" };
    if (L0 >= thr + 5 && L1 < thr + 3 && L0 - L1 > 5) return { label: "bright, then dark", meaning: "likely new water or flooding" };
    if (useG && gi > 0 && gi < n - 1 && Gmax - Math.min(G0, G1) > Math.max(15, 0.2 * Gmean) && Gmax - G1 > 10) return { label: "plant signal rises then drops", meaning: "likely crops grown and harvested" };
    if (useG && G1 - G0 > Math.max(12, 0.2 * Gmean)) return { label: "plant signal rising", meaning: "likely growing vegetation" };
    if (useG && G0 - G1 > Math.max(12, 0.2 * Gmean)) return { label: "plant signal falling", meaning: "likely harvest or drying vegetation" };
    if (L1 - L0 > 8) return { label: "getting brighter", meaning: "likely drier, rougher or freshly bare ground" };
    if (L0 - L1 > 8) return { label: "getting darker", meaning: "likely wetter or smoother ground" };
    if (Lmean > thr * 2.2 || Lmean > 150) return { label: "bright all season", meaning: "likely town, rock or rough ground" };
    return { label: "steady, mid brightness", meaning: "likely fields or bare ground, little change" };
  }

  /* ---------------- context events ---------------- */
  async function jget(url, ms = 12000) { const ac = new AbortController(), t = setTimeout(() => ac.abort(), ms); try { const r = await fetch(url, { signal: ac.signal }); if (!r.ok) throw new Error(r.status); return await r.json() } finally { clearTimeout(t) } }
  async function events(bbox, d0, d1) {
    const [W, S, E, N] = bbox, P = EVENT_PAD, end = new Date(Date.parse(d1) + 864e5).toISOString().slice(0, 10);
    const out = { quakes: null, eonet: null };
    const q = jget(`https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=${d0}&endtime=${end}&minlatitude=${S - P}&maxlatitude=${N + P}&minlongitude=${W - P}&maxlongitude=${E + P}&minmagnitude=4`)
      .then(j => out.quakes = j.features.map(f => ({ mag: f.properties.mag, place: f.properties.place, date: new Date(f.properties.time).toISOString().slice(0, 10), id: f.id }))).catch(() => { });
    const e = jget(`https://eonet.gsfc.nasa.gov/api/v3/events?bbox=${W - P},${N + P},${E + P},${S - P}&start=${d0}&end=${end}&status=all`)
      .then(j => out.eonet = (j.events || []).map(v => ({ title: v.title, cat: (v.categories[0] || {}).title, date: ((v.geometry || [])[0] || {}).date?.slice(0, 10) }))).catch(() => { });
    await Promise.all([q, e]);
    return out;
  }

  /* ---------------- main analysis ---------------- */
  let ctl = null, facts = null, ui = null, mode = "changes";
  function pickFrames(studio) {
    const all = (studio.frames || []).filter(f => f && /^\d{4}-\d{2}-\d{2}$/.test(f.date)).map(f => ({ ...f, sensor: normSensor(f.sensor || studio.sensor) }));
    if (!all.length) return { err: "No time-lapse frames yet. Run a time-lapse first, then ask again." };
    const count = (arr, key) => arr.reduce((m, f) => (m[key(f)] = (m[key(f)] || 0) + 1, m), {});
    const sc = count(all, f => f.sensor), sensor = studio.sensor && sc[normSensor(studio.sensor)] ? normSensor(studio.sensor) : Object.keys(sc).sort((a, b) => sc[b] - sc[a])[0];
    const same = all.filter(f => f.sensor === sensor);
    const tk = f => `${f.track ?? "?"}|${normDir(f.dir)}`, tc = count(same, tk), key = Object.keys(tc).sort((a, b) => tc[b] - tc[a])[0];
    const seen = new Set(); let fr = same.filter(f => tk(f) === key).sort((a, b) => a.date < b.date ? -1 : 1).filter(f => !seen.has(f.date) && seen.add(f.date));
    let thinned = 0;
    if (fr.length > MAX_FRAMES) { const keep = []; for (let i = 0; i < MAX_FRAMES; i++) keep.push(fr[Math.round(i * (fr.length - 1) / (MAX_FRAMES - 1))]); thinned = fr.length - MAX_FRAMES; fr = keep }
    const [track, dir] = key.split("|");
    return { sensor, track, dir, frames: fr, thinned, otherSensors: Object.keys(sc).filter(s => s !== sensor), otherTracks: Object.keys(tc).length - 1, total: all.length };
  }

  async function run(studio) {
    studio = studio || window.FALAKUS_STUDIO;
    if (!ui) build();
    if (ctl) ctl.abort();
    const ac = ctl = new AbortController();
    clearMap(); ui.out.innerHTML = ""; facts = null; api.facts = null;
    if (!studio || !Array.isArray(studio.bbox) || studio.bbox.length !== 4) { status("No area selected yet. Draw a box and run a time-lapse first.", 0, true); return null }
    const pick = pickFrames(studio);
    if (pick.err) { status(pick.err, 0, true); return null }
    if (pick.frames.length < 2) { status(`Only one ${pick.sensor} pass on the same track here, so there is nothing to compare yet. Pick a longer period.`, 0, true); return null }
    const bbox = studio.bbox.map(Number), cfg = SENSORS[pick.sensor], colour = pick.sensor === "NISAR";
    const g = makeGrid(bbox, cfg.max, pick.frames.length);
    Object.assign(STATS, { ok: 0, scrambled: 0, retries: 0, failed: 0, empty: 0, parentFill: 0 }); PARENT.clear();
    const totalTiles = g.tiles * pick.frames.length; let done = 0;
    status(`Fetching ${pick.frames.length} ${cfg.label} passes · ${totalTiles} tiles at zoom ${g.z}`, 0);
    const evP = events(bbox, pick.frames[0].date, pick.frames[pick.frames.length - 1].date);
    const raw = [];
    try {
      const mj = pick.frames.map(f => mosaicJobs(pick.sensor, f.date, g, colour, ac.signal));
      await pool(mj.flatMap(m => m.jobs), 12, () => { done++; status(`Fetching radar tiles ${done}/${totalTiles} · scrambled tiles caught and re-fetched: ${STATS.scrambled}`, done / totalTiles * 0.8) });
      for (let i = 0; i < pick.frames.length; i++) { raw.push({ ...pick.frames[i], ...frameFeatures(mj[i].rgba, g) }); mj[i].rgba = null; await tick() }
    } catch (e) { if (e.name === "AbortError") return null; status("Could not fetch radar tiles: " + e.message, 0, true); return null }
    if (ac.signal.aborted) return null;
    status("Comparing passes…", 0.85); await tick();

    // frames with good coverage; compare only on the common footprint
    const maxV = Math.max(...raw.map(f => f.validPct));
    const fr = raw.filter(f => f.validPct >= Math.max(5, 0.7 * maxV)), skipped = raw.filter(f => !fr.includes(f));
    if (fr.length < 2) { status(`The radar tiles over this box are mostly empty (best pass covers ${maxV.toFixed(0)}%). Try a box inside the swath.`, 0, true); return null }
    const N = g.W * g.H, common = new Uint8Array(N); let commonKm2 = 0, boxKm2 = 0;
    for (let p = 0; p < N; p++) { const r = p / g.W | 0; boxKm2 += g.rowKm2[r]; let ok = 1; for (const f of fr) if (!f.valid[p]) { ok = 0; break } common[p] = ok; if (ok) commonKm2 += g.rowKm2[r] }
    const F = fr[0], Lst = fr[fr.length - 1];
    const wt = waterThr(F.L, F.valid), darkThr = wt.thr;
    // main dark body: the largest connected patch of "dark in any pass" (the lake / reservoir / river), tracked per pass
    const anyDark = new Uint8Array(N); for (let p = 0; p < N; p++) if (common[p]) for (const f of fr) if (f.L[p] < darkThr) { anyDark[p] = 1; break }
    const dbAll = blobs(anyDark, g).sort((a, b) => b.area - a.area), db = dbAll[0], main = new Uint8Array(N);
    if (db && db.area >= 0.5) for (const p of db.px) main[p] = 1;
    const series = fr.map(f => { let a = 0, mk = 0, sh = 0, sg = 0, c = 0; for (let p = 0; p < N; p++) if (common[p]) { if (f.L[p] < darkThr) { const k = g.rowKm2[p / g.W | 0]; a += k; if (main[p]) mk += k } sh += f.L[p]; sg += f.G[p]; c++ } return { date: f.date, darkKm2: a, mainKm2: mk, meanL: c ? sh / c : 0, meanG: c ? sg / c : 0, validPct: f.validPct } });
    const mainBody = db && db.area >= 0.5 ? { lon: g.ll(db.sx / db.px.length, db.sy / db.px.length)[0], lat: g.ll(db.sx / db.px.length, db.sy / db.px.length)[1], extentKm2: db.area,
      edge: db.minx <= 2 || db.miny <= 2 || db.maxx >= g.W - 3 || db.maxy >= g.H - 3, boxShare: db.area / Math.max(1e-9, commonKm2) } : null;

    const both = new Uint8Array(N); for (let p = 0; p < N; p++) both[p] = F.valid[p] && Lst.valid[p];

    // water lost / gained: water-dark in the first pass vs the last, only inside the dark bodies (≥ 0.5 km², dark in any pass)
    // grown by 300 m, so hillside shadow and speckle elsewhere cannot show up as "water"
    const zone = new Uint8Array(N), BUF_M = 300, rad = Math.max(1, Math.round(BUF_M / g.pxM));
    const minBody = Math.max(0.5, 0.1 * (dbAll[0] ? dbAll[0].area : 0));   // the main body and any dark body ≥ 10% of its size
    let nBodies = 0; for (const b of dbAll) if (b.area >= minBody) { nBodies++; for (const p of b.px) zone[p] = 1 }
    dilate(zone, g.W, g.H, rad);
    const wcls = new Uint8Array(N);
    for (let p = 0; p < N; p++) if (zone[p] && both[p]) { const was = F.L[p] < darkThr, now = Lst.L[p] < darkThr; if (was && !now) wcls[p] = 2; else if (!was && now) wcls[p] = 1 }
    const wbl = blobs(wcls, g); let wLost = 0, wGained = 0;
    for (const b of wbl) { if (b.kind === 2) wLost += b.area; else wGained += b.area; b.ll = g.ll(b.sx / b.px.length, b.sy / b.px.length); b.bounds = [g.ll(b.minx, b.maxy), g.ll(b.maxx, b.miny)]; let bs = 0, as = 0; for (const p of b.px) { bs += F.L[p]; as += Lst.L[p] } b.before = bs / b.px.length; b.after = as / b.px.length }
    wbl.sort((a, b) => b.area - a.area);
    const waterHot = wbl.slice(0, 3).map((b, i) => ({ n: i + 1, kind: b.kind === 2 ? "water lost" : "water gained", area: b.area, lon: b.ll[0], lat: b.ll[1], bounds: b.bounds, before: b.before, after: b.after, wasDark: b.kind === 2 ? 1 : 0, nowDark: b.kind === 2 ? 0 : 1 }));
    const waterImg = overlay(g, a => { for (let p = 0; p < N; p++) if (wcls[p]) { const c = wcls[p] === 2 ? C_BRIGHT : C_DARK; a[p * 4] = c[0]; a[p * 4 + 1] = c[1]; a[p * 4 + 2] = c[2]; a[p * 4 + 3] = 225 } });

    // steep-terrain proxy: local brightness spread (9×9 std of the first pass). Radar on hillsides alternates bright fore-slopes
    // and dark shadows, so change blobs sitting on the most textured 15% of the scene are dropped from the Changes view.
    const lstd = localStd(F.L, F.valid, g.W, g.H, 4), rough = pctl(lstd, F.valid, 0.85);

    // first vs last change map
    const ds = diffStats(F.L, Lst.L, both), cls = new Uint8Array(N);
    for (let p = 0; p < N; p++) if (both[p]) { const d = Lst.L[p] - F.L[p] - ds.med; if (d < -ds.thr) cls[p] = 1; else if (d > ds.thr) cls[p] = 2 }
    const bl0 = blobs(cls, g), bl = []; let droppedSteep = 0;
    for (const b of bl0) { let sd = 0; for (const p of b.px) sd += lstd[p]; if (sd / b.px.length >= rough) { droppedSteep += b.area; for (const p of b.px) cls[p] = 0 } else bl.push(b) }
    let darker = 0, brighter = 0, brightWasDark = 0, darkNowDark = 0;
    for (const b of bl) {
      let bs = 0, as = 0, wasDark = 0, nowDark = 0;
      for (const p of b.px) { bs += F.L[p]; as += Lst.L[p]; if (F.L[p] < darkThr) wasDark++; if (Lst.L[p] < darkThr) nowDark++ }
      b.before = bs / b.px.length; b.after = as / b.px.length; b.wasDark = wasDark / b.px.length; b.nowDark = nowDark / b.px.length;
      b.ll = g.ll(b.sx / b.px.length, b.sy / b.px.length); b.bounds = [g.ll(b.minx, b.maxy), g.ll(b.maxx, b.miny)];
      if (b.kind === 1) { darker += b.area; darkNowDark += b.nowDark * b.area } else { brighter += b.area; brightWasDark += b.wasDark * b.area }
    }
    bl.sort((a, b) => b.area - a.area);
    const hot = bl.slice(0, 3).map((b, i) => ({ n: i + 1, kind: b.kind === 1 ? "darker" : "brighter", area: b.area, lon: b.ll[0], lat: b.ll[1], bounds: b.bounds, before: b.before, after: b.after, wasDark: b.wasDark, nowDark: b.nowDark }));
    const changeImg = overlay(g, a => { for (let p = 0; p < N; p++) if (cls[p]) { const c = cls[p] === 1 ? C_DARK : C_BRIGHT; a[p * 4] = c[0]; a[p * 4 + 1] = c[1]; a[p * 4 + 2] = c[2]; a[p * 4 + 3] = 220 } });
    status("Looking at each step between passes…", 0.9); await tick();

    // consecutive steps
    const steps = [];
    for (let i = 0; i + 1 < fr.length; i++) {
      const a = fr[i], b = fr[i + 1], m = new Uint8Array(N); for (let p = 0; p < N; p++) m[p] = a.valid[p] && b.valid[p];
      const s = diffStats(a.L, b.L, m); let dk = 0, br = 0;
      for (let p = 0; p < N; p++) if (m[p]) { const d = b.L[p] - a.L[p] - s.med; if (d < -s.thr) dk += g.rowKm2[p / g.W | 0]; else if (d > s.thr) br += g.rowKm2[p / g.W | 0] }
      steps.push({ from: a.date, to: b.date, darker: dk, brighter: br, med: s.med });
    }
    let un = null, zn = null;
    if (fr.length >= 4) {
      status("Unusual-change test and radar fingerprint zones…", 0.93); await tick();
      un = unusual(fr, common, g, steps.map(s => s.med)); await tick();
      zn = zones(fr, common, g, darkThr, steps.map(s => s.med));
    }
    status("Checking NASA EONET and USGS for events…", 0.97);
    const ev = await evP;
    if (ac.signal.aborted) return null;

    facts = {
      bbox, sensor: pick.sensor, sensorLabel: cfg.label, product: cfg.product, track: pick.track, dir: pick.dir, zoom: g.z, pixelM: g.pxM,
      tiles: { ...STATS }, frames: fr.map(f => f.date), skipped: skipped.map(f => ({ date: f.date, validPct: f.validPct })), thinned: pick.thinned,
      otherSensors: pick.otherSensors, otherTracks: pick.otherTracks, boxKm2, commonKm2, darkThr, darkThrHow: wt.how, mainBody, series,
      water: { lostKm2: wLost, gainedKm2: wGained, bufferM: BUF_M, bodies: nBodies },
      waterHotspots: waterHot,
      change: { droppedSteepKm2: droppedSteep, roughStd: rough, from: F.date, to: Lst.date, darkerKm2: darker, brighterKm2: brighter, median: ds.med, mad: ds.mad, threshold: ds.thr, brighterWasDarkPct: brighter ? brightWasDark / brighter * 100 : 0, darkerNowDarkPct: darker ? darkNowDark / darker * 100 : 0 },
      hotspots: hot, steps,
      unusual: un && { areaKm2: un.area, baselineKm2: un.baseArea, topFrom: un.fromDate, topTo: un.toDate, topKm2: un.topStepArea, baseFrom: un.baseFrom, baseTo: un.baseTo },
      zones: zn && { k: zn.k, sample: zn.sample, list: zn.zones.map(z => ({ label: z.label, meaning: z.meaning, areaKm2: z.area, color: z.col, L: z.L.map(v => +v.toFixed(1)), G: z.G.map(v => +v.toFixed(1)) })) },
      events: ev
    };
    if (window.FALAKUS_DEBUG) api.debug = { fr, g, common };
    facts.narrative = narrate(facts);
    api.facts = facts;
    api.overlays = { corners: g.corners, water: waterImg, changes: changeImg, unusual: un && un.img, zones: zn && zn.img };
    render(facts, api.overlays);
    status(`Done · ${fr.length} passes · ${STATS.ok} tiles · ${STATS.scrambled} scrambled tiles re-fetched${STATS.failed ? ` · ${STATS.failed} could not be fixed (left blank)` : ""}`, 1);
    document.dispatchEvent(new CustomEvent("falakus:explained", { detail: facts }));
    return facts;
  }

  /* ---------------- narrative: ≤ 8 templated sentences ---------------- */
  function trend(series, key = "darkKm2") {
    const v = series.map(s => s[key]), n = v.length, d0 = v[0], d1 = v[n - 1];
    const rel = (d1 - d0) / Math.max(0.5, d0);
    if (Math.abs(rel) < 0.1 && Math.abs(d1 - d0) < 1) return { kind: "flat", d0, d1 };
    const sign = Math.sign(d1 - d0);
    // the stretch of passes where most of the net change happened (max-sum run of steps in the net direction)
    let best = -Infinity, bi = 0, bj = 1, cur = 0, ci = 0;
    for (let i = 1; i < n; i++) { const s = sign * (v[i] - v[i - 1]); if (cur <= 0) { cur = s; ci = i - 1 } else cur += s; if (cur > best) { best = cur; bi = ci; bj = i } }
    const steady = bj < n - 1 && Math.abs(v[n - 1] - v[bj]) <= Math.max(0.5, 0.12 * Math.abs(v[bj]));
    const peak = Math.max(...v), pk = v.indexOf(peak);
    return { kind: sign > 0 ? "rose" : "fell", d0, d1, from: series[bi].date, to: series[bj].date, steady, peak, peakDate: series[pk].date, peakMid: pk > 0 && pk < n - 1 && peak > 1.15 * Math.max(d0, d1) };
  }
  function narrate(f) {
    const S = [], n = f.frames.length, d0 = dD(f.change.from), d1 = dD(f.change.to), c = f.change;
    const src = `NASA GIBS · ${f.product} display tiles, ${dD(f.change.from, false)} vs ${dD(f.change.to)}`;
    const trackTxt = `${f.track && f.track !== "?" ? "track " + f.track + (f.dir ? " " + f.dir : "") : "one track"}`;
    const N = x => `<span class="num">${x}</span>`;
    const ctx = `Between ${d0} and ${d1} (${f.sensor}, ${n} passes, ${trackTxt})`;
    // 2 dark-area trend
    const useMain = !!f.mainBody, key = useMain ? "mainKm2" : "darkKm2", tr = trend(f.series, key);
    const openWater = useMain && f.mainBody.edge && f.mainBody.boxShare > 0.25;
    const what = openWater ? "The open water in the box (sea or a large lake running past the box edge)" : useMain ? "The main dark body (likely the lake, reservoir or river)" : "The darkest part of the scene (likely calm water)";
    // open water turns radar-bright when wind roughens it: big pass-to-pass swings there are weather, not shoreline
    const vals = f.series.map(x => x[key]), med = vals.slice().sort((a, b) => a - b)[vals.length >> 1];
    const jumpy = vals.some((v, i) => i && Math.abs(v - vals[i - 1]) > 0.3 * Math.max(1, med));
    const windNote = jumpy && (openWater || !useMain) ? " Careful: open water jumps like this when wind roughens it and it turns radar-bright, so this is more likely weather than a real shoreline change." : jumpy ? " Some passes jump sharply, which can also be wind on the water, so trust the steady trend more than single passes." : "";
    const thrTxt = `Water-dark = smoothed brightness below ${f.darkThr} of 255 (${f.darkThrHow} in the ${dD(f.series[0].date, false)} histogram)${useMain ? `; main body = largest connected dark patch, ${km(f.mainBody.extentKm2)} km² at its widest` : ""}`;
    const verb = { rose: useMain ? "grew" : "rose", fell: useMain ? "shrank" : "fell" }[tr.kind];
    if (tr.kind === "flat") S.push({ t: `${ctx}, ${what.toLowerCase().replace(/^the /, "the ")} stayed about the same: ${N(km(tr.d0) + " km²")} on ${dD(f.series[0].date, false)} and ${N(km(tr.d1) + " km²")} on ${dD(f.series[f.series.length - 1].date, false)}.${windNote}`, s: thrTxt });
    else S.push({ t: `${ctx}, ${what.toLowerCase()} ${verb} from ${N(km(tr.d0) + " km²")} on ${dD(f.series[0].date, false)} to ${N(km(tr.d1) + " km²")} on ${dD(f.series[f.series.length - 1].date, false)}, mostly between ${dD(tr.from, false)} and ${dD(tr.to, false)}${tr.steady ? ", then held steady" : ""}${tr.peakMid ? `, after peaking at ${km(tr.peak)} km² on ${dD(tr.peakDate, false)}` : ""}${useMain ? ` (all water-dark pixels in the box: ${km(f.series[0].darkKm2)} → ${km(f.series[f.series.length - 1].darkKm2)} km²)` : ""}.${windNote}`, s: thrTxt });
    // water lost / gained (the map's default view)
    if (f.water && f.water.bodies) S.push({ t: `On the map, ${N(km(f.water.lostKm2) + " km²")} that was water-dark on ${dD(f.change.from, false)} no longer is by ${dD(f.change.to, false)} (orange, "water lost": drying shore), and ${N(km(f.water.gainedKm2) + " km²")} became water-dark (blue, "water gained").`, s: `${src}; same water threshold, first vs last pass, only within ${f.water.bufferM} m of the dark water bodies` });
    // darker / brighter elsewhere
    S.push({ t: `Across the whole box, ${N(km(c.darkerKm2) + " km²")} became much darker in radar (new water, wetter or smoother ground) and ${N(km(c.brighterKm2) + " km²")} became much brighter${c.brighterWasDarkPct > 50 ? `, ${c.brighterWasDarkPct.toFixed(0)}% of it water-dark at the start, so mostly exposed shore` : " (rougher or bare ground, structures, debris or crops)"}.`, s: `${src}; more than ${K_SIGMA} robust σ (${c.threshold.toFixed(0)} of 255 levels) after 5×5 smoothing${c.droppedSteepKm2 > 0.05 ? `; ${km(c.droppedSteepKm2)} km² on steep, shadowed terrain left out` : ""}` });
    // 4 hotspot (marker 1 of the default map view)
    const h = (f.waterHotspots && f.waterHotspots[0]) || f.hotspots[0];
    if (h) S.push({ t: `The largest single patch (marker 1) is ${N(km(h.area) + " km²")} ${/water/.test(h.kind) ? `of ${h.kind}` : `that became ${h.kind}`}, around ${h.lat.toFixed(3)}° N, ${Math.abs(h.lon).toFixed(3)}° ${h.lon < 0 ? "W" : "E"} (brightness ${h.before.toFixed(0)} → ${h.after.toFixed(0)} of 255).`, s: `Connected-blob analysis, patches ≥ ${MIN_BLOB_PX} pixels` });
    // 5 when / unusual
    if (f.unusual && f.unusual.areaKm2 >= 0.05) S.push({ t: `${N(km(f.unusual.areaKm2) + " km²")} jumped by more than 4× its own normal pass-to-pass wobble, most of it (${km(f.unusual.topKm2)} km²) between ${dD(f.unusual.topFrom, false)} and ${dD(f.unusual.topTo, false)}; the same test on the first pair flags ${N(km(f.unusual.baselineKm2) + " km²")}, a rough false-alarm level.`, s: `Per-pixel temporal anomaly over ${n} passes (median absolute successive difference)` });
    else if (f.steps.length) { const st = f.steps.reduce((a, b) => (b.darker + b.brighter > a.darker + a.brighter ? b : a)); S.push({ t: `The biggest change between two passes in a row was ${dD(st.from, false)} → ${dD(st.to, false)}: ${N(km(st.darker) + " km²")} darker and ${N(km(st.brighter) + " km²")} brighter.`, s: `Consecutive-pass comparison, ${K_SIGMA} robust σ rule` }) }
    // 6 plant signal
    if (f.sensor === "NISAR") {
      const g0 = f.series[0].meanG, g1 = f.series[f.series.length - 1].meanG, pc = (g1 - g0) / Math.max(1, g0) * 100;
      S.push({ t: Math.abs(pc) < 5 ? `The plant signal (HV-like green channel) is about the same across the box (${N((pc >= 0 ? "+" : "") + pc.toFixed(0) + "%")}).` : `The plant signal (HV-like green channel) ${pc > 0 ? "rose" : "fell"} by ${N(Math.abs(pc).toFixed(0) + "%")} across the box, ${pc > 0 ? "consistent with more vegetation or rougher surfaces" : "consistent with harvest, drying or clearing"}.`, s: `Mean green channel ${g0.toFixed(0)} → ${g1.toFixed(0)} of 255, display-scaled` });
    }
    // 7 zones
    if (f.zones && f.zones.list.length) { const z = f.zones.list.filter(z => !/^steady|all season/.test(z.label)).sort((a, b) => b.areaKm2 - a.areaKm2)[0] || f.zones.list[0]; const wz = f.zones.list.find(z => z.label === "dark all season");
      S.push({ t: /^steady|all season/.test(z.label) ? `Grouping pixels that behave alike over time gives ${f.zones.list.length} zones; none changes strongly as a whole${wz ? `, and the "dark all season" zone (likely open water) covers ${N(km(wz.areaKm2) + " km²")}` : ""}.` : `Grouping pixels that behave alike over time gives ${f.zones.list.length} zones; the biggest changing one, "${z.label}" (${z.meaning}), covers ${N(km(z.areaKm2) + " km²")}.`, s: `Unsupervised k-means on per-pixel time profiles; labels are interpretations` }) }
    // 8 events
    const e = f.events, parts = [];
    if (e.eonet) parts.push(e.eonet.length ? `NASA EONET lists ${e.eonet.slice(0, 2).map(v => `${v.cat ? v.cat.toLowerCase() + " " : ""}"${v.title}"${v.date ? " on " + dD(v.date, false) : ""}`).join(" and ")}${e.eonet.length > 2 ? ` and ${e.eonet.length - 2} more` : ""}` : "NASA EONET lists no natural events");
    if (e.quakes) parts.push(e.quakes.length ? `USGS lists ${e.quakes.length} M4+ earthquake${e.quakes.length > 1 ? "s" : ""} (largest M${Math.max(...e.quakes.map(q => q.mag)).toFixed(1)})` : "USGS lists no M4+ earthquakes");
    if (parts.length) S.push({ t: `${parts.join("; ")} within about 50 km of this box in this period. That is context, not proof of cause.`, s: `NASA EONET v3 and USGS FDSN event APIs, box ± ${EVENT_PAD}°` });
    else S.push({ t: `NASA EONET and USGS could not be reached, so there is no event context.`, s: `NASA EONET v3, USGS FDSN` });
    return S.slice(0, 8);
  }

  /* ---------------- answers to fixed questions ---------------- */
  function answer(q) {
    const f = facts; if (!f) return "Run the analysis first.";
    q = q.toLowerCase(); const c = f.change;
    if (/most|biggest|largest|what changed/.test(q)) { const h = f.hotspots[0]; return h ? `Most change: ${km(c.darkerKm2)} km² became darker and ${km(c.brighterKm2)} km² brighter between ${dD(c.from)} and ${dD(c.to)}. The largest patch is ${km(h.area)} km² (${h.kind}) at ${h.lat.toFixed(3)}° N, ${h.lon.toFixed(3)}° E.` : `No patch passed the ${K_SIGMA}-σ test between ${dD(c.from)} and ${dD(c.to)}.` }
    if (/when|date|time/.test(q)) { const st = f.steps.reduce((a, b) => (b.darker + b.brighter > a.darker + a.brighter ? b : a), f.steps[0]); const tr = trend(f.series); return `The biggest pass-to-pass change was ${dD(st.from)} → ${dD(st.to)} (${km(st.darker)} km² darker, ${km(st.brighter)} km² brighter).` + (tr.kind !== "flat" ? ` The dark (likely water) area ${tr.kind} mostly between ${dD(tr.from)} and ${dD(tr.to)}.` : "") + (f.unusual ? ` The unusual-change test puts the main jump at ${dD(f.unusual.topFrom)} → ${dD(f.unusual.topTo)}.` : "") }
    if (/water|flood|lake|reservoir|wet/.test(q)) return `Calm water is very dark in radar. Here "water-dark" means below ${f.darkThr} of 255 (${f.darkThrHow} of the first pass). ${f.mainBody ? `The main dark body went ${km(f.series[0].mainKm2)} → ${km(f.series[f.series.length - 1].mainKm2)} km²; all water-dark pixels together` : "That area"} went ${km(f.series[0].darkKm2)} → ${km(f.series[f.series.length - 1].darkKm2)} km². ${c.darkerNowDarkPct > 50 ? `Of the area that got darker, ${c.darkerNowDarkPct.toFixed(0)}% is now water-dark.` : ""} ${c.brighterWasDarkPct > 50 ? `Of the area that got brighter, ${c.brighterWasDarkPct.toFixed(0)}% was water-dark at the start, which looks like receding water.` : ""} Smooth tarmac, sand or radar shadow can also look dark, so treat it as "likely".`.replace(/\s+/g, " ");
    if (/unusual|normal|anomal|false/.test(q)) return f.unusual ? `${km(f.unusual.areaKm2)} km² changed by more than 4× its own normal wobble (vs ${km(f.unusual.baselineKm2)} km² flagged by the same test on the first pair).` : "Needs at least 4 passes on the same track.";
    if (/zone|cluster|alike/.test(q)) return f.zones ? f.zones.list.map(z => `${z.label} (${z.meaning}): ${km(z.areaKm2)} km²`).join("; ") + "." : "Needs at least 4 passes on the same track.";
    if (/plant|crop|veget|green|tree/.test(q)) { const g0 = f.series[0].meanG, g1 = f.series[f.series.length - 1].meanG; return f.sensor === "NISAR" ? `Mean plant signal (HV-like green) went ${g0.toFixed(0)} → ${g1.toFixed(0)} of 255.` : "Sentinel-1 tiles here are single-channel, so there is no plant (HV) signal." }
    return `I can answer from the measured facts only: try "what changed most?", "when?", "is it water?", "is it unusual?", "zones" or "plants".`;
  }
  async function ask(q) {
    const out = ui.ans; if (!q.trim()) return;
    const ep = window.FALAKUS_LLM_ENDPOINT;
    if (ep && facts) {
      out.textContent = "Asking…";
      try { const r = await fetch(ep, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question: q, facts }) }); const j = await r.json().catch(() => null); out.textContent = (j && (j.answer || j.text)) || "No answer."; return }
      catch (e) { out.textContent = answer(q) + " (offline answer: the server was not reachable)"; return }
    }
    out.textContent = answer(q);
  }

  /* ---------------- panel ---------------- */
  function build() {
    injectStyle();
    const el = document.createElement("aside"); el.id = "fx-panel"; el.setAttribute("aria-label", "Falakus explains");
    el.innerHTML = `<div class="fx-h"><div><b>Falakus explains</b><small>What changed in radar, measured from NASA data. Every sentence shows its number and source.</small></div><button class="fx-x" aria-label="Close">×</button></div>
<div class="fx-body"><div class="fx-prog"><i></i></div><div class="fx-st" aria-live="polite"></div><div class="fx-out"></div></div>`;
    document.body.appendChild(el);
    ui = { el, bar: el.querySelector(".fx-prog i"), st: el.querySelector(".fx-st"), out: el.querySelector(".fx-out") };
    el.querySelector(".fx-x").onclick = close;
  }
  function status(t, p, err) { if (!ui) return; ui.st.innerHTML = err ? `<span class="err">${esc(t)}</span>` : esc(t); ui.bar.style.width = (p * 100).toFixed(0) + "%"; ui.bar.parentNode.style.visibility = p >= 1 || err ? "hidden" : "visible" }
  function spark(series, key) {
    const v = series.map(s => s[key]), mx = Math.max(...v, 0.1), W = 380, H = 64, n = v.length;
    const X = i => 6 + i * (W - 12) / Math.max(1, n - 1), Y = y => H - 14 - y / mx * (H - 26);
    const pts = v.map((y, i) => `${X(i).toFixed(1)},${Y(y).toFixed(1)}`).join(" ");
    return `<svg class="spark" viewBox="0 0 ${W} ${H}" role="img" aria-label="Dark (likely water) area per pass"><polyline fill="none" stroke="#56B4E9" stroke-width="2" points="${pts}"/>${v.map((y, i) => `<circle cx="${X(i)}" cy="${Y(y)}" r="2.6" fill="#F2F5FA"><title>${dD(series[i].date)}: ${km(y)} km²</title></circle>`).join("")}
<text x="6" y="${H - 2}" fill="#8A9BB4" font-size="10" font-family="JetBrains Mono">${dD(series[0].date, false)}</text><text x="${W - 6}" y="${H - 2}" text-anchor="end" fill="#8A9BB4" font-size="10" font-family="JetBrains Mono">${dD(series[n - 1].date, false)}</text>
<text x="6" y="10" fill="#8A9BB4" font-size="10" font-family="JetBrains Mono">${km(mx)} km² max</text></svg>`;
  }
  function miniCurve(z) { const W = 60, H = 18, a = z.L, mn = 0, mx = 255, X = i => i * W / Math.max(1, a.length - 1), Y = v => H - 1 - (v - mn) / (mx - mn) * (H - 2); return `<svg width="${W}" height="${H}" aria-hidden="true"><polyline fill="none" stroke="${z.color}" stroke-width="1.6" points="${a.map((v, i) => X(i).toFixed(1) + "," + Y(v).toFixed(1)).join(" ")}"/>${z.G && z.G.some(v => v) ? `<polyline fill="none" stroke="#9BD28A" stroke-width="1" stroke-dasharray="2 2" points="${z.G.map((v, i) => X(i).toFixed(1) + "," + Y(v).toFixed(1)).join(" ")}"/>` : ""}</svg>` }

  function render(f, img) {
    const mapOk = !!getMap();
    const legend = {
      water: f.water && f.water.bodies ? `<div><span class="sw" style="background:rgb(${C_BRIGHT})"></span>Water lost: ${km(f.water.lostKm2)} km² <span class="note">water-dark on ${dD(f.change.from, false)}, not on ${dD(f.change.to, false)}: shore dried or water roughened</span></div><div><span class="sw" style="background:rgb(${C_DARK})"></span>Water gained: ${km(f.water.gainedKm2)} km² <span class="note">not water-dark at first, water-dark at the end</span></div><span class="note">Only within ${f.water.bufferM} m of the ${f.water.bodies > 1 ? f.water.bodies + " largest dark water bodies" : "main dark water body"} in this box (each at least 10% of the biggest one), so hillside shadow elsewhere is ignored.</span>` : `<span class="note">No water body of 0.5 km² or more in this box.</span>`,
      changes: `<div><span class="sw" style="background:rgb(${C_DARK})"></span>Became darker: ${km(f.change.darkerKm2)} km² <span class="note">possible new water, flooding, smoother ground</span></div><div><span class="sw" style="background:rgb(${C_BRIGHT})"></span>Became brighter: ${km(f.change.brighterKm2)} km² <span class="note">rougher or bare ground, structures, debris, crops</span></div>${f.change.droppedSteepKm2 > 0.05 ? `<span class="note">${km(f.change.droppedSteepKm2)} km² of change on steep, shadowed terrain is hidden (9×9 brightness spread above ${f.change.roughStd.toFixed(1)}, the scene's top 15%).</span>` : ""}`,
      unusual: f.unusual ? `<div><span class="sw" style="background:rgb(${C_UNUSUAL})"></span>Unusual change (vs this pixel's own normal): ${km(f.unusual.areaKm2)} km²</div><span class="note">Each pixel's biggest pass-to-pass jump, flagged when it is more than 4× that pixel's median jump. Main date ${dD(f.unusual.topFrom, false)} → ${dD(f.unusual.topTo)}. Quiet baseline (first pair, ${dD(f.unusual.baseFrom, false)} → ${dD(f.unusual.baseTo, false)}): ${km(f.unusual.baselineKm2)} km².</span>` : "",
      zones: f.zones ? f.zones.list.map(z => `<div><span class="sw" style="background:${z.color}"></span>${miniCurve(z)}<span><b>${esc(z.label)}</b> → ${esc(z.meaning)} · ${km(z.areaKm2)} km²</span></div>`).join("") + `<span class="note">Zones that behave alike: unsupervised k-means (k=${f.zones.k}) on each pixel's brightness${f.sensor === "NISAR" ? " and plant-signal" : ""} curve, display-scaled radar. Labels are interpretations. Curve: brightness (solid), plant signal (dashed).</span>` : ""
    };
    const fewer = !f.unusual;
    ui.out.innerHTML = `<ol class="fx-say">${f.narrative.map(s => `<li>${s.t}<span class="src">${esc(s.s)}</span></li>`).join("")}</ol>
<h4>${f.mainBody ? "Main dark body (likely water)" : "Dark (likely water) area"}, km² per pass</h4>${spark(f.series, f.mainBody ? "mainKm2" : "darkKm2")}
<div class="fx-seg" role="group" aria-label="Map view"><button data-m="water" ${f.water && f.water.bodies ? "" : "disabled title='No water body here'"}>Water</button><button data-m="changes">Changes</button><button data-m="unusual" ${fewer ? "disabled title='Needs 4+ passes'" : ""}>Unusual</button><button data-m="zones" ${fewer || !f.zones ? "disabled title='Needs 4+ passes'" : ""}>Zones</button></div>
<div class="fx-leg"></div>
${mapOk ? `<label class="tg"><input type="checkbox" checked> Show on map</label>` : `<p class="err">No map found on this page, so the changes are listed but not drawn.</p>`}
<div class="fx-spots"></div>
<details><summary>How we know / limits</summary><ul>
<li>Source: NASA GIBS ${esc(f.product)} display tiles (zoom ${f.zoom}, ~${f.pixelM.toFixed(0)} m pixels), ${f.frames.length} passes: ${f.frames.map(d => dD(d, false)).join(", ")}.</li>
<li>These are display-scaled PNG tiles, not calibrated dB backscatter, so this is screening only. "Brightness" is the mean of the three colour channels on a 0–255 scale.</li>
<li>Speckle is smoothed with a 5×5 mean. A pixel counts as changed when its difference is more than ${K_SIGMA} robust standard deviations (1.4826 × MAD = ${(1.4826 * f.change.mad).toFixed(1)}) from the median difference, and at least ${MIN_ABS} levels; patches smaller than ${MIN_BLOB_PX} pixels are dropped.</li>
<li>"Likely water" = smoothed brightness below ${f.darkThr}/255 (${esc(f.darkThrHow)} of the first pass's histogram). Smooth tarmac, wet mud, sand and radar shadow behind hills can also be this dark.</li>
<li>Only one sensor and one track are compared (${esc(f.sensor)}, ${f.track && f.track !== "?" ? "track " + esc(f.track) + " " + esc(f.dir) : "most frequent track"}), so viewing angle stays the same.${f.otherSensors.length ? ` Frames from ${esc(f.otherSensors.join(", "))} were not compared: different sensors are never compared to each other.` : ""}${f.otherTracks ? ` ${f.otherTracks} other track(s) were left out.` : ""}${f.thinned ? ` ${f.thinned} passes were thinned out (max ${MAX_FRAMES}).` : ""}</li>
<li>Areas are on the ${km(f.commonKm2)} km² of the ${km(f.boxKm2)} km² box that every pass covers.${f.skipped.length ? ` Left out for partial coverage: ${f.skipped.map(s => dD(s.date, false) + " (" + s.validPct.toFixed(0) + "%)").join(", ")}.` : ""}</li>
<li>Tiles: ${f.tiles.ok} good, ${f.tiles.scrambled} scrambled tiles rejected and re-fetched, ${f.tiles.parentFill} filled from a coarser zoom level, ${f.tiles.failed} could not be fixed and are treated as no data. Zoom is chosen so the box is up to 1024 px wide within a budget of ${TILE_BUDGET} tiles.</li>
<li>Events from NASA EONET and USGS are shown as context only, never as proof.</li></ul></details>
<h4>Ask</h4><div class="chips"><button class="chip">What changed most?</button><button class="chip">When?</button><button class="chip">Is it water?</button>${f.unusual ? `<button class="chip">Is it unusual?</button>` : ""}</div>
<form class="fx-ask"><input placeholder="Ask about this area" aria-label="Ask a question about this analysis"><button>Ask</button></form><div class="fx-ans" aria-live="polite"></div>`;
    ui.ans = ui.out.querySelector(".fx-ans");
    ui.out.querySelectorAll(".chip").forEach(b => b.onclick = () => ask(b.textContent));
    ui.out.querySelector(".fx-ask").onsubmit = e => { e.preventDefault(); ask(e.target.querySelector("input").value) };
    const leg = ui.out.querySelector(".fx-leg");
    const spots = ui.out.querySelector(".fx-spots");
    const setMode = m => {
      mode = m; ui.out.querySelectorAll(".fx-seg button").forEach(b => b.setAttribute("aria-pressed", b.dataset.m === m)); leg.innerHTML = legend[m];
      const hs = hotFor(f, m);
      spots.innerHTML = hs.length ? `<h4>Biggest ${m === "water" ? "water" : "change"} spots</h4><div class="fx-hs">${hs.map(h => `<button data-h="${h.n}"><span class="fx-pin ${pinCls(h)}">${h.n}</span><span>${km(h.area)} km² ${/water/.test(h.kind) ? h.kind : "became " + h.kind}<span class="dt">brightness ${h.before.toFixed(0)} → ${h.after.toFixed(0)} of 255${/water/.test(h.kind) ? "" : ` · ${(h.wasDark * 100).toFixed(0)}% water-dark before, ${(h.nowDark * 100).toFixed(0)}% after`}</span></span></button>`).join("")}</div>` : "";
      spots.querySelectorAll("button").forEach(b => b.onclick = () => focusHot(hs[b.dataset.h - 1]));
      applyVis();
    };
    ui.out.querySelectorAll(".fx-seg button").forEach(b => b.onclick = () => !b.disabled && setMode(b.dataset.m));
    const tg = ui.out.querySelector("label.tg input"); if (tg) tg.onchange = () => { shown = tg.checked; applyVis() };
    shown = true; setMode(f.water && f.water.bodies ? "water" : "changes");
    drawMap(f, img);
  }

  /* ---------------- map ---------------- */
  const LAYERS = { water: "fx-water", changes: "fx-change", unusual: "fx-unusual", zones: "fx-zones" };
  const hotFor = (f, m) => m === "water" ? f.waterHotspots || [] : m === "changes" ? f.hotspots : [];
  const pinCls = h => /gained|darker/.test(h.kind) ? "dark" : "bright";
  let markers = [], popup = null, shown = true;
  function clearMap() {
    const m = getMap(); markers.forEach(k => k.remove()); markers = []; if (popup) { popup.remove(); popup = null }
    if (!m) return;
    for (const id of Object.values(LAYERS)) { try { if (m.getLayer(id)) m.removeLayer(id); if (m.getSource(id)) m.removeSource(id) } catch (e) { } }
  }
  function applyVis() {
    const m = getMap(); if (!m) return;
    for (const [k, id] of Object.entries(LAYERS)) try { if (m.getLayer(id)) m.setLayoutProperty(id, "visibility", shown && k === mode ? "visible" : "none") } catch (e) { }
    markers.forEach(k => k.getElement().style.display = shown && k._fxMode === mode ? "" : "none");
  }
  async function drawMap(f, img) {
    const m = getMap(); if (!m) return;
    const add = () => {
      for (const k of Object.keys(LAYERS)) { const url = img[k]; if (!url) continue; const id = LAYERS[k]; m.addSource(id, { type: "image", url, coordinates: img.corners }); m.addLayer({ id, type: "raster", source: id, paint: { "raster-opacity": 0.9, "raster-resampling": "nearest", "raster-fade-duration": 0 } }) }
    };
    try { add() } catch (e) { clearMap(); await new Promise(r => { m.once("idle", r); setTimeout(r, 4000) }); try { add() } catch (e2) { console.warn("Falakus explain: could not draw overlay", e2); return } }
    const ML = window.maplibregl;
    if (ML && ML.Marker) for (const md of ["water", "changes"]) for (const h of hotFor(f, md)) {
      const el = document.createElement("button"); el.className = "fx-pin " + pinCls(h); el.textContent = h.n; el.setAttribute("aria-label", `Spot ${h.n}: ${km(h.area)} km² ${h.kind}`);
      el.addEventListener("click", ev => { ev.stopPropagation(); focusHot(h) });
      const mk = new ML.Marker({ element: el }).setLngLat([h.lon, h.lat]).addTo(m); mk._fxMode = md; markers.push(mk);
    }
    applyVis();
  }
  function focusHot(h) {
    const m = getMap(); if (!m || !h) return;
    const [[w, s], [e, n]] = h.bounds, pw = Math.max(0.004, (e - w) * 0.3), ph = Math.max(0.004, (n - s) * 0.3);
    m.fitBounds([[w - pw, s - ph], [e + pw, n + ph]], { padding: 60, maxZoom: 14, duration: 900 });
    const ML = window.maplibregl; if (!ML || !ML.Popup) return;
    if (popup) popup.remove();
    popup = new ML.Popup({ offset: 16, closeButton: true, className: "fx-pop" }).setLngLat([h.lon, h.lat])
      .setHTML(`<div style="font:13px/1.4 'Fira Sans',sans-serif;color:#0D1B2E"><b>Spot ${h.n}: ${km(h.area)} km² ${/water/.test(h.kind) ? h.kind : "became " + h.kind}</b><br>Radar brightness ${h.before.toFixed(0)} → ${h.after.toFixed(0)} of 255<br>Water-dark: ${(h.wasDark * 100).toFixed(0)}% before → ${(h.nowDark * 100).toFixed(0)}% after<br><span style="color:#5a6b84">${dD(facts.change.from)} vs ${dD(facts.change.to)} · ${esc(facts.product)}</span></div>`).addTo(m);
  }

  /* ---------------- public API ---------------- */
  /* ---------------- cached analyses (web/cases/explain/<placeId>.json, written by tools/explain_cache.mjs) ---------------- */
  const CACHE_DIR = (SCRIPT_SRC || location.href).replace(/[^/]*$/, "") + "cases/explain/";
  let cIndex = null; const cMem = {};
  const cacheIndex = () => cIndex || (cIndex = fetch(CACHE_DIR + "index.json").then(r => r.ok ? r.json() : []).catch(() => []));
  function precompute(id) { return cMem[id] || (cMem[id] = fetch(CACHE_DIR + encodeURIComponent(id) + ".json").then(r => r.ok ? r.json() : null).catch(() => null)) }
  const iou = (a, b) => { const w = Math.min(a[2], b[2]) - Math.max(a[0], b[0]), h = Math.min(a[3], b[3]) - Math.max(a[1], b[1]); if (w <= 0 || h <= 0) return 0; const i = w * h; return i / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i) };
  const days = (a, b) => Math.abs(Date.parse(a) - Date.parse(b)) / 864e5;
  async function findCached(studio) {
    if (!studio || !Array.isArray(studio.bbox)) return null;
    const pk = pickFrames(studio); if (pk.err || pk.frames.length < 2) return null;
    const d0 = pk.frames[0].date, d1 = pk.frames[pk.frames.length - 1].date, list = await cacheIndex();
    const hit = (Array.isArray(list) ? list : []).find(e => e.sensor === pk.sensor && (studio.placeId === e.id || iou(studio.bbox.map(Number), e.bbox) >= 0.5) && days(d0, e.from) <= 12 && days(d1, e.to) <= 12);
    return hit ? precompute(hit.id) : null;
  }
  function showCached(c, studio) {
    facts = c.facts; api.facts = facts; api.overlays = c.overlays; clearMap();
    render(facts, c.overlays);
    const b = document.createElement("div"); b.className = "fx-cached";
    b.innerHTML = `Cached analysis from ${esc(new Date(c.ts).toUTCString().slice(5, 22))} UTC <button>Re-run live</button>`;
    b.querySelector("button").onclick = () => run(studio);
    ui.out.prepend(b); status(`Same steps as a live run, computed ahead of time for this place and period (${facts.frames.length} passes).`, 1);
    document.dispatchEvent(new CustomEvent("falakus:explained", { detail: facts }));
    return facts;
  }
  async function open() {
    if (!ui) build(); const studio = window.FALAKUS_STUDIO;
    if (ctl) ctl.abort(); clearMap(); ui.out.innerHTML = ""; status("Looking for a ready analysis of this place…", 0.02);
    const c = await findCached(studio);
    return c && c.facts && c.overlays ? showCached(c, studio) : run(studio);
  }
  function close() { if (ctl) ctl.abort(); clearMap(); if (ui) { ui.el.remove(); ui = null } }
  const api = { open, close, run, precompute, facts: null, overlays: null, answer: q => answer(q) };
  window.FalakusExplain = api;
  document.addEventListener("falakus:studio", e => { if (e.detail) window.FALAKUS_STUDIO = e.detail; if (ui) run(window.FALAKUS_STUDIO) });
})();
