---
title: Speculative Decoding — Fast Inference from Transformers via Speculative Decoding
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# Speculative Decoding

## Paper Metadata

Fast Inference from Transformers via Speculative Decoding

- Authors：Leviathan, Yaniv; Kalman, Matan; Matias, Yossi
- 发表/版本：ICML 2023；归档 main.tex 包含 ICML 2023 接收版设置，首个 arXiv 版本为2022年。
- arXiv：[2211.17192v2](https://arxiv.org/abs/2211.17192v2)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2211.17192v2](https://arxiv.org/pdf/2211.17192v2)
- [TeX 原始归档](https://arxiv.org/src/2211.17192v2)；[解压源码](https://arxiv.org/src/2211.17192v2)
- [arXiv 元数据快照](https://arxiv.org/abs/2211.17192v2)

## Problem and Main Idea

自回归生成串行调用大模型；在内存带宽主导且还有算力余量时，用小 draft 模型先提议多个 token，大 target 一次并行验证，以减少 target 串行调用轮数并保持目标采样分布。

## Method

`main.tex` §2–3 与 Appendix correctness：从 q 提议 token，以 min(1,p/q) 接受；首个拒绝位置改从 normalize(max(0,p−q)) 采样。全接受则从 target 额外采一个 token。这里的 p、q 已包含 temperature/top-k 等采样变换。

在 acceptance 独立同分布、验证 γ+1 个位置与一次 target 调用等耗时的理想假设下：E[tokens]=(1−α^(γ+1))/(1−α)，speedup=E[tokens]/(1+γc)。真实 batching、attention/KV 成本和 draft overhead 会破坏理想条件；α 不是越高越好，还要看 draft 时间 c。

保证的是**输出分布一致**，不保证相同随机种子逐 token 输出路径一致。greedy 是退化分布的特殊情形。

## Experiments

论文报告：batch=1、单 TPU-v4，T5-XXL 11B + T5-small/base/large，WMT EnDe 与 CNN/DailyMail，T5X baseline。T5-small 温度0/1的 EnDe 实测为3.4×/2.6×，摘要口径2–3×。LaMDA/GPT-like 部分主要评估 acceptance α，不应扩写成所有大模型都已实测相同 walltime speedup。

## Code Inspection

本次主文未定位到可核验的独立官方实现仓库，repositories 为空并登记原因；不以第三方实现冒充作者 artifact。论文算法与 correctness proof 已读，未编写或执行采样/TPU实验。

## Limitations and Open Questions

作者指出计算资源饱和时可能无收益，算术总工作量可能增加。beam-search、lenience 与完整附录扩展未全部阅读，reading=partial；严格分布不变也不能推广到所有后续 speculative 方法。

## Relation to This Wiki

- [index](../sglang-2024/index.md)
- [index](../flashinfer-2025/index.md)
- [index](../awq-2024/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已做方法/实验定向阅读，`reading.status: partial`；不标记 processed。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [main.tex](https://arxiv.org/src/2211.17192v2)
