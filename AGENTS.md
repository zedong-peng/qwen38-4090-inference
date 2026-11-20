# Working on this project

- The benchmark is AA-AgentPerf-Local's default replay, unmodified: 65,536-token context, one sequence, exact output
  lengths, standard sampling. A run that changes any of these is a different result and is not published.
- Where it is published (user, 11-20: merge the leaderboard into the decode study's post, fill in our data, remove what
  is redundant): two figures in the "An agent workload" section of the post
  zedong-peng.github.io/_posts/2026-10-06-qwen38-4090-decode.md. First AA's Completion Time by Model and System chart
  with the RTX 4090 as one more column (models down, systems across, darker for faster, fastest system first), the
  RTX 4090 column showing our fastest ranked setup, not AA's configuration (user, 11-20: "保持图里用我们的数据"); then every RTX 4090 setup we ran, ranked. Only setups that keep
  the official weights are ranked: extreme quantization is always faster, and that is not what the ranking is for (user,
  11-13). AA's side comes from `bench/aa_snapshot.json`, refreshed with `python3 tools/fetch_aa.py`.
- GPU work runs on the experiment server through its GPU queue; nothing else of ours on that card.
- No machine details in the repo (paths, host names, user names): they live in the untracked `bench/env.local.sh`.
- After changes: `python3 bench/collect.py --runs RUNS` (full copies of the run trees: a slim copy loses the launch
  commands), `python3 tools/build_site.py --post PATH/TO/the post`, build the home page repo, and look at the section at
  desktop and phone width before pushing both repos.
- The models are the three on AA's page; our runs are Qwen3.8 27B, the only one that fits 24 GB. The NInfer engine of
  the decode study (qwen38-4090-decode, a separate repo) goes on the RTX 4090 leaderboard, measured on the same replay
  on the official weights. No weights are changed to make a setup fit: one that cannot hold the 65,536-token context
  is listed as not supported (user, 11-14). The study's re-quantized container does fit with the dense verify head
  (measured 11-19); it is listed with its numbers and unranked.
- Each figure has a one-line title and a short caption; numbers come from the data through `tools/build_site.py`. The
  figures use the post's classes (`q-`) and styles, which take their colors from zedongpeng.com's variables.
- A push to `main` publishes, through `.github/workflows/site.yml`, only a page at zedongpeng.com/qwen38-4090-inference/
  that forwards to the post.
