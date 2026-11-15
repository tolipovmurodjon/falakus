"use strict";
// Falakus Explorer: NISAR radar + NASA GIBS context layers + EONET events on one timeline.
// Layer identifiers, matrix sets, formats and time ranges were read from the live GIBS
// WMTSCapabilities.xml (epsg3857/best) on 2026-11-15; ranges are the real gaps, not guesses.
const RANGES={"MODIS_Terra_CorrectedReflectance_TrueColor":[["2000-02-24","2000-04-25"],["2000-04-28","2000-08-06"],["2000-08-18","2001-06-15"],["2001-07-03","2002-03-19"],["2002-03-28","2003-12-16"],["2003-12-24","2008-12-20"],["2008-12-23","2016-02-18"],["2016-02-27","2022-10-10"],["2022-10-23","2025-08-08"],["2025-08-10","2025-11-08"],["2025-11-10","2026-11-15"]],"VIIRS_NOAA20_CorrectedReflectance_TrueColor":[["2018-01-05","2018-02-21"],["2018-02-24","2018-03-12"],["2018-03-14","2019-12-31"],["2020-01-02","2022-01-12"],["2022-01-14","2026-11-15"]],"MODIS_Terra_Land_Surface_Temp_Day":[["2000-02-24","2000-04-25"],["2000-04-28","2000-08-06"],["2000-08-18","2001-06-15"],["2001-07-03","2002-03-19"],["2002-03-28","2003-12-16"],["2003-12-24","2008-12-20"],["2008-12-23","2016-02-18"],["2016-02-27","2022-10-10"],["2022-10-23","2026-11-15"]],"IMERG_Precipitation_Rate":[["2000-06-01","2025-10-22"],["2025-10-30","2026-01-07"],["2026-01-09","2026-02-02"],["2026-02-04","2026-02-09"],["2026-02-12","2026-05-24"],["2026-05-27","2026-11-13"]],"IMERG_Precipitation_Rate_30min":[["2026-01-19T20:30:00Z","2026-01-19T21:30:00Z"],["2026-01-20T03:30:00Z","2026-01-20T03:30:00Z"],["2026-01-20T06:30:00Z","2026-01-20T06:30:00Z"],["2026-01-22T09:00:00Z","2026-01-22T09:00:00Z"],["2026-01-22T20:00:00Z","2026-01-22T20:30:00Z"],["2026-01-23T06:00:00Z","2026-01-23T08:30:00Z"],["2026-01-23T12:30:00Z","2026-01-23T12:30:00Z"],["2026-01-23T17:00:00Z","2026-01-23T17:00:00Z"],["2026-01-23T20:00:00Z","2026-01-23T20:30:00Z"],["2026-01-24T06:30:00Z","2026-01-24T06:30:00Z"],["2026-01-24T12:30:00Z","2026-01-24T13:30:00Z"],["2026-01-24T18:00:00Z","2026-01-24T19:00:00Z"],["2026-01-24T20:00:00Z","2026-01-24T20:00:00Z"],["2026-01-24T21:30:00Z","2026-01-24T23:00:00Z"],["2026-01-25T01:00:00Z","2026-01-25T01:00:00Z"],["2026-01-25T02:30:00Z","2026-01-25T02:30:00Z"],["2026-01-25T03:30:00Z","2026-01-25T03:30:00Z"],["2026-01-25T07:30:00Z","2026-01-25T08:30:00Z"],["2026-01-25T19:00:00Z","2026-01-25T19:00:00Z"],["2026-01-25T23:00:00Z","2026-01-25T23:00:00Z"],["2026-01-26T00:00:00Z","2026-01-26T00:00:00Z"],["2026-01-26T02:00:00Z","2026-01-26T02:30:00Z"],["2026-01-26T22:00:00Z","2026-01-26T22:00:00Z"],["2026-01-27T02:00:00Z","2026-01-27T02:00:00Z"],["2026-01-27T03:30:00Z","2026-01-27T03:30:00Z"],["2026-01-27T05:00:00Z","2026-01-27T05:00:00Z"],["2026-01-27T06:30:00Z","2026-01-27T06:30:00Z"],["2026-01-27T08:00:00Z","2026-01-27T08:00:00Z"],["2026-01-27T13:30:00Z","2026-01-27T13:30:00Z"],["2026-01-27T14:30:00Z","2026-01-27T14:30:00Z"],["2026-01-27T18:00:00Z","2026-01-27T18:30:00Z"],["2026-01-27T19:30:00Z","2026-01-27T19:30:00Z"],["2026-01-27T21:00:00Z","2026-01-27T21:30:00Z"],["2026-01-27T22:30:00Z","2026-01-27T22:30:00Z"],["2026-01-28T03:00:00Z","2026-01-28T03:00:00Z"],["2026-01-28T04:00:00Z","2026-01-28T04:00:00Z"],["2026-01-28T05:00:00Z","2026-01-28T05:30:00Z"],["2026-01-28T10:00:00Z","2026-01-28T10:00:00Z"],["2026-01-28T16:00:00Z","2026-01-28T16:00:00Z"],["2026-01-28T17:00:00Z","2026-01-28T17:00:00Z"],["2026-01-28T18:00:00Z","2026-01-28T18:00:00Z"],["2026-01-28T21:00:00Z","2026-01-28T22:00:00Z"],["2026-01-28T23:00:00Z","2026-01-28T23:30:00Z"],["2026-01-29T04:00:00Z","2026-01-29T04:00:00Z"],["2026-01-29T11:00:00Z","2026-01-29T11:00:00Z"],["2026-01-29T16:00:00Z","2026-01-29T16:30:00Z"],["2026-01-30T00:00:00Z","2026-01-30T00:30:00Z"],["2026-01-30T06:00:00Z","2026-01-30T06:00:00Z"],["2026-01-30T07:30:00Z","2026-01-30T08:00:00Z"],["2026-01-30T11:30:00Z","2026-01-30T11:30:00Z"],["2026-01-30T12:30:00Z","2026-01-30T12:30:00Z"],["2026-01-30T18:00:00Z","2026-01-30T21:30:00Z"],["2026-01-31T02:00:00Z","2026-01-31T02:00:00Z"],["2026-01-31T09:30:00Z","2026-01-31T10:00:00Z"],["2026-01-31T20:30:00Z","2026-01-31T20:30:00Z"],["2026-01-31T22:30:00Z","2026-01-31T22:30:00Z"],["2026-02-01T01:30:00Z","2026-02-01T01:30:00Z"],["2026-02-01T02:30:00Z","2026-02-01T02:30:00Z"],["2026-02-01T12:00:00Z","2026-02-01T12:30:00Z"],["2026-02-01T22:30:00Z","2026-02-01T22:30:00Z"],["2026-02-02T06:00:00Z","2026-02-02T06:30:00Z"],["2026-02-03T08:30:00Z","2026-02-03T08:30:00Z"],["2026-02-03T09:30:00Z","2026-02-03T09:30:00Z"],["2026-02-03T10:30:00Z","2026-02-03T10:30:00Z"],["2026-02-03T14:00:00Z","2026-02-03T14:00:00Z"],["2026-02-03T21:00:00Z","2026-02-03T21:30:00Z"],["2026-02-04T04:30:00Z","2026-02-04T05:00:00Z"],["2026-02-04T09:30:00Z","2026-02-04T09:30:00Z"],["2026-02-04T10:30:00Z","2026-02-04T10:30:00Z"],["2026-02-04T21:00:00Z","2026-02-04T22:30:00Z"],["2026-02-05T00:30:00Z","2026-02-05T00:30:00Z"],["2026-02-05T07:30:00Z","2026-02-05T07:30:00Z"],["2026-02-05T08:30:00Z","2026-02-05T08:30:00Z"],["2026-02-05T12:30:00Z","2026-02-05T12:30:00Z"],["2026-02-05T13:30:00Z","2026-02-05T13:30:00Z"],["2026-02-05T17:00:00Z","2026-02-05T17:00:00Z"],["2026-02-05T18:30:00Z","2026-02-05T18:30:00Z"],["2026-02-05T21:30:00Z","2026-02-05T21:30:00Z"],["2026-02-05T23:00:00Z","2026-02-05T23:00:00Z"],["2026-02-06T02:00:00Z","2026-02-06T02:00:00Z"],["2026-02-06T12:00:00Z","2026-02-06T12:00:00Z"],["2026-02-06T13:30:00Z","2026-02-06T13:30:00Z"],["2026-02-06T17:30:00Z","2026-02-06T17:30:00Z"],["2026-02-07T00:00:00Z","2026-02-07T01:30:00Z"],["2026-02-07T11:00:00Z","2026-02-07T11:00:00Z"],["2026-02-07T12:00:00Z","2026-02-07T12:30:00Z"],["2026-02-08T07:00:00Z","2026-02-08T07:30:00Z"],["2026-02-08T16:00:00Z","2026-02-08T16:30:00Z"],["2026-02-08T18:30:00Z","2026-02-08T19:00:00Z"],["2026-02-08T22:00:00Z","2026-02-08T22:30:00Z"],["2026-02-08T23:30:00Z","2026-02-08T23:30:00Z"],["2026-02-09T00:30:00Z","2026-02-09T00:30:00Z"],["2026-02-09T01:30:00Z","2026-02-09T01:30:00Z"],["2026-02-09T04:00:00Z","2026-02-09T04:30:00Z"],["2026-02-09T06:00:00Z","2026-02-09T06:00:00Z"],["2026-02-09T07:00:00Z","2026-02-09T07:00:00Z"],["2026-02-09T08:30:00Z","2026-02-09T08:30:00Z"],["2026-02-09T11:30:00Z","2026-02-09T12:00:00Z"],["2026-02-10T05:00:00Z","2026-02-10T06:30:00Z"],["2026-02-11T09:00:00Z","2026-11-14T21:30:00Z"]],"MODIS_Terra_NDSI_Snow_Cover":[["2000-02-24","2000-08-06"],["2000-08-18","2001-06-15"],["2001-07-03","2002-03-19"],["2002-03-28","2003-12-16"],["2003-12-24","2008-12-20"],["2008-12-23","2016-02-18"],["2016-02-27","2022-10-10"],["2022-10-23","2026-11-15"]],"SMAP_L3_Passive_Enhanced_Day_Soil_Moisture":[["2015-03-31","2015-05-12"],["2015-05-14","2015-12-15"],["2015-12-17","2016-04-30"],["2016-05-02","2016-09-26"],["2016-09-28","2019-06-19"],["2019-07-23","2022-08-06"],["2022-09-21","2022-09-21"],["2022-10-07","2022-11-16"],["2022-11-18","2025-03-17"],["2025-03-19","2026-09-02"],["2026-09-04","2026-09-08"],["2026-09-10","2026-09-19"],["2026-09-21","2026-09-29"],["2026-10-01","2026-10-17"],["2026-10-19","2026-10-25"],["2026-10-27","2026-10-28"],["2026-10-30","2026-11-01"],["2026-11-03","2026-11-12"]],"SMAP_L4_Analyzed_Surface_Soil_Moisture":[["2015-03-31","2025-07-27"],["2025-07-29","2025-10-09"],["2025-12-12","2026-03-16"],["2026-03-18","2026-05-10"],["2026-05-12","2026-05-16"],["2026-05-19","2026-08-09"],["2026-08-16","2026-08-30"],["2026-09-01","2026-11-06"],["2026-11-08","2026-11-10"]],"VIIRS_NOAA20_Thermal_Anomalies_375m_All":[["2020-01-01","2020-03-17"],["2020-03-19","2023-02-24"],["2023-02-26","2023-07-08"],["2023-07-10","2024-03-19"],["2024-03-25","2025-07-06"],["2025-07-08","2025-08-07"],["2025-08-09","2025-09-04"],["2025-09-06","2025-12-21"],["2025-12-23","2026-11-14"]],"MODIS_Combined_Thermal_Anomalies_All":[["2002-07-04","2023-07-08"],["2023-07-10","2025-06-28"],["2025-06-30","2025-08-09"],["2025-08-11","2025-08-26"],["2025-08-28","2025-09-01"],["2025-09-03","2025-09-15"],["2025-09-17","2026-11-14"]]};
const $=id=>document.getElementById(id);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const GIBS="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/";
// GIBS WMS, 256 px PNG tiles with real transparency. Used for (a) fires: the epsg3857 thermal-anomaly WMTS layers
// are vector tiles that answer 404, and (b) coastlines: the WMTS answers tiles with nothing in them with an opaque
// black PNG (921 B palette, no alpha), which painted the big black rectangles over the map (checked 2026-11-15).
const WMS="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS=EPSG:3857&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256&FORMAT=image/png&TRANSPARENT=TRUE";
const LEGEND_SVG="https://gibs.earthdata.nasa.gov/legends/";
// Esri light grey canvas: keyless base map + labels (CARTO now answers "API key required" tiles).
const ESRI="https://server.arcgisonline.com/ArcGIS/rest/services/";
// Local data is addressed relative to this page, so the site still works when it is deployed under a sub-path.
// (tools/export_static.py collects data files by scanning for root paths; the ones this page needs:
//  /explorer/nisar_passes.json /api/events.json /api/science_boxes.json /waterroad/andijan_res.json /ml/water_model.json)
const HERE=location.href.replace(/[?#].*$/,"").replace(/[^/]*$/,"");
const DAY=864e5;
const iso=d=>new Date(d).toISOString().slice(0,10);
const addDays=(s,n)=>iso(Date.parse(s+"T00:00:00Z")+n*DAY);
const TODAY=iso(Date.now());
const MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const fmtD=(d,y=true)=>`${+d.slice(8,10)} ${MON[+d.slice(5,7)-1]}${y?" "+d.slice(0,4):""}`;
const fmtRange=(a,b)=>a.slice(0,7)===b.slice(0,7)?`${+a.slice(8,10)}–${fmtD(b)}`:`${fmtD(a,a.slice(0,4)!==b.slice(0,4))} – ${fmtD(b)}`;
const nf=n=>n.toLocaleString("en-US");

const G=(id,tms,ext)=>(t)=>`${GIBS}${id}/default/${t?t+"/":""}${tms}/{z}/{y}/{x}.${ext}`;
const RAMP_SM=["rgb(255,162,0)","rgb(255,212,0)","rgb(255,254,0)","rgb(130,193,0)","rgb(6,130,0)","rgb(0,189,124)","rgb(0,254,255)","rgb(0,142,255)","rgb(0,18,255)","rgb(0,0,190)","rgb(0,0,114)","rgb(34,34,90)"];
const RAMP_RAIN=["rgb(0,118,78)","rgb(3,167,0)","rgb(153,217,0)","rgb(242,230,0)","rgb(255,160,12)","rgb(255,26,26)","rgb(169,0,0)","rgb(57,0,0)"];
const TC_KEYS=[["#E9E6DF","cloud"],["#2E5E2A","plants"],["#B79A6A","dry land"],["#1E3550","water"],["#000","no pass yet"]];
// heatmap colour ramps: transparent -> light -> dark, readable on the light base map
const HEAT={nisar:["rgba(23,81,95,0)","rgba(120,178,190,.55)","#3F8797","#17515F","#082A33"],
 events:["rgba(224,122,46,0)","rgba(246,190,120,.6)","#E07A2E","#B42318","#5E0B07"],
 quakes:["rgba(109,63,214,0)","rgba(200,175,240,.6)","#8E5BD9","#5B2BB8","#24104F"]};

// short: one line, at most 12 words. info: the longer story, behind the (i) button.
const LAYERS=[
 {key:"heat_nisar",group:"heat",kind:"heat",heat:"nisar",title:"Where NISAR looked",short:"Every NISAR radar frame from one 12-day orbit cycle.",
  info:"One point per NISAR GCOV frame in our frame index, at the frame's centre. Darker means more frames overlap. NISAR repeats its orbit every 12 days, so one cycle shows the whole pattern. Zoom in and the heat turns into single frames. Not tied to the timeline date.",
  src:"NASA-ISRO NISAR L2 GCOV frame index (ASF DAAC), tools/explorer_density.py"},
 {key:"heat_events",group:"heat",kind:"heat",heat:"events",title:"Disasters NASA tracked",short:"Wildfires, floods, storms and icebergs logged by NASA EONET.",
  info:"Each NASA EONET event counts once, at its latest reported position. The feed keeps the 200 largest wildfires. Earthquakes have their own heatmap. Not tied to the timeline date.",
  src:"NASA EONET v3"},
 {key:"heat_quakes",group:"heat",kind:"heat",heat:"quakes",title:"Earthquakes",short:"Magnitude 5+ quakes, weighted by magnitude.",
  info:"USGS earthquakes of magnitude 5 or more since NISAR's first science passes. Each step up in magnitude doubles the weight, so an M7 counts four times an M5. Not tied to the timeline date.",
  src:"USGS earthquake catalogue, M5+"},

 {key:"nisar_mosaic",group:"radar",title:"NISAR radar mosaic",gid:"NISAR GCOV browse images",short:"Every NISAR pass side by side. Dark means water.",
  info:"Every NISAR pass laid side by side. Radar sees through cloud and at night: dark is smooth water, bright is rough ground, towns and forest. Recent passes, newest on top. Not tied to the timeline date.",
  src:"NASA-ISRO NISAR L2 GCOV (provisional), ASF DAAC browse images",static:"Not tied to the timeline date.",
  url:()=>HERE+"tiles/{z}/{x}/{y}.webp?v=7",maxz:10,resampling:"nearest",
  legend:{keys:[["#0b0b0b","smooth water"],["#7a7a7a","fields, bare soil"],["#f2f2f2","towns, forest"]]}},
 {key:"nisar_sci",group:"radar",title:"NISAR calibrated radar (20 m)",gid:"NISAR_L2_GCOV_PROVISIONAL_V1 HHHH, HVHV",short:"Calibrated radar inside our study boxes. Zoom past 10.",
  info:"Calibrated backscatter at 10-20 m inside our study boxes. Red = HH, green = HV, blue = HH minus HV. HH -25..+5 dB, HV -30..-5 dB, HH-HV 0..16 dB. Box dates: see the box card.",
  src:"NASA-ISRO NISAR GCOV gamma0, our Lee-filtered science tiles",static:"Visible from zoom 10.",
  url:()=>HERE+"scitiles/raw/{z}/{x}/{y}.webp?v=3",minz:10,maxz:14,resampling:"nearest",
  legend:{keys:[["#101418","water"],["#e8b8d8","towns"],["#3f9a48","crops, forest"],["#3b5fb0","bare soil"]]}},
 {key:"nisar_boxes",group:"radar",title:"NISAR study boxes",kind:"boxes",short:"Where we read full NISAR files. Click a box.",
  info:"Places where we downloaded the full NISAR files and measured them. Click a box for its date and pixel size.",src:"Falakus science boxes"},
 {key:"water_andijan",group:"radar",title:"Andijan reservoir water",kind:"water",short:"Reservoir water area from every NISAR pass. Click it.",
  info:"Water surface of the Andijan reservoir from every NISAR pass, June to November 2026, checked against Sentinel-2 photos. One value per NISAR pass.",
  src:"Falakus water road (NISAR HH threshold) + gradient-boosting water model"},

 {key:"events",group:"events",title:"Natural events",kind:"events",short:"Events near the timeline date. Click one for a briefing.",
  info:"Fires, floods, storms, ice and earthquakes within the date window. Pick types and the window in the Events tab.",src:"NASA EONET v3, USGS earthquakes (M5+)"},
 {key:"tracks",group:"events",title:"Storm tracks",kind:"tracks",short:"The path each tropical storm has taken.",info:"Storm positions reported to NASA EONET by JTWC and NHC, joined in time order.",src:"NASA EONET v3"},

 {key:"fires_viirs",group:"context",title:"Fires (VIIRS 375 m)",gid:"VIIRS_NOAA20_Thermal_Anomalies_375m_All",wms:true,maxz:12,step:"d",short:"Hot spots seen from orbit on the timeline date.",
  info:"Hot spots seen by VIIRS on NOAA-20 in the 24 h of the date, day and night passes. Each red mark is a 375 m pixel burning.",
  src:"NASA FIRMS / LANCE VIIRS, via GIBS WMS",legend:{keys:[["#EE2626","fire pixel, 375 m"]]}},
 {key:"fires_modis",group:"context",title:"Fires (MODIS 1 km)",gid:"MODIS_Combined_Thermal_Anomalies_All",wms:true,maxz:12,step:"d",short:"Coarser fire record, back to the year 2000.",
  info:"MODIS Terra + Aqua hot spots, 1 km pixels: coarser than VIIRS, but the same record back to 2000.",
  src:"NASA FIRMS / LANCE MODIS, via GIBS WMS",legend:{keys:[["#FF7F00","fire pixel, 1 km"]]}},
 {key:"imerg_day",group:"context",title:"Rain, daily (IMERG)",gid:"IMERG_Precipitation_Rate",tms:"GoogleMapsCompatible_Level6",maxz:6,ext:"png",step:"d",short:"Where rain fell on the timeline date.",
  info:"GPM IMERG rain rate for the whole day: the quickest way to see where a storm or flood rain fell.",
  src:"NASA GPM IMERG, via GIBS",legend:{stops:RAMP_RAIN,lo:"0.1",hi:"≥ 53",units:"mm/hr",svg:"GPM_Precipitation_Rate_H.svg"}},
 {key:"imerg_30",group:"context",title:"Rain, every 30 min (IMERG)",gid:"IMERG_Precipitation_Rate_30min",tms:"GoogleMapsCompatible_Level6",maxz:6,ext:"png",step:"h",short:"Rain rate every half hour. Pick the time beside the date.",
  info:"GPM IMERG rain and snowfall rate, every 30 minutes. Pick the hour with the clock next to the date.",
  src:"NASA GPM IMERG Early Run, via GIBS",legend:{stops:RAMP_RAIN,lo:"0.1",hi:"≥ 53",units:"mm/hr",svg:"GPM_Precipitation_Rate_H.svg"}},
 {key:"smap_l4",group:"context",title:"Soil moisture (SMAP L4)",gid:"SMAP_L4_Analyzed_Surface_Soil_Moisture",tms:"GoogleMapsCompatible_Level6",maxz:6,ext:"png",step:"d",short:"How wet the top 5 cm of soil is.",
  info:"How wet the top 5 cm of soil is, daily at 12z, SMAP L-band radiometer merged with a land model. Same L-band as NISAR.",
  src:"NASA SMAP L4, via GIBS",legend:{stops:RAMP_SM,lo:"0.00",hi:"≥ 0.70",units:"m³/m³",svg:"SMAP_Analyzed_Soil_Moisture_H.svg"}},
 {key:"smap_l3",group:"context",title:"Soil moisture, radiometer only (SMAP L3)",gid:"SMAP_L3_Passive_Enhanced_Day_Soil_Moisture",tms:"GoogleMapsCompatible_Level6",maxz:6,ext:"png",step:"d",short:"Morning-pass soil moisture; gaps between swaths are real.",
  info:"Daily SMAP 9 km soil moisture from the morning pass only: gaps between swaths are real, not missing tiles.",
  src:"NASA SMAP L3 enhanced, via GIBS",legend:{stops:RAMP_SM,lo:"0.00",hi:"≥ 0.60",units:"cm³/cm³",svg:"SMAP_Soil_Moisture_H.svg"}},
 {key:"snow_modis",group:"context",title:"Snow cover (MODIS)",gid:"MODIS_Terra_NDSI_Snow_Cover",tms:"GoogleMapsCompatible_Level8",maxz:8,ext:"png",step:"d",short:"Share of the ground under snow. Gaps are cloud.",
  info:"Share of each 500 m pixel under snow, from the Normalized Difference Snow Index. Cloud is masked, so gaps are cloud.",
  src:"NASA MODIS Terra MOD10A1, via GIBS",legend:{stops:["rgb(240,240,128)","rgb(240,210,132)","rgb(240,180,136)","rgb(240,150,140)","rgb(240,128,128)","rgb(255,0,0)"],lo:"1",hi:"100",units:"NDSI snow cover",svg:"MODIS_NDSI_Snow_Cover_H.svg"}},
 {key:"lst_modis",group:"context",title:"Ground temperature, day (MODIS)",gid:"MODIS_Terra_Land_Surface_Temp_Day",tms:"GoogleMapsCompatible_Level7",maxz:7,ext:"png",step:"d",short:"Daytime ground temperature. Watered fields run cooler.",
  info:"Daytime skin temperature of the ground, 1 km. Irrigated fields run cooler than the desert around them.",
  src:"NASA MODIS Terra MOD11A1, via GIBS",legend:{stops:["rgb(201,0,255)","rgb(33,0,255)","rgb(0,179,255)","rgb(26,255,196)","rgb(179,255,0)","rgb(255,253,0)","rgb(255,124,0)","rgb(255,1,0)"],lo:"< 200 K",hi:"≥ 350 K",units:"kelvin",svg:"MODIS_Land_Surface_Temp_H.svg"}},
 {key:"tc_modis",group:"context",title:"Photo from orbit (MODIS)",gid:"MODIS_Terra_CorrectedReflectance_TrueColor",tms:"GoogleMapsCompatible_Level9",maxz:9,ext:"jpeg",step:"d",short:"The planet as a camera saw it that morning.",
  info:"MODIS Terra true colour, 250 m. Clouds hide the ground here; radar does not. Black wedges are gaps between satellite passes.",
  src:"NASA MODIS Terra corrected reflectance, via GIBS",legend:{keys:TC_KEYS}},
 {key:"tc_viirs",group:"context",title:"Photo from orbit (VIIRS)",gid:"VIIRS_NOAA20_CorrectedReflectance_TrueColor",tms:"GoogleMapsCompatible_Level9",maxz:9,ext:"jpeg",step:"d",short:"Afternoon photo with wider swaths, fewer gaps.",
  info:"Afternoon true colour from VIIRS on NOAA-20, wider swaths than MODIS, so fewer gaps near the equator. Black wedges are gaps between passes.",
  src:"NASA VIIRS NOAA-20 corrected reflectance, via GIBS",legend:{keys:TC_KEYS}},

 {key:"labels",group:"base",pos:"top",title:"Place names and borders",short:"Country and city names, borders.",info:"Esri light grey reference layer. (The GIBS label layer returns empty tiles today, so it was replaced.)",
  src:"Esri, HERE, Garmin, © OpenStreetMap contributors",static:"Static reference.",url:()=>ESRI+"Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}",maxz:16},
 {key:"ref_coast",group:"base",pos:"top",title:"Coastlines",gid:"Coastlines_15m",wms:true,maxz:13,short:"Thin coastline outline.",info:"Coastline and lake shore outline from OpenStreetMap, drawn by GIBS.",src:"OpenStreetMap, via GIBS WMS",static:"Static reference."},
 {key:"base_light",group:"base",pos:"bottom",title:"Light grey map",short:"Calm grey base map so the data stands out.",info:"Esri World Light Gray Canvas: land, water and borders only.",src:"Esri, HERE, Garmin, © OpenStreetMap contributors",static:"Static base map.",url:()=>ESRI+"Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",maxz:16},
 {key:"bluemarble",group:"base",pos:"bottom",title:"Blue Marble relief",gid:"BlueMarble_ShadedRelief_Bathymetry",tms:"GoogleMapsCompatible_Level8",maxz:8,ext:"jpeg",short:"Cloud-free shaded relief and sea floor.",
  info:"NASA Blue Marble: cloud-free shaded relief and sea floor, a calm base under the daily layers.",src:"NASA Blue Marble, via GIBS",static:"Static base map."}
];
const LK=Object.fromEntries(LAYERS.map(l=>[l.key,l]));
const GROUPS=[["heat","Heatmaps",true],["radar","NISAR radar",true],["events","Events",true],["context","Fire, rain, soil, snow",false],["base","Base map",false]];
const CAT={
 "Wildfires":{c:"#D9481E",k:"fire",on:true,say:"Wildfire",g:[["f","M12 3c1.2 3.4 5 5.2 5 10a5 5 0 0 1-10 0c0-2.4 1.3-3.9 2.5-5 0 2 .8 3.3 2 3.6C11.8 9 11 6.4 12 3z"]]},
 "Floods":{c:"#2563EB",k:"flood",on:true,say:"Flood",g:[["s","M3 15c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0M3 19.5c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0"],["f","M12 2.5l3.6 5.4a4.2 4.2 0 1 1-7.2 0z"]]},
 "Severe Storms":{c:"#6D3FD6",k:"storm",on:true,say:"Severe storm",g:[["s","M12 12m-2.6 0a2.6 2.6 0 1 0 5.2 0a2.6 2.6 0 1 0-5.2 0M5 10a7.5 7.5 0 0 1 11-5.5M19 14a7.5 7.5 0 0 1-11 5.5"]]},
 "Volcanoes":{c:"#A1460B",k:"volcano",on:true,say:"Volcano",g:[["f","M3 21l6-10h6l6 10z"],["s","M12 8V3.5M8.5 6.5L7 4M15.5 6.5L17 4"]]},
 "Sea and Lake Ice":{c:"#0E8FC4",k:"ice",on:true,say:"Iceberg or sea ice",g:[["s","M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5L12 7l2.5-2.5M9.5 19.5L12 17l2.5 2.5"]]},
 "Dust and Haze":{c:"#9A6A14",k:"dust",on:true,say:"Dust or haze",g:[["s","M3 8.5h11a2.5 2.5 0 1 0-2.5-2.5M3 12.5h16M3 16.5h10a2.5 2.5 0 1 1-2.5 2.5"]]},
 "Earthquakes":{c:"#9F1D1D",k:"quake",on:false,say:"Earthquake",g:[["s","M2.5 12h4l2.2-6 3.6 12 2.4-8 1.8 2h5"]]},
 "Landslides":{c:"#7A5230",k:"slide",on:true,say:"Landslide",g:[["s","M3 20h18M5 20l7-11 4 5 3-2"]]},
 "Drought":{c:"#B88A0C",k:"drought",on:true,say:"Drought",g:[["s","M12 12m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5"]]},
 "Snow":{c:"#5B6B7E",k:"snow",on:true,say:"Heavy snow",g:[["s","M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9"]]}
};
const catOf=c=>CAT[c]||{c:"#6B7280",k:"dot",on:true,say:c,g:[["f","M12 12m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0"]]};
const glyphSVG=c=>`<svg viewBox="0 0 24 24" aria-hidden="true">${catOf(c).g.map(([m,d])=>m==="f"?`<path d="${d}" fill="currentColor" stroke="none"/>`:`<path d="${d}"/>`).join("")}</svg>`;

// ---------- state + URL hash ----------
const S={date:addDays(TODAY,-1),hhmm:"12:00",step:"d",active:["labels","nisar_mosaic","heat_events","events","tracks","base_light"],op:{},cmp:false,dateB:null,win:7,cats:null,view:null,swipe:.5};
function readHash(){const h=new URLSearchParams(location.hash.slice(1));
 if(h.get("d")&&/^\d{4}-\d\d-\d\d$/.test(h.get("d")))S.date=h.get("d");
 if(/^\d\d:\d\d$/.test(h.get("t")||""))S.hhmm=h.get("t");
 if(h.get("s")==="h")S.step="h";
 if(h.has("l")){S.active=[];h.get("l").split(",").forEach(p=>{const [k,o]=p.split("~");if(LK[k]&&!S.active.includes(k)){S.active.push(k);if(o)S.op[k]=Math.max(0,Math.min(1,+o/100))}})}
 if(h.get("b")&&/^\d{4}-\d\d-\d\d$/.test(h.get("b"))){S.cmp=true;S.dateB=h.get("b")}
 if(h.get("w"))S.win=+h.get("w")||7;
 if(h.has("ev"))S.cats=new Set(h.get("ev").split(",").filter(Boolean));
 if(h.get("m")){const [z,la,lo]=h.get("m").split("/").map(Number);if([z,la,lo].every(isFinite))S.view={zoom:z,center:[lo,la]}}}
let hashT=0;
function writeHash(){clearTimeout(hashT);hashT=setTimeout(()=>{const c=map.getCenter();
 const p=[`m=${map.getZoom().toFixed(2)}/${c.lat.toFixed(4)}/${c.lng.toFixed(4)}`,`d=${S.date}`,`l=${S.active.map(k=>S.op[k]!=null&&S.op[k]!==1?k+"~"+Math.round(S.op[k]*100):k).join(",")}`];
 if(S.active.includes("imerg_30"))p.push(`t=${S.hhmm}`);if(S.step==="h")p.push("s=h");
 if(S.cmp&&S.dateB)p.push(`b=${S.dateB}`);if(S.win!==7)p.push(`w=${S.win}`);
 if(S.cats)p.push(`ev=${[...S.cats].join(",")}`);
 history.replaceState(null,"","#"+p.join("&"))},250)}
readHash();
if(!S.cats)S.cats=new Set(Object.keys(CAT).filter(c=>CAT[c].on));

// ---------- time availability (snap to the nearest earlier real granule, like Worldview) ----------
function rangesOf(l){return RANGES[l.gid]||null}
function snap(l,date,hhmm){const R=rangesOf(l);if(!R||!l.step)return null;
 if(l.step==="h"){const t=Date.parse(`${date}T${hhmm}:00Z`);let best=null;
  for(const [a,b] of R){const ta=Date.parse(a),tb=Date.parse(b);if(t>=ta&&t<=tb){const k=Math.floor((t-ta)/18e5);return new Date(ta+k*18e5).toISOString().replace(".000","")}
   if(tb<t)best=b}
  return best||R[0][0]}
 let best=null;for(const [a,b] of R){if(date>=a&&date<=b)return date;if(b<date)best=b}
 return best||R[0][0]}
function hasData(l,date){const R=rangesOf(l);if(!R)return true;return R.some(([a,b])=>date>=a.slice(0,10)&&date<=b.slice(0,10))}
function tileURL(l,date,hhmm){if(l.url)return l.url();const t=l.step?snap(l,date,hhmm):null;
 if(l.wms)return `${WMS}&LAYERS=${l.gid}${t?"&TIME="+t:""}`;
 return G(l.gid,l.tms,l.ext)(t)}

// ---------- map ----------
const isRaster=k=>!LK[k].kind;
const baseStyle={version:8,sources:{},layers:[{id:"bg",type:"background",paint:{"background-color":"#EFEAE0"}},{id:"anchor",type:"background",paint:{"background-opacity":0}}]};
const narrow=()=>innerWidth<=760;
const map=new maplibregl.Map({container:"map",style:baseStyle,center:S.view?.center||[66,38],zoom:S.view?.zoom??(narrow()?2.3:3.3),maxZoom:16,attributionControl:{compact:true},dragRotate:false,pitchWithRotate:false});
map.touchZoomRotate.disableRotation();
map.addControl(new maplibregl.NavigationControl({showCompass:false}),"top-right");
map.addControl(new maplibregl.ScaleControl({unit:"metric"}),"bottom-right");
let mapB=null;

function makeIcons(m){const sz=44;for(const [name,cat] of [...Object.entries(CAT),["dot",catOf("x")]]){
 const cv=document.createElement("canvas");cv.width=cv.height=sz;const x=cv.getContext("2d");
 x.beginPath();x.arc(sz/2,sz/2,sz/2-2,0,7);x.fillStyle=cat.c;x.fill();x.lineWidth=3;x.strokeStyle="#fff";x.stroke();
 x.save();x.translate(sz*.2,sz*.2);x.scale(sz*.6/24,sz*.6/24);x.strokeStyle="#fff";x.fillStyle="#fff";x.lineWidth=2.4;x.lineCap="round";x.lineJoin="round";
 for(const [mode,d] of cat.g){const p=new Path2D(d);mode==="f"?x.fill(p):x.stroke(p)}x.restore();
 const id="ev-"+(cat.k||"dot");if(!m.hasImage(id))m.addImage(id,x.getImageData(0,0,sz,sz),{pixelRatio:2})}}

// Heatmap that fades into single points as you zoom in (heat gone by zoom `z`, points from z-2).
function addHeat(m,id,ramp,o){const empty={type:"FeatureCollection",features:[]};m.addSource(id,{type:"geojson",data:empty});
 m.addLayer({id:id+"-heat",type:"heatmap",source:id,maxzoom:o.z+0.01,paint:{
  "heatmap-weight":o.weight||1,
  "heatmap-intensity":["interpolate",["linear"],["zoom"],0,o.i[0],o.z,o.i[1]],
  "heatmap-radius":["interpolate",["linear"],["zoom"],0,o.r[0],o.z,o.r[1]],
  "heatmap-color":["interpolate",["linear"],["heatmap-density"],0,ramp[0],0.12,ramp[1],0.4,ramp[2],0.7,ramp[3],1,ramp[4]],
  "heatmap-opacity":["interpolate",["linear"],["zoom"],o.z-2,o.op||0.9,o.z,0]}});
 m.addLayer({id:id+"-pt",type:"circle",source:id,minzoom:o.z-2,paint:{
  "circle-radius":o.pr||4,"circle-color":ramp[3],"circle-stroke-color":"#fff","circle-stroke-width":1,
  "circle-opacity":["interpolate",["linear"],["zoom"],o.z-2,0,o.z-1,0.85],"circle-stroke-opacity":["interpolate",["linear"],["zoom"],o.z-2,0,o.z-1,1]}})}
function addOverlays(m){makeIcons(m);
 addHeat(m,"hn",HEAT.nisar,{z:7,i:[0.1,0.8],r:[9,40],pr:3.5,op:0.82});
 addHeat(m,"he",HEAT.events,{z:6,i:[0.9,2],r:[9,30],pr:5});
 addHeat(m,"hq",HEAT.quakes,{z:6,i:[0.5,1.5],r:[8,26],weight:["^",2,["-",["min",["get","mag"],8.5],5]],pr:["interpolate",["linear"],["get","mag"],5,3.5,8,11]});
 for(const s of ["boxes","water","evs","trk","sel"])m.addSource(s,{type:"geojson",data:{type:"FeatureCollection",features:[]}});
 m.addLayer({id:"boxes-fill",type:"fill",source:"boxes",paint:{"fill-color":"#17515F","fill-opacity":0.08}});
 m.addLayer({id:"boxes-line",type:"line",source:"boxes",paint:{"line-color":"#17515F","line-width":1.6}});
 m.addLayer({id:"water-fill",type:"fill",source:"water",paint:{"fill-color":"#2F6FD1","fill-opacity":0.10}});
 m.addLayer({id:"water-line",type:"line",source:"water",paint:{"line-color":"#2F6FD1","line-width":2,"line-dasharray":[2,1]}});
 m.addLayer({id:"trk",type:"line",source:"trk",layout:{"line-cap":"round","line-join":"round"},paint:{"line-color":["get","color"],"line-width":2.2,"line-opacity":0.85}});
 m.addLayer({id:"sel",type:"circle",source:"sel",paint:{"circle-radius":17,"circle-color":"rgba(0,0,0,0)","circle-stroke-color":"#14120D","circle-stroke-width":2}});
 m.addLayer({id:"evs",type:"symbol",source:"evs",layout:{"icon-image":["get","icon"],"icon-size":["interpolate",["linear"],["zoom"],1,.62,6,.9,10,1.05],"icon-allow-overlap":true,"symbol-sort-key":["get","rank"]}});}

const OVER={nisar_boxes:["boxes-fill","boxes-line"],water_andijan:["water-fill","water-line"],events:["evs","sel"],tracks:["trk"],heat_nisar:["hn-heat","hn-pt"],heat_events:["he-heat","he-pt"],heat_quakes:["hq-heat","hq-pt"]};
function rasterIds(m){return m.getStyle().layers.filter(l=>l.type==="raster").map(l=>l.id)}
function overlayVis(m){for(const [k,ids] of Object.entries(OVER))ids.forEach(id=>m.getLayer(id)&&m.setLayoutProperty(id,"visibility",S.active.includes(k)?"visible":"none"))}
// Sync one map's rasters to the active list: add, remove, retime, restyle, reorder.
function syncRasters(m,date){if(!m||!m.getSource("evs"))return;
 const want=S.active.filter(isRaster);
 for(const id of rasterIds(m))if(!want.includes(id)){m.removeLayer(id);m.removeSource(id)}
 for(const k of want){const l=LK[k],u=tileURL(l,date,S.hhmm);
  if(!m.getSource(k)){m.addSource(k,{type:"raster",tiles:[u],tileSize:256,maxzoom:l.maxz||9,minzoom:l.minz||0,attribution:l.src});
   m.addLayer({id:k,type:"raster",source:k,minzoom:l.minz||0,paint:{"raster-fade-duration":120,"raster-resampling":l.resampling||"linear"}},"anchor")}
  else{const s=m.getSource(k);if(s.tiles&&s.tiles[0]!==u)s.setTiles([u])}
  m.setPaintProperty(k,"raster-opacity",S.op[k]??1)}
 [...want].reverse().forEach(k=>m.moveLayer(k,"anchor"));
 overlayVis(m)}
function syncAll(){syncRasters(map,S.date);if(mapB)syncRasters(mapB,S.dateB);renderPanelState();renderMapLegend();drawStrip();writeHash();
 if(EV)renderEvents()}

// ---------- panel ----------
function legendHTML(l){const g=l.legend;if(!g)return "";
 if(g.stops)return `<div class="leg"><div class="bar" style="background:linear-gradient(90deg,${g.stops.join(",")})"></div><div class="lab mono"><span>${esc(g.lo)}</span><span>${esc(g.units)}</span><span>${esc(g.hi)}</span></div></div>`;
 return `<div class="leg"><div class="keys">${g.keys.map(([c,t])=>`<span><i style="background:${c}"></i>${esc(t)}</span>`).join("")}</div></div>`}
const heatBar=h=>`linear-gradient(90deg,${HEAT[h].slice(1).join(",")})`;
const HEAT_LAB={nisar:["fewer frames","more frames"],events:["fewer events","more events"],quakes:["fewer, smaller","more, stronger"]};
const INFO_SVG='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7.5v.01" stroke-width="2.6"/></svg>';
function buildPanel(){$("groups").innerHTML=GROUPS.map(([g,name,open])=>`<section class="grp${open?" open":""}" data-g="${g}"><button class="gh" aria-expanded="${open}"><svg class="chev" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg><span>${name}</span><span class="cnt mono" data-cnt="${g}"></span></button><div class="gb">${
 LAYERS.filter(l=>l.group===g).map(l=>`<div class="ly${l.kind==="heat"?" heat":""}" data-k="${l.key}"><div class="row"><input type="checkbox" class="sw" id="sw-${l.key}" aria-label="Show ${esc(l.title)}"><label class="t" for="sw-${l.key}"><b>${esc(l.title)}</b><span>${esc(l.short)}</span></label><button class="inf" aria-expanded="false" aria-label="About ${esc(l.title)}" title="About this layer">${INFO_SVG}</button></div>
 <div class="more"><p>${esc(l.info)}</p><div class="src">${esc(l.src)}${l.gid?` · <span class="mono">${esc(l.gid)}</span>`:""}${l.legend?.svg?` · <a href="${LEGEND_SVG}${l.legend.svg}" target="_blank" rel="noopener">NASA legend</a>`:""}</div></div>
 <div class="det">${l.kind==="heat"?`<div class="leg"><div class="bar" style="background:${heatBar(l.heat)}"></div><div class="lab"><span>${HEAT_LAB[l.heat][0]}</span><span>${HEAT_LAB[l.heat][1]}</span></div></div>`:legendHTML(l)}${l.kind?"":`<div class="opr">Opacity<input type="range" min="0" max="100" value="100" data-op="${l.key}" aria-label="Opacity"><span class="mono" data-opv="${l.key}">100%</span></div>`}<div class="state" data-st="${l.key}"></div></div></div>`).join("")}</div></section>`).join("");
 $("groups").querySelectorAll(".gh").forEach(b=>b.onclick=()=>{const s=b.parentElement;s.classList.toggle("open");b.setAttribute("aria-expanded",s.classList.contains("open"))});
 $("groups").querySelectorAll(".inf").forEach(b=>b.onclick=()=>{const ly=b.closest(".ly");ly.classList.toggle("info");b.setAttribute("aria-expanded",ly.classList.contains("info"))});
 $("groups").querySelectorAll(".sw").forEach(c=>c.onchange=()=>setLayer(c.closest(".ly").dataset.k,c.checked));
 $("groups").querySelectorAll("[data-op]").forEach(r=>r.oninput=()=>{const k=r.dataset.op;S.op[k]=r.value/100;$("groups").querySelector(`[data-opv="${k}"]`).textContent=r.value+"%";
  [map,mapB].forEach(m=>m&&m.getLayer(k)&&m.setPaintProperty(k,"raster-opacity",S.op[k]));writeHash()})}
// New imagery goes on top of other imagery, under place names and coastlines; base maps stay at the bottom, one at a time.
function addImagery(keys){S.active=S.active.filter(k=>!keys.includes(k));
 for(const k of [...keys].reverse()){const l=LK[k];
  if(l.kind||l.pos==="top")S.active.unshift(k);
  else if(l.pos==="bottom"){S.active=S.active.filter(x=>LK[x].pos!=="bottom");S.active.push(k)}
  else{const at=S.active.findIndex(x=>isRaster(x)&&LK[x].pos!=="top");S.active.splice(at<0?S.active.length:at,0,k)}}}
function setLayer(k,on){const i=S.active.indexOf(k);
 if(on&&i<0)addImagery([k]);
 if(!on&&i>=0)S.active.splice(i,1);
 if(k==="imerg_30"&&on)$("step").value=S.step="h";
 syncAll()}
const HM={};// heatmap one-liners built from the loaded data
function renderPanelState(){const shown=S.active;
 $("nLayers").textContent=shown.length;
 for(const l of LAYERS){const el=$("groups").querySelector(`.ly[data-k="${l.key}"]`);if(!el)continue;const on=shown.includes(l.key);
  el.classList.toggle("on",on);el.querySelector(".sw").checked=on;
  const r=el.querySelector("[data-op]");if(r){r.value=Math.round((S.op[l.key]??1)*100);el.querySelector("[data-opv]").textContent=r.value+"%"}
  const st=el.querySelector(`[data-st]`);
  if(l.kind==="heat")st.textContent=HM[l.key]||"Loading…",st.className="state";
  else if(l.static)st.textContent=l.static,st.className="state";
  else if(l.step){const t=snap(l,S.date,S.hhmm);const exact=l.step==="h"?t&&t.startsWith(S.date):t===S.date;
   st.className="state"+(exact?"":" warn");
   st.innerHTML=exact?`Showing <span class="mono">${l.step==="h"?t.slice(0,16).replace("T"," ")+" UTC":t}</span>`:`No data on <span class="mono">${S.date}</span>; showing <span class="mono">${(t||"").slice(0,16).replace("T"," ")}</span>`}
  else st.textContent=""}
 for(const [g] of GROUPS){const n=LAYERS.filter(l=>l.group===g&&shown.includes(l.key)).length;const c=$("groups").querySelector(`[data-cnt="${g}"]`);if(c)c.textContent=n?n+" on":""}
 const ord=shown.filter(isRaster);
 $("order").innerHTML=ord.map((k,i)=>`<li><span title="${esc(LK[k].title)}">${esc(LK[k].title)}</span><button class="ib" data-up="${k}" ${i===0?"disabled":""} aria-label="Move up" title="Move up"><svg viewBox="0 0 24 24"><path d="M6 15l6-6 6 6"/></svg></button><button class="ib" data-dn="${k}" ${i===ord.length-1?"disabled":""} aria-label="Move down" title="Move down"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></button><button class="ib" data-rm="${k}" aria-label="Hide" title="Hide"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg></button></li>`).join("")||`<li><span>No image layers on.</span></li>`;
 $("order").querySelectorAll("button").forEach(b=>b.onclick=()=>{const k=b.dataset.up||b.dataset.dn||b.dataset.rm;
  if(b.dataset.rm)return setLayer(k,false);
  const ordNow=S.active.filter(isRaster),i=ordNow.indexOf(k),j=b.dataset.up?i-1:i+1;if(j<0||j>=ordNow.length)return;
  [ordNow[i],ordNow[j]]=[ordNow[j],ordNow[i]];S.active=[...S.active.filter(x=>!isRaster(x)),...ordNow];syncAll()});
 $("hhmm").disabled=!shown.includes("imerg_30");}
// On-map key for the heatmaps that are on: what the colour means, and what data it counts.
function renderMapLegend(){const on=LAYERS.filter(l=>l.kind==="heat"&&S.active.includes(l.key));
 $("mapleg").innerHTML=on.map(l=>`<div class="hl"><b>${esc(l.title)}</b><div class="bar" style="background:${heatBar(l.heat)}"></div><div class="lab"><span>${HEAT_LAB[l.heat][0]}</span><span>${HEAT_LAB[l.heat][1]}</span></div><div class="n">${esc(HM[l.key]||"")}</div></div>`).join("");
 $("mapleg").hidden=!on.length}

// ---------- timeline ----------
const T0DEF="2026-06-01";
let T0=T0DEF,TN=TODAY;
const dayIdx=s=>Math.round((Date.parse(s)-Date.parse(T0))/DAY);
function fixRange(){T0=S.date<T0DEF?addDays(S.date,-45):T0DEF;if(S.dateB&&S.dateB<T0)T0=addDays(S.dateB,-15);TN=TODAY;
 $("slider").max=dayIdx(TN);$("slider").value=dayIdx(S.date)}
for(let h=0;h<24;h++)for(const mm of ["00","30"]){const o=document.createElement("option");o.textContent=o.value=String(h).padStart(2,"0")+":"+mm;$("hhmm").appendChild(o)}
function setDate(d){if(!/^\d{4}-\d\d-\d\d$/.test(d))return;if(d>TODAY)d=TODAY;S.date=d;$("date").value=d;$("hhmm").value=S.hhmm;fixRange();$("tagA").textContent=d;syncAll()}
function stepBy(n){if(S.step==="h"){let t=Date.parse(`${S.date}T${S.hhmm}:00Z`)+n*18e5;if(t>Date.now())t=Date.now()-36e5;const z=new Date(t).toISOString();S.hhmm=z.slice(11,16);if(S.hhmm.slice(3)!=="00"&&S.hhmm.slice(3)!=="30")S.hhmm=S.hhmm.slice(0,3)+(+S.hhmm.slice(3)<30?"00":"30");setDate(z.slice(0,10))}
 else setDate(addDays(S.date,n))}
$("prev").onclick=()=>stepBy(-1);$("next").onclick=()=>stepBy(1);
$("date").max=TODAY;$("date").min="2000-02-24";$("dateB").max=TODAY;$("dateB").min="2000-02-24";
$("date").onchange=e=>setDate(e.target.value);
$("hhmm").onchange=e=>{S.hhmm=e.target.value;syncAll()};
$("step").onchange=e=>{S.step=e.target.value;writeHash()};
$("slider").oninput=e=>setDate(addDays(T0,+e.target.value));
let playT=null;
$("play").onclick=()=>{if(playT){clearInterval(playT);playT=null;$("playico").innerHTML='<path d="M8 5l11 7-11 7z"/>';$("play").setAttribute("aria-label","Play");return}
 $("playico").innerHTML='<path d="M8 5v14M16 5v14"/>';$("play").setAttribute("aria-label","Pause");
 playT=setInterval(()=>{const end=S.step==="h"?Date.parse(`${S.date}T${S.hhmm}:00Z`)+18e5>Date.now()-3*36e5:S.date>=TODAY;if(end){$("play").click();return}stepBy(1)},S.step==="h"?700:1100)};
document.addEventListener("keydown",e=>{if(e.target.closest("input,select,textarea"))return;
 if(e.key==="ArrowLeft"){stepBy(-1);e.preventDefault()}else if(e.key==="ArrowRight"){stepBy(1);e.preventDefault()}else if(e.key===" "){$("play").click();e.preventDefault()}});

function drawStrip(){const cv=$("strip"),w=cv.clientWidth,h=cv.clientHeight;if(!w)return;const dpr=devicePixelRatio||1;cv.width=w*dpr;cv.height=h*dpr;
 const x=cv.getContext("2d");x.scale(dpr,dpr);x.clearRect(0,0,w,h);const n=dayIdx(TN)+1,px=w/n;
 x.fillStyle="#EFEAE0";x.fillRect(0,0,w,h);
 // event count per day (filtered categories), small bars along the top
 if(EV){const cnt=new Array(n).fill(0);for(const e of EV){if(!S.cats.has(e.category))continue;const i=dayIdx(e.date);if(i>=0&&i<n)cnt[i]++}
  const mx=Math.max(1,...cnt);x.fillStyle="rgba(194,65,12,.5)";cnt.forEach((c,i)=>{if(c){const bh=Math.max(1.5,c/mx*11);x.fillRect(i*px,12-bh,Math.max(1,px-.5),bh)}})}
 // availability rows for each active timed layer
 const timed=S.active.filter(k=>LK[k].step).slice(0,4);timed.forEach((k,r)=>{const l=LK[k],y=14+r*2.5;x.fillStyle=r%2?"#3F8797":"#17515F";
  for(let i=0;i<n;i++)if(hasData(l,addDays(T0,i)))x.fillRect(i*px,y,Math.max(1,px),1.8)});
 const ni=dayIdx("2026-06-17");if(ni>=0){x.fillStyle="#B54708";x.fillRect(ni*px,0,1.5,h)}
 if(S.cmp&&S.dateB){const bi=dayIdx(S.dateB);x.fillStyle="#14120D";x.fillRect(bi*px-1,0,2,h)}
 const lab=[];for(let i=0;i<n;i++){const d=addDays(T0,i);if(d.endsWith("-01"))lab.push(`<span style="left:${(i/n*100).toFixed(2)}%">${new Date(d).toLocaleString("en",{month:"short",timeZone:"UTC"})}${d.slice(5,7)==="01"?" "+d.slice(0,4):""}</span>`)}
 if(ni>=0)lab.push(`<span class="nis" style="left:${(ni/n*100).toFixed(2)}%">NISAR</span>`);
 $("tlab").innerHTML=lab.join("")}
addEventListener("resize",()=>{drawStrip();placeSwipe()});

// ---------- compare (swipe) ----------
function placeSwipe(){if(!S.cmp)return;const W=$("maps").clientWidth,x=Math.round(W*S.swipe);$("swipe").style.left=x+"px";$("mapB").style.clipPath=`inset(0 0 0 ${x}px)`}
function setCompare(on){S.cmp=on;$("cmp").setAttribute("aria-pressed",on);$("dateB").hidden=!on;$("swipe").hidden=!on;$("mapB").hidden=!on;
 if(on){if(!S.dateB)S.dateB=addDays(S.date,-30);$("dateB").value=S.dateB;$("tagB").textContent=S.dateB;$("tagA").textContent=S.date;
  if(!mapB){mapB=new maplibregl.Map({container:"mapB",style:baseStyle,center:map.getCenter(),zoom:map.getZoom(),interactive:false,attributionControl:false,fadeDuration:0});
   mapB.on("load",()=>{addOverlays(mapB);pushData(mapB);syncRasters(mapB,S.dateB)});}
  placeSwipe();toast("Left: "+S.date+". Right: "+S.dateB+". Drag the handle.")}
 else if(mapB){mapB.remove();mapB=null}
 fixRange();drawStrip();writeHash()}
$("cmp").onclick=()=>setCompare(!S.cmp);
$("dateB").onchange=e=>{S.dateB=e.target.value;$("tagB").textContent=S.dateB;fixRange();syncAll()};
map.on("move",()=>{if(mapB)mapB.jumpTo({center:map.getCenter(),zoom:map.getZoom()})});
(()=>{const k=$("swipe").querySelector(".knob");let drag=false;
 k.addEventListener("pointerdown",e=>{drag=true;k.setPointerCapture(e.pointerId)});
 k.addEventListener("pointermove",e=>{if(!drag)return;const r=$("maps").getBoundingClientRect();S.swipe=Math.min(.97,Math.max(.03,(e.clientX-r.left)/r.width));placeSwipe()});
 k.addEventListener("pointerup",()=>drag=false);
 k.addEventListener("keydown",e=>{if(e.key==="ArrowLeft")S.swipe=Math.max(.03,S.swipe-.03);else if(e.key==="ArrowRight")S.swipe=Math.min(.97,S.swipe+.03);else return;placeSwipe();e.preventDefault()})})();

// ---------- data: events, NISAR frames, boxes, water ----------
let EV=null,BOXES=[],WATER=null,WML=null,FR=null,HFC=null;
const FC=features=>({type:"FeatureCollection",features});
const pt=(lon,lat,props)=>({type:"Feature",geometry:{type:"Point",coordinates:[lon,lat]},properties:props});
const evFC=()=>FC((EV||[]).map((e,i)=>({e,i})).filter(({e})=>evShown(e)).map(({e,i})=>pt(e.lon,e.lat,{i,icon:"ev-"+catOf(e.category).k,rank:-Math.abs(dayIdx(e.date)-dayIdx(S.date))})));
// keep a track continuous across the antimeridian (lon may run past ±180) so it is not drawn across the whole map
const unwrap=t=>{const o=[t[0]];for(let i=1;i<t.length;i++){let x=t[i][0];const p=o[i-1][0];while(x-p>180)x-=360;while(p-x>180)x+=360;o.push([x,t[i][1]])}return o};
const trkFC=()=>FC((EV||[]).filter(e=>e.track&&e.track.length>1&&evShown(e)).map(e=>({type:"Feature",geometry:{type:"LineString",coordinates:unwrap(e.track)},properties:{color:catOf(e.category).c}})));
const rect=([w,s,e,n],p={})=>({type:"Feature",geometry:{type:"Polygon",coordinates:[[[w,s],[e,s],[e,n],[w,n],[w,s]]]},properties:p});
const boxFC=()=>FC(BOXES.map((b,i)=>rect(b.bbox,{i})));
const waterFC=()=>FC(WATER?[rect(WATER.bbox)]:[]);
function evShown(e){if(!S.cats.has(e.category))return false;if(S.win>=9999)return true;const dd=Math.abs(Date.parse(e.date)-Date.parse(S.date))/DAY;
 // ongoing events (not closed) stay visible from their start until today
 if(!e.closed&&e.category!=="Earthquakes"&&e.date<=S.date)return true;return dd<=S.win}
// NISAR frame rows: [day offset, x1,y1 .. x4,y4]; centre = mean of the 4 corners
const frameCentre=r=>{let x=(r[1]+r[3]+r[5]+r[7])/4;if(x>180)x-=360;return [x,(r[2]+r[4]+r[6]+r[8])/4]};
function buildHeat(){const ev=(EV||[]).map((e,i)=>({e,i}));
 HFC={hn:FC(FR?FR.f.map((r,i)=>pt(...frameCentre(r),{i})):[]),
  he:FC(ev.filter(({e})=>e.category!=="Earthquakes").map(({e,i})=>pt(e.lon,e.lat,{i}))),
  hq:FC(ev.filter(({e})=>e.category==="Earthquakes"&&isFinite(e.mag)).map(({e,i})=>pt(e.lon,e.lat,{i,mag:+e.mag})))};
 const span=list=>{const d=list.map(x=>x.e.date).sort();return d.length?fmtRange(d[0],d[d.length-1]):""};
 if(FR)HM.heat_nisar=`${nf(FR.count)} frames · ${fmtRange(FR.first,FR.last)}`;
 const eo=ev.filter(({e})=>e.category!=="Earthquakes"),eq=ev.filter(({e})=>e.category==="Earthquakes");
 if(EV){HM.heat_events=`${nf(eo.length)} events · ${span(eo)}`;HM.heat_quakes=`${nf(eq.length)} quakes, M${Math.min(...eq.map(x=>x.e.mag))}–${Math.max(...eq.map(x=>x.e.mag))} · ${span(eq)}`}}
function pushData(m){if(!m||!m.getSource("evs"))return;m.getSource("evs").setData(evFC());m.getSource("trk").setData(trkFC());m.getSource("boxes").setData(boxFC());m.getSource("water").setData(waterFC());
 if(HFC)for(const k of ["hn","he","hq"])m.getSource(k).setData(HFC[k])}
// Which NISAR frames in the index cover a point: returns their dates, oldest first.
function nisarDates(lon,lat){if(!FR)return null;const out=[];
 for(const r of FR.f){const xs=[r[1],r[3],r[5],r[7]],ys=[r[2],r[4],r[6],r[8]];let x=lon;if(Math.max(...xs)>180&&x<0)x+=360;
  if(x<Math.min(...xs)||x>Math.max(...xs)||lat<Math.min(...ys)||lat>Math.max(...ys))continue;
  let inside=false;for(let i=0,j=3;i<4;j=i++){if((ys[i]>lat)!==(ys[j]>lat)&&x<(xs[j]-xs[i])*(lat-ys[i])/(ys[j]-ys[i])+xs[i])inside=!inside}
  if(inside)out.push(addDays(FR.first,r[0]))}
 return [...new Set(out)].sort()}
const andJoin=a=>a.length<2?a.join(""):a.slice(0,-1).join(", ")+" and "+a[a.length-1];
function nisarLine(lon,lat){const d=nisarDates(lon,lat);if(!d)return "";
 if(!d.length)return `No NISAR frame in our ${fmtRange(FR.first,FR.last)} index covers this spot.`;
 if(d.length>4)return `<b>NISAR imaged this spot</b> ${d.length} times, ${fmtRange(d[0],d[d.length-1])}.`;
 const sameMonth=d.every(x=>x.slice(0,7)===d[0].slice(0,7));
 return `<b>NISAR imaged this spot</b> on ${sameMonth?andJoin(d.map(x=>+x.slice(8,10)))+" "+fmtD(d[0]).split(" ").slice(1).join(" "):andJoin(d.map(x=>fmtD(x,false)))+" "+d[0].slice(0,4)}.`}
async function loadData(){
 const [ev,bx,wr,wm,fr]=await Promise.all(["api/events.json","api/science_boxes.json","waterroad/andijan_res.json","ml/water_model.json","explorer/nisar_passes.json"].map(u=>fetch(HERE+u).then(r=>r.ok?r.json():null).catch(()=>null)));
 // tools/event_coords.py marks a point "unverified" when neither the given nor the swapped lat/lon fits the country in its title
 EV=Array.isArray(ev)?ev.filter(e=>isFinite(e.lon)&&isFinite(e.lat)&&e.coords!=="unverified"&&e.coords!=="unchecked_bad"):[];
 BOXES=Array.isArray(bx)?bx.filter(b=>Array.isArray(b.bbox)):[];WATER=wr&&wr.bbox?wr:null;WML=wm&&wm.series?wm:null;
 FR=fr&&Array.isArray(fr.f)?fr:null;
 if(!FR)HM.heat_nisar="NISAR frame file did not load.";
 if(!Array.isArray(ev)){$("evlist").innerHTML='<p class="empty">The events feed did not answer. Reload to try again.</p>';HM.heat_events=HM.heat_quakes="Events feed did not load."}
 // calibrated science tiles and study boxes exist only where tools/science_pyramid.py was run: hide both rows when there are none
 if(!BOXES.length){for(const k of ["nisar_sci","nisar_boxes"]){$("groups").querySelector(`.ly[data-k="${k}"]`)?.remove();S.active=S.active.filter(x=>x!==k)}syncRasters(map,S.date);if(mapB)syncRasters(mapB,S.dateB)}
 buildHeat();buildCats();pushData(map);pushData(mapB);renderEvents();renderPanelState();renderMapLegend();drawStrip()}
function buildCats(){const n=c=>EV.filter(e=>e.category===c).length;const cats=[...new Set(EV.map(e=>e.category))].sort((a,b)=>n(b)-n(a));
 $("evcats").innerHTML=cats.map(c=>`<button class="chip" data-c="${esc(c)}" aria-pressed="${S.cats.has(c)}"><span class="ic" style="background:${catOf(c).c}">${glyphSVG(c)}</span>${esc(c)} <span class="mono">${n(c)}</span></button>`).join("");
 $("evcats").querySelectorAll(".chip").forEach(b=>b.onclick=()=>{const c=b.dataset.c;S.cats.has(c)?S.cats.delete(c):S.cats.add(c);b.setAttribute("aria-pressed",S.cats.has(c));renderEvents();drawStrip();writeHash()})}
function renderEvents(){pushData(map);pushData(mapB);
 const list=EV.map((e,i)=>({e,i})).filter(({e})=>evShown(e)).sort((a,b)=>Math.abs(Date.parse(a.e.date)-Date.parse(S.date))-Math.abs(Date.parse(b.e.date)-Date.parse(S.date)));
 $("nEvents").textContent=list.length;
 $("evhead").textContent=`${list.length} events ${S.win>=9999?"on all dates":"within ± "+S.win+" day"+(S.win>1?"s":"")+" of "+fmtD(S.date)}`;
 $("evlist").innerHTML=list.slice(0,300).map(({e,i})=>`<button class="ev" data-i="${i}"><span class="ic" style="background:${catOf(e.category).c}">${glyphSVG(e.category)}</span><span><b>${esc(e.title)}</b><small>${fmtD(e.date)} · ${esc(catOf(e.category).say)}${sizeOf(e)}</small></span></button>`).join("")||'<p class="empty">No events in this window. Widen the window or turn on more types.</p>';
 $("evlist").querySelectorAll(".ev").forEach(b=>b.onclick=()=>openEvent(+b.dataset.i,true))}
const sizeOf=e=>e.mag?` · ${e.unit==="M"?"M "+e.mag:e.mag+" "+(e.unit||"")}`:"";
// one context layer per event type, turned on when an event is opened
const EV_LAYERS={"Wildfires":"fires_viirs","Floods":"imerg_day","Severe Storms":"imerg_day","Volcanoes":"fires_viirs","Dust and Haze":"tc_modis","Sea and Lake Ice":"tc_modis","Snow":"snow_modis","Earthquakes":"nisar_mosaic","Drought":"smap_l4","Landslides":"imerg_day"};
const ll=(lat,lon)=>`${Math.abs(lat).toFixed(1)}° ${lat>=0?"N":"S"}, ${Math.abs(lon).toFixed(1)}° ${lon>=0?"E":"W"}`;
function openEvent(i,fly){const e=EV[i];if(!e)return;
 const ctx=EV_LAYERS[e.category];if(ctx&&!S.active.includes(ctx)){addImagery([ctx]);if(S.op[ctx]==null&&ctx!=="nisar_mosaic")S.op[ctx]=0.75}
 if(!S.active.includes("events"))S.active.unshift("events");
 if(S.step==="h"&&!S.active.includes("imerg_30"))S.step=$("step").value="d";
 setDate(e.date);
 if(fly)map.flyTo({center:[e.lon,e.lat],zoom:Math.max(map.getZoom(),e.track&&e.track.length>1?4.5:6.5),speed:1.6});
 map.getSource("sel").setData(FC([pt(e.lon,e.lat,{})]));
 const quake=e.category==="Earthquakes";
 const what=catOf(e.category).say+(quake?`, magnitude ${e.mag}${e.depth_km!=null?`, ${Math.round(e.depth_km)} km deep`:""}`:"");
 const when=quake?`Struck on ${fmtD(e.date)}`:`Last report ${fmtD(e.date)}${e.closed?`, ended ${fmtD(e.closed)}`:", still open"}`;
 const inBox=BOXES.find(b=>e.lon>=b.bbox[0]&&e.lon<=b.bbox[2]&&e.lat>=b.bbox[1]&&e.lat<=b.bbox[3]);
 const src=(e.sources||[]).map(u=>{try{return `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(new URL(u).hostname.replace("www.",""))}</a>`}catch(x){return ""}}).filter(Boolean).join(" · ");
 card(`<h3>${esc(e.title)}</h3>
 <p class="brief"><span class="dot" style="background:${catOf(e.category).c}"></span>${esc(what)} · ${ll(e.lat,e.lon)}<br>${when}<br>${nisarLine(e.lon,e.lat)}</p>
 <details class="more"><summary>More</summary>
 ${e.mag&&!quake?`<p>Size: ${esc(e.mag)} ${esc(e.unit||"")}</p>`:""}${e.track&&e.track.length>1?`<p>Track: ${e.track.length} reported positions.</p>`:""}
 ${ctx?`<p>Turned on: ${esc(LK[ctx].title)}.</p>`:""}
 ${inBox?`<p>Inside our NISAR study box <b>${esc(inBox.stop.replace(/_/g," "))}</b> (${inBox.res} m, ${inBox.date}). Zoom past 10 for calibrated radar.</p>`:""}
 ${e.coords==="swapped_fixed"?`<p>EONET listed this point with latitude and longitude swapped; we swapped it back because only the swapped point lies in the country named in the title.</p>`:""}
 ${src?`<p>Sources: ${src}</p>`:""}</details>
 <div class="acts"><button class="btn ghost" id="c-radar">Show NISAR radar here</button></div>`);
 $("c-radar").onclick=()=>{if(!S.active.includes("nisar_mosaic"))setLayer("nisar_mosaic",true);map.flyTo({center:[e.lon,e.lat],zoom:Math.max(map.getZoom(),8)})};
 if(narrow())$("panel").classList.remove("open")}
function spotCard(lon,lat){card(`<h3>${ll(lat,lon)}</h3><p class="brief">${nisarLine(lon,lat)||"NISAR frame file not loaded."}</p><div class="acts"><button class="btn ghost" id="s-radar">Show NISAR radar here</button></div>`);
 $("s-radar").onclick=()=>{if(!S.active.includes("nisar_mosaic"))setLayer("nisar_mosaic",true);map.flyTo({center:[lon,lat],zoom:Math.max(map.getZoom(),7)})}}

function card(html){$("cardbody").innerHTML=html;$("card").hidden=false}
$("cardx").onclick=()=>{$("card").hidden=true;map.getSource("sel")?.setData(FC([]))};
let toastT=0;function toast(t){$("toast").textContent=t;$("toast").hidden=false;clearTimeout(toastT);toastT=setTimeout(()=>$("toast").hidden=true,3200)}

function waterCard(){if(!WATER)return;const P=WATER.passes.filter(p=>isFinite(p.water_km2));const ML=WML?WML.series:[];
 const all=[...P.map(p=>p.water_km2),...ML.map(p=>p.ml_km2)];const lo=Math.floor(Math.min(...all)/5)*5,hi=Math.ceil(Math.max(...all)/5)*5;
 const t0=Date.parse(P[0].date),t1=Date.parse(P[P.length-1].date);const W=280,H=96,X=t=>8+(Date.parse(t)-t0)/(t1-t0||1)*(W-16),Y=v=>H-14-(v-lo)/(hi-lo||1)*(H-26);
 const line=(arr,f)=>arr.map((p,i)=>(i?"L":"M")+X(p.date).toFixed(1)+","+Y(f(p)).toFixed(1)).join("");
 const near=P.reduce((a,p)=>Math.abs(Date.parse(p.date)-Date.parse(S.date))<Math.abs(Date.parse(a.date)-Date.parse(S.date))?p:a,P[0]);
 const sm=WML?.summary;
 card(`<h3>Andijan reservoir: water area from NISAR</h3><div class="m">${P.length} passes, ${fmtD(P[0].date)} to ${fmtD(P[P.length-1].date)}</div>
 <svg class="spark" viewBox="0 0 ${W} ${H}" role="img" aria-label="Water area over time"><path d="${line(P,p=>p.water_km2)}" stroke="#2F6FD1" stroke-width="2" fill="none"/>${ML.length?`<path d="${line(ML,p=>p.ml_km2)}" stroke="#17515F" stroke-width="1.6" stroke-dasharray="3 2" fill="none"/>`:""}
 ${P.map(p=>`<circle cx="${X(p.date).toFixed(1)}" cy="${Y(p.water_km2).toFixed(1)}" r="${p===near?4:2.2}" fill="${p===near?"#14120D":"#2F6FD1"}"/>`).join("")}
 <text x="4" y="10" font-size="9" fill="#8A8171" font-family="ui-monospace,Consolas,monospace">${hi} km²</text><text x="4" y="${H-3}" font-size="9" fill="#8A8171" font-family="ui-monospace,Consolas,monospace">${lo} km²</text></svg>
 <div class="m"><span style="color:#2F6FD1">solid</span>: HH threshold ${WATER.threshold_db} dB · <span style="color:#17515F">dashed</span>: learned model</div>
 <dl class="kv"><dt>Nearest pass</dt><dd class="mono">${near.date} · ${near.water_km2.toFixed(1)} km²</dd>${sm?`<dt>Model vs photo</dt><dd class="mono">IoU ${sm.ml_iou} (rule ${sm.rule_iou}, chance ${sm.null_iou})</dd><dt>Area error</dt><dd class="mono">${sm.ml_area_mae_km2} km² mean</dd>`:""}</dl>
 <details class="more"><summary>Why water is dark</summary><p>Calm water reflects the L-band pulse away from the satellite. The model is scored only on dates it never trained on, against cloud-free Sentinel-2 photos.</p></details>
 <div class="acts"><button class="btn ghost" id="w-day">Set timeline to nearest pass</button></div>`);
 $("w-day").onclick=()=>setDate(near.date)}

const CLICKABLE=["evs","he-pt","hq-pt","hn-pt","water-fill","boxes-fill"];
const visibleIds=m=>CLICKABLE.filter(id=>m.getLayer(id)&&m.getLayoutProperty(id,"visibility")!=="none");
map.on("click",ev=>{const f=map.queryRenderedFeatures(ev.point,{layers:visibleIds(map)});
 const e=f.find(x=>["evs","he-pt","hq-pt"].includes(x.layer.id));if(e)return openEvent(e.properties.i,false);
 if(f.find(x=>x.layer.id==="water-fill"))return waterCard();
 const b=f.find(x=>x.layer.id==="boxes-fill");if(b){const B=BOXES[b.properties.i];
  card(`<h3>NISAR study box: ${esc(B.stop.replace(/_/g," "))}</h3><div class="m">Full NISAR file read and calibrated</div><dl class="kv"><dt>Pass date</dt><dd class="mono">${B.date}</dd><dt>Pixel</dt><dd class="mono">${B.res} m</dd></dl><div class="acts"><button class="btn" id="b-zoom">Zoom to calibrated radar</button></div>`);
  $("b-zoom").onclick=()=>{if(!S.active.includes("nisar_sci"))setLayer("nisar_sci",true);map.fitBounds([[B.bbox[0],B.bbox[1]],[B.bbox[2],B.bbox[3]]],{padding:40,maxZoom:12.5})};return}
 spotCard(ev.lngLat.wrap().lng,ev.lngLat.lat)});
map.on("mousemove",ev=>{const ids=visibleIds(map);map.getCanvas().style.cursor=ids.length&&map.queryRenderedFeatures(ev.point,{layers:ids}).length?"pointer":""});
map.on("moveend",writeHash);

// ---------- search ----------
let qT=0,qAbort=null;
function placeHits(q){const s=q.toLowerCase();const out=[];
 BOXES.forEach(b=>{if(b.stop.toLowerCase().includes(s))out.push({name:"NISAR box: "+b.stop.replace(/_/g," "),sub:b.date+" · "+b.res+" m",bbox:b.bbox})});
 if(WATER&&"andijan reservoir".includes(s))out.push({name:"Andijan reservoir water series",sub:"NISAR, "+WATER.passes.length+" passes",bbox:WATER.bbox,water:true});
 (EV||[]).forEach((e,i)=>{if(out.length<8&&e.title.toLowerCase().includes(s))out.push({name:e.title,sub:e.date+" · "+e.category,ev:i})});
 return out.slice(0,8)}
function showHits(h){const r=$("qres");if(!h.length){r.hidden=true;return}
 r.innerHTML=h.map((x,i)=>`<button data-i="${i}">${esc(x.name)}<small>${esc(x.sub||"")}</small></button>`).join("");r.hidden=false;
 r.querySelectorAll("button").forEach(b=>b.onclick=()=>{const x=h[+b.dataset.i];r.hidden=true;$("q").blur();
  if(x.ev!=null)return openEvent(x.ev,true);
  if(x.bbox)map.fitBounds([[x.bbox[0],x.bbox[1]],[x.bbox[2],x.bbox[3]]],{padding:40,maxZoom:12});else map.flyTo({center:[x.lon,x.lat],zoom:x.zoom||8});
  if(x.water){if(!S.active.includes("water_andijan"))setLayer("water_andijan",true);waterCard()}})}
$("q").addEventListener("input",()=>{const q=$("q").value.trim();clearTimeout(qT);if(q.length<2){$("qres").hidden=true;return}
 const m=q.match(/^(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)$/);
 if(m){const la=+m[1],lo=+m[2];if(Math.abs(la)<=90&&Math.abs(lo)<=180)return showHits([{name:`Go to ${la}, ${lo}`,sub:"latitude, longitude",lat:la,lon:lo,zoom:9}])}
 const local=placeHits(q);showHits(local);
 qT=setTimeout(async()=>{try{qAbort?.abort();qAbort=new AbortController();
  const r=await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&q=${encodeURIComponent(q)}`,{signal:qAbort.signal,headers:{"Accept-Language":"en"}});
  const js=await r.json();if($("q").value.trim()!==q)return;
  showHits([...local,...js.map(p=>({name:p.name||p.display_name.split(",")[0],sub:p.display_name,bbox:p.boundingbox?[+p.boundingbox[2],+p.boundingbox[0],+p.boundingbox[3],+p.boundingbox[1]]:null,lat:+p.lat,lon:+p.lon}))].slice(0,10))}catch(e){}},450)});
