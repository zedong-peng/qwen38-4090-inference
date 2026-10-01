#!/usr/bin/env python3
"""Build the archived leaderboard using only Python's standard library."""

import argparse
import html
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build(output):
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or (output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "dist")):
        raise ValueError("Use dist/ or a separate output directory; never overwrite project sources")
    source = ROOT / "site"
    page = (source / "_pages/qwen38-4090-leaderboard.md").read_text()
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", page, re.S)
    if not frontmatter:
        raise ValueError("Expected the archived Jekyll frontmatter")
    title_match = re.search(r"^title: (.+)$", frontmatter[1], re.M)
    title = html.escape(title_match[1].strip("\"'"))
    body = page[frontmatter.end():]
    body = re.sub(r"\{\{\s*(['\"])(.*?)\1\s*\|\s*relative_url\s*\}\}", lambda m: m[2], body)
    if "{{" in body or "{%" in body:
        raise ValueError("New Liquid syntax requires a Jekyll build; the standalone renderer cannot expand it")
    shutil.copytree(source / "assets", output / "assets", dirs_exist_ok=True)
    document = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root { --global-bg-color:#fff; --global-text-color:#202124; --global-text-color-light:#666; --global-card-bg-color:#fff; --global-divider-color:rgba(0,0,0,.12); --global-theme-color:#b509ac; color-scheme:light; }
html[data-theme="dark"] { --global-bg-color:#1c1c1d; --global-text-color:#eee; --global-text-color-light:#aaa; --global-card-bg-color:#242426; --global-divider-color:rgba(255,255,255,.15); color-scheme:dark; }
* { box-sizing:border-box; } body { margin:0; background:var(--global-bg-color); color:var(--global-text-color); font:16px/1.55 system-ui,-apple-system,sans-serif; }
a { color:var(--global-theme-color); text-decoration:none; } a:hover { text-decoration:underline; }
header { border-bottom:1px solid var(--global-divider-color); } nav { max-width:1080px; margin:auto; padding:1rem 1.25rem; display:flex; justify-content:space-between; align-items:center; gap:1rem; }
nav button { background:var(--global-card-bg-color); color:var(--global-text-color); border:1px solid var(--global-divider-color); border-radius:.4rem; padding:.45rem .7rem; cursor:pointer; }
main { max-width:1080px; padding:2.5rem 1.25rem 4rem; margin:auto; } h1 { font-size:clamp(2rem,5vw,2.7rem); font-weight:500; line-height:1.2; } h2 { font-size:1.45rem; } .subtitle { color:var(--global-text-color-light); margin-bottom:2rem; }
footer { max-width:1080px; margin:auto; padding:1.25rem; color:var(--global-text-color-light); border-top:1px solid var(--global-divider-color); font-size:.8rem; }
</style></head><body>
<header><nav><a href="https://github.com/zedong-peng/qwen38-4090-inference">Zedong Peng · Inference archive</a><button type="button" id="theme-toggle">Light / dark</button></nav></header>
<main><h1>__TITLE__</h1><p class="subtitle">Single-GPU inference speed, with configurations and evidence.</p>__BODY__</main>
<footer>Archived snapshot: 2026-10-02. See the protocol and raw samples before comparing measurements.</footer>
<script>document.getElementById('theme-toggle').addEventListener('click',function(){document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';});</script>
</body></html>
""".replace("__TITLE__", title).replace("__BODY__", body)
    target = output / "benchmarks/qwen38-4090/index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(document)
    (output / "index.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Qwen3.8 / RTX 4090</title><p><a href="/benchmarks/qwen38-4090/">Open the Qwen3.8-27B / RTX 4090 leaderboard</a></p></html>\n')
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    print(build(args.output))
