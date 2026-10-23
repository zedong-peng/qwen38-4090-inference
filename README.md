# Qwen3.8 27B on one RTX 4090

How long one 24 GB RTX 4090 takes to serve a recorded coding agent with Qwen3.8 27B, across inference engines, weights
and speculative decoding. The workload is the [AA-AgentPerf-Local](https://github.com/ArtificialAnalysis/aa-agentperf-local)
default replay, the one Artificial Analysis uses on its
[laptops & workstations](https://artificialanalysis.ai/hardware-inference-stack/laptops-workstations) page, so their
systems share the axis.

Page: [zedongpeng.com/benchmarks/qwen38-4090/](https://zedongpeng.com/benchmarks/qwen38-4090/)

| path | contents |
|---|---|
| `bench/methods.sh` | how each method's server is launched (65,536-token context, one sequence, its own prefix cache) |
| `bench/run_method.sh` | one method end to end: start the server, an `aa-mini-v1` check, the full replay, GPU telemetry, stop |
| `bench/methods.json` | what each method is: engine, weights, drafting, KV cache |
| `bench/references.json` | Artificial Analysis's published runs of the same replay (other systems) |
| `bench/collect.py` | run tree → `results/results.json` and `results/samples.json` (per-turn timings) |
| `site/` | the page: `index.html`, `leaderboard.css`, `leaderboard.js` |
| `tools/build_site.py` | static build into `dist/` (what the personal site deploys) |

Methods without a finished replay show as "not measured yet".

## Run a method

On the GPU server, with the engines and models in place (paths in an untracked `bench/env.local.sh`, see
`bench/env.example.sh`) and `agentperf-local` 0.3.4 in `$Q38_WORK/envs/aa`:

```bash
bash bench/run_method.sh lcpp-q4km-mtp2 1      # METHOD GPU [REPS]
python3 bench/collect.py --runs $Q38_WORK/runs  # refresh results/
```

## Preview the page

```bash
python3 tools/build_site.py
python3 -m http.server 8080 --directory dist --bind 127.0.0.1   # /benchmarks/qwen38-4090/
```

The 2026-10-02 short-prompt leaderboard (34–77-token prompts, 4K context) is tagged `v1-short-prompts`; its files
(`site/_pages`, `site/assets`, `qa/`, `archives/`, `docs/`, `research/`) are no longer used by the build.
