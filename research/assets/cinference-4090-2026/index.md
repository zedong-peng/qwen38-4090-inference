---
title: "Cinference RTX 4090：固定 K7 与采样 MTP"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# Cinference RTX 4090：固定 K7 与采样 MTP

来源：[官方/作者仓库](https://github.com/jram4/ninfer-4090/tree/70ebb1290dc7abe246c20696a24d21f77faee8d4)；固定 commit `70ebb1290dc7abe246c20696a24d21f77faee8d4`，分支 `main`。2026-10-01检索 stars **11**、最近push `2026-09-24T17:47:19Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/jram4/ninfer-4090/blob/70ebb1290dc7abe246c20696a24d21f77faee8d4/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

`jram4/ninfer-4090` 在 stock Qwen3.8-27B 上有 Linux RTX 4090 的公开任务矩阵、原始结果与构建脚本，是高 acceptance 的代码/JSON 任务首要候选。作者选择固定 MTP K7、K8V4 cache、Q4 draft head，不能把它的 200+ tok/s 推广到所有请求。

2026-09-24 当前分支 stock greedy 矩阵：code **209.2 tok/s**、structured JSON **221.6**、prose **88.8**、long generation **97.3**；同一当前矩阵 reasoning **179.9**、8K needle recall **275.5**。K0 无 draft 常规长输出约 **52.7**。旧 K3 prose 98.2 比 K7 的 87.7 更快，因此 K7 不是所有任务最优。作者原始结果在 `results/rtx4090-20260923/` 和 `results/rtx4090-20260924-sampled/`，矩阵脚本是 `tools/bench/cinf_matrix.py`。

greedy 矩阵每次 cold prefill，`--greedy --no-prefix-reuse`，thinking 关闭，个别 reasoning 例外。TTFT 随 prompt 长度上升：8,192 tokens 约 3.6s、130,421 tokens 77.7s、189,004 tokens 127.4s。代码任务生成的 unit tests 在包括 K0 的各模式都失败；JSON/needle 的检查不能替代代码正确率评估。

另一个温度 1 的 Claude Code replay 在 **abliterated 模型**上由 127.4 提升到 141.6 tok/s，含 prefix reuse、seed 42、32 条私人请求。公开的是聚合统计，原始请求体没有发布，故它不是可完全公开复现的 stock-model 速度/质量结果。

## 可执行入口与 CUDA 条件

README 验证环境为 Linux、CUDA 13.x、CMake>=3.28、Ninja、sm89。固定源码的 CMake 没有硬性要求 CUDA13 的版本判断；这只是源码检查，不能代替在 CUDA12.8 上构建/运行的实测。

```bash
cmake -S . -B build-sm89 -G Ninja -DCMAKE_BUILD_TYPE=Release   -DCMAKE_CUDA_ARCHITECTURES=89 -DNINFER_BUILD_APPS=ON -DBUILD_TESTING=OFF
cmake --build build-sm89 --target ninfer-serve
./build-sm89/apps/ninfer-serve models/model.ninfer   --host 127.0.0.1 --max-context 4096 --kv-capacity 4096 --kv-dtype k8v4   --max-concurrency 1 --prefill-chunk 1024 --spec mtp --draft-tokens 7 --lm-head-draft
```

上面把 README 的 production 188416 窗口缩为共享卡初测 4096，其余具体 flags 与 API 见 `docs/cli.md`、`docs/serving.md`。升级 v2→v3 的 `tools/upgrade_ninfer_v2_to_v3.py` 复制量化权重不重新量化；header 的随机 identity bytes 会使整体文件 SHA 改变，须单独验证 payload。公开最高 code/JSON 值仍是作者测量，本文没有执行 GPU 测试。


## 证据范围与关系

选择性检查：`README.md`, `CMakeLists.txt`, `tools/upgrade_ninfer_v2_to_v3.py`, `tools/bench/cinf_matrix.py`, `results/rtx4090-20260924-sampled/greedy-k7-summary.json`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
