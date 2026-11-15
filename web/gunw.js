/* Falakus: NISAR ground-motion (InSAR) pairs from NASA CMR, drawn on a MapLibre map.
 *
 * window.FalakusGUNW = {
 *   listFor(bbox, from, to)        -> Promise<pair[]>   GUNW pairs touching bbox [w,s,e,n] in [from,to] (YYYY-MM-DD)
 *   eventPairs(lon, lat, timeISO)  -> Promise<pair[]>   pairs whose reference < event < secondary over that point
 *   controlPairs(pair, n)          -> Promise<pair[]>   up to n earlier pairs, same track/direction/frame (for comparison)
 *   show(map, pair, {opacity})     -> Promise<info>     drape the browse PNG on its footprint (+ legend)
 *   setOpacity(map, value 0..1), hide(map), legendHTML(), FRINGE_CM
 * }
 *
 * Data: NISAR L2 GUNW (geocoded unwrapped interferogram), provisional C2854335566-ASF and validated C3622247503-ASF.
 * The public browse PNG ("..._LATLON.png") shows WRAPPED phase, north-up on a lon/lat grid, transparent outside the
 * swath. Its canvas is larger than the footprint, so we georeference it the same way as tools/gunw_common.py: the
 * four extreme points of the opaque area are matched to the four corners of the CMR footprint polygon (measured
 * residual <= 0.006 deg on full frames). Because the PNG is north-up, the MapLibre image corners form a rectangle; the
 * swath rotation is inside the picture. If the fit fails (truncated data), we borrow the transform of a full image of
 * the same track/direction/frame, else fall back to the polygon's bounding box and flag it as approximate.
 */
