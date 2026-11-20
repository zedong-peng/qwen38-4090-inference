#!/usr/bin/env python3
"""Render the agent-workload figures of the decode post (standard library only), and the page that forwards this
repo's old leaderboard address to it.

The two figures come from results/results.json (our RTX 4090) and bench/aa_snapshot.json (Artificial Analysis's
systems, models and runs; tools/fetch_aa.py refreshes it). They live in the post
zedong-peng.github.io/_posts/2026-10-06-qwen38-4090-decode.md, between the markers <!-- BEGIN qwen38 NAME --> and
<!-- END qwen38 NAME -->, and take the post's own styles.

usage: python3 tools/build_site.py --post PATH/TO/2026-10-06-qwen38-4090-decode.md   # rewrites the two figures
       python3 tools/build_site.py [--output dist]   # the forwarding page this repo's Pages workflow publishes
"""

import argparse
import datetime
import json
import math
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS, AA = ROOT / "results" / "results.json", ROOT / "bench" / "aa_snapshot.json"
REPO = "https://github.com/zedong-peng/qwen38-4090-inference"
POST = "https://zedongpeng.com/blog/2026/qwen38-4090-decode/#an-agent-workload"

SHORT = {"geforce-rtx-5090": "RTX 5090", "dgx-spark": "DGX Spark", "nvidia-rtx-spark-laptop": "RTX Spark laptop",
         "amd-ryzen-ai-halo": "Ryzen AI Halo", "macbook-pro-14-m5-pro-20gpu-64gb": "MacBook Pro M5 Pro"}
OURS = "rtx-4090"
# how the post names our engine's setups, after its first figure
NAMES = {"ninfer-tree15": ("Ours", "official weights"), "ninfer-requant": ("Ours", "our weights")}


def ranked(data):
    """Setups with a time, ranked ones fastest first, then the unranked ones."""
    timed = [m for m in data["methods"] if m.get("completion_s")]
    return sorted(timed, key=lambda m: (m.get("ranked") is False, m["completion_s"]))


def month(iso):
    return datetime.date.fromisoformat(iso).strftime("%B %Y")


def heat(data, aa):
    """Artificial Analysis's Completion Time by Model and System chart, with the RTX 4090 running our fastest ranked
    setup as one more column. Darker is faster, on a log scale."""
    mem = {s["key"]: f'{s["memoryGb"]} GB {"VRAM" if s["memoryKind"] == "dedicated" else s["memoryKind"]}' for s in aa["systems"]}
    mem[OURS] = f'{data["hardware"]["memory_gb"]} GB VRAM'
    cs = {(r["systemKey"], r["modelKey"]): r["completionSeconds"] / 60 for r in aa["runs"]}
    for m in aa["models"]:
        for d in m["doesNotFitOn"]:
            cs[d["systemKey"], m["key"]] = mem[d["systemKey"]]
    for k in data["does_not_fit"]:
        cs[OURS, k] = mem[OURS]
    best = ranked(data)[0]
    cs[OURS, data["model"]] = best["completion_s"] / 60
    cols = [(s["key"], SHORT.get(s["key"], s["shortName"])) for s in aa["systems"]] + [(OURS, "RTX 4090")]
    cols.sort(key=lambda c: cs[c[0], aa["defaultModelKey"]])  # fastest first on the default model, so ours leads on a phone
    times = [v for v in cs.values() if isinstance(v, float)]
    lo, hi = math.log(min(times)), math.log(max(times))
    out = ["<div></div>"] + [f'<div class="q-hcol{" q-ours" if k == OURS else ""}"><b>{escape(n)}</b><span>{escape(mem[k])}</span></div>'
                             for k, n in cols]
    for m in aa["models"]:
        params = (f'{m["parametersB"]:g}B, {m["activeParametersB"]:g}B active' if m["activeParametersB"] else f'{m["parametersB"]:g}B')
        out.append(f'<div class="q-hrow"><b>{escape(m["name"].split(" (")[0])}</b><span>{params} parameters</span></div>')
        for k, _ in cols:
            v = cs.get((k, m["key"]))
            if isinstance(v, float):
                p = round(100 - 85 * (math.log(v) - lo) / (hi - lo))
                out.append(f'<div class="q-cell{" q-dark" if p >= 55 else ""}" style="--p:{p}%">{v:.1f} min</div>')
            else:
                out.append(f'<div class="q-cell q-nofit">Does not fit<span>in {escape(v)}</span></div>' if v
                           else '<div class="q-cell q-nofit">Not run</div>')
    w = aa["workload"]
    return ('<figure class="q-fig">\n  <div class="q-title">Time to finish the agent replay, by model and system</div>\n'
            f'  <div class="scroll"><div class="q-heat" style="--n:{len(cols)}">\n' + "\n".join(out) + "\n</div></div>\n"
            f'  <figcaption>AA-AgentPerf-Local default replay, {w["turns"]} turns and {w["toolCalls"]} tool calls; darker is '
            "faster. The RTX 4090 runs our engine on the official weights, median of three replays. The other systems run "
            f'<a href="{aa["source"]}">Artificial Analysis</a>\'s own configurations, retrieved {month(aa["retrieved"])}.'
            "</figcaption>\n</figure>")


