#!/usr/bin/env python3
"""Build the page as static files (standard library only): the table is rendered here from results/results.json (our
RTX 4090) and bench/aa_snapshot.json (Artificial Analysis's systems, models and runs; tools/fetch_aa.py refreshes it).

dist/ is the whole site, with relative paths; this repo's Pages workflow publishes it at zedongpeng.com/qwen38-4090-inference/.
--inline FILE writes one HTML page instead (this page's styles inlined; the site theme still loads), for previews;
--data replaces results/results.json, for example with illustrative numbers.
"""

import argparse
import datetime
import json
import re
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE, RESULTS, AA = ROOT / "site", ROOT / "results", ROOT / "bench" / "aa_snapshot.json"
CSS = "leaderboard.css"
REPO = "https://github.com/zedong-peng/qwen38-4090-inference"


SHORT = {"geforce-rtx-5090": "RTX 5090", "dgx-spark": "DGX Spark", "nvidia-rtx-spark-laptop": "RTX Spark laptop",
         "amd-ryzen-ai-halo": "Ryzen AI Halo", "macbook-pro-14-m5-pro-20gpu-64gb": "MacBook Pro M5 Pro"}
ENGINE = {"llama-cpp": "llama.cpp", "vllm": "vLLM"}
DRAFTER = {"mtp": "MTP", "dflash": "DFlash", "dspark": "DSpark"}
OURS = "rtx-4090"


def setup(engine, weights, decoding, draft):
    """Two lines: engine and weights, then the decoding."""
    return f"{engine} · {weights}", f"{decoding} {draft}" if draft else decoding


def aa_setup(run):
    kind = next((v for k, v in DRAFTER.items() if f"-{k}-" in run["speculation"]), "no drafts")
    n = re.search(r'--spec-draft-n-max (\d+)|num_speculative_tokens\\?":(\d+)', run["config"]["launchCommand"])
    return setup(ENGINE.get(run["runtime"]["framework"], run["runtime"]["framework"]), run["quant"], kind,
                 next(filter(None, n.groups())) if n else None)


def best(data):
    """The fastest RTX 4090 setup that finished: the one the matrix shows."""
    return min((m for m in data["methods"] if m.get("completion_s")), key=lambda m: m["completion_s"])


def matrix(data, aa):
    """Systems down, models across. A cell is (minutes, setup), "does not fit", or None where nobody ran it."""
    systems = [dict(key=s["key"], name=SHORT.get(s["key"], s["shortName"]), memory=s["memoryGb"],
                    bandwidth=s["memoryBandwidthGbs"]) for s in aa["systems"]]
    hw = data["hardware"]
    systems.append(dict(key=OURS, name="RTX 4090", memory=hw["memory_gb"], bandwidth=hw["bandwidth_gbs"]))
    cells = {(r["systemKey"], r["modelKey"]): (r["completionSeconds"] / 60, aa_setup(r)) for r in aa["runs"]}
    for m in aa["models"]:
        for d in m["doesNotFitOn"]:
            cells[d["systemKey"], m["key"]] = "does not fit"
    for k in data["does_not_fit"]:
        cells[OURS, k] = "does not fit"
    b = best(data)
    cells[OURS, data["model"]] = (b["completion_s"] / 60, setup(b["engine"], b["weights"], b["decoding"], b.get("draft")))
    first = aa["defaultModelKey"]
    systems.sort(key=lambda s: cells[s["key"], first][0] if isinstance(cells.get((s["key"], first)), tuple) else 1e9)
    return systems, cells


def table(data, aa):
    systems, cells = matrix(data, aa)
    top = max(c[0] for c in cells.values() if isinstance(c, tuple))
    head = "".join(
        f'<th>{escape(m["name"].split(" (")[0])}<span>'
        + (f'{m["activeParametersB"]:g}B of {m["parametersB"]:g}B active' if m["activeParametersB"]
           else f'all {m["parametersB"]:g}B active') + "</span></th>"
        for m in aa["models"])
    body = []
    for s in systems:
        tds = []
        for m in aa["models"]:
            c = cells.get((s["key"], m["key"]))
            if isinstance(c, tuple):
                tds.append(f'<td><div class="qwen38-bar"><i style="--w:{c[0] / top:.3f}"></i><span>{c[0]:.1f}</span></div>'
                           f'<div class="qwen38-setup">{escape(c[1][0])}<br>{escape(c[1][1])}</div></td>')
            else:
                tds.append(f'<td><span class="qwen38-wait">{c or "not run"}</span></td>')
        cls = ' class="qwen38-ours"' if s["key"] == OURS else ""
        body.append(f'<tr{cls}><td class="qwen38-sys"><b>{escape(s["name"])}</b>'
                    f'<div class="qwen38-setup">{s["memory"]} GB · {s["bandwidth"]:,} GB/s</div></td>' + "".join(tds) + "</tr>")
    return ('<figure class="qwen38-card scroll"><table class="qwen38-t">\n'
            f'<thead><tr><th>System<span>memory · bandwidth</span></th>{head}</tr></thead>\n<tbody>\n'
            + "\n".join(body) + "\n</tbody>\n</table></figure>")


