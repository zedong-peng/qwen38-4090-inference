---
title: Sarathi-Serve — Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# Sarathi-Serve

## Paper Metadata

Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve

- Authors：Agrawal, Amey; Kedia, Nitin; Panwar, Ashish; Mohan, Jayashree; Kwatra, Nipun; Gulavani, Bhargav S.; Tumanov, Alexey; Ramjee, Ramachandran
- 发表/版本：OSDI 2024；官方仓库链接到 USENIX presentation/agrawal。
- arXiv：[2403.02310v3](https://arxiv.org/abs/2403.02310v3)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2403.02310v3](https://arxiv.org/pdf/2403.02310v3)
- [TeX 原始归档](https://arxiv.org/src/2403.02310v3)；[解压源码](https://arxiv.org/src/2403.02310v3)
- [arXiv 元数据快照](https://arxiv.org/abs/2403.02310v3)
- 官方代码本地缓存 (original local cache)，commit `96f9911790ecc00af12ee9fae47cb8fa9ba0d199`；本地缓存不由 wiki Git 自动备份。

## Problem and Main Idea

完整长 prefill 与 decode 混跑会造成 generation stalls，而把阶段完全分开又可能降低利用率。Sarathi-Serve 将 prefill 分块并在受控 token budget 内优先容纳已有 decode，以调节吞吐与尾延迟。

## Method

`4-design.tex`：先放 running decodes，再放未完成 prefill chunks，最后接纳新请求；prefill 只能占用剩余 token budget。chunking 不改变 dense attention 总算术工作，但后续块需重复读取先前 KV。token budget 依据 TBT SLO、模型/硬件 profiling、tile-quantization 与 pipeline bubbles 选择。

论文实现基于 vLLM，支持 FlashAttention-2/FlashInfer，实际评测用 FlashAttention backend；NCCL 承担 TP/PP 通信。不要把论文所对比的 prefill-priority vLLM 当作所有后续 vLLM 版本的调度。

## Experiments

论文报告：Mistral-7B 单 A100 80GB，Yi-34B TP2，Llama2-70B 8×A40 TP4-PP2，Falcon-180B 双节点各 4×A100、100Gbps Ethernet。ShareGPT 与 arXiv 摘要长度分布，Poisson arrivals；分别排除总长超过 8192/16384 的请求。

SLO 基于 P99 TBT，另限制 median scheduling delay≤2秒。strict token budget 通常 512，relaxed 通常 2048。strict 下 Yi-34B ShareGPT 对 vLLM 最高 3.7× capacity；pipeline 设置另有更高收益。Yi-34B 的 512 chunk prefill 开销最高约25%，不是免费优化。精度未在本次已读设置段明确确认，不作推定。

源码包有 `6-discussion.tex` 中“只到3K”等旧描述，**main.tex 并未 include 它**；不把未编入的残留文件当作本版实验限制。

## Code Inspection

完整阅读 `sarathi/core/scheduler/sarathi_scheduler.py`：decode-first 计数，按剩余预算截断 prefill，内存不足仍可抢占。当前还包含 dynamic chunk-size schedule 配置，超出本文以固定 budget 为主的实验设置。README 指向 `osdi-experiments`；未执行其环境或实验。

## Limitations and Open Questions

解读：stall-free 是调度机制，不是任意负载下延迟永不增加；token budget、arrival rate、KV 压力和排队都要纳入。背景/动机、引用文献与全部 artifact 未逐项阅读，状态 partial。

## Relation to This Wiki

- [index](../vllm-2023/index.md)
- [index](../distserve-2024/index.md)
- [index](../splitwise-2024/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已做方法/实验定向阅读，`reading.status: partial`；不标记 processed。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [main.tex](https://arxiv.org/src/2403.02310v3)
- [4-design.tex](https://arxiv.org/src/2403.02310v3)
- [5-eval.tex](https://arxiv.org/src/2403.02310v3)
- [5.1-eval-capacity.tex](https://arxiv.org/src/2403.02310v3)
- [5.2-eval-pp-viability.tex](https://arxiv.org/src/2403.02310v3)
- [5.3-eval-ablation.tex](https://arxiv.org/src/2403.02310v3)