$("q").addEventListener("keydown",e=>{if(e.key==="Enter"){const b=$("qres").querySelector("button");b&&b.click()}if(e.key==="Escape"){$("qres").hidden=true}});
document.addEventListener("click",e=>{if(!e.target.closest(".search"))$("qres").hidden=true});

// ---------- tabs + mobile sheet ----------
document.querySelectorAll(".tab").forEach(t=>t.onclick=ev=>{ev.stopPropagation();document.querySelectorAll(".tab").forEach(x=>{x.classList.toggle("on",x===t);x.setAttribute("aria-selected",x===t)});
 $("tab-layers").hidden=t.dataset.tab!=="layers";$("tab-events").hidden=t.dataset.tab!=="events";$("panel").classList.add("open")});
$("ph").addEventListener("click",e=>{if(narrow()&&!e.target.closest(".tab"))$("panel").classList.toggle("open")});
$("evwin").value=String(S.win);$("evwin").onchange=e=>{S.win=+e.target.value;renderEvents();writeHash()};

// ---------- boot ----------
buildPanel();
$("date").value=S.date;$("hhmm").value=S.hhmm;$("step").value=S.step;fixRange();
map.on("load",()=>{addOverlays(map);syncRasters(map,S.date);renderPanelState();renderMapLegend();loadData();if(S.cmp)setCompare(true);drawStrip()});
map.on("error",e=>{// GIBS answers 400/404 for a tile outside a granule swath; MapLibre reports it here, so keep it quiet
 if(e&&e.sourceId&&e.error&&/40[04]|50\d|Failed to fetch/.test(String(e.error.status||e.error.message)))return;console.warn(e&&e.error)});
