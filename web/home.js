/* Falakus home: NISAR radar explorer.
   Data paths (all public, no keys): NASA GIBS WMTS tiles of NISAR L2 GCOV by pass date, NASA CMR granule search (CORS) for the
   exact passes over a box, USGS + NASA EONET live events, MODIS/VIIRS true colour and OPERA Sentinel-1 RTC from GIBS. */
"use strict";
(() => {
const Q = new URLSearchParams(location.search);
const PITCH = Q.get("pitch") === "1", DEBUG = Q.get("debug") === "1" && !PITCH;
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const iso = d => d.toISOString().slice(0, 10);
const today = iso(new Date());
const addDays = (s, n) => { const d = new Date(s + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return iso(d) };
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const fmt = s => { const [y, m, d] = s.slice(0, 10).split("-"); return `${+d} ${MON[+m - 1]} ${y}` };
const fmtS = s => { const [, m, d] = s.slice(0, 10).split("-"); return `${+d} ${MON[+m - 1]}` };
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ---------------- icons: one 1.5 px stroke set (24 px grid), used inline and drawn on the map ---------------- */
const IC = {
  quake: "M2 12h4l2-6 3 12 3-9 2 3h6",
  fire: "M12 3c3.5 4 6 6.8 6 10.5a6 6 0 0 1-12 0c0-2.6 1.6-4.3 3.2-5.8.1 2 .9 3.3 2.3 3.6-.5-3 .1-5.6.5-8.3z",
  flood: "M3 16c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0M3 20c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0M12 3c-2.4 3-3.8 5-3.8 6.8a3.8 3.8 0 0 0 7.6 0C15.8 8 14.4 6 12 3z",
  storm: "M12 12m-2.2 0a2.2 2.2 0 1 0 4.4 0a2.2 2.2 0 1 0-4.4 0M4.5 10A8 8 0 0 1 17 5.2M19.5 14A8 8 0 0 1 7 18.8",
  volcano: "M3 20l6-9h6l6 9zM10 7.5L9 4M14 7.5l1-3.5M12 7V2.5",
  ice: "M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5L12 7l2.5-2.5M9.5 19.5L12 17l2.5 2.5",
  other: "M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0-6 0",
  camera: "M4 8h3l2-3h6l2 3h3v11H4zM12 16.5a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4z",
  radar: "M4.5 19.5a9 9 0 0 1 0-12.7l12.7 12.7a9 9 0 0 1-12.7 0zM10.8 13.2l5-5M15 3.5a5.5 5.5 0 0 1 5.5 5.5M15 6.5A2.5 2.5 0 0 1 17.5 9",
  play: "M8 5v14l11-7z", pause: "M8 5v14M16 5v14", record: "M12 12m-6 0a6 6 0 1 0 12 0a6 6 0 1 0-12 0",
  compare: "M12 3v18M4 7h5v10H4zM15 7h5v10h-5z", swipe: "M9 8l-4 4 4 4M15 8l4 4-4 4",
  timelapse: "M12 7v5l3 2M3.5 12A8.5 8.5 0 1 0 6 6M3 3v4h4",
  draw: "M4 4h3M10 4h4M17 4h3v3M20 10v4M20 17v3h-3M14 20h-4M7 20H4v-3M4 14v-4M4 7V4",
  globe: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3c2.6 2.6 2.6 15.4 0 18M12 3c-2.6 2.6-2.6 15.4 0 18",
  map: "M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2zM9 4v14M15 6v14",
  search: "M11 11m-6.5 0a6.5 6.5 0 1 0 13 0a6.5 6.5 0 1 0-13 0M20 20l-4.4-4.4",
  close: "M6 6l12 12M18 6L6 18", pulse: "M3 12h4l3 7 4-14 3 7h4",
  book: "M4 5a2 2 0 0 1 2-2h13v15H6a2 2 0 0 0-2 2zM4 20a2 2 0 0 0 2 2h13v-4", learn: "M2 9l10-5 10 5-10 5zM6 11v5c3 2.5 9 2.5 12 0v-5M22 9v6",
  city: "M4 21V9l5-3v15M9 21V3l7 4v14M16 21V11l4 2v8M3 21h18", forest: "M12 3l-6 8.5h3.8L7 16.5h10l-2.8-5H18zM12 16.5V21",
  lake: "M3 13c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0M5 18c1.8-1.2 3.6-1.2 5.4 0s3.6 1.2 5.4 0M7 8.5c1.7-3.5 8.3-3.5 10 0",
  mountain: "M2 20l7-12 4 6 3-4 6 10zM7.6 10.5l1.4 1 1.4-1", ext: "M14 4h6v6M20 4l-9 9M18 14v6H4V6h6"
};
const svg = (k, s = 18) => `<svg class="i" width="${s}" height="${s}" viewBox="0 0 24 24" aria-hidden="true"><path d="${IC[k] || IC.other}"/></svg>`;
$$("[data-ic]").forEach(e => e.outerHTML = svg(e.dataset.ic));

/* ---------------- config ---------------- */
const NISAR = "NISAR_L2_Geocoded_Polarimetric_Covariance";
const COLL = [["C3622241360-ASF", "validated"], ["C2854338529-ASF", "provisional"]];
const NISAR_FIRST = "2025-10-29";
const gibsUrl = (layer, date, set, ext = "png") => `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${layer}/default/${date}/${set}/{z}/{y}/{x}.${ext}`;
const T = (layer, date, set, ext) => gibsUrl(layer, date, set, ext).replace("https://", "gibs://");
const NIS = d => T(NISAR, d, "GoogleMapsCompatible_Level13");
const EV_COL = { quake: "#D93025", Wildfires: "#E8590C", Floods: "#3B82F6", "Severe Storms": "#8B6CF0", Volcanoes: "#C2410C", "Sea and Lake Ice": "#14B8A6", other: "#8A9BB4" };
const EV_IC = { quake: "quake", Wildfires: "fire", Floods: "flood", "Severe Storms": "storm", Volcanoes: "volcano", "Sea and Lake Ice": "ice", other: "other" };
const EV_LBL = { quake: "Earthquake", Wildfires: "Wildfire", Floods: "Flood", "Severe Storms": "Storm", Volcanoes: "Volcano", "Sea and Lake Ice": "Sea & lake ice", other: "Event" };
/* Start places: each one was checked against NASA CMR (15 Nov 2026) and has NISAR passes. */
/* Start places, grouped. Every place was checked against NASA CMR (15 Nov 2026) and has NISAR GCOV passes; "pre" places are
   prefetched into the browser cache for an instant demo. One neutral line each. */
const PLACES = [
  { g: "Big events of 2026", gmTrack: "141D", id: "panama_m77", name: "Panama M7.7 earthquake", sub: "9 Oct 2026, 17:56 UTC · USGS us6000u18k · same-track before / after", c: [-80.7566, 7.6069], z: 9.3, ic: "quake", ev: "2026-10-09T17:56:05Z", pre: 1, feat: 1 },
  { g: "Big events of 2026", id: "flores", name: "Indonesia M7.8, Flores Sea", sub: "14 Aug 2026, 21:58 UTC · USGS us6000tkt2", c: [121.3446, -8.3358], z: 9, ic: "quake", ev: "2026-08-14T21:58:21Z" },
  { g: "Big events of 2026", id: "venezuela", name: "Venezuela M7.5, Catia La Mar", sub: "24 Jun 2026, 22:05 UTC · USGS us6000t7zp", c: [-67.12, 10.58], z: 9.3, ic: "quake", ev: "2026-06-24T22:05:04Z" },
  { g: "Big events of 2026", id: "colombia", name: "Colombia M7.4, San José del Palmar", sub: "10 Aug 2026, 12:34 UTC · USGS us6000tjl2", c: [-76.2558, 4.8601], z: 9.5, ic: "quake", ev: "2026-08-10T12:34:28Z" },
  { g: "Big events of 2026", id: "chiapas", name: "Mexico M7.3, offshore Chiapas", sub: "17 Jul 2026, 14:48 UTC · USGS us7000t1bu · coast nearest the epicentre", c: [-92.6, 14.75], z: 8.8, ic: "quake", ev: "2026-07-17T14:48:39Z" },
  { g: "Big events of 2026", id: "nagqu", name: "Tibet M7.0, Nagqu", sub: "22 Oct 2026, 14:33 UTC · USGS us6000u43g", c: [93.7837, 32.3376], z: 9.3, ic: "quake", ev: "2026-10-22T14:33:40Z" },
  { g: "Famous change", id: "aral", name: "Aral Sea", sub: "Remaining water, salt flats and former seabed", c: [59.8, 45.2], z: 8, ic: "lake", pre: 1 },
  { g: "Famous change", id: "rondonia", name: "Rondônia, Amazon", sub: "Clearing frontier: cleared land loses the green (HV)", c: [-63.9, -9.2], z: 9, ic: "forest" },
  { g: "Famous change", id: "jakobshavn", name: "Sermeq Kujalleq (Jakobshavn), Greenland", sub: "Fast glacier and iceberg-filled fjord", c: [-49.6, 69.2], z: 8.6, ic: "ice", pre: 1 },
  { g: "Famous change", id: "deadsea", name: "Dead Sea", sub: "Shoreline, evaporation ponds and sinkhole belt", c: [35.5, 31.5], z: 9.6, ic: "lake" },
  { g: "Famous change", id: "dubai", name: "Dubai coast, UAE", sub: "Artificial islands and a growing coastline", c: [55.15, 25.1], z: 10.3, ic: "city", pre: 1 },
  { g: "Famous change", id: "nile_delta", name: "Nile delta, Egypt", sub: "Irrigated fields, canals and towns", c: [31.0, 30.9], z: 9.5, ic: "flood", pre: 1 },
  { g: "NASA's own NISAR first images", id: "ndakota", name: "North Dakota wetlands & farmland", sub: "NASA's first NISAR image, 23 Aug 2025 (PIA26615) · see it today", c: [-97.2, 48.1], z: 9.3, ic: "radar", nasa: { id: "PIA26615", img: "https://images-assets.nasa.gov/image/PIA26615/PIA26615~medium.jpg", date: "2025-08-23" } },
  { g: "NASA's own NISAR first images", id: "maine", name: "Mount Desert Island, Maine", sub: "NASA's NISAR first image, 21 Aug 2025 (PIA26616) · see it today", c: [-68.3, 44.35], z: 10, ic: "radar", nasa: { id: "PIA26616", img: "https://images-assets.nasa.gov/image/PIA26616/PIA26616~medium.jpg", date: "2025-08-21" } },
  { g: "Home case: Uzbekistan", id: "andijan", name: "Andijan reservoir, Uzbekistan", sub: "Reservoir shoreline; our own 20 m calibrated radar when zoomed in", c: [73.21, 40.77], z: 10.3, ic: "lake", pre: 1 },
  { g: "Home case: Uzbekistan", id: "tashkent", name: "Tashkent, Uzbekistan", sub: "City blocks are bright: walls and streets reflect the radar back", c: [69.28, 41.31], z: 10.5, ic: "city", pre: 1 },
  { g: "Conflict-affected areas", id: "gaza", name: "Gaza Strip", sub: "Radar backscatter change since 19 Jun 2026; radar shows surface change, not its cause", c: [34.4, 31.45], z: 10.2, ic: "radar", span: 1, pre: 1 },
  { g: "Conflict-affected areas", id: "ukraine_east", name: "Eastern Ukraine, near Bakhmut", sub: "Radar backscatter change since 21 Jun 2026; radar shows surface change, not its cause", c: [38.0, 48.6], z: 10.2, ic: "radar", span: 1 },
  { g: "More places", id: "langtang", name: "Langtang valley, Nepal", sub: "Steep Himalayan valley, often under monsoon cloud", c: [85.51, 28.19], z: 10.5, ic: "mountain" },
  { g: "More places", id: "mekong", name: "Mekong delta, Vietnam", sub: "Rice paddies, channels and the coast", c: [105.8, 10.0], z: 9.5, ic: "flood" },
  { g: "More places", id: "urmia", name: "Lake Urmia, Iran", sub: "Salt lake: water and exposed lakebed", c: [45.4, 37.7], z: 8.8, ic: "lake" },
  { g: "More places", id: "borneo", name: "Central Kalimantan, Borneo", sub: "Peatland forest, canals and plantations", c: [114, -2.3], z: 9.5, ic: "forest" },
  { g: "More places", id: "lagos", name: "Lagos, Nigeria", sub: "Lagoon city and coast", c: [3.4, 6.5], z: 10.3, ic: "city" },
  { g: "More places", id: "mumbai", name: "Mumbai, India", sub: "Calm sea black, city bright, mangroves green", c: [72.87, 19.05], z: 10.3, ic: "city" },
  { g: "More places", id: "charvak", name: "Charvak reservoir, Uzbekistan", sub: "Mountain reservoir above Tashkent", c: [69.95, 41.62], z: 10.5, ic: "lake" },
  { g: "More places", id: "pineisland", name: "Pine Island glacier, Antarctica", sub: "Ice shelf and glacier front", c: [-100, -75.2], z: 7.5, ic: "ice" }
];

/* ---------------- debug counters ---------------- */
const DBG = { ok: 0, rejected: 0, err: 0, hit: 0, pre: 0, preTot: 0, ready: 0, last: "" };
const dbgEl = $("#debug");
function dbg() { if (!DEBUG) return; dbgEl.hidden = false; dbgEl.innerHTML = `<b>debug</b><br>GIBS tiles ok ${DBG.ok} · cache hits ${DBG.hit}<br>scrambled seen <b>${DBG.rejected}</b> · retries ${DBG.retry || 0} (fixed ${DBG.retryOk || 0})<br>final failures ${DBG.fail || 0} · parent fill ${DBG.fallback || 0}<br>tile/map errors ${DBG.err}<br>prefetch ${DBG.pre}/${DBG.preTot} tiles<br>Ready offline: <b>${DBG.ready}/${PLACES.filter(x => x.pre).length}</b> places${DBG.last ? "<br><span style='color:#8A9BB4'>" + esc(DBG.last.slice(0, 80)) + "</span>" : ""}` }
setInterval(dbg, 1000);

/* ---------------- GIBS tile guard + browser cache ----------------
   GIBS sometimes returns scrambled NISAR tiles at z11-13 (random alpha, or grey static). We decode each tile and reject those,
   so MapLibre keeps the parent tile. Good tiles go into the Cache API, so prefetched start places never wait on the network. */
const CACHE_NAME = "falakus-gibs-v1";
const cacheP = (async () => { try { return "caches" in self ? await caches.open(CACHE_NAME) : null } catch (e) { return null } })();
async function checkTile(url, buf) {
  if (buf.byteLength < 400) return buf;                                  // empty / transparent tile
  if (url.includes("HLS_")) {                                            // optical no-data comes as black: make it transparent
    const bmp = await createImageBitmap(new Blob([buf])); const c = new OffscreenCanvas(bmp.width, bmp.height), x = c.getContext("2d"); x.drawImage(bmp, 0, 0);
    const im = x.getImageData(0, 0, c.width, c.height), a = im.data; for (let i = 0; i < a.length; i += 4) if (a[i] + a[i + 1] + a[i + 2] < 9) a[i + 3] = 0; x.putImageData(im, 0, 0);
    return await (await c.convertToBlob({ type: "image/png" })).arrayBuffer();
  }
  if (!url.includes(NISAR)) return buf;
  // Measured on real vs broken GIBS tiles (15 Nov 2026): real NISAR tiles have alpha 0/255 only, colour (green > red > blue),
  // and equal horizontal/vertical texture. Broken ones: semi-transparent noise, grey static, all-black, horizontal streaks,
  // or a large file that decodes fully transparent.
  let bad = false;
  try {
    const bmp = await createImageBitmap(new Blob([buf]));
    const c = new OffscreenCanvas(bmp.width, bmp.height), x = c.getContext("2d"); x.drawImage(bmp, 0, 0);
    const W = bmp.width, a = x.getImageData(0, 0, W, bmp.height).data, N = a.length / 4;
    let zero = 0, mid = 0, op = 0, sat = 0, mx = 0, gh = 0, gv = 0, nh = 0;
    const L = i => a[i] + a[i + 1] + a[i + 2];
    for (let i = 0, p = 0; i < a.length; i += 4, p++) {
      const al = a[i + 3]; if (al <= 8) { zero++; continue } if (al < 247) mid++;
      op++; const hi = Math.max(a[i], a[i + 1], a[i + 2]); sat += hi - Math.min(a[i], a[i + 1], a[i + 2]); mx += hi;
      if ((p & 1) === 0 && p % W < W - 1 && i + W * 4 + 3 < a.length && a[i + 7] > 8 && a[i + W * 4 + 3] > 8) { gh += Math.abs(L(i) - L(i + 4)); gv += Math.abs(L(i) - L(i + W * 4)); nh++ }
    }
    if (zero / N > 0.98) bad = buf.byteLength > 5000;                   // big file, nothing in it
    else if (mid / N > 0.2) bad = true;                                   // semi-transparent noise
    else if (op > 500 && mx / op < 4) bad = true;                         // all black
    else if (op > 500 && sat / op < 12) bad = true;                       // grey static (real tiles are colour)
    else if (nh > 800 && gv > 1.45 * gh + 50) bad = true;                 // horizontal streaks
  } catch (e) { }
  if (bad) { DBG.rejected++; throw new Error("scrambled tile") }
  return buf;
}
/* GIBS corruption is random per request: the same tile can come back scrambled, then fine. So on a scrambled tile or a 5xx
   we retry up to 5 times with a cache-buster (?r=n) and backoff 150, 300, 600 ms...; only then give up (parent fill below). */
const MEM = new Map();
let EMPTY = new ArrayBuffer(0);
(async () => { try { EMPTY = await (await new OffscreenCanvas(1, 1).convertToBlob({ type: "image/png" })).arrayBuffer() } catch (e) { } })();
async function gibsGet(url, signal) {
  if (MEM.has(url)) { DBG.hit++; return MEM.get(url).slice(0) }
  const c = await cacheP;
  if (c) { try { const h = await c.match(url); if (h) { DBG.hit++; const b = await h.arrayBuffer(); MEM.set(url, b); return b.slice(0) } } catch (e) { } }
  let lastErr;
  const zt = +((url.match(/\/(\d+)\/\d+\/\d+\.(?:png|jpg)$/) || [])[1] || 0), tries = zt >= 11 ? 3 : 2;   // scrambling is a z11-13 problem
  for (let n = 0; n <= tries; n++) {
    if (n) { DBG.retry = (DBG.retry || 0) + 1; await new Promise((res, rej) => { const t = setTimeout(res, 150 * 2 ** (n - 1)); signal && signal.addEventListener("abort", () => { clearTimeout(t); rej(new DOMException("aborted", "AbortError")) }, { once: true }) }) }
    let r;
    try { r = await fetch(n ? url + "?r=" + n : url, { signal }) } catch (e) { if (e.name === "AbortError") throw e; DBG.net = (DBG.net || 0) + 1; return EMPTY.slice(0) }   // network/CORS failure: empty tile, quietly
    if (r.status >= 500) { lastErr = new Error("GIBS " + r.status); continue }
    if (!r.ok) throw new Error("GIBS " + r.status);
    try {
      const buf = await checkTile(url, await r.arrayBuffer());
      if (n) DBG.retryOk = (DBG.retryOk || 0) + 1;
      if (MEM.size > 3000) MEM.delete(MEM.keys().next().value);
      MEM.set(url, buf);
      if (c) c.put(url, new Response(buf.slice(0), { headers: { "content-type": r.headers.get("content-type") || "image/png" } })).catch(() => { });
      DBG.ok++;
      return buf.slice(0);
    } catch (e) { lastErr = e; if (e.message !== "scrambled tile") throw e }
  }
  DBG.fail = (DBG.fail || 0) + 1;
  throw lastErr || new Error("scrambled tile");
}
window.FK = { checkTile, gibsGet };
/* a rejected tile is replaced by the matching quarter of its parent (up to 3 levels up), so the map is never blank */
async function gibsTile(url, signal, depth = 0) {
  try { return await gibsGet(url, signal) }
  catch (e) {
    if (e.name === "AbortError" || depth >= 3) throw e;
    const m = url.match(/\/(\d+)\/(\d+)\/(\d+)\.(png|jpg)$/); if (!m) throw e;
    const z = +m[1], y = +m[2], x = +m[3]; if (z <= 3) throw e;
    const pb = await gibsTile(url.slice(0, m.index) + `/${z - 1}/${y >> 1}/${x >> 1}.${m[4]}`, signal, depth + 1);
    if (pb.byteLength < 400) return pb;
    const bmp = await createImageBitmap(new Blob([pb])); const c = new OffscreenCanvas(256, 256), g = c.getContext("2d");
    g.drawImage(bmp, (x & 1) * 128, (y & 1) * 128, 128, 128, 0, 0, 256, 256); DBG.fallback = (DBG.fallback || 0) + 1;
    return await (await c.convertToBlob({ type: "image/png" })).arrayBuffer();
  }
}
maplibregl.addProtocol("gibs", async (params, ctl) => ({ data: await gibsTile(params.url.replace("gibs://", "https://"), ctl.signal) }));

/* ---------------- map ---------------- */
const ESRI = p => `https://server.arcgisonline.com/ArcGIS/rest/services/${p}/MapServer/tile/{z}/{y}/{x}`;
function baseStyle() {
  return {
    version: 8, projection: { type: "globe" }, glyphs: "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf",
    sky: { "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 5, 1, 7, 0] },
    sources: {
      "b-dark": { type: "raster", tileSize: 256, maxzoom: 16, tiles: [ESRI("Canvas/World_Dark_Gray_Base")], attribution: "Basemap © Esri" },
      "b-sat": { type: "raster", tileSize: 256, maxzoom: 18, tiles: [ESRI("World_Imagery")], attribution: "Imagery © Esri, Maxar, Earthstar" },
      "r-dark": { type: "raster", tileSize: 256, maxzoom: 16, tiles: [ESRI("Canvas/World_Dark_Gray_Reference")] },
      "r-sat": { type: "raster", tileSize: 256, maxzoom: 16, tiles: [ESRI("Reference/World_Boundaries_and_Places")] },
      mosaic: { type: "raster", tileSize: 256, maxzoom: 10, tiles: [new URL("tiles/{z}/{x}/{y}.webp?v=9", location.href).href.replace(/%7B/g, "{").replace(/%7D/g, "}")], attribution: "NISAR GCOV browse mosaic · ASF DAAC" }
    },
    layers: [
      { id: "bg", type: "background", paint: { "background-color": "#07111F" } },
      { id: "b-dark", type: "raster", source: "b-dark" },
      { id: "b-sat", type: "raster", source: "b-sat", layout: { visibility: "none" } },
      // our own world mosaic so the globe is never sparse; dim under the dated passes once zoomed in
      { id: "mosaic", type: "raster", source: "mosaic", maxzoom: 4, paint: { "raster-opacity": ["interpolate", ["linear"], ["zoom"], 3.5, 0.9, 5, 0.55], "raster-fade-duration": 0 } },
      { id: "ref", type: "raster", source: "r-dark" },
      { id: "ref-sat", type: "raster", source: "r-sat", layout: { visibility: "none" } }
    ]
  };
}
const map = new maplibregl.Map({
  container: "map", style: baseStyle(), center: [66, 30], zoom: 1.7, maxZoom: 15.5, attributionControl: { compact: true },
  canvasContextAttributes: { preserveDrawingBuffer: true }, fadeDuration: 120
});
map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
map.addControl(new maplibregl.ScaleControl(), "bottom-right");
map.on("error", e => { DBG.err++; DBG.last = (e.error && e.error.message) || "" });
Object.assign(window.FK, { map, DBG, S: null });

/* ---------------- state ---------------- */
const S = { passes: [], sel: null, newestHere: null, newestGlobal: null, win: "75d", ev: null, focus: null, area: null, mode: "pass", cmp: null, placeId: null };
FK.S = S;
let base = "dark";
const firstLabel = () => "ref";

/* NISAR day layers. The selected pass sits on top; other recent pass days stay dimmed underneath so a pass strip that covers
   part of the view never leaves empty basemap around it. */
/* the interferogram (gunw.js) always stays above radar layers, just under the labels */
function gmTop(m) { ["falakus-gunw-layer", "falakus-gunw-outline"].forEach(id => { if (m.getLayer(id) && m.getLayer("ref")) m.moveLayer(id, "ref") }) }
function setNisar(top, under = [], topOp = 1, m = map, prefix = "n-", underOp = 0.42) {
  const want = new Set([top, ...under].filter(Boolean));
  for (const l of [...m.getStyle().layers]) if (l.id.startsWith(prefix) && !want.has(l.id.slice(prefix.length))) { m.removeLayer(l.id); m.removeSource(l.id) }
  [...under].reverse().concat(top ? [top] : []).forEach(d => {
    const id = prefix + d;
    if (!m.getSource(id)) m.addSource(id, { type: "raster", tiles: [NIS(d)], tileSize: 256, maxzoom: 13, attribution: "NISAR GCOV © NASA-ISRO · ASF DAAC · NASA GIBS" });
    if (!m.getLayer(id)) m.addLayer({ id, type: "raster", source: id, paint: { "raster-opacity": 0, "raster-fade-duration": 100 } }, "ref");
    m.moveLayer(id, "ref");
    m.setPaintProperty(id, "raster-opacity", d === top ? topOp : underOp);
  });
  gmTop(m);
}
/* "Latest 12-day cycle": like NASA Worldview's rolling 12-day NISAR layer, the same GIBS layer for the last 12 daily dates
   stacked newest on top. One NISAR orbit cycle is 12 days, so this covers (nearly) the whole Earth; empty tiles are 288 B.
   It is the base everywhere; a selected pass / before-after / time-lapse sits on top of it. */
const CYC = { end: null, on: true, days: [] };
async function cycleEnd() {
  try {
    const ac = new AbortController(); setTimeout(() => ac.abort(), 4000);         // slow GIBS: do not hold the base layer hostage
    const r = await fetch(`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/wmts.cgi?SERVICE=WMTS&REQUEST=DescribeDomains&VERSION=1.0.0&LAYER=${NISAR}&TILEMATRIXSET=GoogleMapsCompatible_Level13&TIME=${addDays(today, -60)}/${addDays(today, 1)}`, { signal: ac.signal });
    const m = (await r.text()).match(/<Domain>([^<]*)<\/Domain>/); const last = m && m[1].split(",").pop().split("/");
    if (last && /^\d{4}-\d\d-\d\d/.test(last[1] || last[0])) return (last[1] || last[0]).slice(0, 10);
  } catch (e) { }
  return addDays(today, -2);
}
function cycleBefore(m) { const ls = m.getStyle().layers; const l = ls.find(x => /^(n-|nb-|tl-|vs-|sci|ref)/.test(x.id)); return l && l.id }
/* one composited layer: per tile, fetch the dates newest-first in batches of 6 and paint each batch *behind* what is already
   there; stop as soon as the tile is fully covered. Newest image wins everywhere, nothing is fetched that cannot show. */
maplibregl.addProtocol("cyc", async (params, ctl) => {
  const [, z, x, y] = params.url.match(/^cyc:\/\/(\d+)\/(\d+)\/(\d+)/).map(Number);
  const c = new OffscreenCanvas(256, 256), g = c.getContext("2d"); g.globalCompositeOperation = "destination-over";
  let drawn = 0;
  for (let i = 0; i < CYC.days.length; i += 12) {                       // HTTP/2: 12 dates in parallel, at most two rounds
    const urls = CYC.days.slice(i, i + 12).map(d => NIS(d).replace("gibs://", "https://").replace("{z}", z).replace("{y}", y).replace("{x}", x));
    const get = u => gibsTile(u, ctl.signal).catch(e => { if (e.name === "AbortError") throw e; return null });
    let bufs = await Promise.all(urls.map(get));
    if (!drawn && bufs.some(b => b === null) && !bufs.some(b => b && b.byteLength >= 400)) {   // GIBS 5xx on the only dates with data: one more try
      await new Promise(r => setTimeout(r, 1200)); bufs = await Promise.all(urls.map((u, k) => bufs[k] === null ? get(u) : bufs[k]));
    }
    for (const b of bufs) { if (!b || b.byteLength < 400) continue; try { g.drawImage(await createImageBitmap(new Blob([b])), 0, 0); drawn++ } catch (e) { } }
    if (drawn) { const a = g.getImageData(0, 0, 256, 256).data; let t = 0; for (let k = 3; k < a.length; k += 16) if (a[k] < 250) t++; if (t < 40) break }
  }
  CYC.tiles = (CYC.tiles || 0) + 1; if (drawn && !DBG.cycFirst) DBG.cycFirst = Math.round(performance.now());
  return { data: drawn ? await (await c.convertToBlob({ type: "image/png" })).arrayBuffer() : EMPTY.slice(0) };
});
function addCycle(m = map) {
  if (!CYC.end || m.getSource("cyc")) return;
  m.addSource("cyc", { type: "raster", tiles: [`cyc://{z}/{x}/{y}?e=${CYC.end}`], tileSize: 256, maxzoom: 9, attribution: "NISAR GCOV © NASA-ISRO · ASF DAAC · NASA GIBS" });
  m.addLayer({ id: "cyc", type: "raster", source: "cyc", minzoom: 2.5, layout: { visibility: CYC.on ? "visible" : "none" }, paint: { "raster-fade-duration": 0 } }, cycleBefore(m));
  gmTop(m);
}
function showCycle(on) {
  CYC.on = on; $$("#cycSeg button").forEach(b => b.classList.toggle("on", (b.dataset.c === "cycle") === on));
  [map, mapB].filter(Boolean).forEach(m => m.getLayer("cyc") && m.setLayoutProperty("cyc", "visibility", on ? "visible" : "none"));
  if (!on && S.mode === "pass" && S.sel) setNisar(S.sel.day, underDays(S.sel));   // single pass: older passes dimmed underneath as before
}
async function initCycle() {
  // the newest 12-day cycle, then the one before it underneath: NASA publishes passes days late, so the newest cycle alone leaves holes
  CYC.end = await cycleEnd(); CYC.days = []; for (let i = 0; i < 24; i++) CYC.days.push(addDays(CYC.end, -i));
  $("#cycCap").textContent = `NISAR, 12-day cycle ending ${fmt(CYC.end)} (gaps filled from the cycle before) · NASA GIBS`;
  addCycle(map); if (mapB && mapB.isStyleLoaded()) addCycle(mapB);
  // GIBS unreachable: keep our browse mosaic visible at every zoom so the screen is never empty
  setTimeout(() => { if (!DBG.ok && (DBG.net || DBG.fail)) map.setLayerZoomRange("mosaic", 0, 10.5) }, 20000);
}
function worldCycle() { }

/* "Where NISAR flies today": NASA GIBS NISAR orbit tracks with UTC times (Worldview's "NISAR - Orbit Track & Time").
   GIBS serves them only in EPSG:4326 (2 km matrix, z0 = two 288-degree tiles, gzip body), so we decode the MVT to GeoJSON. */
const ORB = { on: false, fc: null };
async function orbitFC() {
  if (ORB.fc) return ORB.fc;
  const feats = [];
  for (const back of [0, 1]) {
    const d = addDays(today, -back);
    for (const dir of ["Ascending", "Descending"]) for (const col of [0, 1]) {
      try {
        const r = await fetch(`https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/OrbitTracks_NISAR_${dir}/default/${d}/2km/0/0/${col}.mvt`); if (!r.ok) continue;
        let buf = await r.arrayBuffer(); const u8 = new Uint8Array(buf);
        if (u8[0] === 0x1f && u8[1] === 0x8b) buf = await new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
        MVT.decode(buf, (u, v) => [-180 + (col + u) * 288, 90 - v * 288]).forEach(f => { f.properties = { dir, label: String(f.properties.label || "").split("\n")[0], t: f.properties.datetime || "" }; feats.push(f) });   // drop uint64 day_offset: MapLibre cannot re-encode it
      } catch (e) { }
    }
    if (feats.length) { ORB.day = d; break }
  }
  return ORB.fc = { type: "FeatureCollection", features: feats };
}
async function showOrbits(on) {
  ORB.on = on; const b = $("#orbBtn"); b.classList.toggle("on", on); b.setAttribute("aria-pressed", on);
  if (on && !map.getSource("orb")) {
    const fc = await orbitFC(); if (!fc.features.length) { ORB.on = false; b.classList.remove("on"); return toast("NISAR orbit tracks are not available from NASA GIBS right now") }
    map.addSource("orb", { type: "geojson", data: fc });
    const col = ["match", ["get", "dir"], "Ascending", "#7FB2FF", "#F5B85C"];
    map.addLayer({ id: "orb-line", type: "line", source: "orb", filter: ["in", ["geometry-type"], ["literal", ["LineString", "MultiLineString"]]], paint: { "line-color": col, "line-width": 1.4, "line-opacity": 0.8 } });
    map.addLayer({ id: "orb-pt", type: "circle", source: "orb", filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 2.4, "circle-color": col, "circle-stroke-color": "#07111F", "circle-stroke-width": 1 } });
    map.addLayer({ id: "orb-lbl", type: "symbol", source: "orb", filter: ["==", ["geometry-type"], "Point"], layout: { "text-field": ["get", "label"], "text-font": ["Noto Sans Medium"], "text-size": 11, "text-offset": [0, 1], "text-anchor": "top", "text-padding": 14 }, paint: { "text-color": "#E6EEF9", "text-halo-color": "#07111F", "text-halo-width": 1.4 } });
    toast(`NISAR orbit tracks for ${fmt(ORB.day)}, times in UTC · blue = ascending, amber = descending · NASA GIBS`);
  }
  ["orb-line", "orb-pt", "orb-lbl"].forEach(id => map.getLayer(id) && map.setLayoutProperty(id, "visibility", on ? "visible" : "none"));
}
$$("#cycSeg button").forEach(b => b.onclick = () => showCycle(b.dataset.c === "cycle"));
$("#orbBtn").onclick = () => showOrbits(!ORB.on);
/* GIBS can be slow (seconds per tile): load the shown pass first, add the dimmed under-layers once it has painted */
function whenLoaded(id, ms = 8000) { return new Promise(res => { const t0 = Date.now(); const chk = () => { try { if (!map.getSource(id) || map.isSourceLoaded(id) || Date.now() - t0 > ms) return res() } catch (e) { return res() } setTimeout(chk, 250) }; chk() }) }
function hideNisar(h) { map.getStyle().layers.filter(l => l.id.startsWith("n-")).forEach(l => map.setLayoutProperty(l.id, "visibility", h ? "none" : "visible")) }

/* ---------------- our 20 m calibrated NISAR (Andijan science box) ----------------
   GIBS z11-13 is broken over Andijan, so when zoomed in there we lay our own calibrated 20 m frame for the nearest date
   (<= 6 days) over GIBS, edges feathered, box outlined; GIBS stays visible around it. */
const SCI = { dir: "science/andijan_res/", meta: null, cur: null, img: {} };
function sciMeta() { if (!SCI.meta) SCI.meta = fetch(SCI.dir + "frames.json", { cache: "no-cache" }).then(r => r.ok ? r.json() : false).catch(() => false); return SCI.meta }
async function sciImage(d) {
  if (!SCI.img[d]) SCI.img[d] = new Promise(res => {
    const im = new Image(); im.onload = () => {
      const c = document.createElement("canvas"); c.width = im.width; c.height = im.height; const g = c.getContext("2d"); g.drawImage(im, 0, 0);
      const f = Math.round(im.width * 0.07); g.globalCompositeOperation = "destination-out";
      [[0, 0, f, 0, 0, 0, f, c.height], [c.width, 0, c.width - f, 0, c.width - f, 0, f, c.height], [0, 0, 0, f, 0, 0, c.width, f], [0, c.height, 0, c.height - f, 0, c.height - f, c.width, f]].forEach(([x0, y0, x1, y1, rx, ry, rw, rh]) => {
        const gr = g.createLinearGradient(x0, y0, x1, y1); gr.addColorStop(0, "rgba(0,0,0,1)"); gr.addColorStop(1, "rgba(0,0,0,0)"); g.fillStyle = gr; g.fillRect(rx, ry, rw, rh);
      });
      res(c);
    }; im.onerror = () => res(null); im.src = SCI.dir + "img/" + d + "_rgb.webp";
  });
  return SCI.img[d];
}
function sciOff() { SCI.gen = (SCI.gen || 0) + 1; sciRemove() }
function sciRemove() { ["sci", "sci-line"].forEach(id => map.getLayer(id) && map.removeLayer(id)); ["sci", "sci-line"].forEach(id => map.getSource(id) && map.removeSource(id)); SCI.cur = null; $("#sciTag").hidden = true }
async function updateSci() {
  const my = SCI.gen = (SCI.gen || 0) + 1;
  const day = S.mode === "pass" || S.mode === "vs" ? S.sel && S.sel.day : null;
  const m = day && map.getZoom() >= 10.5 ? await sciMeta() : null;
  if (my !== SCI.gen) return;
  DBG.sci = [day, map.getZoom().toFixed(1), !!m, S.mode].join(" ");
  if (!m || !m.bbox) return sciOff();
  const [w, so, e, n] = m.bbox, b = map.getBounds();
  if (b.getEast() < w || b.getWest() > e || b.getNorth() < so || b.getSouth() > n) return sciOff();
  const dd = d => Math.abs(new Date(d) - new Date(day)) / 864e5;
  const best = (m.frames || []).map(f => f.date).filter(d => dd(d) <= 6).sort((a, b) => dd(a) - dd(b))[0];
  if (!best) return sciOff();
  if (SCI.cur === best) return;
  const cv = await sciImage(best); if (my !== SCI.gen) return; if (!cv) return sciOff();
  sciRemove(); SCI.cur = best;
  const coords = [[w, n], [e, n], [e, so], [w, so]];
  map.addSource("sci", { type: "raster", tiles: [`sci://${best}/{z}/{x}/{y}`], tileSize: 256, minzoom: 8, maxzoom: 16, bounds: [w, so, e, n] });
  map.addLayer({ id: "sci", type: "raster", source: "sci", paint: { "raster-fade-duration": 0 } }, "ref");
  map.addSource("sci-line", { type: "geojson", data: { type: "Feature", geometry: { type: "LineString", coordinates: [...coords, coords[0]] }, properties: {} } });
  map.addLayer({ id: "sci-line", type: "line", source: "sci-line", paint: { "line-color": "#F2F5FA", "line-opacity": 0.55, "line-width": 1, "line-dasharray": [4, 3] } }, "ref");
  $("#sciTag").hidden = false; $("#sciTag").textContent = `Falakus 20 m calibrated NISAR (our pipeline, own dB colour scale) · ${fmt(best)}${best !== day ? ` (nearest to ${fmtS(day)})` : ""}`;
}
map.on("moveend", () => updateSci());
/* the feathered 20 m frame is cut into map tiles on the fly (frame is a lat/lon grid; linear within one tile) */
maplibregl.addProtocol("sci", async params => {
  const [, d, z, x, y] = params.url.match(/^sci:\/\/([\d-]+)\/(\d+)\/(\d+)\/(\d+)/).map((v, i) => i > 1 ? +v : v);
  const cv = await sciImage(d), m = await sciMeta(); const [w, so, e, n] = m.bbox, N = 2 ** z;
  const lon = t => t / N * 360 - 180, lat = t => { const k = Math.PI - 2 * Math.PI * t / N; return 180 / Math.PI * Math.atan(0.5 * (Math.exp(k) - Math.exp(-k))) };
  const c = new OffscreenCanvas(256, 256), g = c.getContext("2d");
  if (cv) for (let r = 0; r < 256; r += 8) {                          // 8 px bands: follow the Mercator latitude stretch
    const la0 = lat(y + r / 256), la1 = lat(y + (r + 8) / 256), lo0 = lon(x), lo1 = lon(x + 1);
    const sx = (lo0 - w) / (e - w) * cv.width, sw = (lo1 - lo0) / (e - w) * cv.width, sy = (n - la0) / (n - so) * cv.height, sh = (la0 - la1) / (n - so) * cv.height;
    g.drawImage(cv, sx, sy, sw, sh, 0, r, 256, 8);
  }
  return { data: await (await c.convertToBlob({ type: "image/png" })).arrayBuffer() };
});
/* ---------------- NASA CMR ---------------- */
function parseG(e, coll) {
  const f = (e.producer_granule_id || e.title || "").split("_");   // NISAR_L2_PR_GCOV_<cycle>_<track>_<A|D>_<frame>_...
  return { t: e.time_start, day: e.time_start.slice(0, 10), time: e.time_start.slice(11, 16), cycle: f[4], track: f[5], dir: f[6], frame: f[7], coll };
}
async function cmr(coll, bbox, start, end, { signal, size = 500, pages = 1, asc = false } = {}) {
  let out = [], after = null;
  for (let p = 0; p < pages; p++) {
    const u = `https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=${coll}&bounding_box=${bbox.map(v => v.toFixed(3)).join(",")}&temporal=${start}T00:00:00Z,${end}T23:59:59Z&page_size=${size}&sort_key=${asc ? "" : "-"}start_date`;
    const r = await fetch(u, { signal, headers: after ? { "CMR-Search-After": after } : {} });
    if (!r.ok) throw new Error("CMR " + r.status);
    const j = await r.json(); const e = j.feed.entry || []; out = out.concat(e);
    after = r.headers.get("CMR-Search-After"); if (!after || e.length < size) break;
  }
  return out;
}
/* passes = one per day + track + direction, newest first; validated preferred over provisional */
async function nisarPasses(bbox, start, end, opt = {}) {
  const res = await Promise.all(COLL.map(([c]) => cmr(c, bbox, start, end, opt)));
  const by = new Map();
  res.forEach((list, ci) => list.forEach(e => {
    const g = parseG(e, COLL[ci][1]); const k = g.day + "_" + g.track + g.dir;
    const o = by.get(k);
    if (!o) by.set(k, { ...g, key: k, frames: 1, concept: COLL[ci][0] });
    else { o.frames++; if (g.t < o.t) { o.t = g.t; o.time = g.time } if (ci === 0) { o.coll = "validated"; o.concept = COLL[0][0] } }
  }));
  return [...by.values()].sort((a, b) => a.t < b.t ? 1 : -1);
}
const tk = p => p.track + p.dir;
/* GIBS publishes some passes days after CMR lists them. Probe one coarse tile at the view centre per pass day:
   a ~288-byte tile means no radar image there yet. */
const probeC = new Map();
function hasImage(day, c = map.getCenter(), zv = map.getZoom()) {
  const z = Math.max(5, Math.min(9, Math.round(zv))), x = Math.floor(lon2x(c.lng ?? c[0], z)), y = Math.floor(lat2y(c.lat ?? c[1], z));
  const u = gibsUrl(NISAR, day, "GoogleMapsCompatible_Level13").replace("{z}", z).replace("{y}", y).replace("{x}", x);
  if (!probeC.has(u)) probeC.set(u, gibsGet(u).then(b => b.byteLength > 400).catch(e => e.message === "scrambled tile"));
  return probeC.get(u);
}
async function probePasses(ps, my) {
  await Promise.all([...new Set(ps.map(p => p.day))].map(async d => { const ok = await hasImage(d); ps.filter(p => p.day === d).forEach(p => p.img = ok) }));
  if (my === undefined || my === gen) renderStrip();
}
const withImg = ps => ps.filter(p => p.img !== false);
const dirName = d => d === "A" ? "ascending" : d === "D" ? "descending" : "?";
const passLine = p => `${fmt(p.day)} · ${p.time} UTC · track ${p.track} ${p.dir}`;

function viewBBox() {
  const b = map.getBounds();
  let w = b.getWest(), e = b.getEast(); if (e - w > 360) { w = -180; e = 180 }
  return [Math.max(-180, w), Math.max(-85, b.getSouth()), Math.min(180, e), Math.min(85, b.getNorth())];
}

/* ---------------- UI helpers ---------------- */
function toast(t, ms = 2800) { const e = $("#toast"); e.textContent = t; e.classList.add("on"); clearTimeout(e._t); e._t = setTimeout(() => e.classList.remove("on"), ms) }
function status(k, v, rows, note) {
  $("#status").hidden = false; $("#stK").textContent = k; $("#stV").textContent = v;
  $("#stKV").innerHTML = rows.map(([a, b]) => `<dt>${esc(a)}</dt><dd>${b}</dd>`).join(""); $("#stN").innerHTML = note || "";
}
$("#stX").onclick = () => $("#status").hidden = true;
function setTlH() { const h = $("#timeline").offsetHeight; document.documentElement.style.setProperty("--tlh", (h + 24) + "px") }
new ResizeObserver(setTlH).observe($("#timeline"));
function collBadge(p) { return `<span class="badge ${p.coll === "validated" ? "val" : "prov"}">${p.coll}</span>` }

/* ---------------- pass strip + status ---------------- */
function renderStrip() {
  const s = $("#strip");
  if (!S.passes.length) { s.innerHTML = `<div class="empty">${esc($("#hint").dataset.empty || "Zoom in to list passes")}</div>`; return }
  s.innerHTML = S.passes.map((p, i) => `<button class="chip${p.img === false ? " na" : ""}${S.sel && p.key === S.sel.key ? " on" : ""}${S.cmp && S.cmp.a.key === p.key ? " bef" : ""}" data-i="${i}" title="${esc(passLine(p))} · ${p.coll}">` +
    `<b>${fmtS(p.day)} · ${p.time}</b><small>T${p.track} ${p.dir === "A" ? "asc" : "desc"} · <span class="${p.coll === "validated" ? "" : "pv"}">${p.coll === "validated" ? "valid." : "prov."}</span>${p.img === false ? " · not yet in NASA GIBS" : ""}</small></button>`).join("");
  $$("#strip .chip").forEach(b => b.onclick = () => {
    const p = S.passes[+b.dataset.i];
    if (S.mode === "cmp") { setCmp(S.cmp.a.key === p.key ? S.cmp.a : (p.t < S.cmp.b.t ? p : S.cmp.a), p.t < S.cmp.b.t ? S.cmp.b : p); return }
    if (p.img === false) { const alt = S.passes.find(x => x.t < p.t && x.img !== false); toast(`${fmt(p.day)} is not yet in NASA GIBS here${alt ? "; showing " + fmt(alt.day) : ""}`); if (alt) selectPass(alt); return }
    selectPass(p);
  });
  const on = s.querySelector(".chip.on"); if (on) on.scrollIntoView({ block: "nearest", inline: "nearest" });
}
function setNewest() {
  const p = S.newestHere, g = S.newestGlobal;
  $("#newestTxt").innerHTML = p ? `Newest NISAR pass here: <b class="mono">${esc(passLine(p))}</b>` : g ? `Newest NISAR pass (world): <b class="mono">${esc(passLine(g))}</b>` : "Newest NISAR pass: asking NASA CMR…";
}
function underDays(p) { return [...new Set(withImg(S.passes).filter(x => x.day !== p.day && x.t < p.t).map(x => x.day))].slice(0, 3) }
function selectPass(p, quiet) {
  closeTools();
  S.sel = p; S.mode = "pass";
  setNisar(p.day, []);
  if (!CYC.on) whenLoaded("n-" + p.day).then(() => { if (S.mode === "pass" && S.sel === p) setNisar(p.day, underDays(p)) });
  status("NISAR pass", fmt(p.day), [["Time", `${p.time} UTC`], ["Track", p.track + (p.frame ? ` · frame ${p.frame}` : "")], ["Direction", dirName(p.dir)], ["Cycle", p.cycle || "?"], ["Collection", `${collBadge(p)} <span style="color:#8A9BB4">${p.concept}</span>`]],
    "Older passes shown dimmed underneath where this strip does not cover the view. Source: NASA CMR + NASA GIBS.");
  renderStrip(); updateSci();
}

/* ---------------- pass loading on every view change ---------------- */
let ctrl = null, mt = null, gen = 0;
map.on("moveend", () => { clearTimeout(mt); mt = setTimeout(loadPasses, 380) });
async function loadPasses() {
  if (S.mode === "tl") return;                                     // the time-lapse owns the map while it runs
  if (S.area) return;                                              // a drawn area pins the pass list to that box
  const bbox = viewBBox(), wdeg = bbox[2] - bbox[0];
  const my = ++gen;
  if (ctrl) ctrl.abort(); ctrl = new AbortController();
  if (map.getZoom() < 4.6 || wdeg > 24) {
    S.passes = []; S.newestHere = null; $("#hint").textContent = ""; $("#hint").dataset.empty = "Zoom in to list passes (the view is wider than NASA's catalogue query allows here)";
    if (S.mode === "pass") { S.sel = null; worldCycle(); $("#status").hidden = true }
    renderStrip(); setNewest(); return;
  }
  let start, end, label;
  if (S.focus) { start = S.focus.start; end = S.focus.end; label = S.focus.label }
  else if (S.ev) { start = addDays(S.ev.slice(0, 10), -45); end = addDays(S.ev.slice(0, 10), 45) < today ? addDays(S.ev.slice(0, 10), 45) : today; label = "±45 days around the event" }
  else { start = addDays(today, -75); end = today; label = "last 75 days" }
  $("#tspin").hidden = false; $("#hint").textContent = "· asking NASA CMR…";
  try {
    const pre = S.placeId && placeData[S.placeId];
    let passes;
    if (pre && !S.focus) passes = pre.passes.filter(p => p.day >= start && p.day <= end);
    else passes = await nisarPasses(bbox, start, end, { signal: ctrl.signal });
    if (my !== gen) return;
    S.placeId = null;
    S.passes = passes;
    $("#hint").textContent = passes.length ? `· ${passes.length} passes · ${label}` : `· no NISAR pass over this view · ${label}`;
    $("#hint").dataset.empty = `No NISAR pass over this view in the ${label}.`;
    // newest pass here, always (independent of the window)
    if (!S.ev && !S.focus) S.newestHere = passes[0] || null;
    if (S.ev || S.focus) nisarPasses(bbox, addDays(today, -40), today, { signal: ctrl.signal, size: 20 }).then(n => { if (my === gen) { S.newestHere = n[0] || null; setNewest() } }).catch(() => { });
    setNewest();
    renderStrip();
    // default pass: the newest one that has pixels in NASA GIBS at the view centre (probe newest-first, stop at the first hit)
    if (S.mode === "pass" && $("#t-tl").hidden && !S.ev && !S.focus && (!S.sel || !passes.find(p => p.key === S.sel.key))) {
      // GIBS can take seconds per tile: probe the newest 4 in parallel; if nothing answers within 3.5 s, show the newest anyway
      const cand = passes.slice(0, 4), res = cand.map(p => hasImage(p.day).then(ok => { passes.filter(x => x.day === p.day).forEach(x => x.img = ok); return ok }));
      const pick = Promise.all(res).then(oks => cand.find((p, i) => oks[i]) || null);
      const p = await Promise.race([pick, sleep(3500).then(() => undefined)]); if (my !== gen) return;
      if (p) selectPass(p);
      else if (p === undefined && cand[0]) { selectPass(cand[0]); pick.then(q => { if (my === gen && q && S.mode === "pass" && S.sel && S.sel.key === cand[0].key && q.key !== cand[0].key) selectPass(q) }) }
    }
    await Promise.race([probePasses(passes, my), sleep(4000)]);   // unanswered probes count as "maybe"; chips update when they land
    if (my !== gen) return;
    const shown = withImg(passes);
    const gp = shown[0];
    if (gp && passes[0] && gp.key !== passes[0].key) $("#hint").textContent += ` · newest with a GIBS radar image: ${fmtS(gp.day)}`;
    if (S.focus) { const f = S.focus; S.focus = null; f.then(shown.length ? shown : passes); return }
    if (S.ev) { const t = S.ev; S.ev = null; eventPair(t, shown); return }
    if (S.mode === "pass" && $("#t-tl").hidden) { if (gp && (!S.sel || S.sel.img === false || !passes.find(p => p.key === S.sel.key))) selectPass(gp); else renderStrip() }
  } catch (err) {
    if (err.name === "AbortError") return;
    $("#hint").textContent = "· NASA CMR unreachable, retrying on next move"; DBG.last = err.message;
  } finally { if (my === gen) $("#tspin").hidden = true }
}
/* the event's full timestamp: "before" ends before it, "after" starts after it, both on the same track and direction */
function eventPair(t, passes) {
  const tracks = {};
  passes.forEach(p => (tracks[tk(p)] = tracks[tk(p)] || []).push(p));
  let best = null;
  for (const list of Object.values(tracks)) {
    const bf = list.filter(p => p.t < t).sort((a, b) => a.t < b.t ? 1 : -1)[0], af = list.filter(p => p.t > t).sort((a, b) => a.t > b.t ? 1 : -1)[0];
    if (bf && af && (!best || af.t < best.af.t)) best = { bf, af };
  }
  if (best) { openCompare(best.bf, best.af); toast(`Same track ${best.af.track} ${dirName(best.af.dir)}: ${fmtS(best.bf.day)} (before) → ${fmtS(best.af.day)} (after)`); return }
  const anyAfter = passes.filter(p => p.t > t).sort((a, b) => a.t > b.t ? 1 : -1)[0];
  const anyBefore = passes.filter(p => p.t < t)[0];
  if (anyAfter && anyBefore) { openCompare(anyBefore, anyAfter); toast("No same-track pair yet: comparing different orbits, so the viewing angle differs", 4200); return }
  if (anyAfter) { selectPass(anyAfter); toast("No NISAR pass before the event in the window; showing the first pass after it", 4200); return }
  if (anyBefore) { selectPass(anyBefore); toast("No NISAR pass after the event yet. Showing the last pass before it.", 4200); status("No pass after the event yet", fmt(anyBefore.day), [["Last pass before", passLine(anyBefore)], ["Event", `${t.slice(0, 16).replace("T", " ")} UTC`]], "NISAR revisits every 12 days; the after-pass appears here as soon as NASA publishes it."); return }
  toast("No NISAR pass within ±45 days of this event over this view", 4200);
}

/* earliest vs latest pass on the most frequent track (with a GIBS image) */
function spanPair(ps) {
  const by = {}; ps.forEach(p => (by[tk(p)] = by[tk(p)] || []).push(p));
  const l = Object.values(by).sort((a, b) => b.length - a.length)[0];
  if (!l || l.length < 2) { if (ps[0]) selectPass(ps[0]); return }
  openCompare(l[l.length - 1], l[0]);
  toast(`Earliest vs latest pass on track ${l[0].track} ${dirName(l[0].dir)}: ${fmt(l[l.length - 1].day)} → ${fmt(l[0].day)}`, 4200);
}
/* ---------------- compare: fade and true swipe ---------------- */
let mapB = null, swipeX = 0.5;
function passOpts(sel) { return S.passes.map(p => `<option value="${p.key}"${sel && p.key === sel.key ? " selected" : ""}>${fmtS(p.day)} ${p.time} · T${p.track}${p.dir}${p.coll === "validated" ? "" : " · prov"}</option>`).join("") }
function openCompare(a, b) {
  if (!a || !b) {
    b = S.sel || S.passes[0]; if (!b) return toast("Zoom in until passes are listed, then compare");
    a = withImg(S.passes).find(p => p.t < b.t && tk(p) === tk(b)) || withImg(S.passes).find(p => p.t < b.t);
    if (!a) return toast("Only one pass here so far: nothing to compare yet");
  }
  closeTools(); S.mode = "cmp"; $("#t-cmp").hidden = false; $("#bCmp").classList.add("on");
  setCmp(a, b);
}
function setCmp(a, b) {
  if (a.t > b.t) [a, b] = [b, a];
  S.cmp = { a, b, m: S.cmp ? S.cmp.m : "fade" }; S.sel = b;
  if (!S.passes.find(p => p.key === a.key)) S.passes.push(a);
  if (!S.passes.find(p => p.key === b.key)) S.passes.push(b);
  S.passes.sort((x, y) => x.t < y.t ? 1 : -1);
  $("#cA").innerHTML = passOpts(a); $("#cB").innerHTML = passOpts(b);
  const mixed = tk(a) !== tk(b);
  $("#cWarn").hidden = !mixed; $("#cWarn").innerHTML = mixed ? `Different orbits (T${a.track}${a.dir} vs T${b.track}${b.dir}): the viewing angle changes, not only the ground` : "";
  $("#lblA").textContent = "Before · " + fmt(a.day) + " " + a.time + " UTC"; $("#lblB").textContent = "After · " + fmt(b.day) + " " + b.time + " UTC";
  $("#cmpLabels").hidden = false;
  status("Before / after", `${fmtS(a.day)} → ${fmt(b.day)}`, [["Before", passLine(a)], ["After", passLine(b)], ["Gap", Math.round((new Date(b.t) - new Date(a.t)) / 864e5) + " days"], ["Geometry", mixed ? "<span style='color:#F2C46B'>mixed tracks</span>" : `same track, ${dirName(b.dir)}`]],
    "New black area = new calm water · lost green = lost vegetation · brighter = rougher surface. This is backscatter change, not ground motion.");
  applyCmpMode(); renderStrip();
}
function applyCmpMode() {
  const { a, b, m } = S.cmp;
  $$("#cMode button").forEach(x => x.classList.toggle("on", x.dataset.m === m));
  $("#cFade").hidden = m !== "fade";
  if (m === "fade") {
    killSwipe(); setNisar(b.day, [a.day], +$("#cFade").value / 100);
    map.setPaintProperty("n-" + a.day, "raster-opacity", 1);
    const cm = S.cmp;
    if (!CYC.on) whenLoaded("n-" + b.day).then(() => { if (S.cmp === cm && cm.m === "fade") { setNisar(b.day, [a.day, ...underDays(b).filter(d => d !== a.day).slice(0, 2)], +$("#cFade").value / 100); map.setPaintProperty("n-" + a.day, "raster-opacity", 1) } });
    $("#cmpLabels").style.left = "50%";
  } else {
    setNisar(b.day, underDays(b).filter(d => d !== a.day).slice(0, 1));
    makeSwipe(a);
  }
}
$("#cFade").oninput = e => { if (S.cmp && map.getLayer("n-" + S.cmp.b.day)) map.setPaintProperty("n-" + S.cmp.b.day, "raster-opacity", e.target.value / 100) };
$$("#cMode button").forEach(x => x.onclick = () => { if (!S.cmp) return; S.cmp.m = x.dataset.m; applyCmpMode() });
$("#cA").onchange = () => { const a = S.passes.find(p => p.key === $("#cA").value); if (a) setCmp(a, S.cmp.b) };
$("#cB").onchange = () => { const b = S.passes.find(p => p.key === $("#cB").value); if (b) setCmp(S.cmp.a, b) };
$("#cX").onclick = () => { const b = S.cmp && S.cmp.b; closeTools(); if (b) selectPass(b) };
function syncB() { if (mapB) mapB.jumpTo({ center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch() }) }
function clipB() {
  const W = $("#main").clientWidth, x = Math.round(W * swipeX);
  $("#mapB").style.clipPath = `inset(0 ${W - x}px 0 0)`; $("#handle").style.left = x + "px";
}
function makeSwipe(a) {
  if (!mapB) {
    const d = document.createElement("div"); d.id = "mapB"; $("#main").insertBefore(d, $("#map").nextSibling);
    const st = baseStyle(); st.projection = { type: $("#proj .on").dataset.p };
    st.layers.forEach(l => { if (l.id.startsWith("b-") || l.id.startsWith("ref")) l.layout = { visibility: (l.id === "b-" + base || (l.id === "ref" && base === "dark") || (l.id === "ref-sat" && base === "sat")) ? "visible" : "none" } });
    mapB = new maplibregl.Map({ container: d, style: st, interactive: false, attributionControl: false, center: map.getCenter(), zoom: map.getZoom(), fadeDuration: 0 });
    mapB.on("error", e => { DBG.err++ });
    map.on("move", syncB);
    mapB.once("style.load", () => { addCycle(mapB); if (a) setNisar(a.day, [], 1, mapB, "nb-") });
    new ResizeObserver(() => { if (mapB) { mapB.resize(); clipB() } }).observe($("#main"));
  } else if (!a) { }
  else if (mapB.loaded() || mapB.isStyleLoaded()) setNisar(a.day, [], 1, mapB, "nb-");
  else mapB.once("style.load", () => { addCycle(mapB); setNisar(a.day, [], 1, mapB, "nb-") });
  $("#handle").hidden = false; clipB(); syncB();
}
function killSwipe() { if (mapB) { map.off("move", syncB); mapB.remove(); mapB = null; $("#mapB") && $("#mapB").remove() } $("#handle").hidden = true }
(() => {
  const h = $("#handle"); let drag = false;
  h.addEventListener("pointerdown", e => { drag = true; h.setPointerCapture(e.pointerId) });
  h.addEventListener("pointermove", e => { if (!drag) return; const r = $("#main").getBoundingClientRect(); swipeX = Math.min(.98, Math.max(.02, (e.clientX - r.left) / r.width)); clipB() });
  h.addEventListener("pointerup", () => drag = false);
})();

/* ---------------- time-lapse studio ---------------- */
const TL_SRC = {
  nisar: { name: "NISAR L-band", colls: COLL.map(c => c[0]), first: NISAR_FIRST, layer: NISAR, set: "GoogleMapsCompatible_Level13", max: 13, key: t => { const f = t.split("_"); return f[5] + f[6] } },
  s1: { name: "Sentinel-1 C-band (OPERA RTC)", colls: ["C2777436413-ASF"], first: "2025-01-10", layer: "OPERA_L2_Radiometric_Terrain_Corrected_SAR_Sentinel-1", set: "GoogleMapsCompatible_Level12", max: 12, key: t => (t.split("_")[3] || "").split("-")[0] }
};
TL_SRC.modis = { name: "MODIS Terra camera (on the NISAR pass days)", colls: COLL.map(c => c[0]), first: NISAR_FIRST, layer: "MODIS_Terra_CorrectedReflectance_TrueColor", set: "GoogleMapsCompatible_Level9", max: 9, ext: "jpg", key: TL_SRC.nisar.key };
const tl = { frames: [], i: 0, timer: null, src: "nisar", ready: new Set(), rec: null, chk: null };
const tlId = d => "tl-" + tl.src + "-" + d;
function tlClear() {
  clearInterval(tl.timer); tl.timer = null; clearTimeout(tl.chk);
  if (tl.rec) { try { tl.rec.stop() } catch (e) { } }
  for (const l of [...map.getStyle().layers]) if (l.id.startsWith("tl-")) { map.removeLayer(l.id); map.removeSource(l.id) }
  tl.frames = []; $("#stamp").hidden = true; hideNisar(false);
  $("#tlPlay").disabled = $("#tlRec").disabled = true; $("#tlBar").style.width = "0"; $("#tlLoad").textContent = "";
}
async function tlBuild() {
  const bbox = S.area || viewBBox();
  if (!S.area && (map.getZoom() < 5 || bbox[2] - bbox[0] > 24)) return toast("Zoom in to a country, valley or city first (or draw an area)");
  tlClear(); tl.src = $("#tlSrc").value; const P = TL_SRC[tl.src];
  const rv = $("#tlRange").value; let start, end = today;
  if (rv === "c") { start = $("#tlFrom").value || NISAR_FIRST; end = $("#tlTo").value || today } else start = +rv ? addDays(today, -30 * +rv) : NISAR_FIRST;
  const pStart = start; if (start < P.first) start = P.first;
  const ctr = S.area ? [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2] : [map.getCenter().lng, map.getCenter().lat];
  $("#tlMsg").textContent = `Asking NASA CMR for every ${P.name} pass over ${S.area ? "your area" : "this view"} since ${fmt(start)}…`;
  let g = [];
  try { for (const c of P.colls) g = g.concat(await cmr(c, bbox, start, end, { size: 2000, pages: 2 })) } catch (e) { return $("#tlMsg").textContent = "NASA CMR unreachable: " + e.message }
  g = g.filter(x => covers(x, ctr));                                   // only passes whose footprint covers the view centre
  if (!g.length) return $("#tlMsg").textContent = `No ${P.name.split(" (")[0]} pass here in this period. Try a wider range or another place.`;
  const by = {}; g.forEach(x => { const k = P.key(x.producer_granule_id || x.title || "") || "?"; (by[k] = by[k] || new Set()).add(x.time_start.slice(0, 10)) });
  const tracks = Object.entries(by).sort((a, b) => b[1].size - a[1].size);
  const pick = $("#tlTrack").value === "all" ? null : tracks[0];
  tl.frames = [...(pick ? pick[1] : new Set(g.map(x => x.time_start.slice(0, 10))))].filter(d => d >= P.first).sort();
  const listed = tl.frames.length;
  if (tl.src !== "s1") { $("#tlMsg").textContent = `Checking which of ${listed} passes NASA GIBS has imaged…`; const ok = await Promise.all(tl.frames.map(d => hasImage(d, S.area ? [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2] : map.getCenter()))); tl.frames = tl.frames.filter((d, i) => ok[i]) }
  if (tl.frames.length < 2) return $("#tlMsg").textContent = `No ${P.name.split(" (")[0]} pass with an image here in this period (${tl.frames.length} of ${listed} listed passes have one). Try all tracks or a wider range.`;
  // NISAR public data starts mid-June 2026 in many regions: fill the earlier part of the period with Sentinel-1, as its own segment
  tl.seg = tl.frames.map(d => tl.src); tl.note = "";
  if (tl.src === "nisar" && tl.frames[0] > addDays(pStart, 24)) {
    let s1 = [];
    try { s1 = (await cmr("C2777436413-ASF", bbox, pStart < "2025-01-10" ? "2025-01-10" : pStart, addDays(tl.frames[0], -1), { size: 2000, pages: 2 })).filter(x => covers(x, ctr)) } catch (e) { }
    const by1 = {}; s1.forEach(x => { const k = TL_SRC.s1.key(x.producer_granule_id || x.title || ""); (by1[k] = by1[k] || new Set()).add(x.time_start.slice(0, 10)) });
    const b1 = Object.values(by1).sort((a, b) => b.size - a.size)[0];
    if (b1 && b1.size) { const f1 = [...b1].sort(); tl.frames = f1.concat(tl.frames); tl.seg = f1.map(() => "s1").concat(tl.seg) }
    tl.note = `NISAR public data here starts ${fmt(tl.frames[tl.seg.indexOf("nisar")])} (NASA archive).`;
  }
  S.mode = "tl"; hideNisar(true);
  $("#tlMsg").innerHTML = `<b>${tl.frames.length} frames</b>${listed > tl.frames.length ? ` (of ${listed} passes in CMR; the rest have no GIBS image yet)` : ""} · ${P.name} · ${pick ? "track " + esc(pick[0]) : "all tracks (viewing angle changes between frames)"} · ${fmt(tl.frames[0])} → ${fmt(tl.frames.at(-1))} · source: NASA CMR + GIBS`;
  tl.frames.forEach((d, k) => {
    const id = tlId(d), Q = TL_SRC[tl.seg[k]];
    map.addSource(id, { type: "raster", tiles: [T(Q.layer, d, Q.set, Q.ext)], tileSize: 256, maxzoom: Q.max, attribution: Q.name + " · NASA GIBS" });
    map.addLayer({ id, type: "raster", source: id, paint: { "raster-opacity": 0, "raster-opacity-transition": { duration: 0 }, "raster-fade-duration": 0 } }, "ref");
  });
  const n1 = tl.seg.filter(x => x === "s1").length;
  $("#tlBands").hidden = !(n1 && tl.src === "nisar");
  $("#tlBands").innerHTML = n1 && tl.src === "nisar" ? `<span style="flex:${n1};background:#5b6b82;padding:0 6px;white-space:nowrap;overflow:hidden">Sentinel-1 C-band · ${n1}</span><span style="width:2px;background:#fff"></span><span style="flex:${tl.frames.length - n1};background:#1C5BD9;padding:0 6px;white-space:nowrap;overflow:hidden">NISAR L-band · ${tl.frames.length - n1}</span>` : "";
  if (tl.note) $("#tlMsg").innerHTML += " · " + esc(tl.note);
  publishStudio(bbox);
  $("#tlScrub").max = tl.frames.length - 1; $("#tlScrub").value = 0; tl.ready = new Set(); showFrame(0);
  $("#tlPlay").disabled = $("#tlRec").disabled = false;
  const chk = () => {
    if (!tl.frames.length) return;
    tl.frames.forEach(d => { try { if (!tl.ready.has(d) && map.getSource(tlId(d)) && map.isSourceLoaded(tlId(d))) tl.ready.add(d) } catch (e) { } });
    const n = tl.ready.size, N = tl.frames.length; $("#tlBar").style.width = Math.round(n / N * 100) + "%";
    $("#tlLoad").textContent = n < N ? `Loading ${n}/${N} passes` : `All ${N} passes ready · zoom in and frames reload sharper`;
    tl.chk = setTimeout(chk, n < N ? 400 : 1500);
  };
  chk(); play();
}
function covers(e, c) {
  const poly = e.polygons && e.polygons[0] && e.polygons[0][0], box = e.boxes && e.boxes[0];
  const v = (poly || box || "").trim().split(/\s+/).map(Number); if (v.length < 4) return true;
  const la = v.filter((_, i) => i % 2 === 0), lo = v.filter((_, i) => i % 2 === 1);
  return c[1] >= Math.min(...la) && c[1] <= Math.max(...la) && c[0] >= Math.min(...lo) && c[0] <= Math.max(...lo);
}
function publishStudio(bbox) {
  const d = { bbox, sensor: tl.src, frames: tl.frames.map((date, k) => ({ date, sensor: tl.seg[k], track: null, dir: null, layerId: tlId(date) })) };
  window.FALAKUS_STUDIO = d; document.dispatchEvent(new CustomEvent("falakus:studio", { detail: d }));
}
$("#tlRange").onchange = () => $("#tlCustom").hidden = $("#tlRange").value !== "c";
$("#tlExplain").onclick = () => { if (window.FalakusExplain && FalakusExplain.open) FalakusExplain.open(); else toast("The explanation panel is not available yet") };
function showFrame(i) {
  const P = TL_SRC[tl.seg ? tl.seg[i] : tl.src]; const prev = tl.i; tl.i = i; const d = tl.frames[i];
  tl.frames.forEach((x, k) => { const id = tlId(x); if (map.getLayer(id)) map.setPaintProperty(id, "raster-opacity", k === i || k === prev ? 1 : 0) });  // previous frame stays under the new one
  if (map.getLayer(tlId(d))) map.moveLayer(tlId(d), "ref");
  $("#tlScrub").value = i; $("#stamp").hidden = false; $("#stampD").textContent = fmt(d); $("#stampS").textContent = `${P.name} · frame ${i + 1}/${tl.frames.length}`;
}
function play() {
  clearInterval(tl.timer); $("#tlPlay").innerHTML = svg("pause") + "Pause";
  tl.timer = setInterval(() => { let n = (tl.i + 1) % tl.frames.length, g = 0; while (!tl.ready.has(tl.frames[n]) && g++ < tl.frames.length) n = (n + 1) % tl.frames.length; if (tl.ready.has(tl.frames[n]) || g >= tl.frames.length) showFrame(n) }, +$("#tlSpeed").value);
}
function pause() { clearInterval(tl.timer); tl.timer = null; $("#tlPlay").innerHTML = svg("play") + "Play" }
$("#tlBuild").onclick = tlBuild;
$("#tlPlay").onclick = () => { if (!tl.frames.length) return; tl.timer ? pause() : play() };
$("#tlSpeed").onchange = () => { if (tl.timer) play() };
$("#tlScrub").oninput = e => { pause(); showFrame(+e.target.value) };
$("#tlX").onclick = () => closeTools(true);
$("#tlRec").onclick = () => {
  if (!tl.frames.length) return;
  if (tl.rec) { tl.rec.stop(); return }
  if (!window.MediaRecorder) return toast("This browser cannot record video");
  const src = map.getCanvas(), c = document.createElement("canvas"); c.width = src.width; c.height = src.height; const x = c.getContext("2d"); const P = TL_SRC[tl.src];
  let raf; const draw = () => {
    x.drawImage(src, 0, 0); const s = c.width / src.clientWidth;
    x.fillStyle = "rgba(7,17,31,.86)"; x.fillRect(20 * s, 20 * s, 340 * s, 74 * s);
    x.fillStyle = "#F2F5FA"; x.font = `800 ${28 * s}px Overpass,sans-serif`; x.fillText(fmt(tl.frames[tl.i]), 34 * s, 56 * s);
    x.fillStyle = "#8A9BB4"; x.font = `${13 * s}px 'Fira Sans',sans-serif`; x.fillText(TL_SRC[tl.seg ? tl.seg[tl.i] : tl.src].name + " · NASA GIBS · Falakus", 34 * s, 80 * s); raf = requestAnimationFrame(draw);
  }; draw();
  const mime = ["video/mp4;codecs=avc1", "video/mp4", "video/webm;codecs=vp9", "video/webm"].find(m => MediaRecorder.isTypeSupported(m)) || "video/webm";
  const rec = new MediaRecorder(c.captureStream(30), { mimeType: mime, videoBitsPerSecond: 8e6 }), chunks = []; tl.rec = rec;
  rec.ondataavailable = e => e.data.size && chunks.push(e.data);
  rec.onstop = () => {
    cancelAnimationFrame(raf); tl.rec = null; $("#tlRec").innerHTML = svg("record") + "Record video";
    const a = $("#tlDl"); a.href = URL.createObjectURL(new Blob(chunks, { type: mime.split(";")[0] })); a.download = `falakus_${tl.src}_${tl.frames[0]}_${tl.frames.at(-1)}.${mime.includes("mp4") ? "mp4" : "webm"}`; a.hidden = false; a.click();
  };
  rec.start(); $("#tlRec").innerHTML = svg("record") + "Stop & save"; showFrame(0); play();
  setTimeout(() => tl.rec === rec && rec.stop(), (+$("#tlSpeed").value) * tl.frames.length + 500);
};

/* ---------------- camera vs radar (same day) ---------------- */
let vsSrc = "modis";
const VS = { modis: ["MODIS_Terra_CorrectedReflectance_TrueColor", "MODIS Terra"], viirs: ["VIIRS_NOAA20_CorrectedReflectance_TrueColor", "VIIRS NOAA-20"] };
function vsOff() { if (map.getLayer("vs-cam")) map.removeLayer("vs-cam"); if (map.getSource("vs-cam")) map.removeSource("vs-cam") }
function openVs() {
  const p = S.sel || S.passes[0]; if (!p) return toast("Zoom in and pick a NISAR pass first");
  closeTools(); S.sel = p; S.mode = "vs"; setNisar(p.day, underDays(p)); $("#t-vs").hidden = false; $("#bVs").classList.add("on");
  vsOff(); const [layer, name] = VS[vsSrc];
  map.addSource("vs-cam", { type: "raster", tiles: [T(layer, p.day, "GoogleMapsCompatible_Level9", "jpg")], tileSize: 256, maxzoom: 9, attribution: name + " true colour · NASA GIBS" });
  map.addLayer({ id: "vs-cam", type: "raster", source: "vs-cam", paint: { "raster-opacity": 1, "raster-fade-duration": 150 } }, "ref");
  $("#vsFade").value = 0; $("#vsA").textContent = `Camera · ${name} · ${fmt(p.day)}`; $("#vsB").textContent = `Radar · NISAR · ${fmt(p.day)} ${p.time} UTC`;
  status("Same day: camera vs radar", fmt(p.day), [["Camera", `${name}, daily true colour`], ["Radar", passLine(p)]], "Slide right: where the photo shows cloud, smoke or night, NISAR still measured the ground. MODIS has gaps between swaths near the equator: switch to VIIRS.");
  renderStrip();
}
$("#vsFade").oninput = e => { if (map.getLayer("vs-cam")) map.setPaintProperty("vs-cam", "raster-opacity", 1 - e.target.value / 100) };
$$("#vsSrc button").forEach(b => b.onclick = () => { vsSrc = b.dataset.s; $$("#vsSrc button").forEach(x => x.classList.toggle("on", x === b)); openVs() });
$("#vsX").onclick = () => { const p = S.sel; closeTools(); if (p) selectPass(p) };

function closeTools(reselect) {
  $$(".tool").forEach(t => t.hidden = true); $$("#bCmp,#bTl,#bVs").forEach(b => b.classList.remove("on"));
  $("#cmpLabels").hidden = true; killSwipe(); vsOff(); sciOff();
  const wasTl = S.mode === "tl"; if (tl.frames.length) tlClear();
  S.cmp = null; S.mode = "pass"; setTlH();
  if (wasTl && reselect) { if (S.sel) selectPass(S.sel); loadPasses() }
}
$("#bCmp").onclick = () => S.mode === "cmp" ? $("#cX").onclick() : openCompare();
$("#bTl").onclick = () => { if (!$("#t-tl").hidden) return closeTools(true); closeTools(); $("#t-tl").hidden = false; $("#bTl").classList.add("on"); $("#tlBuild").textContent = S.area ? "Build for my area" : "Build for this view"; $("#tlMsg").textContent = "One orbit track by default, so the viewing geometry stays identical and only the ground changes."; sheet(false) };
$("#bVs").onclick = () => S.mode === "vs" ? $("#vsX").onclick() : openVs();

/* ---------------- draw an area (mouse or touch) ---------------- */
let drawing = false, d0 = null;
function areaFC(b) { return { type: "FeatureCollection", features: b ? [{ type: "Feature", geometry: { type: "Polygon", coordinates: [[[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]]] }, properties: {} }] : [] } }
function setDraw(on) {
  drawing = on; $("#bDraw").classList.toggle("on", on); map.getCanvas().style.cursor = on ? "crosshair" : "";
  if (on) { map.dragPan.disable(); map.touchZoomRotate.disable(); toast("Drag a box on the map to list every NISAR pass inside it"); sheet(false) } else { map.dragPan.enable(); map.touchZoomRotate.enable() }
}
$("#bDraw").onclick = () => setDraw(!drawing);
function drawStart(e) { if (!drawing) return; e.preventDefault && e.preventDefault(); d0 = e.lngLat }
function drawMove(e) { if (!drawing || !d0) return; const b = [Math.min(d0.lng, e.lngLat.lng), Math.min(d0.lat, e.lngLat.lat), Math.max(d0.lng, e.lngLat.lng), Math.max(d0.lat, e.lngLat.lat)]; map.getSource("area").setData(areaFC(b)) }
function drawEnd(e) {
  if (!drawing || !d0) return; const a = d0, b = e.lngLat || a; d0 = null; setDraw(false);
  const box = [Math.min(a.lng, b.lng), Math.min(a.lat, b.lat), Math.max(a.lng, b.lng), Math.max(a.lat, b.lat)];
  if (box[2] - box[0] < 0.005 || box[3] - box[1] < 0.005) { map.getSource("area").setData(areaFC(null)); return toast("Box too small: drag a larger area") }
  if (box[2] - box[0] > 24 || box[3] - box[1] > 24) { map.getSource("area").setData(areaFC(null)); return toast("Box too large for one catalogue query: draw a smaller area") }
  setArea(box);
}
async function setArea(box) {
  closeTools(); S.area = box; map.getSource("area").setData(areaFC(box));
  $("#areaTag").hidden = false; $("#areaTag").innerHTML = `<span class="badge">Area ${box.map(v => v.toFixed(2)).join(", ")}</span> <button class="btn" id="areaX" style="min-height:32px;padding:4px 10px">Clear area</button>`;
  $("#areaX").onclick = clearArea;
  $("#tspin").hidden = false; $("#hint").textContent = "· listing every NISAR pass in your area…";
  try {
    const ps = await nisarPasses(box, NISAR_FIRST, today, { size: 2000, pages: 3 });
    S.passes = ps; S.newestHere = ps[0] || null; setNewest(); renderStrip();
    await probePasses(ps.slice(0, 40));
    $("#hint").textContent = `· ${ps.length} passes in your area since ${fmt(NISAR_FIRST)}`; $("#hint").dataset.empty = "No NISAR pass in this area yet.";
    if (withImg(ps)[0]) selectPass(withImg(ps)[0]); else renderStrip();
    toast(`${ps.length} NISAR passes in your box. Before / after and time-lapse now use this area.`);
  } catch (e) { $("#hint").textContent = "· NASA CMR unreachable" } finally { $("#tspin").hidden = true }
}
function clearArea() { S.area = null; map.getSource("area").setData(areaFC(null)); $("#areaTag").hidden = true; loadPasses() }

/* ---------------- events: USGS + EONET ---------------- */
function iconImage(kind) {
  const s = 56, c = document.createElement("canvas"); c.width = c.height = s; const x = c.getContext("2d"); const col = EV_COL[kind] || EV_COL.other;
  x.fillStyle = "#0D1B2E"; x.beginPath(); x.arc(28, 28, 25, 0, 7); x.fill(); x.lineWidth = 3; x.strokeStyle = col; x.stroke();
  x.save(); x.translate(12, 12); x.scale(32 / 24, 32 / 24); x.strokeStyle = "#F2F5FA"; x.lineWidth = 1.7; x.lineCap = "round"; x.lineJoin = "round"; x.stroke(new Path2D(IC[EV_IC[kind] || "other"])); x.restore();
  return x.getImageData(0, 0, s, s);
}
const evFC = { type: "FeatureCollection", features: [] };
let hot = [];
async function loadEvents() {
  const [q, o] = await Promise.allSettled([
    fetch("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson").then(r => r.json()),
    fetch("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=45").then(r => r.json())]);
  if (q.status === "fulfilled") q.value.features.forEach(f => evFC.features.push({ type: "Feature", geometry: { type: "Point", coordinates: f.geometry.coordinates.slice(0, 2) }, properties: { kind: "quake", name: f.properties.place || "Earthquake", mag: f.properties.mag || 0, t: new Date(f.properties.time).toISOString(), src: "USGS", url: f.properties.url } }));
  if (o.status === "fulfilled") o.value.events.forEach(ev => { const g = ev.geometry[ev.geometry.length - 1]; if (!g || g.type !== "Point") return; const k = ev.categories[0].title; evFC.features.push({ type: "Feature", geometry: { type: "Point", coordinates: g.coordinates }, properties: { kind: EV_COL[k] ? k : "other", name: ev.title, mag: 0, t: new Date(g.date).toISOString(), src: "NASA EONET", url: ev.link } }) });
  if (map.getSource("ev")) map.getSource("ev").setData(evFC);
  const nq = evFC.features.filter(f => f.properties.kind === "quake").length, ne = evFC.features.length - nq;
  $("#liveTxt").innerHTML = `<span class="mono">${nq}</span> quakes M4.5+ (USGS, 30 d) · <span class="mono">${ne}</span> open NASA EONET events`;
  buildHot(q.status === "fulfilled", o.status === "fulfilled");
}
function buildHot(okQ, okO) {
  const now = Date.now(); const F = evFC.features.map(f => ({ ...f.properties, c: f.geometry.coordinates }));
  const age = f => (now - new Date(f.t)) / 864e5;
  const qs = F.filter(f => f.kind === "quake" && f.mag >= 5.5).map(f => ({ ...f, score: f.mag * 10 - age(f) * 0.4 })).sort((a, b) => b.score - a.score).slice(0, 12);
  const groups = [["Earthquakes M5.5+ · last 30 days · USGS", qs]];
  ["Wildfires", "Floods", "Severe Storms", "Volcanoes", "Sea and Lake Ice", "other"].forEach(k => {
    const l = F.filter(f => f.kind === k).sort((a, b) => a.t < b.t ? 1 : -1);
    const wild = l.filter(f => !/prescribed/i.test(f.name)), rx = l.filter(f => /prescribed/i.test(f.name));
    if (l.length) groups.push([`${EV_LBL[k]}s · NASA EONET · newest first`, wild.concat(rx).slice(0, 6)]);
  });
  hot = []; addFirePlace(F);
  $("#hotList").innerHTML = (!okQ && !okO ? `<p class="small">USGS and EONET are unreachable right now.</p>` : "") + groups.filter(g => g[1].length).map(([t, a]) => `<h3>${esc(t)}</h3>` + a.map(f => { hot.push(f); return `<button class="card click place hot" data-h="${hot.length - 1}"><span class="ic" style="color:${EV_COL[f.kind]}">${svg(EV_IC[f.kind], 20)}</span><span><b>${f.kind === "quake" ? "M" + (+f.mag).toFixed(1) + " · " : ""}${esc(f.name)}</b><small class="mono">${fmt(f.t)} ${f.t.slice(11, 16)} UTC · ${esc(f.src)}</small></span></button>` }).join("")).join("");
  $$("#hotList [data-h]").forEach(b => b.onclick = () => { const f = hot[+b.dataset.h]; openEvent(f, { lng: f.c[0], lat: f.c[1] }); flyEvent(f.c[0], f.c[1], f.t) });
}
let pop = null;
function openEvent(p, ll) {
  if (pop) pop.remove();
  const col = EV_COL[p.kind] || EV_COL.other;
  pop = new maplibregl.Popup({ maxWidth: "300px", offset: 14 }).setLngLat(ll).setHTML(`<div style="display:flex;gap:8px;align-items:center;color:${col}">${svg(EV_IC[p.kind] || "other", 18)}<b style="color:#F2F5FA">${EV_LBL[p.kind] || "Event"}${p.mag > 0 ? " · M" + (+p.mag).toFixed(1) : ""}</b></div><div style="font-weight:600;margin:6px 0 2px">${esc(p.name)}</div><div class="mono" style="color:#8A9BB4;font-size:11.5px">${fmt(p.t)} ${String(p.t).slice(11, 16)} UTC · ${esc(p.src)}</div><div style="display:flex;gap:6px;margin-top:10px"><button class="btn pri" id="goEv">Radar before / after</button><a class="btn" href="${esc(p.url)}" target="_blank" rel="noopener">Source</a></div>`).addTo(map);
  setTimeout(() => { const b = document.getElementById("goEv"); if (b) b.onclick = () => { pop.remove(); flyEvent(ll.lng, ll.lat, p.t) } }, 30);
}
function flyEvent(lng, lat, t) { closeTools(); S.ev = t; S.sel = null; sheet(false); map.flyTo({ center: [lng, lat], zoom: 9.5, speed: 1.5, curve: 1.6, essential: true }); toast("Finding NISAR passes before and after " + fmt(t)) }

/* ---------------- places + deep links ---------------- */
const placeBtn = p => `<button class="card click place" data-p="${p.id}"><span class="ic">${svg(p.ic, 20)}</span><span><b>${esc(p.name)}</b><small>${esc(p.sub)}</small></span><span class="cnt" id="cnt-${p.id}"></span></button>`;
function renderPlaces() {
  const groups = [...new Set(PLACES.map(p => p.g))], phone = matchMedia("(max-width:820px)").matches;
  $("#places").innerHTML = groups.map((g, i) => `<details class="pg"${!phone || i < 1 ? " open" : ""}><summary>${esc(g)}</summary>${PLACES.filter(p => p.g === g).map(placeBtn).join("")}</details>`).join("");
  $$("#places [data-p]").forEach(b => b.onclick = () => goPlace(b.dataset.p, true));
  PLACES.forEach(p => { const d = placeData[p.id], c = $("#cnt-" + p.id); if (d && c) c.textContent = d.n ? d.n + " passes" : "" });
}
/* the newest open EONET wildfire becomes an Events place, only if CMR confirms NISAR passes there */
async function addFirePlace(F) {
  const f = F.filter(x => x.kind === "Wildfires" && !/prescribed/i.test(x.name)).sort((a, b) => a.t < b.t ? 1 : -1)[0];
  if (!f || PLACES.find(p => p.id === "fire")) return;
  try {
    const ps = await nisarPasses([f.c[0] - .1, f.c[1] - .1, f.c[0] + .1, f.c[1] + .1], addDays(f.t.slice(0, 10), -45), today, { size: 200 });
    if (!ps.length) return;
    PLACES.splice(PLACES.findIndex(p => p.id === "langtang"), 0, { g: "More places", id: "fire", name: f.name.replace(/^Wildfire\s*/i, "Wildfire: "), sub: `NASA EONET wildfire, ${fmt(f.t)} · before / after`, c: f.c, z: 10.5, ic: "fire", ev: f.t });
    renderPlaces(); if (location.hash === "#p=fire") goPlace("fire", false);
  } catch (e) { }
}
function goPlace(id, fly) {
  const p = PLACES.find(x => x.id === id); if (!p) return;
  closeTools(); if (S.area) { S.area = null; map.getSource("area") && map.getSource("area").setData(areaFC(null)); $("#areaTag").hidden = true }
  S.sel = null; S.ev = p.ev || null; S.placeId = p.span ? null : id; sheet(false);
  if (p.span) S.focus = { start: NISAR_FIRST, end: today, label: "all NISAR passes since " + fmt(NISAR_FIRST), then: ps => spanPair(ps) };
  history.replaceState(null, "", "#p=" + id); showPlaceInfo(p);
  const opt = { center: p.c, zoom: p.z, essential: true };
  if (fly) map.flyTo({ ...opt, speed: 1.6, curve: 1.6 }); else { map.jumpTo(opt); clearTimeout(mt); mt = setTimeout(loadPasses, 60) }
}

/* our dev server lists folders: check the listing first so a missing file is not a 404 in the console (static hosts: just try) */
const listings = {};
async function mayExist(dir, name) {
  if (!(dir in listings)) listings[dir] = fetch(dir, { cache: "no-cache" }).then(async l => (l.ok && /text\/html/.test(l.headers.get("content-type") || "")) ? await l.text() : null).catch(() => null);
  const t = await listings[dir]; return !t || !/Directory listing/i.test(t) || t.includes(`href="${name}"`);
}
/* ---------------- place notes: why it changes, what to watch, in the news ---------------- */
let newsP = null;
function placeNews() { if (!newsP) newsP = mayExist("cases/", "places_news.json").then(ok => ok ? fetch("cases/places_news.json", { cache: "no-cache" }).then(r => r.ok ? r.json() : null) : null).catch(() => null); return newsP }
let gunwP = null;
function loadGunw() { if (!gunwP) gunwP = new Promise(res => { if (window.FalakusGUNW) return res(true); const sc = document.createElement("script"); sc.src = "gunw.js"; sc.onload = () => res(!!window.FalakusGUNW); sc.onerror = () => res(false); document.head.appendChild(sc) }); return gunwP }
async function showPlaceInfo(p) {
  const el = $("#placeInfo"); el.hidden = true;
  const j = await placeNews(); const n = (j && j.places && j.places[p.id]) || {};
  const gunw = p.ev && await loadGunw();
  if (!p.nasa && !gunw && !n.why_it_changes && !n.watch_for && !(n.sources || []).length) return;
  const src = Array.isArray(n.sources) ? n.sources : [];
  const nw = placeData[p.id] && placeData[p.id].newest;
  el.innerHTML = `<div class="small" style="text-transform:uppercase;letter-spacing:.08em">${esc(p.name)}</div>
    ${p.nasa ? `<a href="https://images.nasa.gov/details/${esc(p.nasa.id)}" target="_blank" rel="noopener" style="display:flex;gap:10px;align-items:center;margin:8px 0;text-decoration:none;color:var(--ink2)"><img src="${esc(p.nasa.img)}" alt="NASA ${esc(p.nasa.id)}" width="96" height="64" style="object-fit:cover;border-radius:8px;border:1px solid var(--line)"><span class="small">NASA/JPL ${esc(p.nasa.id)}, NISAR image of ${esc(fmt(p.nasa.date))}. On the map: the newest pass here${nw ? ", " + esc(fmt(nw.day)) : ""}. See it yourself, today.</span></a>` : ""}
    ${gunw ? `<button class="btn" id="gunwBtn">${svg("radar", 16)}Ground motion (interferogram)</button>` : ""}
    ${n.why_it_changes ? `<p><b>Why it changes:</b> ${esc(n.why_it_changes)}</p>` : ""}${n.watch_for ? `<p><b>Watch for:</b> ${esc(n.watch_for)}</p>` : ""}
    ${n.suggested_period && n.suggested_period.from ? `<button class="btn pri" id="playChange">${svg("timelapse", 16)}Play the change · ${esc(fmt(n.suggested_period.from))} → ${esc(fmt(n.suggested_period.to || today))}</button>` : ""}
    ${src.length ? `<h3 style="margin-top:12px">In the news</h3>` + src.map(x => `<a class="newsl" href="${esc(x.url)}" target="_blank" rel="noopener"><span class="mono small">${esc(x.publisher || "")} · ${esc(x.date || "")}</span><br>${esc(x.title || x.url)}</a>`).join("") : ""}`;
  el.hidden = false;
  const b = $("#playChange"); if (b) b.onclick = () => playChange(n.suggested_period);
  const gb = $("#gunwBtn"); if (gb) gb.onclick = () => GM.open(p.c[0], p.c[1], p.ev, p.gmTrack);
}
function playChange(per) {
  closeTools(); $("#t-tl").hidden = false; $("#bTl").classList.add("on");
  $("#tlSrc").value = "nisar"; $("#tlRange").value = "c"; $("#tlCustom").hidden = false;
  $("#tlFrom").value = per.from; $("#tlTo").value = per.to || today; sheet(false);
  const go = () => tlBuild(); if (map.isMoving()) map.once("moveend", go); else go();
}
/* ---------------- ground motion (NISAR GUNW interferograms, web/gunw.js) ----------------
   Event pair over the epicentre (reference before, secondary after the USGS time), opacity, legend, USGS epicentre star,
   and a swipe against an earlier same-track "control" pair: if the fringes are the quake they are absent in the control. */
const GM = { pairs: [], pair: null, ev: null, ctl: null };
function starImage() { const c = document.createElement("canvas"); c.width = c.height = 48; const g = c.getContext("2d"); g.beginPath(); for (let i = 0; i < 10; i++) { const r = i % 2 ? 9 : 21, a = -Math.PI / 2 + i * Math.PI / 5; g.lineTo(24 + r * Math.cos(a), 24 + r * Math.sin(a)) } g.closePath(); g.fillStyle = "#FFD23F"; g.fill(); g.lineWidth = 3; g.strokeStyle = "#07111F"; g.stroke(); return g.getImageData(0, 0, 48, 48) }
function gmEpi(lon, lat) {
  const fc = { type: "FeatureCollection", features: lon == null ? [] : [{ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: [lon, lat] } }] };
  if (!map.hasImage("gm-star")) map.addImage("gm-star", starImage(), { pixelRatio: 2 });
  if (map.getSource("gm-epi")) return map.getSource("gm-epi").setData(fc);
  map.addSource("gm-epi", { type: "geojson", data: fc });
  map.addLayer({ id: "gm-epi", type: "symbol", source: "gm-epi", layout: { "icon-image": "gm-star", "icon-allow-overlap": true } });
}
GM.open = async (lon, lat, evISO, prefer) => {
  if (!window.FalakusGUNW) return toast("Ground-motion module did not load");
  GM.ev = { lon, lat, t: evISO }; $("#gm").hidden = false; $("#gmV").textContent = "Searching NASA CMR for interferograms…"; $("#gmSel").innerHTML = ""; $("#gmLeg").innerHTML = ""; $("#gmN").textContent = "";
  gmEpi(lon, lat);
  try { GM.pairs = await FalakusGUNW.eventPairs(lon, lat, evISO) } catch (e) { GM.pairs = [] }
  if (!GM.pairs.length) { $("#gmV").textContent = "No interferogram spans this event yet"; $("#gmN").textContent = "NASA publishes GUNW pairs after both passes are processed; this updates automatically when they appear in CMR."; return }
  $("#gmSel").innerHTML = GM.pairs.map((p, i) => `<option value="${i}">${esc(p.track + p.dir)} · ${esc(fmtS(p.ref))} → ${esc(fmtS(p.sec))} (${p.days} d)</option>`).join("");
  const k = Math.max(0, GM.pairs.findIndex(p => prefer && (p.track.replace(/^0+/, "") + p.dir) === prefer.replace(/^0+/, "")));
  $("#gmSel").value = k; GM.show(GM.pairs[k]);
};
/* the GUNW agent saved the Panama browse PNGs in cases/gunw/ (+ control/): use our copy when present (offline-safe, fast) */
async function gmLocal(pair) {
  if (pair._local !== undefined) return pair;
  const name = (pair.browse || "").split("?")[0].split("/").pop();
  if (!GM.local) GM.local = fetch("gunw_local.json", { cache: "no-cache" }).then(r => r.ok ? r.json() : {}).catch(() => ({}));   // written by: ls cases/gunw/{,control/}*_LATLON.png
  pair._local = (await GM.local)[name] || null;
  if (pair._local) { pair.browse = pair._local; pair.thumb = null }
  return pair;
}
GM.show = async pair => {
  await gmLocal(pair);
  GM.pair = pair; gmCtlOff();
  $("#gmV").textContent = `${pair.track}${pair.dir}: ${fmtS(pair.ref)} → ${fmtS(pair.sec)}`;
  $("#gmN").textContent = "Quick preview from NASA's thumbnail; the full-resolution image (~20 s) replaces it when it arrives.";
  const info = await FalakusGUNW.show(map, pair, { opacity: +$("#gmOp").value / 100, beforeId: "ref" }); if (!info || GM.pair !== pair) return;
  $("#gmLeg").innerHTML = info.legend;
  info.ready.then(i => { if (GM.pair === pair) $("#gmN").textContent = i.stage === "full" ? `Full-resolution NASA browse image · ${i.method || "georeferenced"}${i.approximate ? " (approximate)" : ""} · USGS epicentre ★` : "Full image unavailable; showing the thumbnail." });
};
function gmCtlOff() { if (GM.ctl) { killSwipe(); $("#cmpLabels").hidden = true; GM.ctl = null; $("#gmCtl").textContent = "Compare with before-quake pair" } }
async function gmCtl() {
  if (GM.ctl) return gmCtlOff();
  const cs = await FalakusGUNW.controlPairs(GM.pair, 3).catch(() => []), c = cs[0];
  if (!c) return toast("No earlier pair on this track yet");
  await gmLocal(c);
  GM.ctl = c; $("#gmCtl").textContent = "Hide the before-quake pair";
  makeSwipe(null);                                       // second map on the left of the divider
  const go = () => { if (!mapB) return; addCycle(mapB); FalakusGUNW.show(mapB, c, { opacity: +$("#gmOp").value / 100, beforeId: "ref" }).then(() => mapB && gmTop(mapB)) };
  if (mapB.isStyleLoaded()) go(); else mapB.once("style.load", go);
  $("#lblA").textContent = `Left · before quake · ${fmtS(c.ref)} → ${fmtS(c.sec)}`; $("#lblB").textContent = `Right · spans quake · ${fmtS(GM.pair.ref)} → ${fmtS(GM.pair.sec)}`; $("#cmpLabels").hidden = false;
  toast("Drag the divider: fringes only on the right = ground motion from the quake");
}
GM.close = () => { gmCtlOff(); if (window.FalakusGUNW) FalakusGUNW.hide(map); gmEpi(null); $("#gm").hidden = true; GM.pair = null };
$("#gmSel").onchange = () => GM.show(GM.pairs[+$("#gmSel").value]);
$("#gmOp").oninput = e => { FalakusGUNW.setOpacity(map, e.target.value / 100); if (mapB) FalakusGUNW.setOpacity(mapB, e.target.value / 100) };
$("#gmCtl").onclick = gmCtl; $("#gmX").onclick = () => GM.close();

/* ---------------- cases ---------------- */
let casesTried = 0;
async function loadCases() {
  const el = $("#caseList");
  let idx = null;
  // our dev server lists folders: check the listing first so a missing index.json is not a 404 in the console
  let exists = true;
  try { const l = await fetch("cases/", { cache: "no-cache" }); if (l.ok && /text\/html/.test(l.headers.get("content-type") || "")) { const t = await l.text(); if (/Directory listing/i.test(t)) exists = /href="index\.json"/.test(t) } } catch (e) { }
  if (exists) { try { const r = await fetch("cases/index.json", { cache: "no-cache" }); if (r.ok) idx = await r.json() } catch (e) { } }
  if (!idx || !Array.isArray(idx.cases)) {
    el.innerHTML = `<div class="card"><div style="display:flex;gap:10px;align-items:center"><span class="spin"></span><span class="small">Case studies are being prepared. This list fills in automatically.</span></div></div>`;
    if (casesTried++ < 40) setTimeout(loadCases, 20000); return;
  }
  const got = new Array(idx.cases.length).fill(null);                    // 4 at a time: small static servers reset bursts
  await pool(idx.cases.map((id, k) => () => fetch(`cases/${encodeURIComponent(id)}.json`, { cache: "no-cache" }).then(r => r.ok ? r.json() : null).catch(() => null).then(j => { got[k] = j })), 4);
  const cs = got.filter(Boolean);
  if (!cs.length) { el.innerHTML = `<p class="small">No case files yet.</p>`; if (casesTried++ < 40) setTimeout(loadCases, 20000); return }
  const sec = (k, t, c) => c.sections && c.sections[k] ? `<details><summary>${t}</summary><p>${esc(c.sections[k])}</p></details>` : "";
  el.innerHTML = cs.map((c, i) => `<article class="card case">
    <h4>${esc(c.title)}</h4><div class="meta">${esc(c.place || "")}${c.date ? " · " + esc(c.date) : ""}</div>
    ${c.finding ? `<p class="find">${esc(c.finding)}</p>` : ""}
    ${Array.isArray(c.numbers) && c.numbers.length ? `<div class="nums">${c.numbers.map(n => `<div><b>${esc(n.value)}${n.unit ? " <small style='font-size:12px'>" + esc(n.unit) + "</small>" : ""}</b><span>${esc(n.label)}</span><em>${esc(n.source || "")}</em></div>`).join("")}</div>` : ""}
    ${sec("what", "What happened", c)}${sec("why", "Why", c)}${sec("radar", "What radar sees", c)}${sec("validation", "How we know (validation)", c)}${sec("limits", "Limits", c)}
    ${c.sections && Array.isArray(c.sections.sources) && c.sections.sources.length ? `<details><summary>Sources</summary><p>${c.sections.sources.map(s => `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a>`).join("<br>")}</p></details>` : ""}
    <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap"><button class="btn pri" data-case="${i}">${svg("compare", 16)}Show on map</button>${c.id === "andijan" ? `<a class="btn" href="case-andijan.html#dashboard">${svg("ext", 16)}Deep dive</a>` : ""}${/^panama/.test(c.id) ? `<button class="btn" data-gm="${i}">${svg("radar", 16)}Ground motion</button>` : ""}${c.id === "panama_gunw" ? `<a class="btn" href="cases/gunw/panama_event_vs_control.jpg" target="_blank" rel="noopener">${svg("ext", 16)}How we know (figure)</a>` : ""}</div>
  </article>`).join("");
  $$("[data-case]").forEach(b => b.onclick = () => showCase(cs[+b.dataset.case]));
  $$("[data-gm]").forEach(b => b.onclick = () => showCase(cs[+b.dataset.gm], true));
}
const PANAMA_EV = { lon: -80.7566, lat: 7.6069, t: "2026-10-09T17:56:05Z" };
function showCase(c, gm) {
  closeTools(); S.ev = null; S.sel = null; sheet(false);
  if (gm || c.id === "panama_gunw") {                    // interferogram case: fly there and drape the quake pair
    const e = c.id.startsWith("panama") ? PANAMA_EV : null;
    if (Array.isArray(c.bbox)) map.fitBounds([[c.bbox[0], c.bbox[1]], [c.bbox[2], c.bbox[3]]], { padding: 60, maxZoom: 10, duration: 1200 }); else if (c.center) map.flyTo({ center: c.center, zoom: c.zoom || 8 });
    if (e) GM.open(e.lon, e.lat, e.t, "141D"); return;
  }
  const tr = c.track ? { track: String(c.track).replace(/[AD]$/i, "").padStart(3, "0"), dir: String(c.track).slice(-1).toUpperCase() } : null;
  if (c.before && c.after) S.focus = {
    start: addDays(c.before, -20), end: addDays(c.after, 20) < today ? addDays(c.after, 20) : today, label: `around ${fmt(c.before)} and ${fmt(c.after)}`,
    then: ps => {
      const near = (d) => { const m = ps.filter(p => !tr || (p.track === tr.track && p.dir === tr.dir)); const pool = m.length ? m : ps; return pool.slice().sort((a, b) => Math.abs(new Date(a.day) - new Date(d)) - Math.abs(new Date(b.day) - new Date(d)))[0] };
      const a = near(c.before), b = near(c.after);
      if (a && b && a.key !== b.key) { openCompare(a, b); if (a.day !== c.before || b.day !== c.after) toast(`Closest passes to the case dates: ${fmtS(a.day)} and ${fmtS(b.day)}`) }
      else if (b) selectPass(b); else toast("No NISAR pass found near the case dates over this view");
    }
  };
  if (Array.isArray(c.bbox) && c.bbox.length === 4) map.fitBounds([[c.bbox[0], c.bbox[1]], [c.bbox[2], c.bbox[3]]], { padding: 60, maxZoom: 12, duration: 1400 });
  else if (c.center) map.flyTo({ center: c.center, zoom: c.zoom || 10, speed: 1.6, curve: 1.6 });
}

/* ---------------- learn ---------------- */
let learnDone = false;
async function loadLearn() {
  if (learnDone) return; learnDone = true;
  const el = $("#p-learn"); let ok = false;
  try { ok = (await fetch("learn.html", { method: "HEAD", cache: "no-cache" })).ok } catch (e) { }
  el.innerHTML = ok ? `<iframe src="learn.html?embed=1" title="Learn: how NISAR radar works"></iframe><a class="btn" style="margin:10px" href="learn.html" target="_blank" rel="noopener">${svg("ext", 16)}Open Learn as a full page</a>`
    : `<div style="padding:14px"><h2>How radar sees change</h2><p>NISAR sends 24 cm microwaves and times the echo. Calm water reflects them away (black); leaves scatter them in all directions (green, HV); walls and ground form corner reflectors (bright).</p><p class="small">The full Learn page is being written and will appear here.</p></div>`;
  if (!ok) learnDone = false;
}

/* ---------------- tabs, routing, sheet ---------------- */
function tab(t) {
  $$("#tabs button").forEach(b => b.classList.toggle("on", b.dataset.t === t)); $$(".pane").forEach(p => p.classList.toggle("on", p.id === "p-" + t));
  if (t === "learn") loadLearn();
}
$$("#tabs button").forEach(b => b.onclick = () => { tab(b.dataset.t); history.replaceState(null, "", "#" + b.dataset.t); sheet(true) });
function sheet(open) { $("#side").classList.toggle("open", open) }
$("#grab").onclick = () => sheet(!$("#side").classList.contains("open"));
function route() {
  const h = location.hash.slice(1);
  if (h.startsWith("p=")) { tab("explore"); goPlace(h.slice(2), false) }
  else if (["explore", "hotspots", "cases", "learn"].includes(h)) tab(h);
}
window.addEventListener("hashchange", route);

/* ---------------- header controls ---------------- */
$$("#proj button").forEach(b => b.onclick = () => { $$("#proj button").forEach(x => x.classList.toggle("on", x === b)); map.setProjection({ type: b.dataset.p }); if (mapB) mapB.setProjection({ type: b.dataset.p }) });
$$("#base button").forEach(b => b.onclick = () => {
  base = b.dataset.b; $$("#base button").forEach(x => x.classList.toggle("on", x === b));
  [map, mapB].filter(Boolean).forEach(m => { m.setLayoutProperty("b-dark", "visibility", base === "dark" ? "visible" : "none"); m.setLayoutProperty("b-sat", "visibility", base === "sat" ? "visible" : "none"); m.setLayoutProperty("ref", "visibility", base === "dark" ? "visible" : "none"); m.setLayoutProperty("ref-sat", "visibility", base === "sat" ? "visible" : "none") });
});

/* ---------------- search (OpenStreetMap Nominatim) ---------------- */
let qt;
$("#q").oninput = e => {
  clearTimeout(qt); const v = e.target.value.trim(); if (v.length < 3) { $("#results").hidden = true; return }
  qt = setTimeout(async () => {
    $("#qspin").hidden = false;
    try {
      const r = await (await fetch("https://nominatim.openstreetmap.org/search?format=json&limit=6&q=" + encodeURIComponent(v))).json();
      $("#results").innerHTML = r.map((x, i) => `<button data-i="${i}">${esc(x.display_name)}</button>`).join("") || `<button disabled>No match</button>`; $("#results").hidden = false;
      $$("#results button[data-i]").forEach(d => d.onclick = () => { const x = r[+d.dataset.i]; const bb = x.boundingbox.map(Number); $("#results").hidden = true; $("#q").value = x.display_name.split(",")[0]; closeTools(); S.sel = null; S.ev = null; map.fitBounds([[bb[2], bb[0]], [bb[3], bb[1]]], { maxZoom: 11, padding: 40, duration: 1500 }) });
    } catch (err) { $("#results").innerHTML = `<button disabled>Search unavailable</button>`; $("#results").hidden = false } finally { $("#qspin").hidden = true }
  }, 350);
};
$("#q").onkeydown = e => { if (e.key === "Enter") { const b = $("#results button[data-i]"); if (b) b.click() } };

/* ---------------- warm-up: prefetch the 8 start places into the browser cache ----------------
   For each place: NASA CMR passes for its view, then the GIBS tiles of the newest pass, the before/after pair and the
   time-lapse frames (most frequent track) at the zoom the place opens at, plus a sharper z+1/z+2 block at the centre. */
const placeData = {}; FK.placeData = placeData;
const lon2x = (lon, z) => (lon + 180) / 360 * 2 ** z;
const lat2y = (lat, z) => { const r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * 2 ** z };
function tilesFor(c, zf, W, H, zt) {
  const tpx = 256 * 2 ** (zf - zt), cx = lon2x(c[0], zt), cy = lat2y(c[1], zt), out = [];
  for (let x = Math.floor(cx - W / 2 / tpx); x <= Math.floor(cx + W / 2 / tpx); x++) for (let y = Math.floor(cy - H / 2 / tpx); y <= Math.floor(cy + H / 2 / tpx); y++) if (y >= 0 && y < 2 ** zt) out.push([zt, ((x % 2 ** zt) + 2 ** zt) % 2 ** zt, y]);
  return out;
}
function placeBBox(p, W, H) { const zt = p.z, cx = lon2x(p.c[0], zt), cy = lat2y(p.c[1], zt), dx = W / 2 / 256, dy = H / 2 / 256; const x2l = x => x / 2 ** zt * 360 - 180, y2l = y => { const n = Math.PI - 2 * Math.PI * y / 2 ** zt; return 180 / Math.PI * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n))) }; return [x2l(cx - dx), y2l(cy + dy), x2l(cx + dx), y2l(cy - dy)] }
async function pool(jobs, n) { let i = 0; await Promise.all(Array.from({ length: n }, async () => { while (i < jobs.length) { const j = jobs[i++]; try { await j() } catch (e) { } DBG.pre++ } })) }
async function warmup() {
  if (Q.get("noprefetch") === "1") return;
  const W = $("#main").clientWidth || 1080, H = $("#main").clientHeight || 820;
  for (const p of PLACES.filter(x => x.pre)) {
    try {
      const passes = await nisarPasses(placeBBox(p, W, H), NISAR_FIRST, today, { size: 2000, pages: 2 });
      const by = {}; passes.forEach(x => (by[tk(x)] = by[tk(x)] || []).push(x));
      const best = Object.values(by).sort((a, b) => b.length - a.length)[0] || [];
      placeData[p.id] = { passes, n: passes.length, newest: passes[0] || null, tlTrack: best[0] ? tk(best[0]) : null, tlFrames: best.length };
      const cnt = $("#cnt-" + p.id); if (cnt) cnt.textContent = passes.length ? `${passes.length} passes` : "";
      await Promise.all([...new Set(passes.slice(0, 40).map(x => x.day))].map(async d => { const ok = await hasImage(d, p.c, p.z); passes.filter(x => x.day === d).forEach(x => x.img = ok) }));
      const days = new Set();
      let pair = [];
      if (p.ev) { for (const l of Object.values(by)) { const bf = l.filter(x => x.t < p.ev)[0], af = l.filter(x => x.t > p.ev).slice(-1)[0]; if (bf && af) { pair = [bf.day, af.day]; break } } }
      const ws = withImg(passes);
      if (!p.ev && ws[0]) { const nb = ws.find(x => x.t < ws[0].t && tk(x) === tk(ws[0])); pair = [ws[0].day, nb && nb.day].filter(Boolean) }
      if (ws[0]) days.add(ws[0].day); pair.forEach(d => days.add(d));
      // dimmed under-layers of the newest pass
      [...new Set(ws.filter(x => ws[0] && x.day !== ws[0].day).map(x => x.day))].slice(0, 3).forEach(d => days.add(d));
      const zr = Math.min(13, Math.round(p.z)), jobs = [];
      const add = (d, tiles) => tiles.forEach(([z, x, y]) => { const u = gibsUrl(NISAR, d, "GoogleMapsCompatible_Level13").replace("{z}", z).replace("{y}", y).replace("{x}", x); jobs.push(() => gibsGet(u)) });
      days.forEach(d => { add(d, tilesFor(p.c, p.z, W, H, zr)); add(d, tilesFor(p.c, zr + 1, 512, 512, Math.min(13, zr + 1))); add(d, tilesFor(p.c, zr + 2, 512, 512, Math.min(13, zr + 2))) });
      withImg(best).slice(0, 16).forEach(x => { if (!days.has(x.day)) add(x.day, tilesFor(p.c, p.z, W, H, zr)) });
      DBG.preTot += jobs.length;
      await pool(jobs, 4);
      DBG.ready++;
    } catch (e) { DBG.last = "prefetch " + p.id + ": " + e.message }
  }
}

