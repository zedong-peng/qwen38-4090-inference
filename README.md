# Qwen3.8 27B on an RTX 4090

Artificial Analysis's [laptops & workstations](https://artificialanalysis.ai/hardware-inference-stack/laptops-workstations)
table for Qwen3.8 27B, with one RTX 4090 added. The workload is the
[AA-AgentPerf-Local](https://github.com/ArtificialAnalysis/aa-agentperf-local) default replay, run with their tool,
unmodified. Their numbers are theirs (`bench/references.json`); the 4090 rows are ours.

Page: [zedongpeng.com/benchmarks/qwen38-4090/](https://zedongpeng.com/benchmarks/qwen38-4090/)

| RTX 4090 setup | how it runs |
|---|---|
| llama.cpp b11026, Q4_K_M, MTP 2 | `agentperf-local managed-run` of AA's recipe `qwen38-27b-q4-k-m-mtp`, the one behind their RTX 5090 result |
| llama.cpp b11236, UD-Q4_K_M, DFlash 7 | `managed-run` of AA's recipe `qwen38-27b-ud-q4-k-m-dflash-rtx-spark`, behind their RTX Spark result |
| vLLM 0.27.1, W4A16 AutoRound, MTP 3 | vLLM started with the flags AA's tool gives vLLM, then `agentperf-local run` against it |

Each setup gets an `aa-mini-v1` check and three full replays; the page shows the median. AA's tool also judged the
other two models on their page: on 24 GB neither Qwen3.6 35B A3B nor Ling 3.0 Flash fits.

| path | contents |
|---|---|
| `bench/run_4090.sh` | the runs: `bash bench/run_4090.sh GPU [REPS] [SETUPS]` (paths in an untracked `bench/env.local.sh`, see `bench/env.example.sh`) |
| `bench/methods.json`, `bench/references.json` | the three 4090 setups; AA's published runs of the same replay |
| `bench/collect.py` | run tree → `results/results.json` (each replay, its launch command) and `results/samples.json` (per-turn timings) |
| `site/`, `tools/build_site.py` | the page; the build renders the table as static HTML into `dist/`, which the personal site deploys |

The earlier leaderboard (2026-10-02, short prompts, 4K context) is at tag `v1-short-prompts`.
