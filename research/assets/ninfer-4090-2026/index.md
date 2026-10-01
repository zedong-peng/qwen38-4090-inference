---
title: "NInfer RTX 4090：原始量化模型、MTP 与长上下文"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# NInfer RTX 4090：原始量化模型、MTP 与长上下文

来源：[官方/作者仓库](https://github.com/sergiuszm/ninfer-4090/tree/aeeba414459d5d6989d57d8487c9d7a2f54bddd3)；固定 commit `aeeba414459d5d6989d57d8487c9d7a2f54bddd3`，分支 `rtx4090-port`。2026-10-01检索 stars **179**、最近push `2026-09-23T12:51:56Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/sergiuszm/ninfer-4090/blob/aeeba414459d5d6989d57d8487c9d7a2f54bddd3/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

该分支有直接 RTX 4090 单卡数据、固定模型 revision、构建命令和与 llama.cpp 的同卡对照，适合作为单请求 Linux 部署的第一轮候选。它是 `sergiuszm/ninfer-4090`；不能把 `eriknelson`、`UDPSendToFailed` 和其他同名 fork 的结果合并。

作者用官方 Qwen3.8-27B Q4/Q5 NInfer artifact，约 16.96 GiB，CUDA graph、单请求 greedy、INT8 KV、prefill chunk 1024。README 的短 code MTP3 为 **148.6 tok/s**，混合任务 **106.5 tok/s**，无 speculation **50.5 tok/s**；code draft acceptance 81%，混合仅 48.7%。数字说明输出分布很影响 MTP，不宜把 code 峰值称为通用聊天速度。

README 的长上下文对照使用 llama.cpp b10358、UD-Q4_K_XL 16.68 GiB、Q8 KV、ubatch 1024、batch 4096。无 draft 浅层分别 45.9/50.4 tok/s，128K 深度 33.1/42.1；MTP 的浅层 code 118.8/142.9，128K prose 42.3/77.5。NInfer 默认 E8 cache 的浅层 decode 有约 5.7% 代价。llama.cpp 的 64K/128K prefill 反而稍快，不能只凭 decode 宣称全流程都更快。

## 模型格式与复现入口

旧分支要求 **NInfer v2**。官方 HF `main` 已变成 v3，必须 pin `neroued/Qwen3.8-27B-NInfer` revision `3526913004b1cf552cb57b88d6a5c6f5e4a89a70`。权重文件 18,210,531,328 bytes，SHA-256 `eec39564993d6e9c7d5e383382a760f093465c9d163ec9a1bd6b80199514bf3e`；不要只按文件名缓存。

构建与 server flags 见固定 README；分支移植差异见 `docs/maintainer/port-ledger.md`。作者的完整窗口启动含 `--max-context 262144 --kv-capacity 262144 --prefill-chunk 1024 --kv-dtype rk4v4-e8 --spec mtp --draft-tokens 3 --lm-head-draft --preserve-thinking`。如果共享卡只剩约 19 GiB，先把两个 context 容量都设为 4096，再测无 draft、MTP3；完整窗口要求更多显存。

精确针检索只证明该小规模探针通过，不能证明整个 262K 窗口的通用质量。本文为源码与作者实验证据归档，未执行此仓库的 GPU 测试。


## 证据范围与关系

选择性检查：`README.md`, `docs/maintainer/port-ledger.md`, `CMakeLists.txt`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
