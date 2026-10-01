---
title: "ik_llama.cpp：IQK/Trellis、量化 KV 与多类草稿"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# ik_llama.cpp：IQK/Trellis、量化 KV 与多类草稿

来源：[官方/作者仓库](https://github.com/ikawrakow/ik_llama.cpp/tree/32cddbfcefed93896a39c64e7c38c119de8682e6)；固定 commit `32cddbfcefed93896a39c64e7c38c119de8682e6`，分支 `main`。2026-10-01检索 stars **3270**、最近push `2026-09-30T05:16:35Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/ikawrakow/ik_llama.cpp/blob/32cddbfcefed93896a39c64e7c38c119de8682e6/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

ik_llama.cpp 是关注度较高的 llama.cpp 性能分支（检索时 3270 stars），值得保留作 GGUF 复现实验的进阶对照。当前 README 明确列出 **Qwen3.8 MTP**（PR2369）、DFlash（PR1970）、DSpark（PR2280），以及 suffix/ngram、Hadamard KV、CUDA graph splitting、IQK/Trellis 格式。

可用量化来源包括 [ubergarm/Qwen3.8-27B-GGUF](https://huggingface.co/ubergarm/Qwen3.8-27B-GGUF) 的 MTP-IQ4_KS。量化格式、MTP 是否内嵌、cache 类型需要与 baseline 同时记录；更小 weight/不同 head precision 得到更快 decode，不能直接归为同权重 engine 胜出。

本次检索没有找到条件完整、可直接引用的该固定版本 **stock Qwen3.8-27B + 单 RTX4090** 控制实验速度。仓库不同模型的 CUDA 优化数字、Artificial Analysis/社区的3090启动命令，不移植为本场景 token/s。其价值是活跃的专门 kernel、公开实现和丰富的 GGUF 选择，不是已经证明的4090最快结果。

构建和 CLI 路径见固定 README/CMake：从 CUDA Release `GGML_CUDA=ON`、sm89 开始，先用同一个 GGUF 运行无 speculation，再激活该版本 MTP/DFlash flags，以 `--help` 为准；不能把官方 llama.cpp 的最新 flags 原样套到历史 fork。本文仅检查列出的文档与接口，没有执行构建或 GPU 测试。


## 证据范围与关系

选择性检查：`README.md`, `CMakeLists.txt`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
