/* Minimal Mapbox Vector Tile decoder (lines + points + properties) -> GeoJSON in lon/lat for a given tile grid.
   Used for NASA GIBS NISAR orbit tracks, which GIBS serves only in EPSG:4326 (2km matrix: z0 = 2x1 tiles of 180 deg). */
(function (root) {
  function R(buf) { this.b = new Uint8Array(buf); this.p = 0 }
  R.prototype.v = function () { let r = 0, s = 0, c; do { c = this.b[this.p++]; r += (c & 0x7f) * 2 ** s; s += 7 } while (c & 0x80); return r };
  R.prototype.sub = function () { const n = this.v(), r = new R(this.b.buffer.slice(this.b.byteOffset + this.p, this.b.byteOffset + this.p + n)); this.p += n; return r };
  R.prototype.str = function () { const n = this.v(), s = new TextDecoder().decode(this.b.subarray(this.p, this.p + n)); this.p += n; return s };
  R.prototype.skip = function (t) { if (t === 0) this.v(); else if (t === 1) this.p += 8; else if (t === 2) this.p += this.v(); else if (t === 5) this.p += 4 };
  R.prototype.packed = function () { const r = this.sub(), o = []; while (r.p < r.b.length) o.push(r.v()); return o };
  const zz = n => (n % 2 ? -(n + 1) / 2 : n / 2);
  function value(r) { let out = null; while (r.p < r.b.length) { const k = r.v(), f = k >> 3, t = k & 7;
    if (f === 1) out = r.str(); else if (f === 2) { out = new DataView(r.b.buffer, r.b.byteOffset + r.p, 4).getFloat32(0, true); r.p += 4 }
    else if (f === 3) { out = new DataView(r.b.buffer, r.b.byteOffset + r.p, 8).getFloat64(0, true); r.p += 8 }
    else if (f === 4 || f === 5) out = r.v(); else if (f === 6) out = zz(r.v()); else if (f === 7) out = !!r.v(); else r.skip(t) } return out }
  function decode(buf, toLL) {
    const t = new R(buf), feats = [];
    while (t.p < t.b.length) { const k = t.v(); if ((k >> 3) !== 3) { t.skip(k & 7); continue }
      const l = t.sub(); let name = "", ext = 4096; const keys = [], vals = [], raw = [];
      while (l.p < l.b.length) { const k2 = l.v(), f = k2 >> 3;
        if (f === 1) name = l.str(); else if (f === 2) raw.push(l.sub()); else if (f === 3) keys.push(l.str()); else if (f === 4) vals.push(value(l.sub())); else if (f === 5) ext = l.v(); else l.skip(k2 & 7) }
      for (const fr of raw) { let type = 0, tags = [], geom = [];
        while (fr.p < fr.b.length) { const k3 = fr.v(), f = k3 >> 3; if (f === 2) tags = fr.packed(); else if (f === 3) type = fr.v(); else if (f === 4) geom = fr.packed(); else fr.skip(k3 & 7) }
        const props = { _layer: name }; for (let i = 0; i < tags.length; i += 2) props[keys[tags[i]]] = vals[tags[i + 1]];
        const parts = []; let x = 0, y = 0, cur = null;
        for (let i = 0; i < geom.length;) { const c = geom[i++], id = c & 7, n = c >> 3;
          if (id === 7) { if (cur && cur.length) cur.push(cur[0]); continue }
          for (let j = 0; j < n; j++) { x += zz(geom[i++]); y += zz(geom[i++]); if (id === 1) { cur = []; parts.push(cur) } cur.push(toLL(x / ext, y / ext)) } }
        if (!parts.length) continue;
        const g = type === 1 ? (parts.length === 1 && parts[0].length === 1 ? { type: "Point", coordinates: parts[0][0] } : { type: "MultiPoint", coordinates: parts.flat() })
          : type === 2 ? { type: "MultiLineString", coordinates: parts } : { type: "Polygon", coordinates: parts };
        feats.push({ type: "Feature", properties: props, geometry: g }) } }
    return feats;
  }
  root.MVT = { decode };
  if (typeof module !== "undefined") module.exports = root.MVT;
})(typeof window !== "undefined" ? window : globalThis);