(function () {
  const COLL = ["C2854335566-ASF", "C3622247503-ASF"];
  const CMR = "https://cmr.earthdata.nasa.gov/search/granules.umm_json";
  const FRINGE_CM = 11.9; // lambda/2, lambda = 0.2384 m (1.257 GHz)
  const SRC = "falakus-gunw", LYR = "falakus-gunw-layer", OUTLINE = "falakus-gunw-outline";
  const geoCache = new Map();

  function parse(name) {
    const p = name.split("_"), d = s => `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
    const t = s => `${d(s)}T${s.slice(9, 11)}:${s.slice(11, 13)}:${s.slice(13, 15)}Z`;
    return { name, cycle: p[4], track: p[5], dir: p[6], frame: p[7], refStart: t(p[11]), secStart: t(p[13]),
      ref: d(p[11]), sec: d(p[13]), fullFrame: p[p.length - 3] === "F",
      days: Math.round((Date.parse(d(p[13])) - Date.parse(d(p[11]))) / 864e5) };
  }

  function toPair(item) {
    const u = item.umm, g = parse(u.GranuleUR);
    const pts = u.SpatialExtent.HorizontalSpatialDomain.Geometry.GPolygons[0].Boundary.Points.map(q => [q.Longitude, q.Latitude]);
    const urls = (u.RelatedUrls || []).map(r => r.URL).filter(x => /^https/.test(x));
    return Object.assign(g, {
      direction: g.dir === "A" ? "ascending" : "descending",
      label: `${g.track}${g.dir} ${g.ref} → ${g.sec} (${g.days} d)`,
      browse: urls.find(x => x.endsWith("_LATLON.png")) || null,
      thumb: urls.find(x => x.endsWith("_LATLON_thumbnail.png")) || null,
      h5: urls.find(x => x.endsWith(".h5")) || null,
      footprint: pts, collection: item.meta["collection-concept-id"],
      validated: item.meta["collection-concept-id"] === COLL[1],
    });
  }

  async function query(params) {
    let out = [], page = 1;
    for (;;) {
      const q = new URLSearchParams();
      COLL.forEach(c => q.append("collection_concept_id", c));
      Object.entries(params).forEach(([k, v]) => [].concat(v).forEach(x => q.append(k, x)));
      q.set("page_size", "200"); q.set("page_num", String(page));
      const r = await fetch(`${CMR}?${q}`);
      if (!r.ok) throw new Error(`CMR ${r.status}`);
      const items = (await r.json()).items || [];
      out = out.concat(items.map(toPair).filter(p => p.browse));
      if (items.length < 200 || page >= 10) break;
      page++;
    }
    // provisional and validated may both exist for one pair: keep validated
    const best = new Map();
    for (const p of out) { const k = p.name.split("_").slice(5, 14).join("_"); if (!best.has(k) || p.validated) best.set(k, p); }
    return [...best.values()].sort((a, b) => a.ref < b.ref ? 1 : a.ref > b.ref ? -1 : (a.track + a.frame).localeCompare(b.track + b.frame));
  }

  function listFor(bbox, from, to) {
    return query({ bounding_box: bbox.map(v => (+v).toFixed(4)).join(","), temporal: `${from}T00:00:00Z,${to}T23:59:59Z`, sort_key: "-start_date" });
  }

  async function eventPairs(lon, lat, timeISO) {
    const t = Date.parse(timeISO), day = 864e5;
    const from = new Date(t - 60 * day).toISOString().slice(0, 10), to = new Date(t + 60 * day).toISOString().slice(0, 10);
    const all = await query({ point: `${lon},${lat}`, temporal: `${from}T00:00:00Z,${to}T23:59:59Z` });
    return all.filter(p => Date.parse(p.refStart) < t && t < Date.parse(p.secStart)).sort((a, b) => a.days - b.days);
  }

  async function controlPairs(pair, n = 3) {
    const pat = `NISAR_L2_*_GUNW_*_${pair.track}_${pair.dir}_${pair.frame}_*`;
    const from = new Date(Date.parse(pair.ref) - 120 * 864e5).toISOString().slice(0, 10);
    const all = await query({ "readable_granule_name[]": pat, "options[readable_granule_name][pattern]": "true", temporal: `${from}T00:00:00Z,${pair.ref}T23:59:59Z` });
    return all.filter(p => p.sec <= pair.ref).sort((a, b) => (a.sec < b.sec ? 1 : -1)).slice(0, n);
  }

  // ---- georeference a browse PNG against its footprint (mirrors tools/gunw_common.py:georef)
  const blobCache = new Map();
  function blobURL(url) { // one download per PNG, shared by the pixel fit and the map layer
    if (!blobCache.has(url)) blobCache.set(url, fetch(url).then(r => { if (!r.ok) throw new Error("browse " + r.status); return r.blob() }).then(b => URL.createObjectURL(b)));
    return blobCache.get(url);
  }
  async function loadPixels(url) {
    const img = new Image(); img.src = await blobURL(url);
    await img.decode();
    const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight;
    const ctx = c.getContext("2d", { willReadFrequently: true }); ctx.drawImage(img, 0, 0);
    return { W: c.width, H: c.height, data: ctx.getImageData(0, 0, c.width, c.height).data, canvas: c, ctx };
  }
  // the browse PNG paints "no data" inside the frame with one flat colour (47,19,55): make it transparent for display
  const maskedCache = new Map();
  function maskedURL(url) {
    if (!maskedCache.has(url)) maskedCache.set(url, loadPixels(url).then(px => {
      const id = px.ctx.getImageData(0, 0, px.W, px.H), d = id.data;
      for (let i = 0; i < d.length; i += 4) if (d[i] === 47 && d[i + 1] === 19 && d[i + 2] === 55) d[i + 3] = 0;
      px.ctx.putImageData(id, 0, 0);
      return new Promise(res => px.canvas.toBlob(b => res(URL.createObjectURL(b)), "image/png"));
    }));
    return maskedCache.get(url);
  }

  function fit({ W, H, data }, poly) {
    let L = [1e9, 0, 0], R = [-1, 0, 0], T = [0, 1e9, 0], B = [0, -1, 0]; // [x, y, n] accumulators for ties
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (!data[(y * W + x) * 4 + 3]) continue;
      if (x < L[0]) L = [x, y, 1]; else if (x === L[0]) { L[1] += y; L[2]++ }
      if (x > R[0]) R = [x, y, 1]; else if (x === R[0]) { R[1] += y; R[2]++ }
      if (y < T[1]) T = [x, y, 1]; else if (y === T[1]) { T[0] += x; T[2]++ }
      if (y > B[1]) B = [x, y, 1]; else if (y === B[1]) { B[0] += x; B[2]++ }
    }
    if (R[0] < 0) return null;
    L = [L[0], L[1] / L[2]]; R = [R[0], R[1] / R[2]]; T = [T[0] / T[2], T[1]]; B = [B[0] / B[2], B[1]];
    const pts = poly.slice(0, poly.length - (poly[0][0] === poly.at(-1)[0] && poly[0][1] === poly.at(-1)[1] ? 1 : 0));
    const by = (f, s) => pts.reduce((a, b) => (s * f(b) > s * f(a) ? b : a));
    const w = by(p => p[0], -1), e = by(p => p[0], 1), n = by(p => p[1], 1), s = by(p => p[1], -1);
    const sx = (e[0] - w[0]) / Math.max(R[0] - L[0], 1), ox = w[0] - sx * L[0];
    const sy = (n[1] - s[1]) / Math.min(T[1] - B[1], -1), oy = n[1] - sy * T[1];
    const res = Math.max(Math.abs(oy + sy * L[1] - w[1]), Math.abs(oy + sy * R[1] - e[1]), Math.abs(ox + sx * T[0] - n[0]), Math.abs(ox + sx * B[0] - s[0]));
    const lat = pts.reduce((a, p) => a + p[1], 0) / pts.length, ratio = sx * Math.cos(lat * Math.PI / 180) / -sy;
    return { ox, sx, oy, sy, W, H, residual: res, ok: res < Math.max(0.02, 2.5 * Math.abs(sx)) && ratio > 0.9 && ratio < 1.1 };
  }

  const corners = g => [[g.ox, g.oy], [g.ox + g.sx * g.W, g.oy], [g.ox + g.sx * g.W, g.oy + g.sy * g.H], [g.ox, g.oy + g.sy * g.H]];

  function bboxOf(pair) {
    const xs = pair.footprint.map(p => p[0]), ys = pair.footprint.map(p => p[1]);
    const w = Math.min(...xs), e = Math.max(...xs), s = Math.min(...ys), n = Math.max(...ys);
    return { coordinates: [[w, n], [e, n], [e, s], [w, s]], method: "footprint bbox", residualDeg: null, approximate: true };
  }

  // quick=true uses the 100 px thumbnail (fast, ~0.03 deg); otherwise the full browse PNG (~0.002 deg)
  async function georef(pair, quick = false) {
    const key = pair.name + (quick ? "#t" : "");
    if (geoCache.has(key)) return geoCache.get(key);
    const url = quick ? pair.thumb : pair.browse;
    let g = null, how = quick ? "thumbnail fit" : "fit";
    try { g = url && fit(await loadPixels(url), pair.footprint) } catch (e) { g = null }
    if (!quick && (!g || !g.ok)) {
      try { // borrow from an earlier full image of the same track/direction/frame (identical canvas)
        const cs = await controlPairs(pair, 4), ref = cs.find(p => p.fullFrame) || cs[0];
        const g2 = ref && fit(await loadPixels(ref.browse), ref.footprint);
        if (g2 && g2.ok && (!g || (g2.W === g.W && g2.H === g.H))) { g = g2; how = "borrowed from " + ref.label }
      } catch (e) { }
    }
    const out = g && g.ok ? { coordinates: corners(g), method: how, residualDeg: +g.residual.toFixed(4), approximate: quick } : bboxOf(pair);
    geoCache.set(key, out);
    return out;
  }

  function legendHTML() {
    return `<div class="fg-legend" style="font:12px/1.4 system-ui,sans-serif;color:#e8eef6;background:rgba(13,27,46,.92);border:1px solid rgba(255,255,255,.15);border-radius:10px;padding:8px 10px;max-width:280px">
<div style="height:10px;border-radius:5px;background:linear-gradient(90deg,#e2d9e2,#6f8fc8,#3a2c79,#2f1337,#7d2a37,#c06a3c,#e2d9e2);margin-bottom:6px"></div>
<b>1 colour cycle = ${FRINGE_CM} cm</b> line-of-sight motion (NISAR L-band)<br>
Noisy speckle = no coherence (water, forest change, broken ground)<br>
<span style="opacity:.75">Screening from NASA's browse images (wrapped phase). Long smooth stripes across a whole frame are often ionosphere or orbit ramps: compare with an earlier pair on the same track.</span></div>`;
  }

  function hide(map) {
    for (const id of [LYR, OUTLINE]) if (map.getLayer(id)) map.removeLayer(id);
    for (const id of [SRC, SRC + "-fp"]) if (map.getSource(id)) map.removeSource(id);
  }

  function setOpacity(map, v) { if (map.getLayer(LYR)) map.setPaintProperty(LYR, "raster-opacity", Math.max(0, Math.min(1, +v))) }

  let showToken = 0;
  async function show(map, pair, opts = {}) {
    const token = ++showToken;
    const quick = pair.thumb ? await georef(pair, true) : bboxOf(pair);
    if (token !== showToken) return null;
    hide(map);
    map.addSource(SRC, { type: "image", url: pair.thumb ? await blobURL(pair.thumb) : await blobURL(pair.browse), coordinates: quick.coordinates });
    map.addLayer({ id: LYR, type: "raster", source: SRC, paint: { "raster-opacity": opts.opacity ?? 0.85, "raster-fade-duration": 0, "raster-resampling": "nearest" } }, opts.beforeId);
    map.addSource(SRC + "-fp", { type: "geojson", data: { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [pair.footprint] } } });
    map.addLayer({ id: OUTLINE, type: "line", source: SRC + "-fp", paint: { "line-color": "#ffffff", "line-width": 1, "line-opacity": 0.6, "line-dasharray": [2, 2] } }, opts.beforeId);
    const info = Object.assign({ pair, legend: legendHTML(), stage: "thumbnail" }, quick);
    // full-resolution PNG (2-3 MB, can take ~20 s from NASA's browse server), then an exact georeference
    info.ready = georef(pair).then(async geo => {
      const src = token === showToken && map.getSource(SRC);
      if (src) { src.updateImage({ url: await maskedURL(pair.browse), coordinates: geo.coordinates }); Object.assign(info, geo, { stage: "full" }) }
      return info;
    }).catch(e => { info.error = String(e); return info });
    return info;
  }

  window.FalakusGUNW = { listFor, eventPairs, controlPairs, show, hide, setOpacity, legendHTML, georef, FRINGE_CM, COLLECTIONS: COLL };
})();
