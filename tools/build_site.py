#!/usr/bin/env python3
"""Build the page as static files (standard library only): the table is rendered here from results/results.json.

dist/benchmarks/qwen38-4090/index.html and dist/assets/... are what the personal site's deploy copies.
--inline FILE writes one self-contained HTML page instead (styles and script inlined), for previews;
--data replaces results/results.json, for example with illustrative numbers.
"""

import argparse
import json
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE, RESULTS = ROOT / "site", ROOT / "results"
CSS, JS = "assets/css/qwen38-4090-leaderboard.css", "assets/js/qwen38-4090-leaderboard.js"
DATA = "assets/benchmarks/qwen38-4090"
REPO = "https://github.com/zedong-peng/qwen38-4090-inference"
MONTH = "October 2026"
FONTS = ("qwen38-dmsans.woff2", "qwen38-sourceserif4.woff2")


def setup(engine, weights, decoding, draft):
    return f"{engine} · {weights} · {decoding} {draft}" if draft else f"{engine} · {weights} · {decoding}"


def rows(data):
    out = []
    for s in data["references"]:
        engine = s["framework"].split(" ")[0]
        out.append(dict(system=s["short"], memory=s["memory_gb"], bandwidth=s["bandwidth_gbs"], ours=False,
                        setup=setup(engine, s["quant"], s["decoding"].replace("DFlash2", "DFlash"), s.get("draft")),
                        minutes=s["completion_s"] / 60))
    hw = data["hardware"]
    for m in data["methods"]:
        out.append(dict(system="RTX 4090", memory=hw["memory_gb"], bandwidth=hw["bandwidth_gbs"], ours=True,
                        setup=setup(m["engine"], m["weights"], m["decoding"], m.get("draft")),
                        minutes=m["completion_s"] / 60 if m.get("completion_s") else None,
                        status=m["status"], reason=m.get("reason")))
    return sorted(out, key=lambda r: (r["minutes"] is None, r["minutes"] or 0))


def table(data):
    rs = rows(data)
    top = max(r["minutes"] for r in rs if r["minutes"] is not None)
    body = []
    for r in rs:
        if r["minutes"] is None:
            cell = f'<span class="qwen38-wait">{"measuring" if r["status"] == "pending" else escape(r["reason"] or "did not run")}</span>'
        else:
            cell = (f'<div class="qwen38-bar"><i style="--w:{r["minutes"] / top:.3f}"></i>'
                    f'<span>{r["minutes"]:.1f}</span></div>')
        cls = ' class="qwen38-ours"' if r["ours"] else ""
        body.append(
            f'<tr{cls}>'
            f'<td class="qwen38-sys"><b>{escape(r["system"])}</b> <span>{r["memory"]} GB</span>'
            f'<div class="qwen38-setup">{escape(r["setup"])}</div></td>'
            f'<td class="qwen38-num qwen38-bw">{r["bandwidth"]:,} GB/s</td>'
            f'<td class="qwen38-mcol">{cell}</td></tr>')
    return ('<figure class="qwen38-card"><table class="qwen38-t">\n'
            '<thead><tr><th>System and setup</th><th class="qwen38-num qwen38-bw">Bandwidth</th>'
            '<th class="qwen38-mcol">Minutes to finish <span>(lower is faster)</span></th></tr></thead>\n<tbody>\n'
            + "\n".join(body) + "\n</tbody>\n</table></figure>")


def note(data):
    return ('<p class="qwen38-note">Minutes to finish the replay. Highlighted: our RTX 4090, median of three runs; '
            f'the other systems are <a href="{data["references_source"]}">Artificial Analysis</a>\'s, {MONTH}.</p>')


def method(data):
    return (f'Workload: <a href="https://github.com/ArtificialAnalysis/aa-agentperf-local">AgentPerf-Local</a>\'s default '
            "replay, 8 recorded coding-agent tasks and 168 turns sent one at a time with a 65,536-token context; every turn "
            "writes its recorded number of tokens, and tool time is not counted. Our runs use their tool and their recipes for "
            "the RTX 5090 (llama.cpp b11026, Q4_K_M, MTP 2) and the RTX Spark (b11236, UD-Q4_K_M, DFlash 7) on one RTX 4090. "
            f'<a href="{REPO}">Commands and raw data</a>.')


