---
title: 'DFlash: Block Diffusion for Flash Speculative Decoding'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-10-01'
tags: [llm-inference, gpu, qwen38, quantization, speculative-decoding]
---

# DFlash: Block Diffusion for Flash Speculative Decoding

## Paper Metadata

Chen, Jian；Liang, Yesheng；Liu, Zhijian。ICML 2026，camera-ready；证据 arXiv 2602.06036v2（2026-05-28）。此论文介绍DFlash第一代，DFlash2另有2026-08-18官方博客。 [arXiv固定版本](https://arxiv.org/abs/2602.06036v2)。归档日期2026-10-01。

## Local Assets

- [Metadata](metadata.yaml)
- [PDF](https://arxiv.org/pdf/2602.06036v2)；[TeX原始下载](https://arxiv.org/src/2602.06036v2)；[解压source](https://arxiv.org/src/2602.06036v2)
- [arXiv身份快照](https://arxiv.org/abs/2602.06036v2)
- 官方repo缓存 (original local cache)，commit `07ebd93db9f472af339b644bb70221ad8428328a`，branch `main`；嵌套repo不会由wiki父Git自动备份。

## Problem and Main Idea / Method

`sections/method.tex`：冻结target并融合多层hidden features，在每个draft层注入为KV；一次forward并行预测masked block。训练随机anchor+屏蔽后续block positions、共享冻结embedding/head，并以指数衰减cross-entropy优先保证前面的draft token。target验证后接受前缀、拒绝后缀，吞吐取决于accepted length、draft成本和verify宽度。

## Experiments

**以下均为论文报告，未在本任务复现。** `sections/exp.tex`：Llama3.1-8B及Qwen3 4B/8B/Coder30B-A3B，主要H200；数学/代码/chat。Qwen3非thinking、Transformers backend、block16，greedy平均4.9×、temperature1平均4.1×baseline。SGLang Spec-v1、不重叠调度、B200上Llama3.1-8B block10的HumanEval：c1 baseline245 tok/s，DFlash为2.8×；c32的aggregate吞吐baseline5854 tok/s，DFlash为1.8×，不是每请求5854 tok/s。该表列DFlash(10)，数字不能记为DFlash2或4090。

## Code Inspection

当前README已支持DFlash2 Qwen3.8-27B，并指向SGLang#35371、vLLM#52816、llama.cpp#27342；论文版本与repo的新工程能力分开记录。`dflash/model.py:dflash_generate`有block_size、target_hidden提取、greedy前缀匹配与非greedy rejection sample；`dflash/benchmark.py`统一gsm8k/math500/humaneval/mbpp/mt-bench和reasoning template选项。README明确Qwen3.8的DFlash2 CUDA部署使用外部server；其native Transformers backend的DFlash2仅列Muse-Glimmer-30B。

## Limitations and Open Questions

本轮没有本地论文benchmark。DFlash2专用Qwen3.8 checkpoint、GDN state回滚与24GB显存开销属于后续工程，不能从本文默认H200 BF16路径推断。严格分布条件与实际greedy数值差异要分别验证；低比特target已与原始BF16模型不同。

## Relation to This Wiki

本次最直接的speculative路线是Qwen3.8内置MTP与DFlash2官方drafter，先固定engine/checkpoint/bitrate、再扫draft depth。关联 [index](../eagle-3-2025/index.md)、[2026-10-01-qwen38-4090-paper-search](../../threads/2026-10-01-qwen38-4090-paper-search.md)；[DFlash2官方博客](https://inco.ai/blog/dflash2/)。

## Reading and Reproduction Status

`reading.status: partial`，source优先。PDF已归档并检查首页身份，没有声称逐页精读；代码仅README和指定接口观察，没有执行下载代码、编译、量化、训练或GPU推理。本页不将历史论文结果填入g4090实测栏。

- [sections/method.tex](https://arxiv.org/src/2602.06036v2)：方法/训练定向阅读
- [sections/exp.tex](https://arxiv.org/src/2602.06036v2)：setup、Instruct Models、长context与SGLang数据/部分消融定向阅读；未完整读全部结果表和附录
