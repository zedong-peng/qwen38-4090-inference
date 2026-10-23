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
    month = MONTH
    return (f'<p class="qwen38-note">Workload: <a href="https://github.com/ArtificialAnalysis/aa-agentperf-local">AgentPerf-Local</a>\'s '
            "default, 8 recorded coding-agent tasks and 168 turns, sent one at a time; every turn writes its recorded number "
            "of tokens, and tool time is not counted. Other systems: "
            f'<a href="{data["references_source"]}">Artificial Analysis</a>, {month}. Highlighted: our RTX 4090 runs with their tool, '
            "median of three; the two llama.cpp setups are their recipes for the RTX 5090 and the RTX Spark. "
            f'<a href="{REPO}">Commands and raw data</a>.</p>')


def render(data):
    return ((SITE / "index.html").read_text().replace("<!--TABLE-->", table(data)).replace("<!--NOTE-->", note(data))
            .replace("<!--MONTH-->", MONTH))


def build(output, data_path):
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or (output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "dist")):
        raise ValueError("Use dist/ or a separate output directory; never overwrite project sources")
    page = output / "benchmarks/qwen38-4090/index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(render(json.loads(Path(data_path).read_text())))
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
    html = render(json.loads(Path(data_path).read_text()))
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
