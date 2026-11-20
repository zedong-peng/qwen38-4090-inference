# Qwen3.8 27B on an RTX 4090

Artificial Analysis's [laptops & workstations](https://artificialanalysis.ai/hardware-inference-stack/laptops-workstations)
table, all three models, with one RTX 4090 added. The workload is the
[AA-AgentPerf-Local](https://github.com/ArtificialAnalysis/aa-agentperf-local) default replay, run with their tool,
unmodified. Their numbers are theirs (`bench/aa_snapshot.json`); the 4090 is ours, measured on Qwen3.8 27B.

The results are part of the decode study's post,
[zedongpeng.com/blog/2026/qwen38-4090-decode](https://zedongpeng.com/blog/2026/qwen38-4090-decode/#an-agent-workload):
AA's chart with the RTX 4090 added, and every RTX 4090 setup below. This repo holds the runs and the data behind them.

| RTX 4090 setup | how it runs |
|---|---|
| llama.cpp b11026, Q4_K_M, MTP 2 | `agentperf-local managed-run` of AA's recipe `qwen38-27b-q4-k-m-mtp`, the one behind their RTX 5090 result |
| llama.cpp b11236, UD-Q4_K_M, DFlash 7 | `managed-run` of AA's recipe `qwen38-27b-ud-q4-k-m-dflash-rtx-spark`, behind their RTX Spark result |
| vLLM 0.27.1, W4A16 AutoRound, MTP 3 | vLLM started with the flags AA's tool gives vLLM, then `agentperf-local run` against it |
| NInfer (decode study build), official NInfer v3 container, DFlash2 verify tree 15 | `ninfer-serve` of [qwen38-4090-decode](https://github.com/zedong-peng/qwen38-4090-decode) with its engine knobs that keep the dense verify head and `NINFER_ANCHOR_BEFORE_LAST_USER=1` (the turn checkpoint sits before a trailing user message, which three of the tasks replace every turn; 15.8 min without it), then `agentperf-local run` against it |
| the same, on the study's re-quantized container | the same flags plus its weight knobs; listed, not ranked: only setups on the official weights are ranked |

Each setup gets an `aa-mini-v1` check and three full replays, and the table ranks the medians. The chart's RTX 4090
column is the fastest ranked setup. AA's tool also judged the other two models on their page: on 24 GB neither Qwen3.6
35B A3B nor Ling 3.0 Flash fits.

| path | contents |
|---|---|
| `bench/run_4090.sh` | the runs: `bash bench/run_4090.sh GPU [REPS] [SETUPS]` (paths in an untracked `bench/env.local.sh`, see `bench/env.example.sh`) |
| `bench/methods.json` | the 4090 setups, and the models that do not fit the card |
| `bench/aa_snapshot.json`, `tools/fetch_aa.py` | AA's page data as published (systems, models, runs with launch commands); the script refreshes it |
| `bench/collect.py` | run tree → `results/results.json` (each replay, its launch command) and `results/samples.json` (per-turn timings) |
| `tools/build_site.py` | `--post PATH` renders the two figures into the post (between its `<!-- BEGIN qwen38 heat/board -->` markers); without it, the page in `dist/` that forwards this repo's old address to the post, which `.github/workflows/site.yml` publishes |

The earlier leaderboard (2026-10-02, short prompts, 4K context) is at tag `v1-short-prompts`.
