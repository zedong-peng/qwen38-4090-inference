---
title: "ExLlamaV3：Qwen3.8 EXL3、原生 MTP 与 DFlash2"
domain: research
area: llm-inference
type: engineering
status: active
updated: 2026-10-01
tags: [qwen3-8, rtx4090, inference, engineering, reproducibility]
---

# ExLlamaV3：Qwen3.8 EXL3、原生 MTP 与 DFlash2

来源：[官方/作者仓库](https://github.com/turboderp-org/exllamav3/tree/d3739fd393337b1ff4d6c2a342b12f0c87a9592f)；固定 commit `d3739fd393337b1ff4d6c2a342b12f0c87a9592f`，分支 `master`。2026-10-01检索 stars **1561**、最近push `2026-09-30T19:55:34Z`；stars是时点信号，不是性能或质量证明。原始 [README](https://github.com/turboderp-org/exllamav3/blob/d3739fd393337b1ff4d6c2a342b12f0c87a9592f/README.md)、[metadata](metadata.yaml)、[GitHub API缓存](supplementary/github-api-repository.json)。

ExLlamaV3 提供 EXL3/QTIP 权重量化、低比特 KV、CUDA kernels 和草稿解码，当前官方主干已经包含 Qwen3.5/3.8 dense 架构、MTP 和 **DFlash2**。2026-08 的教程说需要 Mia fork，是当时的实现状态；不要按旧教程误判当前官方代码缺少支持。

固定源码的 `architecture/qwen3_5.py` 对应 `Qwen3_5ForConditionalGeneration`，`qwen3_5_mtp.py` 实现 MTP，`dflash2.py` 实现 selector 与动态卷积并校验 target hidden/vocab；`architectures.py` 注册 DFlash2。模型名称 3.8 仍使用 3.5 架构标识，这能解释 loader 路径，但不意味着不同 checkpoint 的性能可以互换。

## 直接可核对的速度证据

缓存的 [r0b0tlab 部署](https://github.com/r0b0tlab/qwen38-exl3-dflash2) 在 **RTX3090**、target EXL3 4.00bpw（6-bit head/vision、4-bit MTP）、draft 4bpw、GSM8K greedy、最多512输出、ctx8192 上测 AR **42.8**、MTP **116.3**、DFlash2 **162.9 tok/s**，每 verify round 平均 accepted length 4.12/5.66。full262K cache 加载约21.7GB；peak23.13GB 来自150K depth开放生成测试。ACCEPTANCE的PASS是acceptance/latency gates，没有证明GSM8K答案正确率。这是作者固定 community engine `355c6ee` 的3090结果，不能重标成4090或当成官方 master 复现。

缓存的 Mia model kit target 3.5bpw 约14.2GiB，draft约1.4GB，DFlash2约160K窗口，MTP可到262K；其 GB10 数字与基于带宽估计的消费卡预测不是4090实测。NVFP4 KV 可经软件解码用于 Ada，不代表4090具备 Blackwell 原生 NVFP4 W4A4 tensor instructions。

## 在 CUDA12.8 上的复现入口

不是纯 Python：安装需要 Torch 和 C++/CUDA extension。官方 minimum Torch2.6/CUDA12.4，当前声明 cu124/cu126/cu128/cu129/cu130/cu132；选择与 driver/toolkit 匹配的 cu128，并 pin 实际安装版本。匹配 ABI 的官方 release wheel 可避免本地编译，源码方式如下（尚未执行）：

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu128
TORCH_CUDA_ARCH_LIST=8.9 pip install --no-build-isolation .
python examples/chat.py -m /models/target -dm /models/dflash2   -cs 4096 -cq 4 -ndt 7 -mode chatml -maxr 512 -prompt 'Write a short Python function.' -tps
```

对照 AR 去掉 `-dm/-ndt`；MTP 用 `-mtp` 替代 `-dm`，二者互斥。`-tps` 分别报告 prompt 与 generation tokens/s，并扣除 cached prompt tokens。服务层官方建议 [TabbyAPI](https://github.com/theroyallab/tabbyAPI)，其 OpenAI API、Jinja 模板和 batch scheduler 不应与底层 kernel 混为独立推理引擎。本文只归档选择性源码/模型卡/部署说明，没有执行 GPU 测试。


## 证据范围与关系

选择性检查：`README.md`, `pyproject.toml`, `exllamav3/architecture/architectures.py`, `exllamav3/architecture/qwen3_5.py`, `exllamav3/architecture/qwen3_5_mtp.py`, `exllamav3/architecture/dflash2.py`, `exllamav3/model_init.py`, `examples/chat.py`。这是部分文档/接口/实验阅读，未进行完整源码审计。公开速度都归属于作者实验，execution为not_run。

综合比较见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)；本机条件与同机复现见 [index](../g4090-qwen38-benchmark-2026/index.md)。
