(function () {
  "use strict";
  var DATA_URL = "/assets/benchmarks/qwen38-4090/results.json";
  var COLOR = { Autoregressive: "var(--ar)", MTP: "var(--mtp)", DFlash2: "var(--dflash)" };
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
  function colorOf(r) { return r.ref ? "var(--ref)" : COLOR[r.decoding]; }

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
    var rows = [["Completion", mins(r.completion_s) + " min"], ["Generation", fmt(r.output_tps) + " tok/s"], ["Prefill", fmt(r.prefill_tps) + " tok/s"],
      ["First token, median", r.ttft_p50_ms == null ? "–" : (r.ttft_p50_ms / 1000).toFixed(2) + " s"]];
    if (r.energy_wh != null) rows.push(["Energy", fmt(r.energy_wh) + " Wh"]);
    if (r.price_usd != null) rows.push(["System price", "$" + fmt(r.price_usd)]);
    tip.innerHTML = "";
    tip.appendChild(el("div", { class: "t" }, r.title));
    tip.appendChild(el("div", { style: "color:var(--ink-3);margin-bottom:6px" }, r.subtitle));
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

  function legend(ul) {
    ul.innerHTML = "";
    [["Autoregressive", "no drafting"], ["MTP", "MTP: the model's own draft head"], ["DFlash2", "DFlash2: a separate draft model"]].forEach(function (d) {
      var li = el("li"); li.appendChild(el("span", { class: "key", style: "background:" + COLOR[d[0]] })); li.appendChild(document.createTextNode(d[1])); ul.appendChild(li);
    });
    var li = el("li"); li.appendChild(el("span", { class: "key", style: "background:var(--ref)" })); li.appendChild(document.createTextNode("other systems, measured by Artificial Analysis")); ul.appendChild(li);
  }

  function label(parent, r) {
    var lab = el("div", { class: "label" + (r.ref ? " ref" : "") + (r.status === "pending" ? " pending" : "") });
    lab.appendChild(el("b", null, r.title)); lab.appendChild(el("span", null, r.subtitle));
    parent.appendChild(lab);
  }

  function bars(rows, pending) {
    var box = $("bars"); box.innerHTML = "";
    var grid = el("div", { class: "bars" });
    var sc = rows.length ? scale(Math.max.apply(null, rows.map(function (r) { return r.completion_s / 60; }))) : { max: 40, step: 10 };
    rows.forEach(function (r) {
      label(grid, r);
      var track = el("div", { class: "track" });
      var w = (r.completion_s / 60) / sc.max * 100;
      var bar = el("div", { class: "bar", tabindex: "0", style: "width:" + w + "%;background:" + colorOf(r), "aria-label": r.title + ": " + mins(r.completion_s) + " minutes" });
      track.appendChild(bar); track.appendChild(el("div", { class: "val", style: "left:" + w + "%" }, mins(r.completion_s) + " min"));
      hover(bar, r);
      grid.appendChild(track);
    });
    if (pending.length && rows.length) grid.appendChild(el("div", { class: "divider" }));
    pending.forEach(function (r) {
      label(grid, r);
      var track = el("div", { class: "track" });
      track.appendChild(el("div", { class: "val pending", style: "left:0" }, "not measured yet"));
      grid.appendChild(track);
    });
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

  function axes(s, W, H, m, xt, yt, X, Y, xl, yl, xf, yf) {
    xt.forEach(function (v) { s.appendChild(sv("line", { class: "gl", x1: X(v), x2: X(v), y1: m.t, y2: H - m.b })); s.appendChild(sv("text", { x: X(v), y: H - m.b + 18, "text-anchor": "middle" }, xf(v))); });
    yt.forEach(function (v) { s.appendChild(sv("line", { class: "gl", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) })); s.appendChild(sv("text", { x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, yf(v))); });
    s.appendChild(sv("text", { x: (m.l + W - m.r) / 2, y: H - 8, "text-anchor": "middle" }, xl));
    var cy = (m.t + H - m.b) / 2;
    s.appendChild(sv("text", { x: 14, y: cy, "text-anchor": "middle", transform: "rotate(-90 14 " + cy + ")" }, yl));
  }

  function points(s, rows, X, Y, W, labelled, text, rad, left) {
    var L = new Labels(left);
    rows.forEach(function (r) { L.block(X(r), Y(r), rad + 2); });
    rows.slice().sort(function (a, b) { return (b.ref ? 1 : 0) - (a.ref ? 1 : 0); }).forEach(function (r) {
      var g = sv("g", { tabindex: "0" });
      g.appendChild(sv("circle", { class: "hit", cx: X(r), cy: Y(r), r: 12 }));
      g.appendChild(sv("circle", { class: "pt", cx: X(r), cy: Y(r), r: rad, fill: colorOf(r) }));
      hover(g, r); s.appendChild(g);
    });
    rows.filter(function (r) { return labelled(r); }).forEach(function (r) { L.place(s, X(r), Y(r), text(r), W); });
  }

  // log-log: generation speed against prefill speed
  function scatterSpeeds(rows) {
    var box = $("scatter-speeds"); box.innerHTML = "";
    if (!rows.length) return;
    var W = Math.max(320, Math.min(900, box.clientWidth || 900)), H = Math.round(Math.max(300, W * 0.47)), m = { l: 60, r: 16, t: 16, b: 46 };
    var xv = rows.map(function (r) { return r.output_tps; }), yv = rows.map(function (r) { return r.prefill_tps; });
    var x0 = Math.min.apply(null, xv) * 0.8, x1 = Math.max.apply(null, xv) * 1.25, y0 = Math.min.apply(null, yv) * 0.8, y1 = Math.max.apply(null, yv) * 1.25;
    function lx(v) { return m.l + (Math.log(v) - Math.log(x0)) / (Math.log(x1) - Math.log(x0)) * (W - m.l - m.r); }
    function ly(v) { return H - m.b - (Math.log(v) - Math.log(y0)) / (Math.log(y1) - Math.log(y0)) * (H - m.t - m.b); }
    var s = sv("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Generation speed against prefill speed" });
    var inX = function (v) { return v >= x0 && v <= x1; }, inY = function (v) { return v >= y0 && v <= y1; };
    axes(s, W, H, m, [10, 20, 30, 50, 100, 200, 300, 500].filter(inX), [100, 200, 300, 500, 1000, 2000, 3000, 5000, 10000].filter(inY), lx, ly,
      "Generation, tokens/s (log scale)", "Prefill, tokens/s (log scale)", fmt, fmt);
    var best = rows.filter(function (r) { return !r.ref; }).sort(function (a, b) { return a.completion_s - b.completion_s; }).slice(0, 2);
    points(s, rows, function (r) { return lx(r.output_tps); }, function (r) { return ly(r.prefill_tps); }, W,
      function (r) { return r.ref || best.indexOf(r) >= 0; }, function (r) { return r.short; }, 6, m.l);
    box.appendChild(s);
  }

  function scatterPrice(rows) {
    var box = $("scatter-price"); box.innerHTML = "";
    var W = Math.max(320, Math.min(900, box.clientWidth || 900)), H = Math.round(Math.max(280, W * 0.4)), m = { l: 52, r: 16, t: 16, b: 46 };
    var sx = scale(Math.max.apply(null, rows.map(function (p) { return p.price_usd; })) * 1.05);
    var sy = scale(Math.max.apply(null, rows.map(function (p) { return p.completion_s / 60; })) * 1.05);
    function X(v) { return m.l + v / sx.max * (W - m.l - m.r); }
    function Y(v) { return H - m.b - v / sy.max * (H - m.t - m.b); }
    var s = sv("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Completion time against system price" });
    var xt = [], yt = [];
    for (var v = 0; v <= sx.max + 1e-9; v += sx.step) xt.push(v);
    for (v = 0; v <= sy.max + 1e-9; v += sy.step) yt.push(v);
    axes(s, W, H, m, xt, yt, X, Y, "System price, USD", "Completion time, min", function (v) { return "$" + fmt(v); }, fmt);
    points(s, rows, function (r) { return X(r.price_usd); }, function (r) { return Y(r.completion_s / 60); }, W,
      function () { return true; }, function (r) { return r.price_label; }, 7, m.l);
    box.appendChild(s);
  }

  var COLS = [
    ["Method", function (r) { return r.title; }, false],
    ["Weights", function (r) { return r.weights; }, false],
    ["KV cache", function (r) { return r.kv || ""; }, false],
    ["Completion, min", function (r) { return r.completion_s == null ? null : r.completion_s / 60; }, true, 1],
    ["Generation, tok/s", function (r) { return r.output_tps; }, true, 0],
    ["Prefill, tok/s", function (r) { return r.prefill_tps; }, true, 0],
    ["First token, s", function (r) { return r.ttft_p50_ms == null ? null : r.ttft_p50_ms / 1000; }, true, 2],
    ["Energy, Wh", function (r) { return r.energy_wh; }, true, 0],
    ["Peak memory, GB", function (r) { return r.peak_mem_gb; }, true, 1]
  ];
  function table(rows) {
    var t = $("table"), sortCol = 3, dir = 1;
    function render() {
      t.innerHTML = "";
      var thead = el("thead"), tr = el("tr");
      COLS.forEach(function (c, i) {
        var th = el("th", { class: c[2] ? "num" : "", scope: "col" }, c[0]);
        if (i === sortCol) th.setAttribute("aria-sort", dir > 0 ? "ascending" : "descending");
        th.addEventListener("click", function () { dir = sortCol === i ? -dir : 1; sortCol = i; render(); });
        tr.appendChild(th);
      });
      thead.appendChild(tr); t.appendChild(thead);
      var body = el("tbody");
      rows.slice().sort(function (a, b) {
        var va = COLS[sortCol][1](a), vb = COLS[sortCol][1](b);
        if (va == null) return vb == null ? 0 : 1; if (vb == null) return -1;
        return (va > vb ? 1 : va < vb ? -1 : 0) * dir;
      }).forEach(function (r) {
        var tr = el("tr", { class: r.ref ? "ref" : "" });
        COLS.forEach(function (c, i) {
          var v = c[1](r), td = el("td", { class: c[2] ? "num" : "" });
          if (i === 0) {
            td.className = "method";
            td.appendChild(el("span", { class: "key", style: "background:" + (r.status === "pending" ? "transparent;box-shadow:inset 0 0 0 1px var(--axis)" : colorOf(r)) }));
            td.appendChild(document.createTextNode(v));
            var note = r.ref ? r.framework : [r.engine_build, r.note].filter(Boolean).join(" · ");
            if (note) td.appendChild(el("div", { class: "small" }, note));
          } else td.textContent = c[2] ? (v == null ? "–" : fmt(v, c[3])) : v;
          tr.appendChild(td);
        });
        body.appendChild(tr);
      });
      t.appendChild(body);
    }
    render();
  }

  function render(d) {
    var notice = d.demo || (d.methods.some(function (m) { return m.status === "ok"; }) ? null :
      "RTX 4090 measurements are in progress. Each method's row fills in when its replay finishes; the other systems are Artificial Analysis's published runs.");
    if (notice) document.querySelector("main").insertBefore(el("p", { class: "demo" + (d.demo ? "" : " quiet") }, notice), document.querySelector("main h1"));
    d.methods.forEach(function (m) {
      m.title = m.engine + " · " + drafting(m);
      m.subtitle = [m.weights, m.engine_build, m.note].filter(Boolean).join(" · ");
      m.short = m.engine.replace(" + sidnaZ patches", " (sidnaZ)") + (m.decoding === "Autoregressive" ? "" : " " + drafting(m));
    });
    var ok = d.methods.filter(function (m) { return m.status === "ok"; });
    var pending = d.methods.filter(function (m) { return m.status === "pending"; });
    var refs = d.references.map(function (r) {
      return Object.assign({ ref: true, title: r.short + " (AA)", subtitle: r.framework + " · " + r.quant + " · " + r.decodingText,
        weights: r.quant, kv: "", price_label: r.short }, r);
    });
    document.querySelectorAll('[data-fill="n-methods"]').forEach(function (e) { e.textContent = d.methods.length; });
    legend($("legend-time")); legend($("legend-speeds"));
    var measured = ok.concat(refs).sort(function (a, b) { return a.completion_s - b.completion_s; });
    bars(measured, pending);
    var miss = $("missing"); miss.innerHTML = "";
    d.methods.filter(function (m) { return m.status === "failed"; }).forEach(function (m) {
      var li = el("li"); li.appendChild(el("b", null, m.title + ": ")); li.appendChild(document.createTextNode(m.reason || "did not run")); miss.appendChild(li);
    });
    var hw = d.hardware, best = ok.slice().sort(function (a, b) { return a.completion_s - b.completion_s; })[0];
    function charts() {
      scatterSpeeds(measured.filter(function (r) { return r.output_tps && r.prefill_tps; }));
      scatterPrice(refs.concat(best ? [Object.assign({}, best, { price_usd: hw.msrp_usd + hw.rest_of_system_usd, price_label: "RTX 4090 (fastest here)" })] : []));
    }
    charts();
    var lastW = innerWidth, timer;
    addEventListener("resize", function () { if (innerWidth === lastW) return; lastW = innerWidth; clearTimeout(timer); timer = setTimeout(charts, 150); });
    table(measured.concat(pending));
    var notes = $("notes"); notes.innerHTML = "";
    d.notes.forEach(function (n) { var li = el("li"); li.innerHTML = n; notes.appendChild(li); });
    $("footer").innerHTML = "Updated " + d.updated + ". Code and raw results: <a href=\"https://github.com/zedong-peng/qwen38-4090-inference\">github.com/zedong-peng/qwen38-4090-inference</a>.";
  }

  if (window.QWEN38_DATA) render(window.QWEN38_DATA);
  else fetch(DATA_URL).then(function (r) { return r.json(); }).then(render).catch(function (e) { $("bars").textContent = "Could not load results: " + e; });
})();
