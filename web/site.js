/* Falakus shared header. Include with <script src="site.js"></script> as the FIRST element in <body>.
   Inside the one-site shell (index.html loads a page in an iframe with ?embed=1) the page hides its own header:
   <html> gets class "embed", which site.css uses. Standalone, every page shows the same header and tabs. */
(function () {
  if (!document.querySelector("link[rel~=icon]")) {
    var fav = document.createElement("link"); fav.rel = "icon";
    fav.href = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 26 26"><circle cx="13" cy="13" r="12" fill="#17515F"/><path d="M4 15.5c3-3 6-3 9 0s6 3 9 0" stroke="#F6F3ED" stroke-width="2" fill="none"/><path d="M4 10.5c3-3 6-3 9 0s6 3 9 0" stroke="#9CC3CC" stroke-width="2" fill="none"/></svg>');
    document.head.appendChild(fav);
  }
  var embed = /[?&]embed=1/.test(location.search) || window.top !== window;
  if (embed) { document.documentElement.classList.add("embed"); return; }
  var here = (location.pathname.split("/").pop() || "index.html").replace(".html", "");
  var ic = {
    dash: '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="1.5" y="1.5" width="5.5" height="7" rx="1.2"/><rect x="9" y="1.5" width="5.5" height="4" rx="1.2"/><rect x="9" y="7.5" width="5.5" height="7" rx="1.2"/><rect x="1.5" y="10.5" width="5.5" height="4" rx="1.2"/></svg>',
    time: '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="8" cy="8" r="6.3"/><path d="M6.6 5.4v5.2L10.8 8z" fill="currentColor" stroke="none"/></svg>',
    explore: '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="8" cy="8" r="6.3"/><path d="M1.8 8h12.4M8 1.7c2 2.1 2 10.5 0 12.6M8 1.7c-2 2.1-2 10.5 0 12.6"/></svg>',
    map: '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M1.5 3.5l4.3-1.6 4.4 1.6 4.3-1.6v10.6l-4.3 1.6-4.4-1.6-4.3 1.6z"/><path d="M5.8 1.9v10.6M10.2 3.5v10.6"/></svg>'
  };
  var tabs = [["dashboard", "index.html#dashboard", ic.dash, "Dashboard", ""], ["timelapse", "index.html#timelapse", ic.time, "Time-lapse", ""],
    ["explorer", "index.html#explorer", ic.explore, "Explorer", ""]];
  var on = { index: "dashboard", timelapse: "timelapse", explorer: "explorer", app: "app" }[here] || "";
  var h = document.createElement("header");
  h.className = "fk-hdr";
  h.innerHTML = '<a class="fk-brand" href="index.html#dashboard" aria-label="Falakus home">' +
    '<svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><circle cx="13" cy="13" r="12" fill="#17515F"/><path d="M4 15.5c3-3 6-3 9 0s6 3 9 0" stroke="#F6F3ED" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M4 10.5c3-3 6-3 9 0s6 3 9 0" stroke="#9CC3CC" stroke-width="2" fill="none" stroke-linecap="round"/></svg>' +
    '<span><b>Falakus</b><br><span>Water watch from NISAR radar</span></span></a>' +
    '<nav class="fk-tabs" aria-label="Sections">' + tabs.map(function (t) {
      return '<a data-tab="' + t[0] + '" href="' + t[1] + '"' + (t[0] === on ? ' class="on" aria-current="page"' : "") + ">" + t[2] + "<span>" + t[3] + "</span>" + t[4] + "</a>";
    }).join("") + "</nav>" +
    '<span class="fk-live" title="NASA-ISRO NISAR L-band radar, every 12 days"><i></i>NISAR L-band</span>';
  document.body.insertBefore(h, document.body.firstChild);
})();