/* ---------------- boot ---------------- */
map.once("style.load", async () => {
  initCycle();
  map.on("sourcedata", e => { if (e.sourceId === "cyc" && !DBG.cycLoaded && map.isSourceLoaded("cyc")) DBG.cycLoaded = Math.round(performance.now()) });
  Object.keys(EV_COL).forEach(k => map.addImage("ic-" + k, iconImage(k), { pixelRatio: 2 }));
  map.addSource("ev", { type: "geojson", data: evFC });
  map.addSource("area", { type: "geojson", data: areaFC(null) });
  map.addLayer({ id: "area-fill", type: "fill", source: "area", paint: { "fill-color": "#3B74F0", "fill-opacity": 0.06 } });
  map.addLayer({ id: "area-line", type: "line", source: "area", paint: { "line-color": "#F2F5FA", "line-width": 1.2, "line-opacity": 0.75, "line-dasharray": [3, 2] } });
  const MAJOR = ["any", ["!=", ["get", "kind"], "quake"], [">=", ["get", "mag"], 6]];
  map.addLayer({ id: "ev-halo", type: "circle", source: "ev", filter: ["all", ["==", ["get", "kind"], "quake"], [">=", ["get", "mag"], 6]], paint: { "circle-radius": ["interpolate", ["linear"], ["get", "mag"], 6, 14, 8, 30], "circle-color": "#D93025", "circle-opacity": 0.12, "circle-stroke-color": "#D93025", "circle-stroke-opacity": 0.4, "circle-stroke-width": 1 } });
  map.addLayer({ id: "ev-minor", type: "circle", source: "ev", minzoom: 3.5, filter: ["!", MAJOR], paint: { "circle-radius": ["interpolate", ["linear"], ["get", "mag"], 4.5, 2.5, 6, 5], "circle-color": "#D93025", "circle-opacity": 0.7, "circle-stroke-color": "#07111F", "circle-stroke-width": 1 } });
  map.addLayer({ id: "ev", type: "symbol", source: "ev", filter: MAJOR, layout: { "icon-image": ["concat", "ic-", ["get", "kind"]], "icon-size": ["interpolate", ["linear"], ["zoom"], 1, 0.7, 6, 0.9, 10, 1], "icon-allow-overlap": false, "icon-padding": 1, "symbol-sort-key": ["-", 10, ["get", "mag"]] } });
  ["ev", "ev-minor"].forEach(l => { map.on("click", l, e => { if (drawing) return; openEvent(e.features[0].properties, e.lngLat) }); map.on("mouseenter", l, () => { if (!drawing) map.getCanvas().style.cursor = "pointer" }); map.on("mouseleave", l, () => { if (!drawing) map.getCanvas().style.cursor = "" }) });
  map.on("mousedown", drawStart); map.on("mousemove", drawMove); map.on("mouseup", drawEnd);
  map.on("touchstart", drawStart); map.on("touchmove", drawMove); map.on("touchend", e => drawEnd(e));
  setTlH();
  // newest NISAR pass worldwide (validated collection first)
  try {
    const j = await (await fetch(`https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=${COLL[0][0]}&page_size=1&sort_key=-start_date`)).json();
    if (j.feed.entry[0]) { S.newestGlobal = { ...parseG(j.feed.entry[0], "validated"), concept: COLL[0][0] }; S.newestGlobal.key = S.newestGlobal.day + "_" + tk(S.newestGlobal) }
  } catch (e) { }
  setNewest();
  route();
  if (!location.hash) { setTimeout(() => goPlace("panama_m77", true), 1200) }        // featured first view
  else if (!location.hash.startsWith("#p=")) loadPasses();
  loadEvents(); loadCases();
  map.once("idle", () => setTimeout(warmup, 6000));   // prefetch only after the first view has painted
});
renderPlaces();
Object.assign(FK, { GM, CYC, ORB, orbitFC, showCycle, showOrbits, updateSci, SCI, tl, selectPass, openCompare, goPlace, setArea, tlBuild, openVs, loadPasses });
renderStrip();
})();
