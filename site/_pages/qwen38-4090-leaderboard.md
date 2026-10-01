---
layout: page
title: Qwen3.8-27B / RTX 4090
description: Single-GPU inference speed, with configurations and evidence.
permalink: /benchmarks/qwen38-4090/
nav: true
nav_order: 3
---

<link rel="stylesheet" href="{{ '/assets/css/qwen38-4090-leaderboard.css' | relative_url }}">

<div
  class="qwen38-board"
  id="qwen38-board"
  data-results-url="{{ '/assets/benchmarks/qwen38-4090/results.json' | relative_url }}"
>
  <div class="qwen38-intro">
    <span class="qwen38-kicker">Provisional measurements · one GPU</span>
    <p>Compare short-request deployment configurations on one RTX 4090. Quantization varies; choose a workload and timer before reading the ranking.</p>
    <p class="qwen38-muted">Measured inputs: 34–77 tokens. Configured capacity: 4K. Output budget: up to 512 tokens.</p>
    <div class="qwen38-downloads">
      <a href="{{ '/assets/benchmarks/qwen38-4090/results.json' | relative_url }}">Results JSON</a>
      <a href="{{ '/assets/benchmarks/qwen38-4090/samples.json' | relative_url }}">Raw samples</a>
      <a href="{{ '/assets/benchmarks/qwen38-4090/README.md' | relative_url }}">Protocol &amp; reproduction</a>
    </div>
  </div>

  <div class="qwen38-controls" aria-label="Benchmark filters">
    <div class="qwen38-control">
      <label for="qwen38-workload">Workload</label>
      <select id="qwen38-workload">
        <option value="code">Code</option>
        <option value="json">JSON</option>
        <option value="prose">Prose</option>
      </select>
    </div>
    <div class="qwen38-control">
      <label for="qwen38-cohort">Measurement</label>
      <select id="qwen38-cohort">
        <option value="http">HTTP servers</option>
        <option value="native">Native Python</option>
      </select>
    </div>
    <div class="qwen38-control">
      <label for="qwen38-metric">Timer</label>
      <select id="qwen38-metric">
        <option value="decode_tps">Decode</option>
        <option value="e2e_tps">HTTP end to end</option>
      </select>
    </div>
    <div class="qwen38-control">
      <label for="qwen38-view">Configurations</label>
      <select id="qwen38-view">
        <option value="best">Best per engine</option>
        <option value="all">All measured</option>
      </select>
    </div>
  </div>

  <div class="qwen38-reading-note" id="qwen38-timer-note"></div>

  <div class="qwen38-summary" aria-live="polite">
    <div class="qwen38-summary-item qwen38-leading-result">
      <span class="qwen38-label">Fastest in this view</span>
      <span class="qwen38-result-number" id="qwen38-fastest-speed">—</span>
      <span class="qwen38-summary-detail" id="qwen38-fastest-engine">Loading results…</span>
    </div>
    <div class="qwen38-summary-item">
      <span class="qwen38-label">Hardware</span>
      <span class="qwen38-summary-value">1 × RTX 4090</span>
      <span class="qwen38-summary-detail">24 GB · shared machine</span>
    </div>
    <div class="qwen38-summary-item">
      <span class="qwen38-label">Measurement</span>
      <span class="qwen38-summary-value">3-run median</span>
      <span class="qwen38-summary-detail">4K capacity · batch 1</span>
    </div>
  </div>

  <div class="qwen38-status" id="qwen38-status" role="status">Loading benchmark data…</div>

  <section class="qwen38-section" aria-labelledby="qwen38-comparison-title">
    <div class="qwen38-section-heading">
      <h2 id="qwen38-comparison-title">Speed comparison</h2>
      <span class="qwen38-muted" id="qwen38-result-count"></span>
    </div>
    <ol class="qwen38-bars" id="qwen38-bars" aria-label="Speed comparison, fastest first"></ol>
    <div class="qwen38-table-wrap">
      <table class="qwen38-table" id="qwen38-results-table">
        <caption class="qwen38-visually-hidden">Measured speed and deployment configuration. Select a column heading to sort.</caption>
        <thead id="qwen38-table-head"></thead>
        <tbody id="qwen38-table-body"></tbody>
      </table>
    </div>
  </section>

  <p class="qwen38-quality-note">
    These are speed measurements, with different quantizations and KV caches. Code and prose were capped at 512 output tokens and truncated;
    JSON completed and parsed. The recorded fenced-code syntax checks failed; semantic tests were not run.
    The bars do not establish equal quality or a universal winner.
  </p>

  <details class="qwen38-method">
    <summary>What is comparable?</summary>
    <div>
      <p>
        Every measured configuration used the same physical RTX 4090, sequentially: batch 1, 4,096-token configured capacity, 34–77-token inputs,
        greedy decoding, thinking off, and three repetitions of each workload. GPU snapshots are included with the evidence;
        the shared machine was not reserved exclusively.
      </p>
      <p>
        HTTP decode speed is (output tokens − 1) / decode time. HTTP end-to-end speed is output tokens / client wall time, including prefill.
        The non-streaming benchmark does not measure time to first token.
      </p>
      <p>
        Native generation speed uses output tokens / generation time; in-process call speed also includes prefill. Native and HTTP results have
        different timing boundaries and are shown separately. Public reports below have their own protocols and are not ranked against these runs.
      </p>
    </div>
  </details>

  <section class="qwen38-section" aria-labelledby="qwen38-coverage-title">
    <div class="qwen38-section-heading">
      <h2 id="qwen38-coverage-title">Scheme coverage</h2>
      <span class="qwen38-muted">Missing measurements stay missing</span>
    </div>
    <div class="qwen38-coverage" id="qwen38-coverage"></div>
  </section>

  <section class="qwen38-section" aria-labelledby="qwen38-reports-title">
    <div class="qwen38-section-heading">
      <h2 id="qwen38-reports-title">Public reports &amp; other leaderboards</h2>
      <span class="qwen38-muted">Different protocols</span>
    </div>
    <div class="qwen38-reports" id="qwen38-reports"></div>
  </section>

  <p class="qwen38-footer-note" id="qwen38-updated"></p>
  <noscript>
    <p>The interactive comparison requires JavaScript. The results, raw samples, and protocol are available from the download links above.</p>
  </noscript>
</div>

<script defer src="{{ '/assets/js/qwen38-4090-leaderboard.js' | relative_url }}"></script>
