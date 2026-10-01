---
title: vLLM / PagedAttention — Efficient Memory Management for Large Language Model
  Serving with PagedAttention
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# vLLM / PagedAttention

## Paper Metadata

Efficient Memory Management for Large Language Model Serving with PagedAttention

- Authors：Kwon, Woosuk; Li, Zhuohan; Zhuang, Siyuan; Sheng, Ying; Zheng, Lianmin; Yu, Cody Hao; Gonzalez, Joseph E.; Zhang, Hao; Stoica, Ion
- 发表/版本：SOSP 2023；主 TeX 含会议元数据与 DOI 10.1145/3600006.3613165。
- arXiv：[2309.06180v1](https://arxiv.org/abs/2309.06180v1)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2309.06180v1](https://arxiv.org/pdf/2309.06180v1)
- [TeX 原始归档](https://arxiv.org/src/2309.06180v1)；[解压源码](https://arxiv.org/src/2309.06180v1)
- [arXiv 元数据快照](https://arxiv.org/abs/2309.06180v1)
- 官方代码本地缓存 (original local cache)，commit `79f0be21ff4044d53f0a6f911422b9f52064639c`；本地缓存不由 wiki Git 自动备份。

## Problem and Main Idea

在线自回归服务需要把足够多请求组成 batch，但 KV cache 随输出增长，连续预留最大长度会产生保留空间、内部碎片和外部碎片。PagedAttention 将序列逻辑块映射到非连续物理 KV 块，让工作集更紧凑，进而提高可批处理的请求数。

## Method

- `main.tex` §4：固定 token 数的 KV blocks、逻辑/物理 block table 和按需分配；尾块可有未用槽位，并非物理上绝对零浪费。论文默认 block size=16。
- §4.4：引用计数和 copy-on-write 支持 parallel sampling、beam search；预定义公共前缀可共享物理块。不能据此把后来的自动 prefix cache 全部归入 2023 原始实现。
- §4.5：FCFS、sequence group 一起调度，内存不足时整组抢占；恢复采用 CPU swap 或重算 KV。重算将既有生成 token 合并为一次 prefill。
- §4.6–5：中心 scheduler 广播 token 与 block tables；tensor-parallel workers 分别保存其 attention heads 的 KV，CUDA kernels 融合 block 读写和 attention。

## Experiments

论文报告（`eval.tex`、`main.tex` §6–7）：OPT-13B/66B/175B 与 LLaMA-13B，GCP A100，ShareGPT/Alpaca 长度分布加 Poisson 到达；参数内存表对应 FP16。指标是每请求 E2E latency / output length 的均值和可维持请求率，不能直接称为 P99 ITL。

摘要报告同等延迟下 2–4× 吞吐。ShareGPT basic sampling 对 Orca Oracle 为 1.7–2.7×；**Orca 是作者重实现**，包含 Oracle/Pow2/Max 三种输出预留策略。kernel 微基准中 paged attention 本身反而有 20–26% latency 开销，E2E 收益来自更好的批处理容量。短序列、KV 空间充裕且进入 compute-bound 时，优势减小。

## Code Inspection

`README.md`、`vllm/v1/core/kv_cache_manager.py` 的 `KVCacheBlocks`/`allocate_slots`、`vllm/v1/core/sched/scheduler.py` 的 `schedule` 及 `vllm/config/scheduler.py` 做了局部阅读。当前 scheduler 用 computed tokens 与待计算 tokens 统一表示工作，并覆盖 chunked prefill、prefix cache、speculative decode；这是后续演化，不能替代论文的历史基线。此次未审计完整 CUDA kernel。

## Limitations and Open Questions

作者指出非 LLM、静态形状或 compute-bound 场景不一定受益。解读：分页减少碎片，不减少每个已缓存 token 的 KV 数值本体大小，也不把 dense attention 变成 linear attention。吞吐倍率需要匹配模型、长度、到达率与调度策略。

## Relation to This Wiki

- [index](../sglang-2024/index.md)
- [index](../sarathi-serve-2024/index.md)
- [index](../flashattention-2022/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已阅读论文主文和附录；已做局部代码核查。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [main.tex](https://arxiv.org/src/2309.06180v1)
- [intro.tex](https://arxiv.org/src/2309.06180v1)
- [eval.tex](https://arxiv.org/src/2309.06180v1)
- [discussion.tex](https://arxiv.org/src/2309.06180v1)
- [related_work.tex](https://arxiv.org/src/2309.06180v1)
- [conclusion.tex](https://arxiv.org/src/2309.06180v1)