def board(data):
    """Every RTX 4090 setup on the default model: ranked ones fastest first, then unranked ones, then those that did not run."""
    def name(m):
        title, weights = NAMES.get(m["id"], (f'{m["engine"]} {m["version"].split(" ")[0]}', m["weights"]))
        return f'<td><b>{escape(title)}</b> <span class="q-sub">{escape(weights)} · {escape(m["decoding"])} {m["draft"]}</span></td>'

    rows, rank = [], 0
    for m in ranked(data):
        run = next(r for r in m["runs"] if r["completion_s"] == m["completion_s"])
        if m.get("ranked") is not False:
            rank += 1
        rows.append(f'<tr><td>{rank if m.get("ranked") is not False else ""}</td>{name(m)}'
                    f'<td class="q-num">{m["completion_s"] / 60:.1f}</td><td class="q-num">{run["output_tps"]:.0f}</td>'
                    f'<td class="q-num">{run["ttft_p50_ms"] / 1000:.2f}</td></tr>')
    for m in data["methods"]:
        if not m.get("completion_s"):
            why = "measuring" if m["status"] == "pending" else m.get("reason") or "did not run"
            rows.append(f'<tr><td></td>{name(m)}<td class="q-sub" colspan="3">{escape(why)}</td></tr>')
    return ('<figure class="q-fig">\n  <div class="q-title">Every setup we ran on one RTX 4090</div>\n'
            '  <div class="scroll"><table class="q-board">\n<thead><tr><th></th><th>Setup</th><th class="q-num">Minutes</th>'
            '<th class="q-num">Output tokens/s</th><th class="q-num">First token, s</th></tr></thead>\n<tbody>\n'
            + "\n".join(rows) + "\n</tbody>\n</table></div>\n"
            "  <figcaption>The same replay and settings. Each setup is the median of three replays; output speed and the median "
            "time to first token are from that replay. Only setups on the official weights are ranked. "
            f'<a href="{REPO}">Commands and raw data</a>.</figcaption>\n</figure>')


def post(path, data):
    aa = json.loads(AA.read_text())
    text = path.read_text()
    for key, html in (("heat", heat(data, aa)), ("board", board(data))):
        pat = re.compile(rf"(<!-- BEGIN qwen38 {key} -->\n)(?:.*?\n)?(<!-- END qwen38 {key} -->)", re.S)
        if not pat.search(text):
            raise SystemExit(f"{path}: no <!-- BEGIN qwen38 {key} --> ... <!-- END qwen38 {key} --> markers")
        text = pat.sub(lambda mt: mt.group(1) + html + "\n" + mt.group(2), text)
    path.write_text(text)
    return path


def forward(output):
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or (output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "dist")):
        raise ValueError("Use dist/ or a separate output directory; never overwrite project sources")
    output.mkdir(parents=True, exist_ok=True)
    page = output / "index.html"
    page.write_text(f'<!doctype html>\n<meta charset="utf-8">\n<title>Qwen3.8 27B on an RTX 4090</title>\n'
                    f'<link rel="canonical" href="{POST}">\n<meta http-equiv="refresh" content="0; url={POST}">\n'
                    f'<p>The RTX 4090 leaderboard is now part of <a href="{POST}">this post</a>.</p>\n')
    return page


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--post", type=Path)
    ap.add_argument("--output", type=Path, default=ROOT / "dist")
    ap.add_argument("--data", type=Path, default=RESULTS)
    a = ap.parse_args()
    print(post(a.post, json.loads(a.data.read_text())) if a.post else forward(a.output))
