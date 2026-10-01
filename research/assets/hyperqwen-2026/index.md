---
title: "HyperQwen：vLLM 补丁、DFlash2 与社区复现"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# HyperQwen：vLLM 补丁、DFlash2 与社区复现

来源：[官方/作者仓库](https://github.com/syv-ai/HyperQwen/tree/e1459c7631774f56de2f9425437d54e7e72ea688)；固定 commit `e1459c7631774f56de2f9425437d54e7e72ea688`，分支 `main`。2026-10-01检索 stars **1785**、最近push `2026-09-30T17:56:05Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/syv-ai/HyperQwen/blob/e1459c7631774f56de2f9425437d54e7e72ea688/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

HyperQwen（旧名 syv-ai/qwen38-27b-rtx3090，会重定向）有1785 stars、多位贡献者复现与完整安装/patch/评估脚本，是本轮“流行且有人关注”的强候选。它围绕 exact Qwen3.8-27B 改进 vLLM serving：INT4 head/requant、draft vocabulary selector、MTP/DFlash2、ngram lookup、KV dtype 和 KVarN。

`docs/reproductions/README.md` 的 **RTX4090 450W** harness B：**135.5 tok/s**、no-spec60.3，KV pool57669、PPL8.0921与作者3090复现一致。该行指向公开 issue32，项目内重述此结果；不是本文运行结果。较早 `docs/wsl2-4090.md` 的256-output greedy、median3 client测试：ctx65536 DFlash2K7 prose134.7、code144.5；ctx131072 code180.6；245760浅层 prose122.9。不同 workload/harness/version不合为一个排行榜数字。

README 的127tok/s、copy381和C64 aggregate1035主要是 **RTX3090 250W**。并发 aggregate不能当单用户速度；copy任务的 lookup 更不能当未见文本的生成上限。仓库保留了被撤回的冷启动/lookup因果解释，引用时需使用修订后的证据。GSM8K/PPL与needle 检查也不足以覆盖真实代码代理。

## 可复现但环境较重

精确配置入口为 `docs/install.md`、`docs/vllm-0.30.md`、`start_qwen.sh`、`verify.sh` 和 benchmark docs。本次 pin 主干是 vLLM0.30，native install 明确使用 **CUDA13.0 runtime/compiler** 的 pip pins，旧系统 nvcc 会由启动逻辑切换到 pip CUDA13 toolkit；driver570/CUDA12.8 的 g4090 不宜直接安装最新默认。需选经验证的旧cu128组合或另一个兼容engine，不能默认升级共享服务器driver。

约20GB model加 graph/KV reserve，对只有约19GiB空闲的共享卡限制较大。论文/社区的“24GB可跑”假设整卡可用；短context也不能消除权重和框架固定开销。首轮保留源码，待兼容环境与空间充足再执行。本文已缓存 fixed code、原始公开文档与API元数据，没有安装或运行 vLLM/GPUbenchmark。


## 证据范围与关系

选择性检查：`README.md`, `docs/install.md`, `docs/benchmarks.md`, `docs/reproductions/README.md`, `docs/wsl2-4090.md`, `docs/vllm-0.30.md`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
