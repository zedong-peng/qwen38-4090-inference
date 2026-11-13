# Working on this project

- The benchmark is AA-AgentPerf-Local's default replay, unmodified: 65,536-token context, one sequence, exact output
  lengths, standard sampling. A run that changes any of these is a different result and does not go on the page.
- The page is AA's table plus the RTX 4090, kept as small as theirs: one table, a few setups that people actually use.
- GPU work runs on the experiment server through its GPU queue; nothing else of ours on that card.
- No machine details in the repo (paths, host names, user names): they live in the untracked `bench/env.local.sh`.
- After changes: `python3 bench/collect.py --runs RUNS` and `python3 tools/build_site.py`, then look at the page at
  desktop and phone width in both themes.
- Only Qwen3.8 27B (user, 10-24). The NInfer engine is a separate repo and not on this page.
- The page is a short post around the table: a finding-led hero, two findings (memory decides whether it runs,
  bandwidth how fast; an agent reads far more than it writes), and a Method note. Numbers in the prose come from the
  data through `tools/build_site.py`. Style matches Velodrome's (Anthropic-like): the table on a white card, our 4090
  rows tinted clay. CSS classes start with `qwen38-`.
- A push to `main` builds and publishes the page through `.github/workflows/site.yml`, at
  zedongpeng.com/qwen38-4090-inference/. Paths in the page are relative.
