(function () {
  "use strict";
  var DATA_URL = "/assets/benchmarks/qwen38-4090/results.json";
  var REPO = "https://github.com/zedong-peng/qwen38-4090-inference";
  var DECODING = [["Autoregressive", "No drafting"], ["MTP", "MTP"], ["DFlash2", "DFlash2"]];
  var NS = "http://www.w3.org/2000/svg";

  function $(id) { return document.getElementById(id); }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function sv(tag, attrs, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function fmt(v, d) { return v == null ? "–" : Number(v).toLocaleString("en-US", { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function mins(s) { return s == null ? "–" : (s / 60).toFixed(1); }
  function drafting(m) { return m.decoding === "Autoregressive" ? "no drafting" : m.decoding + (m.draft ? " " + m.draft : ""); }
  function uniq(a) { return a.filter(function (v, i) { return v && a.indexOf(v) === i; }); }

  // round axis: a max and a step that land on clean numbers
  function scale(v) {
    var p = Math.pow(10, Math.floor(Math.log10(v)));
    var steps = [0.1, 0.2, 0.5, 1, 2, 5, 0.25, 2.5];
    for (var i = 0; i < steps.length; i++) {
      var step = steps[i] * p, n = Math.ceil(v / step - 1e-9);
      if (n >= 3 && n <= 6) return { max: n * step, step: step };
    }
    return { max: Math.ceil(v / p) * p, step: p };
  }

  // theme toggle shared with the blog (localStorage "theme")
  $("theme").addEventListener("click", function () {
    var root = document.documentElement;
    var dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  });

  // one tooltip for every chart
  var tip = $("tip");
  function showTip(evt, r) {
    var rows = [];
    if (r.completion_s != null) {
      rows = [["Completion", mins(r.completion_s) + " min"], ["Generation", fmt(r.output_tps) + " tok/s"], ["Prefill", fmt(r.prefill_tps) + " tok/s"],
        ["First token, median", r.ttft_p50_ms == null ? "–" : (r.ttft_p50_ms / 1000).toFixed(2) + " s"]];
      if (r.energy_wh != null) rows.push(["Energy", fmt(r.energy_wh) + " Wh"]);
      if (r.peak_mem_gb != null) rows.push(["Peak memory", fmt(r.peak_mem_gb, 1) + " GB"]);
      if (r.price_usd != null) rows.push(["System price", "$" + fmt(r.price_usd)]);
    } else rows = [[r.status === "failed" ? (r.reason || "did not run") : "not measured yet", ""]];
    tip.innerHTML = "";
    tip.appendChild(el("div", { class: "t" }, r.title));
    tip.appendChild(el("div", { class: "s" }, r.subtitle));
    rows.forEach(function (x) { var d = el("div", { class: "r" }); d.appendChild(el("span", null, x[0])); d.appendChild(el("b", null, x[1])); tip.appendChild(d); });
    tip.style.display = "block";
    moveTip(evt);
  }
  function moveTip(evt) {
    var x = evt.clientX, y = evt.clientY;
    if (x == null) { var b = evt.target.getBoundingClientRect(); x = b.right; y = b.top; }
    var w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.max(8, Math.min(x + 14, innerWidth - w - 8)) + "px";
    tip.style.top = (y + h + 20 > innerHeight ? y - h - 12 : y + 14) + "px";
  }
  function hideTip() { tip.style.display = "none"; }
  function hover(node, r) {
    node.addEventListener("mouseenter", function (e) { showTip(e, r); });
    node.addEventListener("mousemove", moveTip);
    node.addEventListener("mouseleave", hideTip);
    node.addEventListener("focus", function (e) { showTip(e, r); });
    node.addEventListener("blur", hideTip);
  }

  // engines down, drafting across; shade steps from slowest (1) to fastest (5) on a log scale
  function heat(methods) {
    var box = $("heat"); box.innerHTML = "";
    var t = methods.filter(function (m) { return m.status === "ok"; }).map(function (m) { return Math.log(m.completion_s); });
    var lo = Math.min.apply(null, t), hi = Math.max.apply(null, t);
    function step(s) { return hi - lo < 1e-9 ? 4 : 5 - Math.min(4, Math.floor((Math.log(s) - lo) / (hi - lo) * 5)); }
    var grid = el("div", { class: "heat" });
    grid.appendChild(el("div"));
    DECODING.forEach(function (c) { grid.appendChild(el("div", { class: "colh" }, c[1])); });
    uniq(methods.map(function (m) { return m.engine; })).forEach(function (engine) {
      var row = methods.filter(function (m) { return m.engine === engine; });
      var lab = el("div", { class: "rowh" });
      lab.appendChild(el("b", null, engine));
      lab.appendChild(el("span", null, uniq(row.map(function (m) { return m.weights; })).join(" / ")));
      grid.appendChild(lab);
      DECODING.forEach(function (c) {
        var m = row.filter(function (x) { return x.decoding === c[0]; })[0];
        if (!m) { grid.appendChild(el("div", { class: "cell na" })); return; }
        var cell = el("div", { class: "cell", tabindex: "0" });
        if (m.status === "ok") { cell.className += " s" + step(m.completion_s); cell.textContent = mins(m.completion_s) + " min"; }
        else if (m.status === "failed") { cell.className += " failed"; cell.textContent = "did not run"; }
        else { cell.className += " pending"; cell.textContent = "–"; }
        cell.setAttribute("aria-label", m.title + ": " + (m.status === "ok" ? mins(m.completion_s) + " minutes" : "not measured"));
        hover(cell, m);
        grid.appendChild(cell);
      });
    });
    box.appendChild(grid);
    var key = el("div", { class: "heat-key" }), shades = el("span"), missing = el("span");
    shades.appendChild(document.createTextNode("Faster"));
    [5, 4, 3, 2, 1].forEach(function (s) { shades.appendChild(el("i", { class: "s" + s })); });
    shades.appendChild(document.createTextNode("Slower"));
    missing.appendChild(el("i", { class: "pending" }));
    missing.appendChild(document.createTextNode("not measured yet"));
    key.appendChild(shades); key.appendChild(missing);
    box.appendChild(key);
  }

  function legend(parent) {
    var ul = el("ul", { class: "legend" });
    [["var(--ar)", "measured here"], ["var(--ref)", "measured by Artificial Analysis"]].forEach(function (d) {
      var li = el("li"); li.appendChild(el("span", { class: "key", style: "background:" + d[0] })); li.appendChild(document.createTextNode(d[1])); ul.appendChild(li);
    });
    parent.appendChild(ul);
  }

  function bars(rows, pending) {
    var box = $("bars"); box.innerHTML = "";
    legend(box);
    var grid = el("div", { class: "bars" });
    var sc = scale(Math.max.apply(null, rows.map(function (r) { return r.completion_s / 60; })));
    function label(r) {
      var lab = el("div", { class: "label" });
      lab.appendChild(el("b", null, r.system_label));
      if (r.detail) lab.appendChild(el("span", null, r.detail));
      grid.appendChild(lab);
    }
    rows.forEach(function (r) {
      label(r);
      var track = el("div", { class: "track" });
      var w = (r.completion_s / 60) / sc.max * 100;
      var bar = el("div", { class: "bar", tabindex: "0", style: "width:" + w + "%;background:" + (r.ref ? "var(--ref)" : "var(--ar)"),
        "aria-label": r.system_label + ": " + mins(r.completion_s) + " minutes" });
      track.appendChild(bar); track.appendChild(el("div", { class: "val", style: "left:" + w + "%" }, mins(r.completion_s) + " min"));
      hover(bar, r);
      grid.appendChild(track);
    });
    if (pending) {
      label(pending);
      var track = el("div", { class: "track" });
      track.appendChild(el("div", { class: "val pending", style: "left:0" }, "not measured yet"));
      grid.appendChild(track);
    }
    box.appendChild(grid);
    var axisRow = el("div", { class: "axis-row" }); axisRow.appendChild(el("div"));
    var axis = el("div", { class: "axis" });
    for (var v = 0; v <= sc.max + 1e-9; v += sc.step) axis.appendChild(el("span", { style: "left:" + (v / sc.max * 100) + "%" }, fmt(v) + (v + sc.step > sc.max + 1e-9 ? " min" : "")));
    axisRow.appendChild(axis); box.appendChild(axisRow);
  }

  // direct labels that skip a slot when they would collide with one already placed
  function Labels(left) { this.boxes = []; this.left = left; }
  Labels.prototype.place = function (s, x, y, text, W) {
    var w = text.length * 6.4 + 4, h = 14;
    var tries = [[x + 10, y - 7], [x - 10 - w, y - 7], [x - w / 2, y - 22], [x - w / 2, y + 9]];
    for (var i = 0; i < tries.length; i++) {
      var b = { x: tries[i][0], y: tries[i][1], w: w, h: h };
      if (b.x < this.left || b.x + w > W) continue;
      if (this.boxes.some(function (o) { return b.x < o.x + o.w && o.x < b.x + b.w && b.y < o.y + o.h && o.y < b.y + b.h; })) continue;
      this.boxes.push(b);
      s.appendChild(sv("text", { class: "lbl", x: b.x, y: b.y + 11 }, text));
      return true;
    }
    return false;
  };
  Labels.prototype.block = function (x, y, r) { this.boxes.push({ x: x - r, y: y - r, w: 2 * r, h: 2 * r }); };

  function scatterPrice(rows) {
    var box = $("scatter-price"); box.innerHTML = "";
    var W = Math.max(320, Math.min(900, box.clientWidth || 900)), H = Math.round(Math.max(280, W * 0.4)), m = { l: 52, r: 16, t: 16, b: 46 };
    var sx = scale(Math.max.apply(null, rows.map(function (p) { return p.price_usd; })) * 1.05);
    var sy = scale(Math.max.apply(null, rows.map(function (p) { return p.completion_s / 60; })) * 1.05);
    function X(v) { return m.l + v / sx.max * (W - m.l - m.r); }
    function Y(v) { return H - m.b - v / sy.max * (H - m.t - m.b); }
    var s = sv("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Completion time against system price" });
    for (var v = 0; v <= sx.max + 1e-9; v += sx.step) {
      s.appendChild(sv("line", { class: "gl", x1: X(v), x2: X(v), y1: m.t, y2: H - m.b }));
      s.appendChild(sv("text", { x: X(v), y: H - m.b + 18, "text-anchor": "middle" }, "$" + fmt(v)));
    }
    for (v = 0; v <= sy.max + 1e-9; v += sy.step) {
      s.appendChild(sv("line", { class: "gl", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }));
      s.appendChild(sv("text", { x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, fmt(v)));
    }
    s.appendChild(sv("text", { x: (m.l + W - m.r) / 2, y: H - 8, "text-anchor": "middle" }, "System price, USD"));
    var cy = (m.t + H - m.b) / 2;
    s.appendChild(sv("text", { x: 14, y: cy, "text-anchor": "middle", transform: "rotate(-90 14 " + cy + ")" }, "Completion time, min"));
    var L = new Labels(m.l);
    rows.forEach(function (r) { L.block(X(r.price_usd), Y(r.completion_s / 60), 9); });
    rows.forEach(function (r) {
      var x = X(r.price_usd), y = Y(r.completion_s / 60), g = sv("g", { tabindex: "0" });
      g.appendChild(sv("circle", { class: "hit", cx: x, cy: y, r: 12 }));
      g.appendChild(sv("circle", { class: "pt", cx: x, cy: y, r: 7, fill: r.ref ? "var(--ref)" : "var(--ar)" }));
      hover(g, r); s.appendChild(g);
    });
    rows.forEach(function (r) { L.place(s, X(r.price_usd), Y(r.completion_s / 60), r.system_label, W); });
    box.appendChild(s);
  }

  function render(d) {
    d.methods.forEach(function (m) {
      m.title = m.engine + " · " + drafting(m);
      m.subtitle = [m.weights, m.kv && m.kv + " KV cache", m.note].filter(Boolean).join(" · ");
    });
    heat(d.methods);
    var refs = d.references.map(function (r) {
      return Object.assign({ ref: true, title: r.system, subtitle: r.framework + " · " + r.quant + " · " + r.decodingText, system_label: r.short }, r);
    });
    var hw = d.hardware;
    var best = d.methods.filter(function (m) { return m.status === "ok"; }).sort(function (a, b) { return a.completion_s - b.completion_s; })[0];
    var gpu = best && Object.assign({}, best, { system_label: "RTX 4090", detail: best.engine + " · " + drafting(best), price_usd: hw.msrp_usd + hw.rest_of_system_usd });
    var systems = refs.concat(gpu ? [gpu] : []).sort(function (a, b) { return a.completion_s - b.completion_s; });
    bars(systems, gpu ? null : { system_label: "RTX 4090" });
    function charts() { scatterPrice(systems); }
    charts();
    var lastW = innerWidth, timer;
    addEventListener("resize", function () { if (innerWidth === lastW) return; lastW = innerWidth; clearTimeout(timer); timer = setTimeout(charts, 150); });
    $("footer").innerHTML = "Updated " + d.updated + " · <a href=\"/assets/benchmarks/qwen38-4090/results.json\">results.json</a> · " +
      "<a href=\"/assets/benchmarks/qwen38-4090/samples.json\">per-turn timings</a> · <a href=\"" + REPO + "\">launch commands and code</a>";
  }

  if (window.QWEN38_DATA) render(window.QWEN38_DATA);
  else fetch(DATA_URL).then(function (r) { return r.json(); }).then(render).catch(function (e) { $("heat").textContent = "Could not load results: " + e; });
})();
