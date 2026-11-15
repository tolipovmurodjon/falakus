"use strict";
/* Additions to the v8 Live Earth explorer (loaded after explorer.js; v8 colours and defaults unchanged):
   a. an opacity slider for every layer in "More layers" (heatmaps, events, quakes too) + a full-colour satellite base map
   b. "NISAR 15 m (NASA GIBS, latest pass)": off by default, greyscale (HH = red channel of the GIBS false colour)
   c. "Ground motion · Panama M7.7" (NISAR interferogram via gunw.js): off by default, also a tour stop
   d. tour: World, Panama M7.7, Dubai, Jakobshavn, Aral, Borneo, Andijan */

/* ---------- b. NISAR 15 m grey from NASA GIBS: per tile, the newest of the last 24 daily GIBS images wins ---------- */
const V8P={end:null,days:[],empty:null};
const v8pAdd=(s,n)=>{const d=new Date(s+"T00:00:00Z");d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)};
V8P.ready=(async()=>{let end=v8pAdd(TODAY,-2);
 try{const ac=new AbortController();setTimeout(()=>ac.abort(),4000);
  const t=await(await fetch(`${GIBS.replace("/best/","/best/wmts.cgi")}?SERVICE=WMTS&REQUEST=DescribeDomains&VERSION=1.0.0&LAYER=NISAR_L2_Geocoded_Polarimetric_Covariance&TILEMATRIXSET=GoogleMapsCompatible_Level13&TIME=${v8pAdd(end,-60)}/${v8pAdd(end,3)}`,{signal:ac.signal})).text();
  const m=t.match(/<Domain>([^<]*)<\/Domain>/),l=m&&m[1].split(",").pop().split("/");if(l&&/^\d{4}-\d\d-\d\d/.test(l[1]||l[0]))end=(l[1]||l[0]).slice(0,10)}catch(e){}
 V8P.end=end;V8P.days=Array.from({length:24},(_,i)=>v8pAdd(end,-i))})();
async function v8pGet(u,signal){for(let n=0;n<2;n++){try{const r=await fetch(n?u+"?r=1":u,{signal});if(r.status>=500)continue;return r.ok?await r.arrayBuffer():null}catch(e){if(e.name==="AbortError")throw e;return null}}return null}
maplibregl.addProtocol("nisg",async(params,ctl)=>{
 const [,z,x,y]=params.url.match(/^nisg:\/\/(\d+)\/(\d+)\/(\d+)/).map(Number);await V8P.ready;
 const c=new OffscreenCanvas(256,256),g=c.getContext("2d");g.globalCompositeOperation="destination-over";let drawn=0;
 for(let i=0;i<V8P.days.length;i+=12){
  const bufs=await Promise.all(V8P.days.slice(i,i+12).map(d=>v8pGet(`${GIBS}NISAR_L2_Geocoded_Polarimetric_Covariance/default/${d}/GoogleMapsCompatible_Level13/${z}/${y}/${x}.png`,ctl.signal)));
  for(const b of bufs){if(!b||b.byteLength<400)continue;try{g.drawImage(await createImageBitmap(new Blob([b])),0,0);drawn++}catch(e){}}
  if(drawn){const a=g.getImageData(0,0,256,256).data;let t=0;for(let k=3;k<a.length;k+=16)if(a[k]<250)t++;if(t<40)break}}
 if(!drawn){if(!V8P.empty){const e=new OffscreenCanvas(1,1);e.getContext("2d");V8P.empty=await(await e.convertToBlob({type:"image/png"})).arrayBuffer()}return{data:V8P.empty.slice(0)}}
 const im=g.getImageData(0,0,256,256),d=im.data;for(let k=0;k<d.length;k+=4){d[k+1]=d[k];d[k+2]=d[k]}g.globalCompositeOperation="copy";g.putImageData(im,0,0);
 return{data:await(await c.convertToBlob({type:"image/png"})).arrayBuffer()}});

