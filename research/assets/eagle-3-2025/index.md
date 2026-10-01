---
title: 'EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-10-01'
tags: [llm-inference, gpu, qwen38, quantization, speculative-decoding]
---

# EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test

## Paper Metadata

Li, Yuhui；Wei, Fangyun；Zhang, Chao；Zhang, Hongyang。NeurIPS 2025（官方README Update确认）；证据 arXiv 2503.01840v3。 [arXiv固定版本](https://arxiv.org/abs/2503.01840v3)。归档日期2026-10-01。

## Local Assets

- [Metadata](metadata.yaml)
- [PDF](https://arxiv.org/pdf/2503.01840v3)；[TeX原始下载](https://arxiv.org/src/2503.01840v3)；[解压source](https://arxiv.org/src/2503.01840v3)
- [arXiv身份快照](https://arxiv.org/abs/2503.01840v3)
- 官方repo缓存 (original local cache)，commit `cb7e0841fe0c206c6ed74a197ad5e2a1f13f5a2b`，branch `main`；嵌套repo不会由wiki父Git自动备份。

## Problem and Main Idea / Method

§3将EAGLE的feature regression约束改为token prediction；融合target低/中/高三层特征，FC映射到hidden维度，并与已采样token embedding结合。draft后续step用自身输出替代尚不可见target feature；training-time test在训练中模拟这种回馈，使用对应attention mask降低train/inference错配。需要针对目标训练的draft，不能把任意小模型当EAGLE3 head。

## Experiments

**以下均为论文报告，未在本任务复现。** §4涵盖Vicuna13B、Llama3.1-8B、Llama3.3-70B、DeepSeek-R1-Distill-Llama8B与5任务，报告3.0–6.5×（任务/温度相关）。SGLang v0.4.4的单H100、Llama3.1-8B、MT-Bench，batch1 158.34→373.25 tok/s；batch64的aggregate吞吐相对baseline1.38×，chain length3、不用tree，不表示单请求快1.38×。这些是论文报告；vLLM段正文写RTX3090但表caption写A100，存在硬件记载冲突，不取其作为消费者卡可比数据。

## Code Inspection

README提供多框架集成与官方/社区draft区别，但todo仍列未提供official Qwen3 EAGLE3。本地`ea_model.py`接口可选use_eagle3，默认tree总tokens60、depth7、top_k10；`eagle/evaluation/speed.py`从JSONL求平均每prompt tokens/time，带硬编码历史tokenizer路径，需要修改后才可复现，不等于在线aggregate吞吐。检查了训练入口接口，未训练或跑模型。

## Limitations and Open Questions

生成分布保持来自target verification的条件；不保证不同batch shape与浮点路径下greedy字符逐一相同。官方仓库旧模型benchmark、社区Qwen draft与Qwen3.8-27B专用checkpoint是不同证据；本轮未确认该目标专用EAGLE3 checkpoint，低于直接MTP/DFlash2部署优先级。

## Relation to This Wiki

为MTP/DSpark/DFlash2的draft–verify成本对照提供基线，目标模型使用当前engine支持。关联 [index](../speculative-decoding-2023/index.md)、[index](../dflash-2026/index.md)。

## Reading and Reproduction Status

`reading.status: partial`，source优先。PDF已归档并检查首页身份，没有声称逐页精读；代码仅README和指定接口观察，没有执行下载代码、编译、量化、训练或GPU推理。本页不将历史论文结果填入g4090实测栏。

- [paper.tex](https://arxiv.org/src/2503.01840v3)：§3、§4实现/结果、§4 SGLang/vLLM（189–241、302–342、355–422行）定向阅读；未完整读全部表/附录
