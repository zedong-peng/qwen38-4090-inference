#!/usr/bin/env python3
"""Build the page as static files (standard library only): the two figures are rendered here from results/results.json (our
RTX 4090) and bench/aa_snapshot.json (Artificial Analysis's systems, models and runs; tools/fetch_aa.py refreshes it).

dist/ is the whole site, with relative paths; this repo's Pages workflow publishes it at zedongpeng.com/qwen38-4090-inference/.
--inline FILE writes one HTML page instead (this page's styles inlined; the site theme still loads), for previews;
--data replaces results/results.json, for example with illustrative numbers.
"""

import argparse
import datetime
import json
import math
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE, RESULTS, AA = ROOT / "site", ROOT / "results", ROOT / "bench" / "aa_snapshot.json"
CSS = "leaderboard.css"
REPO = "https://github.com/zedong-peng/qwen38-4090-inference"


SHORT = {"geforce-rtx-5090": "RTX 5090", "dgx-spark": "DGX Spark", "nvidia-rtx-spark-laptop": "RTX Spark laptop",
         "amd-ryzen-ai-halo": "Ryzen AI Halo", "macbook-pro-14-m5-pro-20gpu-64gb": "MacBook Pro M5 Pro"}
OURS = "rtx-4090"


def best(data):
    """The fastest of AA's own serving configurations that finished on the RTX 4090: the one the matrix shows."""
    return min((m for m in data["methods"] if m.get("aa_recipe") and m.get("completion_s")), key=lambda m: m["completion_s"])


FAST, SLOW = (21, 128, 61), (220, 252, 231)  # AA's scale: dark green is faster, on a log scale


def cells(data, aa):
    """(system key, model key) -> minutes, or the text of a cell that has no time."""
    out = {(r["systemKey"], r["modelKey"]): r["completionSeconds"] / 60 for r in aa["runs"]}
    mem = {s["key"]: f'{s["memoryGb"]} GB {"VRAM" if s["memoryKind"] == "dedicated" else s["memoryKind"]}' for s in aa["systems"]}
    for m in aa["models"]:
        for d in m["doesNotFitOn"]:
            out[d["systemKey"], m["key"]] = mem[d["systemKey"]]
    for k in data["does_not_fit"]:
        out[OURS, k] = f'{data["hardware"]["memory_gb"]} GB VRAM'
    out[OURS, data["model"]] = best(data)["completion_s"] / 60
    return out, mem


def heat(data, aa):
    """AA's Completion Time by Model and System chart, with the RTX 4090 as one more column."""
    cs, mem = cells(data, aa)
    cols = [(s["key"], SHORT.get(s["key"], s["shortName"]), mem[s["key"]]) for s in aa["systems"]]
    cols.append((OURS, "RTX 4090", f'{data["hardware"]["memory_gb"]} GB VRAM'))
    cols.sort(key=lambda c: -cs[c[0], aa["defaultModelKey"]])  # slowest first on the default model, as AA's chart reads
    times = [v for v in cs.values() if isinstance(v, float)]
    lo, hi = math.log(min(times)), math.log(max(times))
    out = ['<div></div>'] + [
        f'<div class="qwen38-hcol{" qwen38-ours" if k == OURS else ""}"><b>{escape(name)}</b><span>{escape(sub)}</span></div>'
        for k, name, sub in cols]
    for m in aa["models"]:
        params = (f'{m["parametersB"]:g}B, {m["activeParametersB"]:g}B active' if m["activeParametersB"]
                  else f'{m["parametersB"]:g}B') + " parameters"
        out.append(f'<div class="qwen38-hrow"><b>{escape(m["name"].split(" (")[0])}</b><span>{params}</span></div>')
        for k, _, _ in cols:
            v = cs.get((k, m["key"]))
            if isinstance(v, float):
                t = (math.log(v) - lo) / (hi - lo)
                rgb = ", ".join(str(round(a + (b - a) * t)) for a, b in zip(FAST, SLOW))
                out.append(f'<div class="qwen38-cell{" qwen38-dark" if t < 0.5 else ""}" style="background:rgb({rgb})">'
                           f'{v:.1f} min</div>')
            else:
                out.append(f'<div class="qwen38-cell qwen38-nofit">Does not fit<span>in {escape(v)}</span></div>'
                           if v else '<div class="qwen38-cell qwen38-nofit">Not run</div>')
    key = ('<p class="small qwen38-key"><span>Faster<i style="background:linear-gradient(to right, rgb(%d, %d, %d), '
           'rgb(%d, %d, %d))"></i>Slower</span><span><i class="qwen38-nofit"></i>Does not fit in memory</span></p>' % (FAST + SLOW))
    return (f'<figure class="qwen38-card"><div class="scroll"><div class="qwen38-heat" style="--n:{len(cols)}">\n'
            + "\n".join(out) + f'\n</div></div>{key}</figure>')