def month(iso):
    return datetime.date.fromisoformat(iso).strftime("%B %Y")


def note(data, aa):
    return ('<p class="small qwen38-note">Minutes to finish the replay; lower is faster, and all bars share one scale. '
            f'Highlighted: our RTX 4090, the faster of two setups, median of three runs, {month(data["updated"])}. '
            f'The other systems are <a href="{aa["source"]}">Artificial Analysis</a>\'s, retrieved {month(aa["retrieved"])}.</p>')


def others(aa):
    """The two models besides the default one, in a sentence each, from AA's data."""
    models = {m["key"]: m for m in aa["models"]}
    ling, a3b = models["ling-3-0-flash"], models["qwen3-6-35b-a3b"]
    big = sorted({d["weightsBytes"] for d in ling["doesNotFitOn"]})[-1] / 2**30
    ran = [s for s in aa["systems"] if any(r["systemKey"] == s["key"] and r["modelKey"] == ling["key"] for r in aa["runs"])]
    assert len(ran) == 3 and {s["memoryGb"] for s in ran} == {128}, "the sentence about Ling 3.0 Flash no longer holds"
    by = {}
    for r in aa["runs"]:
        by.setdefault(r["systemKey"], {})[r["modelKey"]] = r["completionSeconds"]
    assert all(v[a3b["key"]] == min(v.values()) for v in by.values() if a3b["key"] in v), "Qwen3.6 35B A3B is no longer fastest"
    return (f'The other two models sort the same way. Ling 3.0 Flash is {big:.0f} GiB at 4 bits and runs only on the three '
            f'128 GB machines. Qwen3.6 35B A3B uses {a3b["activeParametersB"]:g} of its {a3b["parametersB"]:g} billion '
            'parameters for each token and is the fastest model on every system that holds it. It does not fit in 24 GB.')


def method(data):
    return (f'Workload: <a href="https://github.com/ArtificialAnalysis/aa-agentperf-local">AgentPerf-Local</a>\'s default '
            "replay, 8 recorded coding-agent tasks and 168 turns sent one at a time with a 65,536-token context; every turn "
            "writes its recorded number of tokens, and tool time is not counted. Our runs use their tool and their recipes for "
            "the RTX 5090 (llama.cpp b11026, Q4_K_M, MTP 2) and the RTX Spark (b11236, UD-Q4_K_M, DFlash 7) on one RTX 4090; "
            "the table shows the faster. Their tool judged the other two models too large for the card. "
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
    aa = json.loads(AA.read_text())
    html = (SITE / "index.html").read_text()
    subs = {"<!--TABLE-->": table(data, aa), "<!--NOTE-->": note(data, aa), "<!--SPLIT-->": split(data, samples),
            "<!--OTHERS-->": others(aa), "<!--METHOD-->": method(data), "<!--MONTH-->": month(aa["retrieved"]),
            **numbers(data, samples)}
    for k, v in subs.items():
        html = html.replace(k, v)
    return html


def build(output, data_path):
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or (output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "dist")):
        raise ValueError("Use dist/ or a separate output directory; never overwrite project sources")
    page = output / "index.html"
    output.mkdir(parents=True, exist_ok=True)
    page.write_text(render(json.loads(Path(data_path).read_text()), json.loads((RESULTS / "samples.json").read_text())))
    for src, dst in ((SITE / CSS, output / CSS),
                     (RESULTS / "results.json", output / "results.json"), (RESULTS / "samples.json", output / "samples.json"),
                     (AA, output / AA.name)):
        shutil.copyfile(src, dst)
    return page


def inline(target, data_path):
    html = render(json.loads(Path(data_path).read_text()), json.loads((RESULTS / "samples.json").read_text()))
    html = html.replace('<link rel="stylesheet" href="leaderboard.css">',
                        "<style>\n" + (SITE / "leaderboard.css").read_text() + "</style>")
    target.write_text(html)
    return target


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "dist")
    ap.add_argument("--inline", type=Path)
    ap.add_argument("--data", type=Path, default=RESULTS / "results.json")
    a = ap.parse_args()
    print(inline(a.inline, a.data) if a.inline else build(a.output, a.data))
