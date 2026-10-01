---
title: 'DistServe — DistServe: Disaggregating Prefill and Decoding for Goodput-optimized
  Large Language Model Serving'
domain: research
area: llm-inference
type: paper
status: active
updated: '2026-09-14'
tags:
- llm-inference
---

# DistServe

## Paper Metadata

DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving

- Authors：Zhong, Yinmin; Liu, Shengyu; Chen, Junda; Hu, Jianbo; Zhu, Yibo; Liu, Xuanzhe; Jin, Xin; Zhang, Hao
- 发表/版本：OSDI 2024；arXiv comments 明确标记。
- arXiv：[2401.09670v3](https://arxiv.org/abs/2401.09670v3)；检索/归档日期：2026-09-14。

## Local Assets

- [metadata.yaml](metadata.yaml)
- [PDF — 2401.09670v3](https://arxiv.org/pdf/2401.09670v3)
- [TeX 原始归档](https://arxiv.org/src/2401.09670v3)；[解压源码](https://arxiv.org/src/2401.09670v3)
- [arXiv 元数据快照](https://arxiv.org/abs/2401.09670v3)
- 官方代码本地缓存 (original local cache)，commit `82831f1604cc6b10bebd360f6c437a07790dde9f`；本地缓存不由 wiki Git 自动备份。

## Problem and Main Idea

prefill 与 decode 的延迟目标和最优并行方式不同，混部署会互相干扰。DistServe 将两阶段分配给不同 GPU instances，分别规划 TP/PP、资源数量和 placement，优化 SLO 约束下 per-GPU goodput。

## Method

`sections/design.tex`：高带宽集群分别搜索两阶段 parallelism 后复制实例；低跨节点带宽集群将相同 pipeline stage 的 prefill/decode segments 放同节点，用 NVLink 传对应层 KV。模拟器根据历史长度/到达分布估计 SLO attainment，枚举 placement 并二分可服务率。

在线控制器按短队列/低负载路由；decode 按需 pull KV，prefill 显存可临时作为队列缓冲。规划有工作负载稳定性前提；preemption 和 fault tolerance 并不是本文已实现的完整能力。

## Experiments

论文报告（`sections/evaluation.tex`）：4节点、32×A100 80GB、节点间25Gbps，FP16 OPT-13B/66B/175B；ShareGPT、HumanEval、LongBench。LongBench 输入受 OPT 2048 positions 限制，**不是超长上下文实测**。

主要以90%请求满足 TTFT 与 TPOT 目标为准，考察 per-GPU rate 和可承受 SLO；chat 对 vLLM 为2.0–4.6× rate，对 DeepSpeed-MII 为1.6–7.4×。summarization 的12.6×是可承受 SLO 严格程度，不是直接吞吐倍率。KV 传输占比<0.1%来自同层 colocate 后走 NVLink 的设置；高带宽 placement 对照属于模拟消融。

## Code Inspection

README 指出执行 backend 是独立 SwiftTransformer 项目；本地仅缓存 DistServe 主仓库，SwiftTransformer 未另行缓存/审计。局部阅读 `distserve/context_stage_scheduler.py` 的 batch 与 migration 接口，确认 context/decode 层分离；没有把 Python 控制器视为完整 GPU 后端实现证据。

## Limitations and Open Questions

作者讨论离线吞吐优先、GPU 很少或单卡时可能更适合非 disaggregated 系统；故不声称 PD 分离总是更快。超长上下文和故障传播需要进一步验证。背景及附录 latency model/99% SLO 未完整阅读。

## Relation to This Wiki

- [index](../sarathi-serve-2024/index.md)
- [index](../splitwise-2024/index.md)
- [index](../vllm-2023/index.md)
- [index](../../index.md)
- `research/fpga-llm-inference/index`：硬件对照需区分 kernel、完整 forward phase 与在线服务。

## Reading and Reproduction Status

已做方法/实验定向阅读，`reading.status: partial`；不标记 processed。 证据为上列固定 arXiv 版本的 TeX；PDF 已归档且完成格式/身份检查，不代表逐页精读 PDF。未运行模型、CUDA、训练或任何论文 benchmark，所有性能数字均为论文报告。

本次阅读路径：

- [sections/design.tex](https://arxiv.org/src/2401.09670v3)
- [sections/implementation.tex](https://arxiv.org/src/2401.09670v3)
- [sections/evaluation.tex](https://arxiv.org/src/2401.09670v3)
- [sections/discussion.tex](https://arxiv.org/src/2401.09670v3)
