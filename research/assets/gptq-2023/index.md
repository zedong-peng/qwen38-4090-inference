---
title: 'GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-10-01'
tags: [llm-inference, gpu, qwen38, quantization, speculative-decoding]
---

# GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers

## Paper Metadata

Frantar, Elias；Ashkboos, Saleh；Hoefler, Torsten；Alistarh, Dan。ICLR 2023；证据为 arXiv 2210.17323v2（2023-03-22）。 [arXiv固定版本](https://arxiv.org/abs/2210.17323v2)。归档日期2026-10-01。

## Local Assets

- [Metadata](metadata.yaml)
- [PDF](https://arxiv.org/pdf/2210.17323v2)；[TeX原始下载](https://arxiv.org/src/2210.17323v2)；[解压source](https://arxiv.org/src/2210.17323v2)
- [arXiv身份快照](https://arxiv.org/abs/2210.17323v2)
- 官方repo缓存 (original local cache)，commit `2d65066eeb06a5c9ff5184d8cebdf33662c67faf`，branch `main`；嵌套repo不会由wiki父Git自动备份。

## Problem and Main Idea / Method

GPTQ以校准输入构造 Hessian 近似，在固定列顺序下舍入权重，并补偿尚未量化的列。128列 lazy block update 提升GPU利用率；阻尼与逆Hessian Cholesky避免递推的数值失稳。论文 §3 的量化算法与用于 decode 的低比特kernel是两个组件。校准128段 C4、每段2048 tokens；权重逐Transformer block处理，下一block使用前面已量化block的输出。

## Experiments

**以下均为论文报告，未在本任务复现。** §4、Table practical-results 和 Appendix benchmarking-setup：OPT-175B、3-bit、batch=1。A100-80GB FP16从5卡降为1卡，平均每token230→71 ms（3.24×）；A6000-48GB从8卡降为2卡，589→130 ms（4.53×）。这些是跨卡数的论文比较，非RTX4090、非Qwen3.8；改善主要来自减少权重搬运，不能把压缩倍率当计算加速倍率。

## Code Inspection

README明确旧3-bit kernel只针对 OPT-175B 的1×A100/2×A6000优化。`gptq.py: GPTQ.fasterquant`可见 `blocksize=128`、`percdamp=.01`、Cholesky、act-order和static-groups；`quant.py`区分对称/非对称、per-channel与fake quant数值。该原始仓库的模型入口是OPT/BLOOM/LLaMA，未观察到Qwen3.8 hybrid适配。现代GPTQModel等工具的支持要另证。

## Limitations and Open Questions

原论文不量化activation/KV；极低位宽仍有质量退化。原始GPTQ algorithm、checkpoint格式、Marlin/GPTQ runtime并非同义词，不能将可加载GPTQ格式直接视为此repo可服务Qwen3.8。

## Relation to This Wiki

目标27B在24GB单卡必须考虑权重表示；GPTQ为W4候选提供基础，部署优先使用当前支持hybrid架构的引擎。关联 [index](../awq-2024/index.md)、[index](../marlin-2024/index.md)。

## Reading and Reproduction Status

`reading.status: partial`，source优先。PDF已归档并检查首页身份，没有声称逐页精读；代码仅README和指定接口观察，没有执行下载代码、编译、量化、训练或GPU推理。本页不将历史论文结果填入g4090实测栏。

- [gptq.tex](https://arxiv.org/src/2210.17323v2)：§3（算法）、§4 setup/practical improvements、Appendix benchmarking-setup定向阅读；未完整读全部精度表/附录
