# Qwen3.8-27B on one RTX 4090: benchmark data

This dataset compares measured deployment configurations for Qwen3.8-27B on one unmodified 24 GB RTX 4090. A configuration means the runtime and commit, model artifact and quantization, KV-cache format, decoding method, and launch settings together. It is not a hardware-independent ranking of engine names.

The current results are an initial speed experiment, not a complete survey or a validated quality leaderboard. No result establishes the fastest possible deployment across all available software. Unsloth is represented by the GGUF artifacts used with llama.cpp; its separate Python inference path, stock vLLM, and stock SGLang were not measured here.

## Existing benchmarks and directories

Checked on **2026-10-02**. Local inference leaderboards and community databases already exist; the remaining gap is a controlled RTX 4090 comparison across the configurations of interest.

| Project                                                                                                                    | Relevant coverage                                                                                                                                                                                                                                   | Relationship to this dataset                                                                                                                                                                                           |
| -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Artificial Analysis: Laptops & Workstations](https://artificialanalysis.ai/hardware-inference-stack/laptops-workstations) | Includes Qwen3.8-27B. The initial published hardware is RTX 5090, DGX Spark, Ryzen AI Halo, and MacBook Pro M5 Pro; **zero RTX 4090 results** were found.                                                                                           | Its [AA-AgentPerf-Local runner](https://github.com/ArtificialAnalysis/aa-agentperf-local) provides a useful common agent workload, but the measurements here do not follow that protocol.                              |
| [Inference Atlas](https://0xbakeer.github.io/inference-atlas/)                                                             | The [repository](https://github.com/0xBakeer/inference-atlas/tree/b93f6281f150788d53c05600725b63f8febddd1e/results) contains 569 result files, including 127 for Qwen3.8-27B; **zero RTX 4090 results**. Observed hardware is DGX Spark and M2 Max. | A community configuration map with measured data and a [contribution workflow](https://github.com/0xBakeer/inference-atlas/blob/main/CONTRIBUTING.md). Its README status paragraph predates the populated result tree. |
| [Qwen Local-Run Directory](https://local.host.impossibuild.ai/)                                                            | Contains sourced Qwen3.8-27B / RTX 4090 recipes alongside other engines and hardware.                                                                                                                                                               | A [provenance-tagged recipe directory](https://github.com/shuenrui/qwen-local-run), not a comparison under one measurement protocol. Its speed sorting is a discovery aid.                                             |
| [Poor Paul's Benchmark](https://poorpaul.dev/)                                                                             | The checked [site snapshot](https://poorpaul.dev/data/results.json) contains 49,465 rows; the `model_base` and `gpu_name` fields contain no Qwen3.8 or RTX 4090 entries.                                                                            | An existing [GGUF benchmark and shared dataset](https://github.com/paulplee/poor-pauls-benchmark), with throughput, latency, memory, and quality measurements.                                                         |

These counts describe the checked snapshots, not permanent coverage guarantees. A registry entry for a GPU is not a measurement on that GPU.

## Measurement contract

All configurations ran sequentially on **one physical RTX 4090**, inside a shared four-GPU workstation. This was not four-card tensor parallelism. Other workloads on the workstation could affect power, temperature, CPU scheduling, and available memory; the experiment did not provide exclusive access to the entire machine.

| Field               | Current experiment                                                                                                                        |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Model               | Qwen3.8-27B; different quantized artifacts for different runtimes                                                                         |
| Request concurrency | 1                                                                                                                                         |
| Configured context  | 4,096 tokens                                                                                                                              |
| Output budget       | At most 512 tokens; natural stops can produce fewer                                                                                       |
| Sampling            | Greedy, temperature 0; fixed seed; thinking disabled; presence and frequency penalties 0                                                  |
| Workloads           | Structured JSON generation, Python code generation, English prose                                                                         |
| Cache condition     | Cold prompt prefix for each measured request; model loading and explicit warmups excluded; first-generation shape initialization retained |
| Repetitions         | Three measured repetitions per configuration and workload                                                                                 |
| HTTP measurements   | 81 requests: 9 configurations × 3 workloads × 3 repetitions                                                                               |
| Native measurements | 27 requests: 3 ExLlamaV3 configurations × 3 workloads × 3 repetitions                                                                     |

The nine HTTP configurations are Cinference with no speculation / MTP3 / MTP7, the tested NInfer branch with no speculation / MTP3 / MTP5, and llama.cpp with no speculation / MTP3 / MTP7. The three native configurations are ExLlamaV3 autoregressive decoding, MTP4, and DFlash2 K7. MTP and DFlash are decoding methods, rather than additional independently measured engines.

Model weights, output-head precision, and KV-cache formats differ: NInfer-family artifacts, Unsloth UD-Q4_K_M GGUF, and EXL3 4 bpw are separate deployment choices. These measurements compare their resulting configurations; they do not isolate runtime speed at identical numerical precision.

## Metrics and output checks

The measured inputs contain **34–77 tokens**, including the rendered chat template. The configured capacity is 4,096 tokens;
this is a short-prompt experiment, not a 4K-prompt-depth benchmark. Input and output counts are retained for every sample.

- **HTTP server decode throughput:** `(output_tokens - 1) / server_decode_seconds`. The server assigns the first output token to its prompt-processing phase.
- **HTTP end-to-end throughput:** `output_tokens / client_request_seconds`, including prompt processing and HTTP overhead.
- **ExLlamaV3 native throughput:** `output_tokens / native_generation_seconds`. This uses the native generator's timing boundary and includes the first generated token; it is not the HTTP metric above. Native results must stay in a separate comparison group.
- **Reported statistic:** median of three repetitions for each workload and configuration. Short, repetitive, or highly predictable output can favor speculative decoding.
- **TTFT:** not measured in this experiment. Server prompt time must not be relabeled as client-observed time to first token.

The code and prose requests reached the output limit. The recorded fenced-code syntax check failed, and prose did not complete the requested length. JSON parsing checks establish output structure only. This experiment did not measure semantic accuracy, runnable code correctness, or a quality score. Speed results must therefore not be presented as completed-task performance.

## Reproduction files

[results.json](results.json) records the runtime commits, model revisions, configuration metadata, and aggregated results. [samples.json](samples.json) preserves the individual measurements used for those aggregates.

[benchmark_http.py](benchmark_http.py) is a standard-library runner for an already configured HTTP server. Run it only after matching the recorded runtime, weights, launch settings, and disabled prefix cache:

```bash
python3 benchmark_http.py --base-url http://127.0.0.1:8080 --engine llama \
  --label llama-udq4-k7 --gpu 0 --out results --reps 3 --max-tokens 512
```

[benchmark_exl3.py](benchmark_exl3.py) runs native ExLlamaV3 measurements in a fresh process per request. Use an environment with the recorded ExLlamaV3 dependencies, and replace the paths below with the pinned target, draft, and source checkout. MTP4 and DFlash2 K7 are separate configurations:

```bash
python3 benchmark_exl3.py --mode ar --target PATH_TO_TARGET --repo EXL3_CLONE \
  --gpu 0 --out results/ar --draft-tokens 0 --context 4096
python3 benchmark_exl3.py --mode mtp --target PATH_TO_TARGET --repo EXL3_CLONE \
  --gpu 0 --out results/mtp --draft-tokens 4 --context 4096
python3 benchmark_exl3.py --mode dflash2 --target PATH_TO_TARGET --draft PATH_TO_DRAFT \
  --repo EXL3_CLONE --gpu 0 --out results/dflash2 --draft-tokens 7 --context 4096
```

These newly added runner copies have not been executed to produce new measurements. [export_results.py](export_results.py) only recomputes the public JSON files from the archived evidence, on CPU, without starting inference:

```bash
python3 export_results.py PATH_TO_BENCHMARK_ARCHIVE --output OUTPUT_DIRECTORY
```

## Compatibility with AA-AgentPerf-Local

The [AA announcement](https://artificialanalysis.ai/articles/aa-agentperf-local) and [current runner documentation](https://github.com/ArtificialAnalysis/aa-agentperf-local/blob/main/README.md) define a different workload: eight recorded agent tasks, 168 turns, a full 65,536-token context at concurrency one, growing conversation history, and recorded output-token targets. Its comparable `exact` policy requires the server to honor `ignore_eos`; prefix reuse occurs within an isolated replay. The default sampling also differs from the greedy experiment here.

The existing 4K, short-output measurements cannot be converted into AA-compatible results by renaming fields. A future AA comparison requires new measurements under its full contract. The mini replay and reduced-context runs are installation checks or separate result groups, not substitutes for the full replay.

[AA submission tools](https://github.com/ArtificialAnalysis/aa-agentperf-local/blob/main/docs/SUBMITTING.md) are available, but **uploading a result does not imply acceptance onto a public leaderboard**. Attached-server metadata currently names llama.cpp, vLLM, SGLang, and Splash; other engines need an accurate supported integration. NVIDIA submissions require power telemetry, and multiple-accelerator machines require an explicit device selection. This dataset has not been submitted to an external service.

## Other published RTX 4090 measurements

The following are community reports, not configurations reproduced in this experiment. Their figures belong to their own workloads and must not be inserted into the same measured ranking.

- [sidnaZ: Qwen3.8-27B / RTX 4090 release results](https://github.com/sidnaZ/qwen38-27b-rtx4090/blob/main/RELEASE.md): reports 237.9 tok/s sustained code decoding with a customized vLLM / AutoRound W4A16 / DFlash2 K7 / lookup configuration, native Linux, 450 W, and a 65K context. Its [checksum-pinned workloads](https://github.com/sidnaZ/qwen38-27b-rtx4090/blob/main/benchmarks/coding_workloads.json) differ from ours. Batch aggregate throughput and context-copy speed are separate metrics.
- [kuotunyu: speculative decoding report](https://github.com/kuotunyu/qwen38-speculative-decoding-benchmark/blob/main/QWEN38_REPORT.md): single RTX 4090 under WSL2, pinned llama.cpp, bartowski Q4_K_M, and Q8 KV. Its main matrix covers four tasks, 16 prompts, and three epochs at 8K; native MTP reports 104.01 tok/s for code and 104.32 tok/s for JSON. It publishes raw samples, TTFT, and paired comparisons, with separate 16K / 32K feasibility probes.

## Adding useful evidence

A new result needs the exact hardware and device count, power setting and load conditions, runtime commit and build environment, model revision and artifact hashes, weight and KV-cache quantization, full launch flags, speculation settings, context, concurrency, sampling, and cache policy. Keep the prompts, generated outputs, tokenizer and token-count rules, metric formulas, warmups, repetitions, raw timing samples, and failures. Report structural checks separately from semantic or functional quality checks. Unmeasured fields stay absent or explicitly unavailable.

Only compare results within a stated common protocol. Preserve community reports as attributed references until independently reproduced. [AA-AgentPerf-Local](https://github.com/ArtificialAnalysis/aa-agentperf-local) and [Inference Atlas](https://github.com/0xBakeer/inference-atlas/blob/main/CONTRIBUTING.md) are existing places to contribute compatible evidence; this topic page can complement them with a focused RTX 4090 view and reproducible deployment instructions.
