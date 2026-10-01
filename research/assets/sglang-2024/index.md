---
title: 'SGLang / RadixAttention — SGLang: Efficient Execution of Structured Language
  Model Programs'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# SGLang / RadixAttention

## Paper Metadata

SGLang: Efficient Execution of Structured Language Model Programs

- Authors：Zheng, Lianmin; Yin, Liangsheng; Xie, Zhiqiang; Sun, Chuyue; Huang, Jeff; Yu, Cody Hao; Cao, Shiyi; Kozyrakis, Christos; Stoica, Ion; Gonzalez, Joseph E.; Barrett, Clark; Sheng, Ying
- 发表/版本：NeurIPS 2024；Crossref proceedings 记录，首个 arXiv 版本于 2023 年。
- arXiv：[2312.07104v2](https://arxiv.org/abs/2312.07104v2)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2312.07104v2](https://arxiv.org/pdf/2312.07104v2)
- [TeX 原始归档](https://arxiv.org/src/2312.07104v2)；[解压源码](https://arxiv.org/src/2312.07104v2)
- [arXiv 元数据快照](https://arxiv.org/abs/2312.07104v2)
- 官方代码本地缓存 (original local cache)，commit `95140a7b0c9fc2f87a2a6cf6f6f0df8640a73174`；本地缓存不由 wiki Git 自动备份。

## Problem and Main Idea

多次 LLM 调用组成的程序具有公共前缀、分支与合并结构。SGLang 用 Python 内嵌语言表达生成和并行关系，并通过 runtime 自动发现 KV 复用与结构化输出跳跃执行机会。

## Method

- `sec-programming-model.tex`：`gen/select/extend/fork/join`，异步 stream executor；获取结果才同步，frontend hints 帮助插入可共享前缀。
- `sec-radix-attention.tex`：CPU radix tree 索引 token 前缀，GPU KV 使用非连续 pages；论文此处一 page 对应一个 token。完成请求后保留 prompt 和 generation KV，按 LRU 淘汰叶子，running nodes 用引用计数保护；缓存和活跃请求共用内存池。
- 调度使用 longest-shared-prefix-first。附录的 DFS 最优命中率证明有**离线请求集合和 cache 至少容纳最长请求**等前提；未知输出长度及在线到达会破坏理想条件。
- `sec-compressed-fsm.tex` 与附录：压缩连续单一路径，在确定字符串上 jump forward；retokenization 处理字符与 token 边界不一致。格式合法不意味着各合法字符串的采样概率天然无偏。
- `sec-endpoint-spec.tex`：API speculative execution 复用黑盒端点提前生成的后续文本；不同于 draft/target 分布校正的 speculative decoding。

## Experiments

论文报告（`sec-eval.tex`、附录）：Llama-2 7B/70B、Mixtral-8x7B、LLaVA，FP16；主要 A10G 24GB，Llama-70B 为 4×A100 80GB。MMLU/HellaSwag、ReAct/ToT/SoT、JSON、RAG、多轮对话；吞吐单位是 **programs/s**，latency 是不批处理的单程序执行时间。

对 Guidance 0.1.8、LMQL 0.7.3 和 **vLLM 0.2.5**，最高 6.4× 吞吐和 3.7× 延迟改善。论文刻意使用尚未集成相关 prefix reuse 的旧版 vLLM，不能当作当前两项目的排名。长输出多轮 chat 因 decode 主导且跨会话少共享，几乎没有加速。命中率消融、树结构/调度/frontend hints 消融支持机制归因；无复用 workload 中树维护约 0.2/74.3 秒。

## Code Inspection

局部阅读 `python/sglang/launch_server.py`、`srt/mem_cache/radix_cache.py` 的 `match_prefix`/`evict`/`inc_lock_ref`、`srt/managers/schedule_policy.py`。当前支持 page-aligned prefix matching、namespace key、可选 eviction strategy，以及 LPM/DFS-weight/HRRN/FCFS 等策略。`test/registered/radix_cache/test_radix_cache_hit.py` 是启动真实服务的多轮 cache-hit 测试，已阅读但未执行。当前代码功能多于论文 v2。

## Limitations and Open Questions

作者讨论贪心 cache-aware 调度饥饿、跨存储层缓存、fuzzy matching 与编译器扩展。附录明确 compressed FSM 有概率扭曲问题；compiler code movement 不严格保持原计算，12/15 模板成功来自人工判定，不是语义等价证明。缓存收益应按 prefix 命中率、长度、并行分支及 eviction 压力分层。

## Relation to This Wiki

- [index](../vllm-2023/index.md)
- [index](../flashinfer-2025/index.md)
- [index](../speculative-decoding-2023/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已阅读论文主文和附录；已做局部代码核查。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [neurips_2024.tex](https://arxiv.org/src/2312.07104v2)
- [sec-intro.tex](https://arxiv.org/src/2312.07104v2)
- [sec-programming-model.tex](https://arxiv.org/src/2312.07104v2)
- [sec-radix-attention.tex](https://arxiv.org/src/2312.07104v2)
- [sec-compressed-fsm.tex](https://arxiv.org/src/2312.07104v2)
- [sec-endpoint-spec.tex](https://arxiv.org/src/2312.07104v2)
- [sec-eval.tex](https://arxiv.org/src/2312.07104v2)
- [sec-related-work.tex](https://arxiv.org/src/2312.07104v2)
- [sec-conclusion.tex](https://arxiv.org/src/2312.07104v2)
- [appendix.tex](https://arxiv.org/src/2312.07104v2)
