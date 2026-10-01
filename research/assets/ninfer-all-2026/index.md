---
title: "NInfer-all：跨 GPU 原生内核与 Qwen3.8 量化选择"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# NInfer-all：跨 GPU 原生内核与 Qwen3.8 量化选择

来源：[官方/作者仓库](https://github.com/iamwavecut/ninfer-all/tree/f118551fb401de073555807a48c50238e180e3b8)；固定 commit `f118551fb401de073555807a48c50238e180e3b8`，分支 `master`。2026-10-01检索 stars **27**、最近push `2026-09-27T13:11:17Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/iamwavecut/ninfer-all/blob/f118551fb401de073555807a48c50238e180e3b8/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

`iamwavecut/ninfer-all` 汇集 NInfer 各消费卡分支，提供原生 v3、GGUF import、device profile 与 autotune。工程较新、27 stars，吸引力主要来自完整的多 GPU 型号原始表和较明确的 CUDA12.8 支持，而不是社区规模。

`docs/performance/reference-2026-09.md` 在单张 RTX4090、450W、CUDA13.1 作者环境给出 **stock Qwen3.8-27B**：短 chat 为五个 512-token 回答，无 draft **54.8 tok/s**；MTP3 **109.0**；DFlash2 K5 **138.1**（rk8v4，167936窗口、23.5GiB）。rk4v4 的 DFlash2 K5 为 137.8（245760窗口）；131K 深度 rk8v4 DFlash2 降至 90.9，不能把浅层速度当长上下文性能。冷 131K TTFT 约 62.7s。

C8 的 MTP **442.2 tok/s 是 aggregate**，不是单请求响应速度。Bonsai 2 的 250+ tok/s 属于不同 ternary checkpoint，不能作为 stock Qwen3.8 27B 的宣传数字。`rk4v4` 405K needle 检索通过只是探针，同时超出模型原生 262144 窗口。

另有 [WaveCut GSQ-RCO IQ3_S 模型](https://huggingface.co/WaveCut/Qwen3.8-27B-GSQ-RCO-IQ3_S-NInfer-v3)：3.5bpw、weights 约 10.95GiB、整个 artifact 约 13.99GiB；模型卡同卡 MTP 146.4 对官方 109.3 tok/s，DFlash2 K5 169.4 对官方141.3。模型卡还提供5090上的EvalScope单次采样任务分数，未形成4090同环境完整质量复现。它改变了权重量化，值得做质量+速度联合对照，但不能算同一权重的纯 kernel 加速。模型卡、API revision 与 SHA 已缓存。

## 构建与格式

`CMakeLists.txt:195` 明确 minimum CUDA **12.8**；`CMAKE_CUDA_ARCHITECTURES=89` 使用 Ada 路径，不能启用仅 sm120a 的选项。最小编译建议：

```bash
cmake -S . -B build-sm89 -G Ninja -DCMAKE_BUILD_TYPE=Release   -DCMAKE_CUDA_ARCHITECTURES=89 -DBUILD_TESTING=OFF
cmake --build build-sm89 --target ninfer-serve
```

可接收原生 v3 或用仓库工具将官方 v2 升级；GGUF import 有 15 种 quant block，避免未经说明的重量化。20–40秒 autotune 的首次启动成本应从 warm steady-state decode 单列。本文没有运行构建、推理或量化质量测试。


## 证据范围与关系

选择性检查：`README.md`, `CMakeLists.txt`, `docs/performance/reference-2026-09.md`, `tools/upgrade_ninfer_v2_to_v3.py`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
