# Working on this project

- The benchmark is AA-AgentPerf-Local's default replay, unmodified: 65,536-token context, one sequence, exact output
  lengths, standard sampling. A run that changes any of these is a different result and does not go on the page.
- The page is AA's Completion Time by Model and System chart with the RTX 4090 as one more column, laid out as theirs
  is (models down, systems across, green for faster), and under it the RTX 4090 Qwen3.8 27B inference leaderboard, our setups ranked on the same workload (user,
  11-13). Only setups that keep the public weights are ranked: extreme quantization is always faster, and that is not
  what the leaderboard is for. Spec-Bench decode speeds stay in the decode study's write-up; AA's workload is the one
  that reflects agent use (user, 11-13). In the chart the
  RTX 4090 follows AA's settings and one of AA's own serving configurations, like every other column.
  AA's side comes from `bench/aa_snapshot.json`, refreshed with `python3 tools/fetch_aa.py`; the RTX 4090 column shows
  its fastest setup.
- GPU work runs on the experiment server through its GPU queue; nothing else of ours on that card.
- No machine details in the repo (paths, host names, user names): they live in the untracked `bench/env.local.sh`.
- After changes: `python3 bench/collect.py --runs RUNS` and `python3 tools/build_site.py`, then look at the page at
  desktop and phone width.
- The models are the three on AA's page; our runs are Qwen3.8 27B, the only one that fits 24 GB. The NInfer engine of
  the decode study (qwen38-4090-decode, a separate repo) goes on the RTX 4090 leaderboard, measured on the same replay
  on the official weights. No weights are changed to make a setup fit: one that cannot hold the 65,536-token context
  is listed as not supported (user, 11-14). The study's re-quantized container does fit with the dense verify head
  (measured 11-19); it stays listed and unranked because its weights are not the public ones.
- The page is figures only (user, 11-13): the two figures, each with a one-line title and a small note; no prose
  sections. Numbers come from the data through `tools/build_site.py`. The page takes zedongpeng.com's theme (its `site.css`, fonts and header;
  see Theme in the home page repo's AGENTS.md); `site/leaderboard.css` holds only this page's parts, such as the table
  card with our 4090 row tinted, and sets no fonts or base colors. Light only: no dark rules, no theme script. CSS classes start with `qwen38-`.
- A push to `main` builds and publishes the page through `.github/workflows/site.yml`, at
  zedongpeng.com/qwen38-4090-inference/. Paths in the page are relative.