def median_turns(data, samples):
    """Per method, the turns of its median run (the run whose time the table shows)."""
    out = {}
    for m in data["methods"]:
        run = next((r["run"] for r in m.get("runs", []) if r.get("completion_s") == m.get("completion_s")), None)
        if run and run in samples["methods"].get(m["id"], {}):
            out[m["id"]] = [dict(zip(samples["columns"], t)) for t in samples["methods"][m["id"]][run]]
    return out


def split(data, samples):
    """Where the minutes go: reading the prompt (time to first token) and writing, for each RTX 4090 setup."""
    turns = median_turns(data, samples)
    bars = []
    for m in data["methods"]:
        if m["id"] not in turns:
            continue
        t = turns[m["id"]]
        read, write = (sum(x[k] for x in t) / 6e4 for k in ("ttft_ms", "generation_ms"))
        bars.append((f'{m["decoding"]} {m["draft"]}', read, write))
    top = max(r + w for _, r, w in bars)
    rows = "".join(
        f'<div class="qwen38-srow"><span class="qwen38-slabel">{escape(name)}</span><div class="qwen38-sbar">'
        f'<i class="qwen38-read" style="--w:{r / top:.3f}" title="Reading: {r:.1f} min">{r:.1f}</i>'
        f'<i class="qwen38-write" style="--w:{w / top:.3f}" title="Writing: {w:.1f} min">{w:.1f}</i></div></div>'
        for name, r, w in bars)
    return ('<figure class="qwen38-split"><div class="qwen38-key"><span><i class="qwen38-read"></i>Reading the prompt</span>'
            '<span><i class="qwen38-write"></i>Writing</span></div>' + rows +
            '<figcaption>Minutes on the RTX 4090, median run. Reading is the time to the first token of each turn.</figcaption></figure>')


def numbers(data, samples):
    turns = median_turns(data, samples)
    t = turns["lcpp-mtp2"]
    tps = {k: sum(x["output_tokens"] for x in v) / (sum(x["generation_ms"] for x in v) / 1e3) for k, v in turns.items()}
    return {"<!--PROMPT-->": f'{sum(x["prompt_tokens"] for x in t) / 1e6:.2f} million',
            "<!--OUTPUT-->": f'{sum(x["output_tokens"] for x in t):,}',
            "<!--UNCACHED-->": f'{round(sum(x["prompt_tokens"] - x["cached_tokens"] for x in t), -3):,}',
            "<!--TPS-->": f'{tps["lcpp-dflash7"]:.0f} tokens a second instead of {tps["lcpp-mtp2"]:.0f}'}


def render(data, samples):
    html = (SITE / "index.html").read_text()
    subs = {"<!--TABLE-->": table(data), "<!--NOTE-->": note(data), "<!--SPLIT-->": split(data, samples),
            "<!--METHOD-->": method(data), "<!--MONTH-->": MONTH, **numbers(data, samples)}
    for k, v in subs.items():
        html = html.replace(k, v)
    return html


def build(output, data_path):
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or (output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "dist")):
        raise ValueError("Use dist/ or a separate output directory; never overwrite project sources")
    page = output / "benchmarks/qwen38-4090/index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(render(json.loads(Path(data_path).read_text()), json.loads((RESULTS / "samples.json").read_text())))
    for src, dst in ((SITE / "leaderboard.css", output / CSS), (SITE / "leaderboard.js", output / JS),
                     (RESULTS / "results.json", output / DATA / "results.json"), (RESULTS / "samples.json", output / DATA / "samples.json")):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    for f in FONTS:
        (output / "assets/fonts").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SITE / "fonts" / f, output / "assets/fonts" / f)
    (output / "index.html").write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=benchmarks/qwen38-4090/">\n')
    return page


def inline(target, data_path):
    html = render(json.loads(Path(data_path).read_text()), json.loads((RESULTS / "samples.json").read_text()))
    html = html.replace('<link rel="stylesheet" href="/assets/css/qwen38-4090-leaderboard.css">',
                        "<style>\n" + (SITE / "leaderboard.css").read_text() + "</style>")
    html = html.replace('<script src="/assets/js/qwen38-4090-leaderboard.js" defer></script>',
                        "<script>\n" + (SITE / "leaderboard.js").read_text() + "</script>")
    target.write_text(html)
    return target


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "dist")
    ap.add_argument("--inline", type=Path)
    ap.add_argument("--data", type=Path, default=RESULTS / "results.json")
    a = ap.parse_args()
    print(inline(a.inline, a.data) if a.inline else build(a.output, a.data))
