---
title: 'AWQ / TinyChat — AWQ: Activation-aware Weight Quantization for LLM Compression
  and Acceleration'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# AWQ / TinyChat

## Paper Metadata

AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration

- Authors：Lin, Ji; Tang, Jiaming; Tang, Haotian; Yang, Shang; Chen, Wei-Ming; Wang, Wei-Chen; Xiao, Guangxuan; Dang, Xingyu; Gan, Chuang; Han, Song
- 发表/版本：MLSys 2024；arXiv comments 标记 Best Paper Award；本次 v6 含后续实验。
- arXiv：[2306.00978v6](https://arxiv.org/abs/2306.00978v6)；检索/归档日期：2026-09-14。

PDF/TeX v6 标题含 **On-Device**：*AWQ: Activation-aware Weight Quantization for On-Device LLM Compression and Acceleration*；arXiv 页面 citation_title 省略这一词。已核对版本、作者组与官方仓库，为同一论文，metadata 保留两种标题。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2306.00978v6](https://arxiv.org/pdf/2306.00978v6)
- [TeX 原始归档](https://arxiv.org/src/2306.00978v6)；[解压源码](https://arxiv.org/src/2306.00978v6)
- [arXiv 元数据快照](https://arxiv.org/abs/2306.00978v6)
- 官方代码本地缓存 (original local cache)，commit `d6e797a42b9ef7778de8ee2352116e0f48a78d61`；本地缓存不由 wiki Git 自动备份。

## Problem and Main Idea

端侧小 batch decode 的 weight traffic 大。AWQ 利用激活统计选择 per-channel 缩放，降低 salient 权重的低比特误差，再用 TinyChat 的融合反量化与算子融合把权重压缩转成加速。

## Method

`text/3_approach.tex`：重要性由输入 activation magnitude 指示。保留1% FP16通道是动机实验，不是最终方法必须混合存储 FP16 的要求。实际优化 Q(W diag(s)) diag(s)^−1 X 对 WX 的误差，s 由 activation scale 的 α 次幂生成，20点 grid search，并做 weight clipping。

`text/4_system.tex`：W4A16，group size 通常128；在 matmul/matvec 内即时反量化，避免中间 FP16 权重写回 DRAM；SIMD-aware packing 和 QKV/norm/attention fusion 缓解解码器开销。量化权重不是量化 KV cache。

## Experiments

论文报告：LLaMA/OPT、Vicuna、Mistral/Mixtral、视觉语言模型，WikiText2 PPL、任务准确率以及校准分布消融。TinyChat 4090/Jetson Orin 测速为 **batch=1，prompt=4，生成200 tokens，median latency**。

4090 三类模型对 HF FP16 为2.7–3.9×；Llama2-7B 先通过 FP16 fusion 从52到62 tokens/s，再由量化 linear 获得额外3.1×。收益同时包含量化和系统优化，不应全部归因到 AWQ scaling。精度损失要按模型/位宽/任务检查，不能泛称无损。

## Code Inspection

`awq/entry.py` 显式区分 fake/real q_backend、w_bit、q_group_size；`awq/quantize/auto_scale.py` 的局部 `_search_module_scale` 实现20点比例搜索、MSE选择、每步恢复权重，支持论文方法说明。TinyChat kernel 与所有模型映射未逐项审计。

## Limitations and Open Questions

解读：权重带宽主导的短 prompt 单用户测速不能外推到长上下文 KV 主导或大 batch compute-bound。v6 的新增模型与设备结果不能自动归入最初预印本版本。相关工作和被 include 的全部精度表未完整阅读，reading=partial。

## Relation to This Wiki

- [index](../speculative-decoding-2023/index.md)
- [index](../vllm-2023/index.md)
- [index](../flashattention-2022/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已做方法/实验定向阅读，`reading.status: partial`；不标记 processed。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [text/3_approach.tex](https://arxiv.org/src/2306.00978v6)
- [text/4_system.tex](https://arxiv.org/src/2306.00978v6)
- [text/5_experiments.tex](https://arxiv.org/src/2306.00978v6)