/* ---------- new layers ---------- */
const V8P_LAYERS=[
 {after:"nisar_mosaic",key:"nisar_gibs",group:"radar",title:"NISAR 15 m (NASA GIBS, latest pass)",gid:"NISAR_L2_Geocoded_Polarimetric_Covariance",
  short:"Sharp NISAR radar from NASA GIBS, newest pass at each spot, in grey. Zoom 6+.",
  info:"NASA GIBS NISAR GCOV, the newest pass over each spot from the last 24 days (one 12-day orbit cycle plus the one before, because NASA publishes passes days late). Shown in grey: the HH channel. Dark is smooth water, bright is rough ground, towns and forest. Not tied to the timeline date.",
  src:"NASA-ISRO NISAR GCOV · ASF DAAC · NASA GIBS",static:"Newest pass, not tied to the timeline date.",url:()=>"nisg://{z}/{x}/{y}",minz:6,maxz:12},
 {after:"events",key:"gm_panama",group:"events",kind:"gm",title:"Ground motion · Panama M7.7",
  short:"NISAR interferogram 27 Sep → 9 Oct 2026 across the 9 Oct quake. One colour cycle = 11.9 cm.",
  info:"NISAR L2 GUNW browse image (wrapped phase) for track 141 descending, 27 Sep → 9 Oct 2026, which spans the USGS M7.7 earthquake of 9 Oct 2026 17:56 UTC (us6000u18k). Each full colour cycle is 11.9 cm of ground motion toward or away from the satellite. Speckle means no coherence (water, forest). Screening from NASA browse images.",
  src:"NASA-ISRO NISAR L2 GUNW (ASF DAAC) · USGS"},
 {after:"base_sat",key:"base_sat_full",group:"base",pos:"bottom",title:"Satellite photo (full colour)",short:"Real satellite imagery, full colour and brightness.",
  info:"Esri World Imagery at full colour, the real satellite photo. Turn the radar layers' opacity down to see it through them.",src:"Esri, Maxar, Earthstar Geographics",static:"Static base map.",url:()=>ESRI+"World_Imagery/MapServer/tile/{z}/{y}/{x}",maxz:18}];
for(const l of V8P_LAYERS){const i=LAYERS.findIndex(x=>x.key===l.after);LAYERS.splice(i<0?LAYERS.length:i+1,0,l);LK[l.key]=l}
// explorer.js read the #l= list before these layers existed: pick ours up again, in their place in the list
(()=>{const h=new URLSearchParams(location.hash.slice(1));if(!h.has("l"))return;const want=h.get("l").split(",").map(p=>p.split("~"));
 const order=want.map(w=>w[0]).filter(k=>LK[k]);for(const [k,o] of want)if(V8P_LAYERS.some(l=>l.key===k)&&o)S.op[k]=Math.max(0,Math.min(1,+o/100));
 S.active=order})();

/* ---------- a. opacity for every layer (vector layers too) ---------- */
const V8P_PAINT={heatmap:["heatmap-opacity"],circle:["circle-opacity","circle-stroke-opacity"],symbol:["icon-opacity","text-opacity"],fill:["fill-opacity"],line:["line-opacity"]};
const V8P_ORIG={};
const v8pScale=(o,v)=>typeof o==="number"?o*v:Array.isArray(o)&&o[0]==="interpolate"?o.map((x,j)=>j>=4&&j%2===0&&typeof x==="number"?x*v:x):v;
function v8pOpacity(m,k){const ids=(OVER[k]||[]).concat(k==="gm_panama"?["falakus-gunw-layer"]:[]),v=S.op[k]??1;if(!m)return;
 for(const id of ids){const L=m.getLayer(id);if(!L)continue;
  if(L.type==="raster"){m.setPaintProperty(id,"raster-opacity",v*0.85);continue}
  for(const p of V8P_PAINT[L.type]||[]){const key=id+"|"+p;if(!(key in V8P_ORIG))V8P_ORIG[key]=m.getPaintProperty(id,p);m.setPaintProperty(id,p,v8pScale(V8P_ORIG[key]??1,v))}}}
function v8pPanel(){buildPanel();
 $("groups").querySelectorAll(".ly").forEach(ly=>{const k=ly.dataset.k;if(ly.querySelector("[data-op]"))return;
  ly.querySelector(".det").insertAdjacentHTML("beforeend",`<div class="opr">Opacity<input type="range" min="0" max="100" value="100" data-op="${k}" aria-label="Opacity"><span class="mono" data-opv="${k}">100%</span></div>`);
  const r=ly.querySelector(`[data-op="${k}"]`);r.oninput=()=>{S.op[k]=r.value/100;ly.querySelector(`[data-opv="${k}"]`).textContent=r.value+"%";v8pOpacity(map,k);v8pOpacity(mapB,k);writeHash()}});
 if(map.isStyleLoaded())renderPanelState()}
v8pPanel();

