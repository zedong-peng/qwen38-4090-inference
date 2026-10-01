---
title: 'Splitwise — Splitwise: Efficient generative LLM inference using phase splitting'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# Splitwise

## Paper Metadata

Splitwise: Efficient generative LLM inference using phase splitting

- Authors：Patel, Pratyush; Choukse, Esha; Zhang, Chaojie; Shah, Aashaka; Goiri, Íñigo; Maleki, Saeed; Bianchini, Ricardo
- 发表/版本：ISCA 2024 线索；本次阅读 arXiv v2，未另外下载 proceedings 版本。
- arXiv：[2311.18677v2](https://arxiv.org/abs/2311.18677v2)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2311.18677v2](https://arxiv.org/pdf/2311.18677v2)
- [TeX 原始归档](https://arxiv.org/src/2311.18677v2)；[解压源码](https://arxiv.org/src/2311.18677v2)
- [arXiv 元数据快照](https://arxiv.org/abs/2311.18677v2)
- 官方代码本地缓存 (original local cache)，commit `8f99e7dc9b407f4ce2488d03dd44c0b8b946dab0`；本地缓存不由 wiki Git 自动备份。

## Problem and Main Idea

prefill 偏计算、decode 更依赖内存容量与带宽，适合不同机器与功耗配置。Splitwise 分离 prompt/token machine pools，并引入可动态扩缩的 mixed pool，在负载变化时缓解资源碎片。

## Method

`sections/splitwise.tex`：两级 scheduler，cluster 层按 pending tokens 的短队列选择 prompt/token 机器，machine 层做 batching。生成首 token 后将 KV 交给 token 机器；长 prompt 按层异步传输，与下一层计算重叠；短 prompt 可直接序列传输以避免细粒度同步开销。

设计空间有 AA、HH、HA、HHcap，分别组合 DGX A100/H100 及 token 机器功耗限制；cost/power/throughput 按固定约束分别优化。这里只讨论 provisioned power，不能直接当作整日实际耗电。

## Experiments

论文报告：BLOOM-176B、Llama2-70B，Azure coding/conversation traces；在两台 A100 或两台 H100 机器上测 transfer prototype，MSCCL++、InfiniBand 200/400Gbps。长 prompt 非重叠 transfer 约8/5ms；特定无 batching coding 实验的 E2E 额外开销0.8%，但第二 token 增加16.5%。

**大规模 cluster provisioning 结论来自离散事件模拟器**，性能模型由硬件 profile 校准。需要同时满足 TTFT/TBT/E2E 的 P50/P90/P99 九个目标。正文给出 iso-power 相对 A100 baseline 的2.15× throughput，以及 iso-throughput 相对 H100 baseline 的25% cost 降低等不同对照。不得将不同成本/功耗约束下倍率拼接成同一结果。

artifact appendix 明确功能评审只测试 traces 和 SplitwiseSim，因硬件限制未测试 transfer prototype。

## Code Inspection

已缓存论文 bibliography 指向的 `Mutinifni/splitwise-sim`，阅读 README、`run.py` 和 `configs/config.yaml`：Hydra 配置实例化 TraceSimulator；默认 performance model 是 constant，论文结果需指定实测 database 配置，不能直接跑默认值声称复现。vLLM PR #2809 与 Zenodo artifact 仅登记来源，未缓存完整历史 prototype。

## Limitations and Open Questions

作者指出异构 H100/A100 InfiniBand 条件不一定现成可用，mixed pool 和多轮会话返回 KV 也影响结论。硬件 profile 与全部 simulation 配置未逐项阅读；此笔记是定向阅读。

## Relation to This Wiki

- [index](../distserve-2024/index.md)
- [index](../sarathi-serve-2024/index.md)
- [index](../vllm-2023/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已做方法/实验定向阅读，`reading.status: partial`；不标记 processed。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [sections/splitwise.tex](https://arxiv.org/src/2311.18677v2)
- [sections/evalnew.tex](https://arxiv.org/src/2311.18677v2)
- [sections/discussion.tex](https://arxiv.org/src/2311.18677v2)
- [sections/artifact.tex](https://arxiv.org/src/2311.18677v2)
