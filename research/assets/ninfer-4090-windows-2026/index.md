---
title: "NInfer Windows 4090：INT8 prefill、MTP 与 ngram"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# NInfer Windows 4090：INT8 prefill、MTP 与 ngram

来源：[官方/作者仓库](https://github.com/JGamboa/ninfer-4090-windows/tree/e7d309e31260052b10e0500433661b03dcdc6e0e)；固定 commit `e7d309e31260052b10e0500433661b03dcdc6e0e`，分支 `main`。2026-10-01检索 stars **10**、最近push `2026-09-27T19:51:30Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/JGamboa/ninfer-4090-windows/blob/e7d309e31260052b10e0500433661b03dcdc6e0e/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

`JGamboa/ninfer-4090-windows` 提供 exact RTX4090 的原生 Windows 代码/命令/结果，虽然只有10 stars，也因公开可复现与 prefill kernel 改进值得归档。它不是已验证的 Linux g4090 部署。

README 当前环境：RTX4090 stock、i9-13900K、Windows11、driver595.97/CUDA13.4，2026-09-27 headless；显示输出可造成15–18%的测量变化。stock Qwen3.8 Q4/Q5 的 `a8.ninfer` 量化权重与官方相同，prefill 激活额外按 token/64-channel 做INT8，decode路径未改。当前无 draft **54.7 tok/s**，MTP3 mixed thinking-off **120**、code **149**；DFlash2 K12 code **211**；MTP+ngram 的 copy/edit **289**，Claude Code 7–11K edit **258**。最后两项不是开放 prose 的通用速度。

prefill 变化更显著：官方 pp512/pp2048 2536/2762 tok/s，INT8 路径 5339/5790；64K cold TTFT 14.8s、128K 41.8s。作者同 session 与 llama.cpp `a894dae`、Q4_K_M15.65GiB/MTP/Q8KV 对照：pp2048 2676→5124、AR43.0→48.1、MTP87.1→106.4。paired warm/thermal 数字小于 idle headless headline，二者应分列。

ngram 对 copy/edit 接受率很高，prose 没有同样收益，DFlash server prose99/MTP85 tok/s。45题小检查44–45/45、PPL4.8007 vs4.7944只能作为小规模 sanity check。Bonsai2 ternary 的532tok/s是另一个 checkpoint，不算原始 Qwen3.8-27B。

## 部署范围

按固定 README 的 MSVC/CMake 和模型卡运行；a8 artifact、draft模型和 benchmark body 都需 pin。当前 CUDA13.4 Windows build 不能直接复制到 driver570 的 Linux 服务；要复用 INT8 prefill 需验证相应 Linux分支内核，而不是把 Windows exe 当本轮部署选项。HF model API和固定 revision 模型卡均已缓存，GPU测试未运行。


## 证据范围与关系

选择性检查：`README.md`, `CMakeLists.txt`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
