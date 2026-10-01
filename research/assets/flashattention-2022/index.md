---
title: 'FlashAttention — FlashAttention: Fast and Memory-Efficient Exact Attention
  with IO-Awareness'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# FlashAttention

## Paper Metadata

FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness

- Authors：Dao, Tri; Fu, Daniel Y.; Ermon, Stefano; Rudra, Atri; Ré, Christopher
- 发表/版本：NeurIPS 2022；归档 TeX 使用 NeurIPS 2022 模板；出版信息未另外查 proceedings。
- arXiv：[2205.14135v2](https://arxiv.org/abs/2205.14135v2)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2205.14135v2](https://arxiv.org/pdf/2205.14135v2)
- [TeX 原始归档](https://arxiv.org/src/2205.14135v2)；[解压源码](https://arxiv.org/src/2205.14135v2)
- [arXiv 元数据快照](https://arxiv.org/abs/2205.14135v2)
- 官方代码本地缓存 (original local cache)，commit `8d3a3b80d4758ebde5a867c50d24d4351443cf2b`；本地缓存不由 wiki Git 自动备份。

## Problem and Main Idea

标准 attention 将 N×N score/probability 矩阵物化到 HBM，造成大量读写与显存占用。FlashAttention 用 SRAM 分块、online softmax 与 backward 重计算，保留 exact dense attention 的数学运算定义。

## Method

`src/algo.tex` Algorithm 1 按 KV 块与 Q 块遍历，保存每行最大值 m、归一化和 l 及部分 output；合并时用新的最大值重标定，使跨块 softmax 正确。反向传播重新计算局部 score/probability，而非保存 N² 中间矩阵。

`src/theory.tex` 在 d≤M≤Nd 的两级内存模型中给出 Θ(N²d²/M) HBM accesses；FLOPs 仍是 O(N²d)，固定 M、d 时不能称为计算对 N 的线性复杂度。lower bound 的原始陈述是不能对**所有 M** 渐近改善，不能扩大成每一组硬件参数的最优性定理。block-sparse 扩展另行改变可见 attention 图。

## Experiments

论文报告：A100 attention forward+backward 微基准及 8×A100 BERT/GPT-2 训练。BERT-large 达到 MLPerf 指定 MLM accuracy 的时间为 17.4±1.4 分钟，对照 20.0±1.5。GPT-2 medium OpenWebText 为 6.9 天，对照 Megatron 11.5 天。长序列分类和 Path-X 展示可训练上下文提升。

这些主要是 **attention/训练** 证据，不是在线 autoregressive decode 服务吞吐；`src/experiments.tex` 明示 dense runtime 仍随长度二次增长。

## Code Inspection

当前共享仓库的 README 与 `flash_attn/flash_attn_interface.py::flash_attn_func` 做了接口阅读：支持 FP16/BF16、MQA/GQA、causal/window 选项，调用 FlashAttnFunc。当前 repository 已包含后续代际；未逐行核查 2022 kernel、反向证明及全套训练配置。

## Limitations and Open Questions

作者指出手写 CUDA 工程量与跨架构可移植性限制。解读：减少 attention 暂存不是消除持久 KV cache；dense exact 与稀疏/linear attention 应分别比较。附录 backward、证明、所有实验表未完整阅读，保留 partial。

## Relation to This Wiki

- [index](../flashattention-2-2023/index.md)
- [index](../vllm-2023/index.md)
- [index](../flashinfer-2025/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已做方法/实验定向阅读，`reading.status: partial`；不标记 processed。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [src/algo.tex](https://arxiv.org/src/2205.14135v2)
- [src/theory.tex](https://arxiv.org/src/2205.14135v2)
- [src/experiments.tex](https://arxiv.org/src/2205.14135v2)
- [src/discussion.tex](https://arxiv.org/src/2205.14135v2)
