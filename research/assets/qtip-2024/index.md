---
title: 'QTIP: Quantization with Trellises and Incoherence Processing'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-10-01'
tags: [llm-inference, gpu, qwen38, quantization, speculative-decoding]
---

# QTIP: Quantization with Trellises and Incoherence Processing

## Paper Metadata

Tseng, Albert；Sun, Qingyao；Hou, David；De Sa, Christopher。NeurIPS 2024 Spotlight；证据 arXiv 2406.11235v4（2025-06-18），含后续Llama3.1/3.2结果。 [arXiv固定版本](https://arxiv.org/abs/2406.11235v4)。归档日期2026-10-01。

## Local Assets

- [Metadata](metadata.yaml)
- [PDF](https://arxiv.org/pdf/2406.11235v4)；[TeX原始下载](https://arxiv.org/src/2406.11235v4)；[解压source](https://arxiv.org/src/2406.11235v4)
- [arXiv身份快照](https://arxiv.org/abs/2406.11235v4)
- 官方repo缓存 (original local cache)，commit `e90c6688c8dfae326a3a81b5eb032db7c6680ec0`，branch `main`；嵌套repo不会由wiki父Git自动备份。

## Problem and Main Idea / Method

QTIP先用随机Hadamard变换改善权重分布，再做 trellis-coded quantization。bitshift trellis让每个weight group仅依赖一个局部bit窗口，可并行解码；1MAD/3INST计算式码本或HYB小lookup+hash使解码不必读取巨大码本。HYB的L=16、V=2、Q=9提供2KiB码本；16×16权重tiles与BlockLDLQ结合获得有效维度256；tail-biting避免初始状态存储浪费。

## Experiments

**以下均为论文报告，未在本任务复现。** `sections/experiments.tex` Table genspeed：Llama2、batch=1、RTX6000 Ada-48GB、矩阵融合。7B FP16 55.9 tok/s，QTIP2/3/4bit为188/161/140；70B为23.5/19.1/16.3，FP16 OOM。吞吐表是融合QKV与gate/up后的论文结果，非Qwen3.8/4090。作者在v4说明Llama3 70B的layer0-v量化会导致zero-shot collapse，低比特质量需按层/任务验证。

## Code Inspection

README与`lib/codebook/bitshift.py`提供HYB 2/3/4bit模块；`eval/interactive_gen.py`使用StaticCache、可选torch.compile/CUDA graphs，并对decode计时。README明确公开脚本没有矩阵融合，公开权重通常只有表中80–90%速度。只定向观察模块接口和generation流程，未运行量化/推理。

## Limitations and Open Questions

QTIP论文代码主要Llama家族；EXL3采用QTIP的简化变体，但EXL3不是此repo checkpoint格式。本文不证明EXL3对Qwen3.8的质量或4090速度；需要当前ExLlamaV3 repo与目标checkpoint证据。

## Relation to This Wiki

ExLlamaV3官方README明确EXL3基于QTIP，因此这是EXL3路线的机制依据；选4090引擎时使用ExLlamaV3当前适配与实测，不能拿QTIP表填目标模型速度。关联 [index](../awq-2024/index.md)、[2026-10-01-qwen38-4090-paper-search](../../threads/2026-10-01-qwen38-4090-paper-search.md)。

## Reading and Reproduction Status

`reading.status: partial`，source优先。PDF已归档并检查首页身份，没有声称逐页精读；代码仅README和指定接口观察，没有执行下载代码、编译、量化、训练或GPU推理。本页不将历史论文结果填入g4090实测栏。

- [sections/qtip.tex](https://arxiv.org/src/2406.11235v4)：bitshift trellis、computed/HYB codes、tail-biting定向阅读
- [sections/experiments.tex](https://arxiv.org/src/2406.11235v4)：HYB setup与Inference Speed及其限制；未完整阅读所有被include的精度表/附录
