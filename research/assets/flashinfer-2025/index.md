---
title: 'FlashInfer — FlashInfer: Efficient and Customizable Attention Engine for LLM
  Inference Serving'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# FlashInfer

## Paper Metadata

FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving

- Authors：Ye, Zihao; Chen, Lequn; Lai, Ruihang; Lin, Wuwei; Zhang, Yineng; Wang, Stephanie; Chen, Tianqi; Kasikci, Baris; Grover, Vinod; Krishnamurthy, Arvind; Ceze, Luis
- 发表/版本：MLSys 2025；arXiv comments 明确 Accepted by MLSys 2025。
- arXiv：[2501.01005v2](https://arxiv.org/abs/2501.01005v2)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2501.01005v2](https://arxiv.org/pdf/2501.01005v2)
- [TeX 原始归档](https://arxiv.org/src/2501.01005v2)；[解压源码](https://arxiv.org/src/2501.01005v2)
- [arXiv 元数据快照](https://arxiv.org/abs/2501.01005v2)
- 官方代码本地缓存 (original local cache)，commit `a72f7269959d5cf39a4c3469387a400ae63e6f42`；本地缓存不由 wiki Git 自动备份。

## Problem and Main Idea

服务中 query/KV 长度动态、KV 非连续且模型 attention 变体多，固定形状 kernel 难以兼顾负载均衡与可维护性。FlashInfer 以 BSR/ragged 结构、可定制模板与 plan/run 分离连接 serving runtime 和高效 attention kernels。

## Method

`sections/design.tex`：将 paged/radix KV 索引视为 block-sparse row，并用 composable formats 分解公共 prefix 和私有 suffix，索引拆分不必复制 KV。FA2/FA3 模板加载稀疏 global memory 到连续 shared memory，再运行 tensor-core 运算。

JIT functors 定义 Q/K/V、logits/mask/output 变换；runtime 按长度将工作分给固定 CTAs，部分输出按确定顺序合并。CPU `plan` 生成调度与 workspace 信息，同步形状的多层可复用；GPU `run` 可被 CUDA Graph 捕获。支持 paged storage 不代表存储稀疏一定删减了 attention token。

## Experiments

论文报告 FlashInfer v0.2、SGLang v0.3.4、Triton v3.0，CUDA12.4/PyTorch2.4，FP16，A100/H100。Llama3.1 8B 单 H100、70B 4×H100，ShareGPT/Variable workload，控制 P99 TTFT<200ms 的在线设置；报告29–69% ITL减少。

StreamingLLM+Vicuna13B 的 fused RoPE attention 为28–30% latency减少；MLC parallel generation n=4 时 ITL 减少13.73%/17.42%（8B/70B）。这些是不同 end-to-end workload，不可相加。kernel 测试另比较固定、均匀、Zipf 长度分布。

`evaluation.tex` 中把某 baseline kernel 描述为 closed-source 的句子与其 Triton 指称不一致；本笔记不沿用这一表述。

## Code Inspection

README 和 `flashinfer/decode.py::BatchDecodeWithPagedKVCacheWrapper.plan` 参数已局部阅读：indptr/indices/last_page_len、Q/KV heads、page size，以及位置/窗口变体配置。当前仓库已经超出 v0.2，含更多 backend/算子；未核验每个模板与论文实验对应 commit。

## Limitations and Open Questions

论文版本以 attention forward 为主，不等同于完整 LLM serving 系统或通用 backward 库；CPU plan 成本与缓存重用必须计入。BSR 转换、调度细节和完整附录未全部阅读，状态 partial。

## Relation to This Wiki

- [index](../vllm-2023/index.md)
- [index](../sglang-2024/index.md)
- [index](../flashattention-2-2023/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已做方法/实验定向阅读，`reading.status: partial`；不标记 processed。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [sections/design.tex](https://arxiv.org/src/2501.01005v2)
- [sections/evaluation.tex](https://arxiv.org/src/2501.01005v2)
- [sections/discussions.tex](https://arxiv.org/src/2501.01005v2)
