"use strict";
/* Falakus explorer upgrades (round 5), loaded after explorer.js and gunw.js; uses explorer.js globals (map, LK, S, STOPS, card, IC...).
   1. NISAR layer = NASA GIBS "latest 12-day cycle": per tile, the last 24 daily GIBS dates newest-first, composited until covered
      (NASA publishes passes days late, so the cycle before fills holes). Below z4 our old browse mosaic.
   2. Rail: Places, Compare, Ground motion, Analyze.   3. Tour: Panama, Dubai, Jakobshavn, Aral, Andijan.   */
const XP_PLACES = [
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
const XP={end:null,days:[],empty:null};
const XP_NIS=(d,z,x,y)=>`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/NISAR_L2_Geocoded_Polarimetric_Covariance/default/${d}/GoogleMapsCompatible_Level13/${z}/${y}/${x}.png`;
const xpIso=d=>d.toISOString().slice(0,10), xpAdd=(s,n)=>{const d=new Date(s+"T00:00:00Z");d.setUTCDate(d.getUTCDate()+n);return xpIso(d)};
async function xpGet(u,signal){for(let n=0;n<2;n++){try{const r=await fetch(n?u+"?r=1":u,{signal});if(r.status>=500)continue;if(!r.ok)return null;return await r.arrayBuffer()}catch(e){if(e.name==="AbortError")throw e;return null}}return null}
maplibregl.addProtocol("cyc",async(params,ctl)=>{
 const [,z,x,y]=params.url.match(/^cyc:\/\/(\d+)\/(\d+)\/(\d+)/).map(Number),colour=/[?&]c=1/.test(params.url);
 if(z<=9){try{const r=await fetch(HERE+`tiles/${z}/${x}/${y}.webp?v=9`,{signal:ctl.signal});if(r.ok)return{data:await r.arrayBuffer()}}catch(e){if(e.name==="AbortError")throw e}}
 if(!XP.days.length)await XP.ready;
 const c=new OffscreenCanvas(256,256),g=c.getContext("2d");g.globalCompositeOperation="destination-over";let drawn=0;
 for(let i=0;i<XP.days.length;i+=12){
  const bufs=await Promise.all(XP.days.slice(i,i+12).map(d=>xpGet(XP_NIS(d,z,x,y),ctl.signal)));
  for(const b of bufs){if(!b||b.byteLength<400)continue;try{g.drawImage(await createImageBitmap(new Blob([b])),0,0);drawn++}catch(e){}}
  if(drawn){const a=g.getImageData(0,0,256,256).data;let t=0;for(let k=3;k<a.length;k+=16)if(a[k]<250)t++;if(t<40)break}}
 if(!drawn){if(!XP.empty){const e=new OffscreenCanvas(1,1);e.getContext("2d");XP.empty=await (await e.convertToBlob({type:"image/png"})).arrayBuffer()}return{data:XP.empty.slice(0)}}
 if(!colour){const im=g.getImageData(0,0,256,256),d=im.data;for(let k=0;k<d.length;k+=4){const v=d[k];d[k+1]=v;d[k+2]=v}g.globalCompositeOperation="copy";g.putImageData(im,0,0)}   // grey = HH (the red channel of the GIBS false colour)
 return{data:await(await c.convertToBlob({type:"image/png"})).arrayBuffer()}});
XP.ready=(async()=>{let end=xpAdd(xpIso(new Date()),-2);
 try{const ac=new AbortController();setTimeout(()=>ac.abort(),4000);
  const t=await(await fetch(`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/wmts.cgi?SERVICE=WMTS&REQUEST=DescribeDomains&VERSION=1.0.0&LAYER=NISAR_L2_Geocoded_Polarimetric_Covariance&TILEMATRIXSET=GoogleMapsCompatible_Level13&TIME=${xpAdd(end,-60)}/${xpAdd(end,3)}`,{signal:ac.signal})).text();
  const m=t.match(/<Domain>([^<]*)<\/Domain>/),l=m&&m[1].split(",").pop().split("/");if(l&&/^\d{4}-\d\d-\d\d/.test(l[1]||l[0]))end=(l[1]||l[0]).slice(0,10)}catch(e){}
 XP.end=end;XP.days=Array.from({length:24},(_,i)=>xpAdd(end,-i));
 if(typeof xpLegend==="function")xpLegend()})();
XP.colour=false;
Object.assign(LK.nisar_mosaic,{title:"NISAR radar mosaic",gid:"NISAR_L2_Geocoded_Polarimetric_Covariance (NASA GIBS)",
 short:"Every NISAR pass side by side. Dark means water. Zoom past 9 for NASA GIBS detail.",
 info:"Up to zoom 9: every NISAR pass side by side from the browse images (grey radar). Past zoom 9: NASA GIBS NISAR GCOV, the last 12-day cycle stacked newest on top (gaps filled from the cycle before), shown as grey HH by default; switch to colour (HH+HV) in the legend.",
 src:"NASA-ISRO NISAR GCOV · ASF DAAC browse mosaic · NASA GIBS",url:()=>`cyc://{z}/{x}/{y}?c=${XP.colour?1:0}`,maxz:12});
window.prefetchStop=function(){};
            // the old mosaic warm-up does not apply to the composited layer

/* ---------- caption ---------- */
/* one legend card (bottom-left, collapsible): the NISAR cycle line first, then the active heat legends */
function xpLegend(){const L=document.querySelector(".mapleg");if(!L)return;let n=document.getElementById("xpleg");
 if(!n){n=document.createElement("div");n.id="xpleg";n.className="hl";L.prepend(n)}
 else if(L.firstChild!==n)L.prepend(n);
 n.innerHTML=`<b>NISAR radar</b><div class="bar" style="background:linear-gradient(90deg,#0b0b0b,#7a7a7a,#f2f2f2)"></div><div class="lab"><span>smooth water</span><span>towns, forest</span></div>
 <div class="n">Past zoom 9: NASA GIBS, 12-day cycle ending ${XP.end?fmtD(XP.end):"…"}</div><button class="xpcolbtn" id="xpcolbtn" aria-pressed="${XP.colour}">${XP.colour?"Grey (HH)":"Colour (HH+HV)"}</button>`;
 n.querySelector("#xpcolbtn").onclick=e=>{e.stopPropagation();XP.colour=!XP.colour;syncRasters(map,S.date);if(typeof mapB!=="undefined"&&mapB)syncRasters(mapB,S.dateB);xpLegend()}}
new MutationObserver(()=>{const L=document.querySelector(".mapleg");if(L&&L.firstChild&&L.firstChild.id!=="xpleg")xpLegend()}).observe(document.body,{childList:true,subtree:true});
XP.ready.then(xpLegend);setTimeout(xpLegend,500);

/* ---------- rail: Places, Compare, Ground motion, Analyze ---------- */
const XP_IC={pin:'<path d="M12 21s-6-5.6-6-10a6 6 0 0 1 12 0c0 4.4-6 10-6 10z"/><circle cx="12" cy="11" r="2.2"/>',
 cmp:'<path d="M12 3v18"/><rect x="3.5" y="5" width="17" height="14" rx="2"/>',gm:'<path d="M3 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0"/><path d="M3 17c2-4 4-4 6 0s4 4 6 0 4-4 6 0" opacity=".5"/>',
 an:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'};
(()=>{const R=$("rail"),sep=R.querySelector(".rsep");
 const html=[["@compare","cmp","Compare","swipe","Swipe between two dates of the current view"],
  ["@gm","gm","Motion","InSAR","Ground motion from NISAR interferograms (Panama M7.7)"]]
  .map(([k,ic,b,s,t])=>`<button class="rb" data-x="${k}" title="${t}" aria-label="${t}"><svg viewBox="0 0 24 24" aria-hidden="true">${XP_IC[ic]}</svg><b>${b}</b><small>${s}</small></button>`).join("");
 sep?sep.insertAdjacentHTML("beforebegin",html):R.insertAdjacentHTML("beforeend",html);
 R.addEventListener("click",e=>{const b=e.target.closest("[data-x]");if(!b)return;e.stopPropagation();const k=b.dataset.x;
  if(k==="@compare")return $("cmp").click();if(k==="@gm")return xpGM(XP_PLACES[0])},true)})();

/* ---------- Places ---------- */
function xpPlaces(){const groups=[...new Set(XP_PLACES.map(p=>p.g))];
 return `<h2>Places</h2><p class="xpm">Click one: we fly there and show the newest NISAR radar.</p><div>${groups.map(g=>`<div style="font:600 10.5px/1 system-ui;letter-spacing:.08em;text-transform:uppercase;color:#5A6472;margin:12px 0 6px">${esc(g)}</div>`+
  XP_PLACES.filter(p=>p.g===g).map(p=>`<button class="xpp" data-p="${p.id}" style="display:block;width:100%;text-align:left;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:9px;padding:8px 10px;margin:0 0 6px;color:inherit;cursor:pointer"><b style="font-size:13px">${esc(p.name)}</b><br><small>${esc(p.sub)}</small></button>`).join("")).join("")}</div>`}
function xpGo(p){if(!p)return;if(typeof stopSpin==="function")stopSpin();if(!S.active.includes("nisar_mosaic"))setLayer("nisar_mosaic",true);
 map.flyTo({center:p.c,zoom:Math.min(p.z,10.5),pitch:30,duration:4000,essential:true});
 card(`<h3>${esc(p.name)}</h3><div class="m">${esc(p.sub)}</div><p class="brief">NISAR radar, newest pass at each spot from NASA GIBS (12-day cycle ending ${XP.end?fmtD(XP.end):"…"}).</p>
  ${p.nasa?`<a href="https://images.nasa.gov/details/${esc(p.nasa.id)}" target="_blank" rel="noopener" style="display:flex;gap:8px;align-items:center;color:inherit;text-decoration:none;margin:8px 0"><img src="${esc(p.nasa.img)}" alt="NASA ${esc(p.nasa.id)}" width="84" height="56" style="object-fit:cover;border-radius:6px"><small>NASA/JPL ${esc(p.nasa.id)}: NASA's own NISAR image of ${esc(fmtD(p.nasa.date))}. The map shows the same place today.</small></a>`:""}
  <div class="acts">${p.ev?`<button class="btn" id="xp-gm">Ground motion</button>`:""}<button class="btn ghost" id="xp-cmp">Before / after</button></div>`);
 const cb=document.getElementById("xp-cmp");if(cb)cb.onclick=()=>$("cmp").click();
 const g=document.getElementById("xp-gm");if(g)g.onclick=()=>xpGM(p)}

/* ---------- Ground motion (gunw.js) ---------- */
let XP_LOCAL=null;
async function xpGM(p){if(!window.FalakusGUNW)return toast("Ground-motion module did not load");
 if(!p.ev)return toast("Ground motion is available for earthquake places");
 map.flyTo({center:p.c,zoom:8.3,pitch:0,duration:3000,essential:true});
 card(`<h3>Ground motion · ${esc(p.name)}</h3><div class="m">Searching NASA CMR for interferograms that span the quake…</div>`);
 let pairs=[];try{pairs=await FalakusGUNW.eventPairs(p.c[0],p.c[1],p.ev)}catch(e){}
 if(!pairs.length){card(`<h3>Ground motion · ${esc(p.name)}</h3><p class="brief">No NISAR interferogram spans this event yet.</p>`);return}
 const pair=pairs.find(q=>(q.track.replace(/^0+/,"")+q.dir)===(p.gmTrack||"").replace(/^0+/,""))||pairs[0];
 if(!XP_LOCAL)XP_LOCAL=fetch("gunw_local.json").then(r=>r.ok?r.json():{}).catch(()=>({}));
 const name=(pair.browse||"").split("?")[0].split("/").pop(),loc=(await XP_LOCAL)[name];if(loc){pair.browse=loc;pair.thumb=null}
 const info=await FalakusGUNW.show(map,pair,{opacity:.85});
 if(!map.hasImage("xp-star")){const c=document.createElement("canvas");c.width=c.height=48;const g=c.getContext("2d");g.beginPath();for(let i=0;i<10;i++){const r=i%2?9:21,a=-Math.PI/2+i*Math.PI/5;g.lineTo(24+r*Math.cos(a),24+r*Math.sin(a))}g.closePath();g.fillStyle="#FFD23F";g.fill();g.lineWidth=3;g.strokeStyle="#07111F";g.stroke();map.addImage("xp-star",g.getImageData(0,0,48,48),{pixelRatio:2})}
 const fc={type:"FeatureCollection",features:[{type:"Feature",properties:{},geometry:{type:"Point",coordinates:p.c}}]};
 if(map.getSource("xp-epi"))map.getSource("xp-epi").setData(fc);else{map.addSource("xp-epi",{type:"geojson",data:fc});map.addLayer({id:"xp-epi",type:"symbol",source:"xp-epi",layout:{"icon-image":"xp-star","icon-allow-overlap":true}})}
 card(`<h3>Ground motion · ${esc(p.name)}</h3><div class="m">NISAR interferogram ${esc(pair.track+pair.dir)}: ${esc(fmtD(pair.ref))} → ${esc(fmtD(pair.sec))} (${pair.days} days, spans the quake) · ★ USGS epicentre</div>
  <label style="display:flex;gap:8px;align-items:center;font-size:12px;margin:8px 0">Opacity <input type="range" id="xp-op" min="0" max="100" value="85" style="flex:1"></label>${info?info.legend:""}
  <div class="acts"><button class="btn ghost" id="xp-gmx">Hide</button><button class="btn ghost" id="xp-fig">How we know</button></div>`);
 $("xp-fig").onclick=()=>window.open("cases/gunw/panama_event_vs_control.jpg","_blank","noopener");
 $("xp-op").oninput=e=>FalakusGUNW.setOpacity(map,e.target.value/100);
 $("xp-gmx").onclick=()=>{FalakusGUNW.hide(map);map.getSource("xp-epi")?.setData({type:"FeatureCollection",features:[]});$("card").hidden=true}}

/* ---------- tour: five stops; captions claim only what the radar shows ---------- */
const XP_TOUR=[
 {id:"panama",name:"Panama M7.7",v:()=>({center:[-80.7566,7.6069],zoom:8.3,pitch:20,bearing:0}),cap:()=>"Panama, M7.7 on 9 Oct 2026 (USGS). The coloured rings are a NISAR interferogram from passes 27 Sep and 9 Oct: tight bands = the ground moved toward or away from the satellite, 11.9 cm per colour cycle.",gm:1},
 {id:"dubai",name:"Dubai",v:()=>({center:[55.15,25.1],zoom:10.3,pitch:40,bearing:-10}),cap:()=>"Dubai: the Palm islands and the city show bright (hard, built surfaces); the calm Gulf shows black."},
 {id:"jakobshavn",name:"Jakobshavn",v:()=>({center:[-49.6,69.2],zoom:8.6,pitch:35,bearing:0}),cap:()=>"Sermeq Kujalleq (Jakobshavn), Greenland, in NISAR radar: the ice sheet and the iceberg-filled fjord, seen through polar night and cloud."},
 {id:"aral",name:"Aral Sea",v:()=>({center:[59.8,45.2],zoom:7.6,pitch:25,bearing:0}),cap:()=>"The Aral Sea: black = remaining calm water; the large textured areas are the dry former seabed."},
 {id:"andijan",name:"Andijan",v:()=>({center:[73.21,40.77],zoom:10.3,pitch:40,bearing:0}),cap:()=>"Andijan reservoir, Uzbekistan: the black shape is open water; our own models track its area every 12 days (Open analysis)."}];
STOPS.splice(0,STOPS.length,...XP_TOUR);
const _tourGo=tourGo;
window.tourGo=async function(i,auto,jump){await _tourGo(i,auto,jump);const st=STOPS[i];
 if(st&&st.gm&&TOUR.on){const once=()=>{if(TOUR.on&&TOUR.i===i)xpGM(XP_PLACES[0]).then(()=>{$("card").hidden=true})};if(map.isMoving())map.once("moveend",once);else once()}
 else if(window.FalakusGUNW&&st&&!st.gm)FalakusGUNW.hide(map)};
window.XP=XP;

/* ---------- one app shell: top bar + white side panel (Live Earth · Places · Cases · Learn) ---------- */
document.querySelector(".fk-hdr")?.remove();document.documentElement.classList.remove("embed");
const XI={live:'<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="8" cy="8" r="6.3"/><path d="M1.8 8h12.4M8 1.7c2 2.1 2 10.5 0 12.6M8 1.7c-2 2.1-2 10.5 0 12.6"/></svg>',
 places:'<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M8 14.5s-4.5-4.2-4.5-7.5a4.5 4.5 0 0 1 9 0c0 3.3-4.5 7.5-4.5 7.5z"/><circle cx="8" cy="7" r="1.6"/></svg>',
 cases:'<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="1.5" y="1.5" width="5.5" height="7" rx="1.2"/><rect x="9" y="1.5" width="5.5" height="4" rx="1.2"/><rect x="9" y="7.5" width="5.5" height="7" rx="1.2"/><rect x="1.5" y="10.5" width="5.5" height="4" rx="1.2"/></svg>',
 learn:'<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M2 4.5l6-2.5 6 2.5-6 2.5z"/><path d="M4.5 6v3.8c1 .9 2.2 1.4 3.5 1.4s2.5-.5 3.5-1.4V6"/></svg>'};
document.body.insertAdjacentHTML("afterbegin",`<header class="fk-hdr" id="xpbar"><a class="fk-brand" href="#live" aria-label="Falakus home"><svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><circle cx="13" cy="13" r="12" fill="#17515F"/><path d="M4 15.5c3-3 6-3 9 0s6 3 9 0" stroke="#F6F3ED" stroke-width="2" fill="none" stroke-linecap="round"/></svg><span><b>Falakus</b><br><span>Earth&rsquo;s changes, seen by NISAR radar</span></span></a>
<nav class="fk-tabs" id="xptabs" aria-label="Sections">${[["live","Live Earth"],["places","Places"],["cases","Cases"],["learn","Learn"]].map(([k,t])=>`<a href="#${k}" data-t="${k}"${k==="live"?' class="on" aria-current="page"':""}>${XI[k]}<span>${t}</span></a>`).join("")}</nav>
<span class="fk-live" title="NASA-ISRO NISAR L-band radar, every 12 days"><i></i>NISAR L-band</span></header>
<aside id="xpside" hidden aria-label="Side panel"><button class="xpx" id="xpsx" aria-label="Close panel">×</button><div id="xpbody"></div></aside>`);
let XP_CASES=null;
const XP_IMGS=new Set(["aral_nisar.png", "borneo_change.png", "charvak_change.png", "deadsea_change.png", "dubai_change.png", "gaza_change.png", "jakobshavn_change.png", "lagos_change.png", "langtang_change.png", "mekong_change.png", "mumbai_change.png", "nile_delta_change.png", "panama_change.png", "pineisland_change.png", "rondonia_change.png", "urmia_change.png"]);
const XP_ORDER=["panama_gunw","panama","borneo","deadsea","andijan","jakobshavn","gaza","aral","nile_delta","langtang"];
function xpThumb(c){const cand=[c.image,`${c.id}_change.png`,`${c.id}_nisar.png`].filter(Boolean).map(x=>String(x).split("/").pop());const f=cand.find(x=>XP_IMGS.has(x));return f?"cases/img/"+f:null}
function xpBadge(c){const v=/valid|calib/i.test(c.quality||"");return `<span class="xpbadge ${v?"ok":""}">${v?"Validated":"Screening"}</span>`}
function xpNums(c){const unit=u=>({km2:"km<sup>2</sup>",km:"km",m:"m",cm:"cm","%":"%"}[u]??esc(u||""));
 return (c.numbers||[]).filter(n=>typeof n.value==="number"&&!/date|passes/i.test(n.unit||"")).slice(0,3)
  .map(n=>`<div class="xpnum"><b>${n.value.toLocaleString("en",{maximumFractionDigits:1})}<small> ${unit(n.unit)}</small></b><span>${esc(String(n.label||"").replace(/\s*\((?:n\s*=|data\/)[^)]*\)/g,""))}</span></div>`).join("")}
async function xpLoadCases(){if(!XP_CASES)XP_CASES=fetch("cases/index.json").then(r=>r.ok?r.json():{cases:[]}).then(async j=>{const ids=[...(j.cases||[])].sort((a,b)=>{const ia=XP_ORDER.indexOf(a),ib=XP_ORDER.indexOf(b);return (ia<0?99:ia)-(ib<0?99:ib)});
  const out=[];for(const id of ids){try{const r=await fetch(`cases/${encodeURIComponent(id)}.json`);if(r.ok)out.push(await r.json())}catch(e){}}return out}).catch(()=>[]);return XP_CASES}
async function xpCases(){const cs=await xpLoadCases();
 return `<h2>Case studies</h2><p class="xpm">Deep, checked stories. Open one for its numbers and how we know.</p>`+cs.map((c,i)=>{const t=xpThumb(c),f=String(c.finding||"").split(/(?<=\.)\s/)[0];
  return `<button class="xpcl" data-co="${i}">${t?`<img src="${t}" alt="" loading="lazy">`:`<span class="xpnoimg"></span>`}<span class="xpct"><b>${esc(c.title)}</b><small>${esc(f.length>140?f.slice(0,137)+"…":f)}</small>${xpBadge(c)}</span></button>`}).join("")}
function xpCaseDetail(c){const t=xpThumb(c),S_=c.sections||{},fold=(k,h)=>S_[k]&&typeof S_[k]==="string"?`<details><summary>${h}</summary><p>${esc(S_[k])}</p></details>`:"";
 const src=Array.isArray(S_.sources)&&S_.sources.length?`<details><summary>Sources</summary><p>${S_.sources.map(x=>`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.name)}</a>`).join("<br>")}</p></details>`:"";
 return `<button class="xpback" id="xpback">‹ All cases</button>${t?`<img class="xphero" src="${t}" alt="${esc(c.title)}">`:""}<h2 style="margin-top:10px">${esc(c.title)}</h2><div class="xpm">${esc(c.place||"")}${c.date?` · <span class="mono">${esc(c.date)}</span>`:""} ${xpBadge(c)}</div>
  <p class="xpfind">${esc(c.finding||"")}</p><div class="xpnums">${xpNums(c)}</div>
  <div class="acts"><button class="btn" id="xc-map">Show on map</button>${c.before&&c.after?`<button class="btn ghost" id="xc-cmp">Before / after</button>`:""}${/^panama/.test(c.id)?`<button class="btn ghost" id="xc-gm">Ground motion</button>`:""}${c.id==="panama_gunw"?`<a class="btn ghost" href="cases/gunw/panama_event_vs_control.jpg" target="_blank" rel="noopener">Figure</a>`:""}${c.id==="andijan"?`<a class="btn ghost" href="case-andijan.html#dashboard">Deep dive</a>`:""}</div>
  <div class="xpfolds">${fold("what","What happened")}${fold("why","Why")}${fold("validation","How we know")}${fold("radar","What radar sees")}${fold("limits","Limits")}${src}</div>`}
function xpFly(c){if(Array.isArray(c.bbox))map.fitBounds([[c.bbox[0],c.bbox[1]],[c.bbox[2],c.bbox[3]]],{padding:60,maxZoom:11,duration:2500});else if(c.center)map.flyTo({center:c.center,zoom:c.zoom||9})}
async function xpCasesBind(body){const cs=await xpLoadCases();
 body.querySelectorAll("[data-co]").forEach(b=>b.onclick=()=>{const c=cs[+b.dataset.co];body.innerHTML=xpCaseDetail(c);body.scrollTop=0;xpFly(c);
  $("xpback").onclick=async()=>{body.innerHTML=await xpCases();xpCasesBind(body)};$("xc-map").onclick=()=>xpFly(c);
  const cm=document.getElementById("xc-cmp");if(cm)cm.onclick=()=>{xpFly(c);if(!S.cmp)$("cmp").click()};
  const g=document.getElementById("xc-gm");if(g)g.onclick=()=>xpGM(XP_PLACES[0])})}
async function xpTab(t,push){const side=$("xpside"),body=$("xpbody");document.querySelectorAll("#xptabs a").forEach(b=>{b.classList.toggle("on",b.dataset.t===t);if(b.dataset.t===t)b.setAttribute("aria-current","page");else b.removeAttribute("aria-current")});
 if(push)history.replaceState(null,"","#"+t);
 if(t==="live"){side.hidden=true;document.documentElement.classList.remove("xp-side");return}
 side.hidden=false;document.documentElement.classList.add("xp-side");$("panel").classList.remove("open");
 if(t==="places"){body.innerHTML=xpPlaces();body.querySelectorAll(".xpp").forEach(b=>b.onclick=()=>xpGo(XP_PLACES.find(p=>p.id===b.dataset.p)))}
 if(t==="cases"){body.innerHTML='<p class="xpm">Loading case studies…</p>';body.innerHTML=await xpCases();
  xpCasesBind(body)}
 if(t==="learn")body.innerHTML='<h2>Learn</h2><iframe src="learn.html?embed=1" title="How NISAR radar works" style="width:100%;height:calc(100vh - 170px);border:0;border-radius:10px;background:#fff"></iframe>'}
document.querySelectorAll("#xptabs a").forEach(b=>b.onclick=e=>{e.preventDefault();xpTab(b.dataset.t,true)});
$("xpsx").onclick=()=>xpTab("live",true);
function xpRoute(){const h=location.hash.slice(1);
 if(["places","cases","learn","live"].includes(h))return xpTab(h,false);
 if(h==="hotspots")return xpTab("live",false);
 const m=h.match(/^p=([\w-]+)/);if(m){const p=XP_PLACES.find(x=>x.id===m[1]);if(p){if(!S.view)S.view={center:p.c,zoom:3};xpTab("places",false);const go=()=>{xpGo(p);if(p.feat)setTimeout(()=>xpGM(p),4200)};map.loaded()?go():map.once("load",go)}}}
window.addEventListener("hashchange",xpRoute);xpRoute();
