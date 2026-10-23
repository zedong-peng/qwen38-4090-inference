#!/usr/bin/env python3
"""Build the leaderboard as static files (standard library only).

dist/benchmarks/qwen38-4090/index.html and dist/assets/... are what the personal site's deploy copies.
--inline FILE writes one self-contained HTML page instead (styles, script and data inlined), for previews;
--data replaces results/results.json, for example with illustrative numbers.
"""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE, RESULTS = ROOT / "site", ROOT / "results"
CSS, JS = "assets/css/qwen38-4090-leaderboard.css", "assets/js/qwen38-4090-leaderboard.js"
DATA = "assets/benchmarks/qwen38-4090"


def build(output):
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or (output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "dist")):
        raise ValueError("Use dist/ or a separate output directory; never overwrite project sources")
    page = output / "benchmarks/qwen38-4090/index.html"
    for src, dst in ((SITE / "index.html", page), (SITE / "leaderboard.css", output / CSS), (SITE / "leaderboard.js", output / JS),
                     (RESULTS / "results.json", output / DATA / "results.json"), (RESULTS / "samples.json", output / DATA / "samples.json")):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    (output / "index.html").write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=benchmarks/qwen38-4090/">\n')
    return page


def inline(target, data_path):
    html = (SITE / "index.html").read_text()
    data = json.loads(Path(data_path).read_text())
    html = html.replace('<link rel="stylesheet" href="/assets/css/qwen38-4090-leaderboard.css">',
                        "<style>\n" + (SITE / "leaderboard.css").read_text() + "</style>")
    script = "<script>window.QWEN38_DATA = " + json.dumps(data).replace("</", "<\\/") + ";</script>\n<script>\n" + \
        (SITE / "leaderboard.js").read_text() + "</script>"
    html = html.replace('<script src="/assets/js/qwen38-4090-leaderboard.js" defer></script>', script)
    target.write_text(html)
    return target


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "dist")
    ap.add_argument("--inline", type=Path)
    ap.add_argument("--data", type=Path, default=RESULTS / "results.json")
    a = ap.parse_args()
    print(inline(a.inline, a.data) if a.inline else build(a.output))
