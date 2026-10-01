---
title: 'MARLIN: Mixed-Precision Auto-Regressive Parallel Inference on Large Language Models'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-10-01'
tags: [llm-inference, gpu, qwen38, quantization, speculative-decoding]
---

# MARLIN: Mixed-Precision Auto-Regressive Parallel Inference on Large Language Models

## Paper Metadata

Frantar, Elias；Castro, Roberto L.；Chen, Jiale；Hoefler, Torsten；Alistarh, Dan。arXiv 2408.11743v1（2024-08-21）；检索API还返回 PPoPP 2025 DOI 10.1145/3710848.3710871，但本地证据版本仍是v1。 [arXiv固定版本](https://arxiv.org/abs/2408.11743v1)。归档日期2026-10-01。

## Local Assets

- [Metadata](metadata.yaml)
- [PDF](https://arxiv.org/pdf/2408.11743v1)；[TeX原始下载](https://arxiv.org/src/2408.11743v1)；[解压source](https://arxiv.org/src/2408.11743v1)
- [arXiv身份快照](https://arxiv.org/abs/2408.11743v1)
- 官方repo缓存 (original local cache)，commit `1f25790bdd49fba53106164a24666dade68d7c90`，branch `master`；嵌套repo不会由wiki父Git自动备份。

## Problem and Main Idea / Method

§3设计FP16 activation ×INT4 weight kernel。权重/scales预重排以匹配tensor-core访问，activation复用L2，cp.async异步加载、cache eviction hint、双缓冲和4级pipeline重叠反量化/计算，striped work partition避免窄矩阵的SM空闲。量化的真正收益在于低比特weights进入kernel后即时恢复，不先写回完整FP16权重。

## Experiments

**以下均为论文报告，未在本任务复现。** §5 kernel/E2E：group=128时理论权重带宽收益约3.87×，A10的大矩阵batch16–32接近该值。vLLM E2E是64输入+64输出token；服务实验Llama2-7B、RTX A6000报告TPOT约2.8×改善。作者刻意用短序列避免attention主导；A100、A10、3090、A6000的旧模型结果不是4090/Qwen3.8的绝对token/s。

## Code Inspection

README要求CUDA≥11.8、compute capability≥8.0，并明确Ampere/Ada可用。`marlin/__init__.py`的Layer要求infeatures整除128、outfeatures整除256、groupsize=-1或128；`Layer.pack`重排weights/scales。`bench.py`默认按group128、多batch测试FP16与Marlin，测同步包围的kernel队列时间；它不测完整服务端。只读了kernel包装与benchmark，未完整审计CUDA内核。

## Limitations and Open Questions

Marlin是linear kernel，无法独立服务hybrid GDN、多模态、tokenizer或API。Sparse-Marlin还要求2:4结构稀疏checkpoint，不能给普通W4直接加上稀疏收益。新引擎中的AWQ/GPTQ-Marlin实现可能超出此原始repo的约束。

## Relation to This Wiki

batch=1或speculative verify的小batch都可受益，作为4090上AWQ/GPTQ引擎的内核候选；必须与GDN/attention graph调度一起测E2E。关联 [index](../gptq-2023/index.md)、[index](../vllm-2023/index.md)。

## Reading and Reproduction Status

`reading.status: partial`，source优先。PDF已归档并检查首页身份，没有声称逐页精读；代码仅README和指定接口观察，没有执行下载代码、编译、量化、训练或GPU推理。本页不将历史论文结果填入g4090实测栏。

- [marlin.tex](https://arxiv.org/src/2408.11743v1)：§3 Kernel Design（340–460行）与§5（573–603、683–791行）定向阅读；其余段落/全部图表未完整阅读
