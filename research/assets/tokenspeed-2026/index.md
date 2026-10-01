---
title: "TokenSpeed：高关注 serving 系统与 Qwen3.8 适用范围"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# TokenSpeed：高关注 serving 系统与 Qwen3.8 适用范围

来源：[官方/作者仓库](https://github.com/lightseekorg/tokenspeed/tree/e8ff04e68a46df2e657f38eb34d2ed36d8a9ae1e)；固定 commit `e8ff04e68a46df2e657f38eb34d2ed36d8a9ae1e`，分支 `main`。2026-10-01检索 stars **2186**、最近push `2026-09-30T20:05:25Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/lightseekorg/tokenspeed/blob/e8ff04e68a46df2e657f38eb34d2ed36d8a9ae1e/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

LightSeek TokenSpeed 是近期关注度较高的 serving engine（2186 stars），应进入广泛检索，但不能仅因为名称含 Qwen3.8 就列成 RTX4090 27B 的最快候选。其系统采用 C++ FSM scheduler 管理 ownership，Python 执行/编译及 SPMD，支持 pluggable kernels。

固定 README、`docs/recipes/models.md`、`docs/guides/getting-started.md` 与 `python/tokenspeed/runtime/models/qwen3_5.py` 是本次代码证据。Qwen3.8 day-0 [作者博文](https://lightseek.org/blog/tokenspeed-qwen3-8.html) 与 recipes 主体围绕 **Qwen3.8-2.4T-A95B / Flash-Next 巨型 MoE**；launch 博文 580TPS 的 Qwen3.5 也是 397B-A17B、多卡 Blackwell 场景，不是27B+4090。

本次没有找到 exact Qwen3.8-27B checkpoint、sm89、单24GB卡的公开安装/权重量化/速度闭环。因此暂列“值得跟踪，当前不优先部署”，而不是断言 engine 完全不支持该模型。B200 的 throughput Pareto 改善只说明其 serving 系统在原测量环境有价值，不能根据卡间 FLOPS 或带宽比例外推4090 token/s。

## 复现边界

执行需同时满足 docs 的 GPU backend、weight recipe、通信和编译依赖。先检查具体27B architecture、quant backend 与 memory allocation，再按 getting-started 固定环境，不能把大模型 recipe 参数简单改成27B就称为可复现。该项目是更长周期的 serving 研究来源；本轮短期单卡重点优先已有直接作者证据的 NInfer/EXL3/HyperQwen。

博客 HTML 直接下载 HTTP403；保留了 web 工具对 Qwen3.8 博文的提取文本，metadata 明确区分失败的 HTML 下载与成功的提取缓存。源码固定在 commit，未执行构建、模型推理或 benchmark。


## 证据范围与关系

选择性检查：`README.md`, `docs/recipes/models.md`, `docs/guides/getting-started.md`, `python/tokenspeed/runtime/models/qwen3_5.py`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