def month(iso):
    return datetime.date.fromisoformat(iso).strftime("%B %Y")


def note(data, aa):
    w, b = aa["workload"], best(data)
    day = b["runs"][0]["run"][:8]  # the run tree names an attempt by its start time
    measured = f"{day[:4]}-{day[4:6]}-{day[6:]}"
    recipe = f'{b["engine"]} {b["version"].split(" ")[0]}, {b["weights"]}, {b["decoding"]} {b["draft"]}'
    return (f'<p class="small qwen38-note">Time to complete the <a href="https://github.com/ArtificialAnalysis/aa-agentperf-local">'
            f'AgentPerf-Local</a> default workload ({w["turns"]} turns, {w["toolCalls"]} tool calls); lower is better. '
            f'The RTX 4090 is ours, run with their tool, settings and serving configuration ({escape(recipe)}), median of three '
            f'runs, {month(measured)}. The other systems are '
            f'<a href="{aa["source"]}">Artificial Analysis</a>\'s, retrieved {month(aa["retrieved"])}.</p>')


def board(data):
    """Our RTX 4090 setups on the default model, fastest first."""
    ms = sorted(data["methods"], key=lambda m: (m.get("completion_s") is None, m.get("completion_s") or 0))
    rows = []
    for i, m in enumerate(ms, 1):
        name = (f'<td class="qwen38-sys"><b>{escape(m["engine"])} {escape(m["version"].split(" ")[0])}</b>'
                f'<div class="qwen38-setup">{escape(m["weights"])} · <span class="qwen38-nb">{escape(m["decoding"])} {m["draft"]}</span></div></td>')
        if m.get("completion_s"):
            run = next(r for r in m["runs"] if r["completion_s"] == m["completion_s"])
            mins = m["completion_s"] / 60
            rows.append(f'<tr><td>{i}</td>{name}<td class="qwen38-num"><b>{mins:.1f}</b></td>'
                        f'<td class="qwen38-num">{run["output_tps"]:.0f}</td>'
                        f'<td class="qwen38-num">{run["ttft_p50_ms"] / 1000:.2f}</td></tr>')
        else:
            why = "measuring" if m["status"] == "pending" else m.get("reason") or "did not run"
            rows.append(f'<tr><td></td>{name}<td class="qwen38-num qwen38-wait" colspan="3">{escape(why)}</td></tr>')
    return ('<figure class="qwen38-card"><div class="scroll"><table class="qwen38-t">\n<thead><tr><th></th><th>Setup</th>'
            '<th class="qwen38-num">Minutes to finish</th><th class="qwen38-num">Output tokens/s</th>'
            '<th class="qwen38-num">First token, s</th></tr></thead>\n<tbody>\n' + "\n".join(rows) + "\n</tbody>\n</table></div></figure>"
            '<p class="small qwen38-note">Same workload and settings. Each setup is the median of three runs; '
            f'output speed and the median time to first token are from that run. <a href="{REPO}">Commands and raw data</a>.</p>')


def render(data):
    aa = json.loads(AA.read_text())
    html = (SITE / "index.html").read_text()
    subs = {"<!--HEAT-->": heat(data, aa), "<!--NOTE-->": note(data, aa), "<!--BOARD-->": board(data),
            "<!--MONTH-->": month(aa["retrieved"])}
    for k, v in subs.items():
        html = html.replace(k, v)
    return html


def build(output, data_path):
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or (output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "dist")):
        raise ValueError("Use dist/ or a separate output directory; never overwrite project sources")
    page = output / "index.html"
    output.mkdir(parents=True, exist_ok=True)
    page.write_text(render(json.loads(Path(data_path).read_text())))
    for src, dst in ((SITE / CSS, output / CSS),
                     (RESULTS / "results.json", output / "results.json"), (RESULTS / "samples.json", output / "samples.json"),
                     (AA, output / AA.name)):
        shutil.copyfile(src, dst)
    return page


def inline(target, data_path):
    html = render(json.loads(Path(data_path).read_text()))
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
