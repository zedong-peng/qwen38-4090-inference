---
title: "BeeLlama：KVarN 与精确 tail 的低比特 KV 工程"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# BeeLlama：KVarN 与精确 tail 的低比特 KV 工程

来源：[官方/作者仓库](https://github.com/Anbeeld/beellama.cpp/tree/58a1629274d8d74ea5a6acf34f30fb5946c2422b)；固定 commit `58a1629274d8d74ea5a6acf34f30fb5946c2422b`，分支 `main`。2026-10-01检索 stars **1141**、最近push `2026-09-30T11:00:40Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/Anbeeld/beellama.cpp/blob/58a1629274d8d74ea5a6acf34f30fb5946c2422b/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

BeeLlama（Anbeeld/beellama.cpp）是近期有关注的 llama.cpp 分支（1141 stars），重点是 KVarN 低比特 KV 和长上下文稳定性。作者最近加入 2–8-bit cache、至少128 token 的精确 tail、adaptive draft length、loop protection 和较小 draft ubatch。适合把 context 容量与 generation 质量一起验证。

作者 [KVarN 实现与 benchmark 博文](https://anbeeld.com/articles/kvarn-kv-cache-implementation-and-benchmarks) 与固定 README 提供实现及对照；主要公开表使用 **Qwen3.6-27B Q5_K_S、RTX3090、WikiText teacher-forced**。这些不是 Qwen3.8-27B RTX4090 的自动回归代码代理验证，故不从旧表抽取本场景“最快”数字。网上约50tok/s/16GB卡或60tok/s/4090长窗口报告也缺少同一模型与完整条件，不纳入受控速度表。

KVarN 把 key/value 旋转与方差分配结合；低比特路径的主要收益常是 KV 内存容量，decode 是否更快取决于 dequant/attention kernel。精确 tail 长度 128、1024 或 reference 部分 tail 不同，也会改变速度和质量。不能只按“2-bit”标签比较 PPL。作者 blog 原始 HTML 下载遭 HTTP403，保留了浏览工具原文提取与失败记录，避免标成已下载 HTML。

Linux 可按 README 使用 CUDA build：

```bash
cmake -S . -B build -DGGML_CUDA=ON -DGGML_CUDA_FA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --target llama-server
```

release 同时提供 CUDA12.4 与13.3，g4090 当前 driver570/CUDA12.8 应选兼容的12.x方案。新 DFlash2 支持仍需按具体 commit、draft architecture 和 model card 检验。本文归档源码/作者文档，没有运行低比特 KV 的质量或 GPU 速度测试。


## 证据范围与关系

选择性检查：`README.md`, `CMakeLists.txt`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
