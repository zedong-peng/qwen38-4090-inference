(function () {
  "use strict";

  var board = document.getElementById("qwen38-board");
  if (!board) return;

  var controls = {
    workload: document.getElementById("qwen38-workload"),
    cohort: document.getElementById("qwen38-cohort"),
    metric: document.getElementById("qwen38-metric"),
    view: document.getElementById("qwen38-view"),
  };
  var metrics = {
    http: [
      { key: "decode_tps", label: "Decode", note: "HTTP decode: (output tokens − 1) / decode time. Prefill is excluded." },
      { key: "e2e_tps", label: "HTTP end to end", note: "HTTP end to end: output tokens / client wall time, including prefill." },
    ],
    native: [
      {
        key: "native_tps",
        label: "Native generation",
        note: "Native generation: output tokens / generation time. Different timer from HTTP decode.",
      },
      { key: "call_tps", label: "In-process call", note: "In-process call: output tokens / call wall time, including prefill. No HTTP transport." },
    ],
  };
  var data;
  var sortKey = "decode_tps";
  var sortDirection = -1;

  function element(tag, className, content) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  }

  function number(value) {
    return typeof value === "number" && Number.isFinite(value) ? value.toFixed(1) : "—";
  }

  function link(href, label) {
    var node = element("a", "", label);
    try {
      var url = new URL(href, window.location.href);
      if (url.protocol !== "https:" && url.protocol !== "http:") return element("span", "", label);
      node.href = url.href;
      if (url.origin !== window.location.origin) node.rel = "noopener noreferrer";
    } catch (error) {
      return element("span", "", label);
    }
    return node;
  }

  function currentMetric() {
    return metrics[controls.cohort.value].find(function (metric) {
      return metric.key === controls.metric.value;
    });
  }

  function updateMetricOptions(preferred) {
    controls.metric.replaceChildren();
    metrics[controls.cohort.value].forEach(function (metric) {
      var option = element("option", "", metric.label);
      option.value = metric.key;
      controls.metric.appendChild(option);
    });
    if (
      metrics[controls.cohort.value].some(function (metric) {
        return metric.key === preferred;
      })
    )
      controls.metric.value = preferred;
  }

  function restoreFilters() {
    var params = new URLSearchParams(window.location.search);
    ["workload", "cohort", "view"].forEach(function (name) {
      var value = params.get(name);
      if (
        Array.from(controls[name].options).some(function (option) {
          return option.value === value;
        })
      )
        controls[name].value = value;
    });
    updateMetricOptions(params.get("metric"));
    sortKey = controls.metric.value;
  }

  function saveFilters() {
    if (window.location.protocol === "file:") return;
    var url = new URL(window.location.href);
    Object.keys(controls).forEach(function (name) {
      url.searchParams.set(name, controls[name].value);
    });
    window.history.replaceState(null, "", url);
  }

  function selectedRows() {
    var key = controls.metric.value;
    var rows = data.results.filter(function (row) {
      return (
        row.workload === controls.workload.value && row.cohort === controls.cohort.value && typeof row[key] === "number" && Number.isFinite(row[key])
      );
    });
    if (controls.view.value === "best") {
      var best = new Map();
      rows.forEach(function (row) {
        var id = row.engine_id || row.engine;
        if (!best.has(id) || row[key] > best.get(id)[key]) best.set(id, row);
      });
      rows = Array.from(best.values());
    }
    return rows;
  }

  function renderBars(rows) {
    var container = document.getElementById("qwen38-bars");
    container.replaceChildren();
    var key = controls.metric.value;
    var ranked = rows.slice().sort(function (a, b) {
      return b[key] - a[key];
    });
    var maximum = ranked.length ? ranked[0][key] : 0;
    ranked.forEach(function (row) {
      var item = element("li", "qwen38-bar-row");
      var label = element("div", "qwen38-bar-label");
      label.appendChild(element("span", "qwen38-bar-engine", row.engine));
      label.appendChild(element("span", "qwen38-bar-mode", row.configuration));
      var track = element("div", "qwen38-bar-track");
      track.setAttribute("aria-hidden", "true");
      var fill = element("div", "qwen38-bar-fill");
      fill.style.width = (maximum > 0 ? Math.max(0, (row[key] / maximum) * 100) : 0) + "%";
      track.appendChild(fill);
      item.appendChild(label);
      item.appendChild(track);
      item.appendChild(element("span", "qwen38-bar-value", number(row[key])));
      container.appendChild(item);
    });
    document.getElementById("qwen38-fastest-speed").textContent = ranked.length ? number(ranked[0][key]) + " tok/s" : "—";
    document.getElementById("qwen38-fastest-engine").textContent = ranked.length
      ? ranked[0].engine + " · " + ranked[0].configuration
      : "No measurements in this view";
    document.getElementById("qwen38-result-count").textContent =
      rows.length + (rows.length === 1 ? " configuration · tok/s" : " configurations · tok/s");
  }

  function compareRows(a, b) {
    var first = a[sortKey];
    var second = b[sortKey];
    if (typeof first === "number" && typeof second === "number") return (first - second) * sortDirection;
    return String(first || "").localeCompare(String(second || "")) * sortDirection;
  }

  function renderTable(rows) {
    var head = document.getElementById("qwen38-table-head");
    var body = document.getElementById("qwen38-table-body");
    head.replaceChildren();
    body.replaceChildren();
    var columns = [
      { key: "engine", label: "Engine" },
      { key: "configuration", label: "Configuration" },
    ]
      .concat(metrics[controls.cohort.value])
      .concat([
        { key: "quantization", label: "Weights" },
        { key: "kv_cache", label: "KV cache" },
        { key: "evidence", label: "Evidence" },
      ]);
    var header = element("tr");
    columns.forEach(function (column) {
      var cell = element("th");
      cell.scope = "col";
      if (column.key === "evidence") {
        cell.textContent = column.label;
      } else {
        cell.setAttribute("aria-sort", column.key === sortKey ? (sortDirection === -1 ? "descending" : "ascending") : "none");
        var button = element("button", "qwen38-sort", column.label + (column.key === sortKey ? (sortDirection === -1 ? " ↓" : " ↑") : " ↕"));
        button.type = "button";
        button.addEventListener("click", function () {
          sortDirection = column.key === sortKey ? -sortDirection : column.key.endsWith("_tps") ? -1 : 1;
          sortKey = column.key;
          renderTable(selectedRows());
        });
        cell.appendChild(button);
      }
      if (column.key === controls.metric.value) cell.classList.add("qwen38-active-metric");
      header.appendChild(cell);
    });
    head.appendChild(header);
    rows
      .slice()
      .sort(compareRows)
      .forEach(function (row) {
        var line = element("tr");
        columns.forEach(function (column) {
          var cell = element("td");
          if (column.key === "evidence") {
            if (row.source_url) cell.appendChild(link(row.source_url, row.commit ? row.commit.slice(0, 7) : "Repository"));
            if (row.samples_url) {
              if (cell.childNodes.length) cell.appendChild(document.createTextNode(" · "));
              cell.appendChild(link(row.samples_url, "Samples"));
            }
            if (!cell.childNodes.length) cell.textContent = "—";
          } else if (column.key.endsWith("_tps")) {
            cell.textContent = number(row[column.key]);
            cell.classList.add("qwen38-numeric");
          } else {
            cell.textContent = row[column.key] || "—";
          }
          if (column.key === controls.metric.value) cell.classList.add("qwen38-active-metric");
          line.appendChild(cell);
        });
        body.appendChild(line);
      });
  }

  function renderCoverage() {
    var container = document.getElementById("qwen38-coverage");
    var labels = { measured: "Measured", partial: "Partial", pending: "Not measured", blocked: "Not measured", unmeasured: "Not measured" };
    (data.coverage || []).forEach(function (scheme) {
      var item = element("article", "qwen38-coverage-item");
      var heading = element("div", "qwen38-coverage-heading");
      heading.appendChild(scheme.url ? link(scheme.url, scheme.name) : element("span", "", scheme.name));
      var statusClasses = {
        measured: "qwen38-badge qwen38-badge-measured",
        partial: "qwen38-badge qwen38-badge-partial",
        pending: "qwen38-badge qwen38-badge-pending",
      };
      heading.appendChild(element("span", statusClasses[scheme.status] || statusClasses.pending, labels[scheme.status] || scheme.status));
      item.appendChild(heading);
      item.appendChild(element("p", "", scheme.detail));
      container.appendChild(item);
    });
  }

  function renderReports() {
    var container = document.getElementById("qwen38-reports");
    (data.public_reports || []).forEach(function (report) {
      var item = element("article", "qwen38-report");
      item.appendChild(link(report.url, report.name));
      item.appendChild(element("p", "", report.detail));
      container.appendChild(item);
    });
  }

  function render() {
    var rows = selectedRows();
    document.getElementById("qwen38-timer-note").textContent = currentMetric().note;
    var status = document.getElementById("qwen38-status");
    status.hidden = rows.length > 0;
    status.textContent = "No measurements for this selection. Missing measurements are not zero-speed results.";
    renderBars(rows);
    renderTable(rows);
    saveFilters();
  }

  restoreFilters();
  Object.keys(controls).forEach(function (name) {
    controls[name].addEventListener("change", function () {
      if (name === "cohort") updateMetricOptions();
      sortKey = controls.metric.value;
      sortDirection = -1;
      if (data) render();
    });
  });

  fetch(board.dataset.resultsUrl)
    .then(function (response) {
      if (!response.ok) throw new Error("Results download failed");
      return response.json();
    })
    .then(function (results) {
      if (!Array.isArray(results.results)) throw new Error("Invalid results data");
      data = results;
      renderCoverage();
      renderReports();
      document.getElementById("qwen38-updated").textContent =
        "Snapshot updated: " +
        (data.updated_at || "see protocol") +
        ". Measurement timestamps and configuration details are included with the samples.";
      render();
    })
    .catch(function () {
      document.getElementById("qwen38-status").textContent =
        "Results could not be loaded. Open the results JSON or protocol directly using the links above.";
      document.getElementById("qwen38-fastest-engine").textContent = "Results unavailable";
    });
})();
