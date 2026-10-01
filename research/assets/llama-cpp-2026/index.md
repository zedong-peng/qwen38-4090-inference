---
title: "llama.cpp：Qwen3.8 4090 的 GGUF 与 CUDA baseline"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# llama.cpp：Qwen3.8 4090 的 GGUF 与 CUDA baseline

来源：[官方/作者仓库](https://github.com/ggml-org/llama.cpp/tree/a4d880fd5c7f88713ded6db9f0111893bd78afa6)；固定 commit `a4d880fd5c7f88713ded6db9f0111893bd78afa6`，分支 `master`。2026-10-01检索 stars **129984**、最近push `2026-09-30T20:20:08Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/ggml-org/llama.cpp/blob/a4d880fd5c7f88713ded6db9f0111893bd78afa6/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

llama.cpp 是本轮最成熟的 GGUF/CUDA baseline（129984 stars），既提供 loader、C++ CUDA kernels、OpenAI server，也能按相同 GGUF 固定无 draft 与 MTP。速度更快的新分支仍需要与它在同机/同任务上比较。

Qwen3.8-27B 的架构标识仍是 `Qwen3_5ForConditionalGeneration`；本次固定源码 `src/models/qwen35.cpp` 明确加载 fullattention、GDN与 `n_layer_nextn`/MTP head，并构建 `graph_mtp`。当前 `docs/speculative.md` 列出 `draft-mtp`、`draft-dflash`、`draft-dspark`、`draft-eagle3` 与多种 ngram，激活head仍依赖具体 GGUF包含MTP权重和该版本flags。

直接4090作者对照已有两组，但不是统一榜单：sergiuszm分支的UD-Q4_K_XL/Q8KV、浅层无draft约45.9、MTP code118.8；JGamboa同sessionWindows Q4_K_M/Q8KV无draft43.0、MTP87.1。任务、quant、commit、OS与功耗不同，不能取其中最大值称该官方fixedcommit已实测。g4090 本地实测应单独记录 [index](../g4090-qwen38-benchmark-2026/index.md)。

## 固定代码复现入口

```bash
cmake -S . -B build-sm89 -DGGML_CUDA=ON   -DCMAKE_CUDA_ARCHITECTURES=89 -DCMAKE_BUILD_TYPE=Release
cmake --build build-sm89 --target llama-server llama-bench
```

以 `llama-bench --help`、`llama-server --help` 和固定 `tools/server/README.md` 为准，分别记录 pp/tg 微基准与真实 HTTP generation；两种tokens/s的分母不同。短 context共享卡初测可用 Q4_K_M、全GPUoffload、context4096、concurrency1、FlashAttention，并对照同一个server无draft和 `--spec-type draft-mtp`。cache量化参数必须使用该版本支持的类型，不能把不同fork的cacheflag混用。

模型SHA、MTP是否另文件、实际prompt/outputtokens、cachedtokens、TTFT、prefilltok/s、decode秒数、temperature/thinking、GPU功耗/其他任务需完整留下。本文 archive本身未构建、未执行GPU推理；remote结果由专门experiment页记录。


## 证据范围与关系

选择性检查：`README.md`, `CMakeLists.txt`, `docs/speculative.md`, `tools/server/README.md`, `src/models/qwen35.cpp`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
