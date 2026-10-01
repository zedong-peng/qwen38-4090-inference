---
title: 'FlashAttention-2 — FlashAttention-2: Faster Attention with Better Parallelism
  and Work Partitioning'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# FlashAttention-2

## Paper Metadata

FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning

- Authors：Dao, Tri
- 发表/版本：本次证据版本为 arXiv 2023 v1；后续 ICLR 2024 发表信息未独立复核。
- arXiv：[2307.08691v1](https://arxiv.org/abs/2307.08691v1)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2307.08691v1](https://arxiv.org/pdf/2307.08691v1)
- [TeX 原始归档](https://arxiv.org/src/2307.08691v1)；[解压源码](https://arxiv.org/src/2307.08691v1)
- [arXiv 元数据快照](https://arxiv.org/abs/2307.08691v1)
- 共享 FlashAttention 官方仓库缓存 (original local cache)；commit 见 FlashAttention metadata。

## Problem and Main Idea

FlashAttention 已降低 HBM IO，但 thread blocks/warps 分工不佳，长序列小 batch 可能 occupancy 不足，warp 间共享内存通信仍昂贵。FA2 优化算子内部并行与非矩阵乘开销。

## Method

`src/algo.tex`：online softmax 累计未最终归一化的输出，末尾再归一化，反向只需 logsumexp。前向按 Q 行块沿 sequence 维并行，多 thread blocks 可处理一个 head；warp 内采用 split-Q、共享 K/V，避免 split-K 方案的跨 warp 输出归约。反向仍需处理 dQ 累积与同步。

支持通过索引隐式共享 KV heads 的 MQA/GQA；tile size 要兼顾 SRAM、寄存器与溢出。算法依然 exact dense attention，FLOPs 仍 O(N²d)。

## Experiments

论文报告：A100 80GB SXM4，sequence 512–16K、总 token=16K、hidden=2048、head dim 64/128，有/无 causal mask。相对 FA1 的 attention 微基准 1.7–3.0×；前向最高约 230 TFLOPs/s。

8×A100 上 GPT 1.3B/2.7B、2K/8K context 训练，最高 225 TFLOPs/s/GPU；论文采用的模型 FLOPs 公式没有将 causal attention 项减半。此值是特定计数口径的训练指标，不能拿来代表单 token decode 的 MFU。

## Code Inspection

与 FlashAttention 共用同一个官方仓库缓存，见下方共享链接，不复制第二份。已阅读当前 `flash_attn_func` 接口；没有固定到 2023 历史 release，也没有执行 CUDA 测试或训练。

## Limitations and Open Questions

后续 Hopper/FP8 优化不属于 v1 中已经验证的结果。源码个别展示公式容易产生缩放方向歧义，本笔记不机械转抄等式；数值实现/证明未逐项复核，故保留 partial。

## Relation to This Wiki

- [index](../flashattention-2022/index.md)
- [index](../flashinfer-2025/index.md)
- [index](../sarathi-serve-2024/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已做方法/实验定向阅读，`reading.status: partial`；不标记 processed。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [src/abstract.tex](https://arxiv.org/src/2307.08691v1)
- [src/intro.tex](https://arxiv.org/src/2307.08691v1)
- [src/background.tex](https://arxiv.org/src/2307.08691v1)
- [src/algo.tex](https://arxiv.org/src/2307.08691v1)
- [src/experiments.tex](https://arxiv.org/src/2307.08691v1)
- [src/discussion.tex](https://arxiv.org/src/2307.08691v1)