/* ---------- c. ground motion layer ---------- */
const V8P_EV={lon:-80.7566,lat:7.6069,t:"2026-10-09T17:56:05Z",track:"141D"};let V8P_LOCAL=null,V8P_GM=0;
async function v8pGM(on){const my=++V8P_GM;const FG=window.FalakusGUNW;
 if(!on){if(FG)FG.hide(map);map.getSource("v8p-epi")?.setData({type:"FeatureCollection",features:[]});return}
 if(!FG){toast("Ground-motion module did not load");return}
 let pairs=[];try{pairs=await FG.eventPairs(V8P_EV.lon,V8P_EV.lat,V8P_EV.t)}catch(e){}if(my!==V8P_GM)return;
 const pair=pairs.find(p=>(p.track.replace(/^0+/,"")+p.dir)===V8P_EV.track)||pairs[0];if(!pair){toast("No NISAR interferogram spans the Panama quake yet");return}
 if(!V8P_LOCAL)V8P_LOCAL=fetch("gunw_local.json").then(r=>r.ok?r.json():{}).catch(()=>({}));
 const loc=(await V8P_LOCAL)[(pair.browse||"").split("?")[0].split("/").pop()];if(loc){pair.browse=loc;pair.thumb=null}
 await FG.show(map,pair,{opacity:0.85*(S.op.gm_panama??1),beforeId:map.getLayer("labels")?"labels":undefined});if(my!==V8P_GM)return;
 if(!map.hasImage("v8p-star")){const c=document.createElement("canvas");c.width=c.height=48;const g=c.getContext("2d");g.beginPath();for(let i=0;i<10;i++){const r=i%2?9:21,a=-Math.PI/2+i*Math.PI/5;g.lineTo(24+r*Math.cos(a),24+r*Math.sin(a))}g.closePath();g.fillStyle="#FFD23F";g.fill();g.lineWidth=3;g.strokeStyle="#0B1015";g.stroke();map.addImage("v8p-star",g.getImageData(0,0,48,48),{pixelRatio:2})}
 const fc={type:"FeatureCollection",features:[{type:"Feature",properties:{},geometry:{type:"Point",coordinates:[V8P_EV.lon,V8P_EV.lat]}}]};
 if(map.getSource("v8p-epi"))map.getSource("v8p-epi").setData(fc);else{map.addSource("v8p-epi",{type:"geojson",data:fc});map.addLayer({id:"v8p-epi",type:"symbol",source:"v8p-epi",layout:{"icon-image":"v8p-star","icon-allow-overlap":true}})}}
const _setLayer=setLayer;
window.setLayer=function(k,on){_setLayer(k,on);if(k==="gm_panama")v8pGM(on)};
map.on("load",()=>{for(const k of Object.keys(S.op))v8pOpacity(map,k);if(S.active.includes("gm_panama"))v8pGM(true)});

/* ---------- d. tour stops (captions claim only what the map shows) ---------- */
const V8P_STOPS=[
 {id:"panama",name:"Panama M7.7",v:()=>({center:[-80.7566,7.6069],zoom:8.3,pitch:20,bearing:0}),gm:1,
  cap:()=>"Panama, M7.7 on 9 Oct 2026 (USGS ★). The coloured rings are a NISAR interferogram from passes on 27 Sep and 9 Oct: each colour cycle is 11.9 cm of ground motion toward or away from the satellite."},
 {id:"dubai",name:"Dubai",v:()=>({center:[55.15,25.1],zoom:10.3,pitch:40,bearing:-10}),cap:()=>"Dubai in L-band radar: the Palm islands and the city bounce the signal back bright; the calm Gulf is black."},
 {id:"jakobshavn",name:"Jakobshavn",v:()=>({center:[-49.6,69.2],zoom:8.6,pitch:35,bearing:0}),cap:()=>"Sermeq Kujalleq (Jakobshavn), Greenland: the ice sheet and the iceberg-filled fjord, seen by radar through cloud and polar night."},
 {id:"aral2",name:"Aral Sea",v:()=>({center:[59.8,45.2],zoom:7.6,pitch:25,bearing:0}),cap:()=>"The Aral Sea: black is the remaining calm water; the large textured areas are the dry former seabed."},
 {id:"borneo",name:"Borneo",v:()=>({center:[114,-2.3],zoom:9.5,pitch:30,bearing:0}),cap:()=>"Central Kalimantan, Borneo: bright forest, the straight lines of drainage canals and plantation blocks in the peatland."},
 {id:"andijan",name:"Andijan",v:()=>({center:[73.21,40.77],zoom:10.3,pitch:40,bearing:0}),cap:()=>"Andijan reservoir, Uzbekistan: the black shape is open water. We measure its area on every NISAR pass."}];
STOPS.splice(1,STOPS.length-1,...V8P_STOPS);
const _tourGo=tourGo;
window.tourGo=async function(i,auto,jump){const st=STOPS[i];
 if(st&&!st.gm&&S.active.includes("gm_panama"))setLayer("gm_panama",false);
 await _tourGo(i,auto,jump);
 if(st&&st.gm&&TOUR.on&&!S.active.includes("gm_panama")){const on=()=>{if(TOUR.on&&TOUR.i===i)setLayer("gm_panama",true)};map.isMoving()?map.once("moveend",on):on()}};
window.V8P=V8P;
