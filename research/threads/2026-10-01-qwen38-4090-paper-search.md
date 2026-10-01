---
title: Qwen3.8-27B × RTX4090 — paper-search长名单、论文机制与速度证据
domain: research
area: llm-inference
type: comparison
status: active
updated: '2026-10-01'
tags: [paper-search, qwen38, rtx4090, quantization, speculative-decoding]
---

# Qwen3.8-27B × RTX4090：论文检索与机制证据

## 检索口径与收缩结果

本页先扩大论文召回，再按目标模型可加载、24GB消费卡可运行、公开代码与checkpoint、维护/关注度及可比测量条件筛选。**5篇新论文完成source/PDF下载、官方repo固定commit与方法/实验定向阅读，均为partial；没有把下载或代码浏览记为论文完整阅读，也没有运行论文GPU benchmark。** 已存在的10篇推理论文和linear-attention的GDN/FLA记录不重复归档。

| 选择 | 新增本地证据 | 保留理由 | Qwen3.8-27B/4090直接部署证据 |
|---|---|---|---|
| P0机制 | [index](../assets/qtip-2024/index.md) | EXL3官方声明基于QTIP，解释非均匀trellis量化 | 论文原repo主要Llama；目标靠当前ExLlamaV3证据 |
| P0机制 | [index](../assets/marlin-2024/index.md) | Ampere/Ada可用，W4A16小/中batch高效 | kernel，不是完整hybrid engine |
| P0机制 | [index](../assets/dflash-2026/index.md) | 有论文、公开checkpoint、成熟框架集成 | Qwen3.8支持来自后续DFlash2博客/模型，非论文原实验 |
| P1基础 | [index](../assets/gptq-2023/index.md) | 低bit量化与现代GPTQ/Marlin格式基础 | 原始repo不是目标部署入口 |
| P1对照 | [index](../assets/eagle-3-2025/index.md) | 公开训练、广泛engine集成、speculative基线 | 尚未确认目标专用EAGLE3 draft；不能直接套Qwen3 draft |

## 速度证据：报告结果与待测结果分开

| 来源 / 方法 | 模型 / 硬件 / 条件 | 报告速度 | 证据边界 |
|---|---|---:|---|
| QTIP Table genspeed | Llama2-7B、RTX6000 Ada、b1、4bit、矩阵融合 | 140 tok/s（FP16 55.9） | 论文；公开脚本无融合，作者预计80–90%表中速度 |
| EAGLE3 SGLang | Llama3.1-8B、H100、MT-Bench、b1 | 373.25 tok/s（baseline158.34） | 论文；不是4090/Qwen3.8 |
| DFlash SGLang | Llama3.1-8B、B200、HumanEval、c1、block10 | baseline245 tok/s，DFlash 2.8× | DFlash第一代，不是DFlash2 |
| [llama.cpp控制研究](https://github.com/thc1006/qwen3.8-speculative-decoding-rtx3090) | Qwen3.8-27B、单3090、ctx8192、25自选prompt、长输出 | baseline41.55；MTP-n2 66.39；DFlash2-n4 63.13；n7 50.95 tok/s | server decode；不同source trees；prompt选择、depth同数据选择，不能外推流量 |
| [EXL3 native社区配方](https://github.com/r0b0tlab/qwen38-exl3-dflash2) | Qwen3.8-27B 4.00bpw、单3090、GSM8K greedy、max512、ctx8192 | AR42.8；MTP116.3；DFlash2 162.9 tok/s | repo报告，engine community@355c6ee；不是本文实测，也不与上一行prompt配对 |
| 同一EXL3配方长context | 150K深度、open-ended text、24GB3090 | decode25.3 tok/s；prefill594 tok/s；peak23.13GB | 长上下文改变瓶颈；不能将短context162.9持续外推 |
| g4090本地实测 | 由部署线程提供 | 本页不填写推测数据 | 需要checkpoint revision、engine commit、token lengths、思考/采样配置 |

历史论文speedup说明机制，当前候选是否最快由同机、同量化/精度、同输入/输出、同reasoning设定的测量决定。应同时记录单流decode tok/s、prefill、TTFT和concurrency下aggregate tok/s；不要将server内部decode time与端到端wall time混用。

## 使用的skill与实际命令

用户所称“idearesearch”的exact skill没有出现在可用目录；找到本地ResearchStudio-Idea套件，其README定义search→generate→review，检索building block是 `skills/paper_search/SKILL.md`。本任务是查推理方案，因此调用其paper-search而非生成一个新研究idea。另调用已安装paper-search，再以原生web检索官方paper/repo/blog补召回。

1. Installed skill：`/Users/LOCAL_USER/.codex/skills/paper-search/SKILL.md`；Python3.9运行：

```bash
python3 /Users/LOCAL_USER/.codex/skills/paper-search/scripts/search_papers.py \
  --query 'low bit quantization speculative decoding efficient LLM inference GPU' \
  --start-year 2022 --end-year 2026 --max-papers 10
```

2. ResearchStudio-Idea：`archive/ResearchStudio/ResearchStudio-Idea/skills/paper_search/SKILL.md`；先Python3.9，随后用Python3.11修复运行环境并复核（不是因429而无限重试）。两次均保存全部日志；Py3.11结果作为下表选择版本：

```bash
PAPER_SEARCH_TIMEOUT_SECONDS=30 PAPER_SEARCH_MAX_ATTEMPTS=1 \
  /Users/LOCAL_USER/anaconda3/bin/python3.11 \
  /Users/LOCAL_USER/Documents/Workspace/archive/ResearchStudio/ResearchStudio-Idea/skills/paper_search/scripts/search_papers.py \
  --queries 'Qwen3.8 inference|Marlin quantization|EAGLE speculative decoding|DFlash diffusion speculative decoding|Gated DeltaNet inference' \
  --start-year 2022 --end-year 2026 --max-papers 10
```

六源：Semantic Scholar、OpenAlex、arXiv、OpenReview、Crossref、DBLP；不设min-score，保留所有低相关与同名噪音。Model knowledge作为额外补召回，随后查primary来源。

[index](../assets/qwen38-4090-paper-search-2026/index.md) 保存3个完整stdout/stderr日志及SHA-256；下列完整表保留CLI排序。API citations是检索snapshot，0不代表无人引用，year有时是首次arXiv年或null，venue可能错配；不是当前影响力排名。

## ResearchStudio-Idea完整结果

per-source hits: arxiv=50, dblp=0, open_alex=50, openreview=0, semantic_scholar=0, crossref=50。
119 unique records，31个cross-source duplicates merged；没有过滤。OpenReview没有匹配，DBLP失败，Semantic Scholar全query受429限流。

| # | Title | API year | API venue | API citations | Score | Sources |
|---|---|---|---|---:|---:|---|
| [1](https://doi.org/10.48550/arxiv.2606.02091) | DFlare: Scaling Up Draft Capacity for Block Diffusion Speculative Decoding | 2026 | arXiv (Cornell University) | 0 | 6 | open_alex |
| [2](http://arxiv.org/abs/2602.06036v2) | DFlash: Block Diffusion for Flash Speculative Decoding | 2026 | arXiv | 0 | 6 | arxiv |
| [3](http://arxiv.org/abs/2609.34832v1) | BV Loss: Block Verification-Aware Loss for Block Diffusion Speculative Decoding | 2026 | arXiv | 0 | 6 | arxiv |
| [4](https://doi.org/10.5281/zenodo.22568252) | HEDGE: Entropy-Gated Adaptive Tree-Depth Selection for EAGLE3 Speculative Decoding | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 5 | open_alex |
| [5](https://doi.org/10.48550/arxiv.2607.19223) | AdaFlash: Adaptive Speculative Decoding via On-Policy Distilled Diffusion Drafters | 2026 | arXiv (Cornell University) | 0 | 5 | open_alex |
| [6](https://doi.org/10.5281/zenodo.21220228) | thc1006/qwen3.6-speculative-decoding-v100: v1.0: DFlash on 2x V100 (controlled dense-vs-MoE sweep) | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 5 | open_alex |
| [7](http://arxiv.org/abs/2604.12989v1) | Accelerating Speculative Decoding with Block Diffusion Draft Trees | 2026 | arXiv | 0 | 5 | arxiv |
| [8](http://arxiv.org/abs/2608.02438v1) | xPress: Parallel Refinement for Diffusion Drafters in Speculative Decoding | 2026 | arXiv | 0 | 5 | arxiv |
| [9](http://arxiv.org/abs/2608.13524v1) | DARTree: Speculative Diffusion Decoding with Autoregressive Draft Trees | 2026 | arXiv | 0 | 5 | arxiv |
| [10](http://arxiv.org/abs/2608.20961v1) | TreeWY: Speculative Verification for Gated DeltaNet Hybrids | 2026 | arXiv | 0 | 5 | arxiv |
| [11](https://doi.org/10.48550/arxiv.2401.15077) | EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty | 2024 | arXiv (Cornell University) | 6 | 4 | open_alex,arxiv |
| [12](http://arxiv.org/abs/2408.05636v4) | Speculative Diffusion Decoding: Accelerating Language Generation through Diffusion | 2024 | arXiv | 6 | 4 | arxiv,crossref |
| [13](https://doi.org/10.3390/math14122137) | SW-SpeedDLM: Sliding Window Speculative Decoding for Diffusion Language Models Under Long Context Constraints | 2026 | Mathematics | 5 | 4 | crossref |
| [14](https://doi.org/10.1109/bigdataservice70481.2026.00022) | Accelerating Paypal's Commerce Agent with Speculative Decoding: An Empirical Study on EAGLE3 with Fine-Tuned Nemotron Models | 2026 | — | 0 | 4 | open_alex |
| [15](https://doi.org/10.48550/arxiv.2512.20573) | Fail Fast, Win Big: Rethinking the Drafting Strategy in Speculative Decoding via Diffusion LLMs | 2025 | arXiv (Cornell University) | 0 | 4 | open_alex |
| [16](http://arxiv.org/abs/2605.01106v1) | Component-Aware Self-Speculative Decoding in Hybrid Language Models | 2026 | arXiv | 0 | 4 | arxiv |
| [17](http://arxiv.org/abs/2602.13836v2) | Speculative Decoding with a Speculative Vocabulary | 2026 | arXiv | 0 | 4 | arxiv,crossref |
| [18](https://doi.org/10.21203/rs.3.rs-10319218/v1) | Multi-Tenant Edge-Cloud Hybrid LLM Serving using Speculative Decoding and Quantization | None | — | 0 | 4 | crossref |
| [19](https://doi.org/10.54097/w9c56t64) | Uncertainty-Aware Speculative Decoding for Diffusion Language Models in Long Document Generation | 2026 | Computer Life | 0 | 4 | crossref |
| [20](https://doi.org/10.21203/rs.3.rs-11160904/v1) | A Node-by-Node White-Box Walkthrough of a Quantized Hybrid Gated DeltaNet Language Model: Instrument Calibration and the Information Trajectory from Embedding to Output | None | — | 0 | 4 | crossref |
| [21](https://doi.org/10.1145/3710848.3710871) | MARLIN: Mixed-Precision Auto-Regressive Parallel Inference on Large Language Models | 2025 | arXiv | 23 | 3 | open_alex,arxiv |
| [22](https://doi.org/10.18653/v1/2026.findings-acl.1048) | DiffuSpec: Unlocking Diffusion Language Models for Speculative Decoding | 2026 | Findings of the Association for Computational Linguistics: ACL 2026 | 1 | 3 | open_alex,crossref |
| [23](https://doi.org/10.48550/arxiv.2603.08088) | EAGLE-Pangu: Accelerator-Safe Tree Speculative Decoding on Ascend NPUs | 2026 | arXiv (Cornell University) | 0 | 3 | open_alex,arxiv |
| [24](https://doi.org/10.5281/zenodo.22210487) | Fixed-K Speculative Decoding vs. EAGLE-3: A Like-for-Like, Energy-Measured Comparison in vLLM and SGLang | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 3 | open_alex |
| [25](https://doi.org/10.5281/zenodo.21090326) | LongFlash: Accelerating Agentic Coding Systems via Diffusion-Retrieval Speculative Decoding | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 3 | open_alex |
| [26](https://doi.org/10.5281/zenodo.20766118) | FlashSpec: Adaptive Speculative Decoding with Online Bandit Draft Selection and Triton-Optimised Verification | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 3 | open_alex,crossref |
| [27](http://arxiv.org/abs/2508.17739v2) | Speculative Safety-Aware Decoding | 2025 | arXiv | 0 | 3 | arxiv |
| [28](http://arxiv.org/abs/2503.00491v1) | Tutorial Proposal: Speculative Decoding for Efficient LLM Inference | 2025 | arXiv | 0 | 3 | arxiv |
| [29](http://arxiv.org/abs/2409.00142v1) | Dynamic Depth Decoding: Faster Speculative Decoding for LLMs | 2024 | arXiv | 0 | 3 | arxiv |
| [30](http://arxiv.org/abs/2603.03251v3) | Speculative Speculative Decoding | 2026 | arXiv | 0 | 3 | arxiv |
| [31](http://arxiv.org/abs/2402.01528v4) | Decoding Speculative Decoding | 2024 | arXiv | 0 | 3 | arxiv |
| [32](http://arxiv.org/abs/2605.22791v1) | Gated DeltaNet-2: Decoupling Erase and Write in Linear Attention | 2026 | arXiv | 0 | 3 | arxiv |
| [33](http://arxiv.org/abs/2605.16640v1) | Provably Shorter Scratchpads in Hybrid DeltaNet-Attention Decoders | 2026 | arXiv | 0 | 3 | arxiv |
| [34](https://doi.org/10.64898/2026.09.02.749017) | EvSpark: Lossless Speculative Decoding for Hybrid DNA Foundation Models | None | — | 0 | 3 | crossref |
| [35](https://doi.org/10.18653/v1/2026.gem-main.33) | Speculative Refinement: A Hybrid Autoregressive Diffusion Decoding Strategy and Its Behavior Across Benchmarks | 2026 | Proceedings of the Fifth Workshop on Generation, Evaluation and Metrics (GEM) | 0 | 3 | crossref |
| [36](https://doi.org/10.18653/v1/2024.naacl-long.88) | REST: Retrieval-Based Speculative Decoding | 2024 | — | 30 | 2 | open_alex |
| [37](https://doi.org/10.52202/075280-1314) | SpecTr: Fast Speculative Decoding via Optimal Transport | 2023 | — | 8 | 2 | open_alex |
| [38](https://doi.org/10.52202/075280-1705) | Speculative Decoding with Big Little Decoder | 2023 | — | 4 | 2 | open_alex |
| [39](https://doi.org/10.1109/eibdct69742.2026.11566699) | A Unified Inference Optimization Framework for Qwen3-VL-2B-Instruct | 2026 | 2026 5th International Conference on Electronic Information Engineering, Big Data and Computer Technology (EIBDCT) | 1 | 2 | open_alex,crossref |
| [40](https://doi.org/10.52202/079017-4067) | A Theoretical Perspective for Speculative Decoding Algorithm | 2024 | — | 1 | 2 | open_alex |
| [41](https://doi.org/10.18653/v1/2026.findings-acl.1809) | Speculative Verification: Exploiting Information Gain for Speculative Decoding | 2026 | Findings of the Association for Computational Linguistics: ACL 2026 | 1 | 2 | crossref |
| [42](https://doi.org/10.5281/zenodo.20453532) | Qwen3-235B Inference Efficiency on SWE-Bench Verified Under Computational Constraints | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 2 | open_alex |
| [43](https://doi.org/10.5281/zenodo.20636496) | Impact of Inference-Optimized Fine-Tuning on Llama-3.1-8B Robustness in Ruler Positional Encoding Tasks | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 2 | open_alex |
| [44](https://doi.org/10.34777/3v9t-vb69) | gated-deltanet-lte-0.4B-10B | 2025 | Idiap Research Institute - Main Repository | 0 | 2 | open_alex |
| [45](https://doi.org/10.34777/fmkn-e764) | gated-deltanet-lte-1.4B-30B | 2025 | Idiap Research Institute - Main Repository | 0 | 2 | open_alex |
| [46](https://doi.org/10.34777/ya9s-3h75) | gated-deltanet-nsa-1.4B-30B | 2025 | Idiap Research Institute - Main Repository | 0 | 2 | open_alex |
| [47](https://doi.org/10.52202/079017-1232) | Gated Inference Network: Inference and Learning State-Space Models | 2024 | Advances in Neural Information Processing Systems 37 | 0 | 2 | open_alex,crossref |
| [48](http://arxiv.org/abs/2508.04435v2) | Cognitive Effort in the Two-Step Task: An Active Inference Drift-Diffusion Model Approach | 2025 | arXiv | 0 | 2 | arxiv |
| [49](http://arxiv.org/abs/2410.05265v2) | PrefixQuant: Eliminating Outliers by Prefixed Tokens for Large Language Models Quantization | 2024 | arXiv | 0 | 2 | arxiv |
| [50](http://arxiv.org/abs/2203.16487v6) | Speculative Decoding: Exploiting Speculative Execution for Accelerating Seq2seq Generation | 2022 | arXiv | 0 | 2 | arxiv |
| [51](http://arxiv.org/abs/2607.16831v1) | Technical Report: AI-Assisted Gated DeltaNet Optimization on NVIDIA Blackwell | 2026 | arXiv | 0 | 2 | arxiv |
| [52](http://arxiv.org/abs/2609.14320v1) | SpectralShift: Effective Context Window Extension of Gated DeltaNet via Spectral Reparameterization | 2026 | arXiv | 0 | 2 | arxiv |
| [53](http://arxiv.org/abs/2604.21100v1) | Preconditioned DeltaNet: Curvature-aware Sequence Modeling for Linear Recurrences | 2026 | arXiv | 0 | 2 | arxiv |
| [54](https://doi.org/10.36227/techrxiv.176799759.97935754/v1) | Medical-Qwen3: A Robust Medical LLM via Two-Stage LoRA Training and Weighted Adapter Merging | None | — | 0 | 2 | crossref |
| [55](https://doi.org/10.36227/techrxiv.177101038.80960856/v1) | Transactional KV Caching for Speculative Decoding under Paged KV Memory | None | — | 0 | 2 | crossref |
| [56](https://doi.org/10.21437/interspeech.2025-382) | Simultaneous Masked and Unmasked Decoding with Speculative Decoding Masking for Fast ASR without Accuracy Loss | 2025 | Interspeech 2025 | 0 | 2 | crossref |
| [57](https://doi.org/10.2139/ssrn.7405518) | Mitigating Transaction-cost Degradation in Financial Forecasting via Volatility-gated Inference | None | — | 0 | 2 | crossref |
| [58](https://doi.org/10.21203/rs.3.rs-4319376/v1) | GANLI: Elevating Natural Language Inference through Advanced Gated Attention Mechanisms | None | — | 0 | 2 | crossref |
| [59](https://doi.org/10.1101/2025.06.20.660684) | Bayesian inference of functional asymmetry in a ligand-gated ion channel | None | — | 0 | 2 | crossref |
| [60](https://doi.org/10.2139/ssrn.7044338) | A Coherence-Gated Extension of Bayesian Inference under Viscous Time Theory: Classical Limit, Informational Viscosity, and Structural Reasoning under Uncertainty | None | — | 0 | 2 | crossref |
| [61](https://doi.org/10.1038/s42003-025-09056-x) | Bayesian inference of functional asymmetry in the homotrimeric ligand-gated ion channel P2X2 | 2025 | Communications Biology | 0 | 2 | crossref |
| [62](https://doi.org/10.22541/authorea.15005064/v1) | ECG-ExitNet: A Morphology-Aware Confidence-Gated Early-Exit Framework with Tiered Sub-Model Decomposition for Activation-SRAM-Decoupled ECG Inference on Wearable Microcontrollers | None | — | 0 | 2 | crossref |
| [63](https://doi.org/10.3390/app16042023) | TDI-SF: Trustworthy Dynamic Inference via Uncertainty-Gated Retrieval and Similarity-Gated Strict Fallback | 2026 | Applied Sciences | 0 | 2 | crossref |
| [64](https://doi.org/10.1109/apccas67402.2025.11376659) | Sparsity-Gated Fp16 Mac Pipeline for Energyefficient Edram-Based Neural Inference | 2025 | 2025 IEEE Asia Pacific Conference on Circuits and Systems (APCCAS) | 0 | 2 | crossref |
| [65](https://doi.org/10.1103/physrevx.12.011010) | Node Metadata Can Produce Predictability Crossovers in Network Inference Problems | 2022 | Physical Review X | 17 | 1 | open_alex |
| [66](https://doi.org/10.1109/tsp.2023.3322813) | Quantized Low-Rank Multivariate Regression With Random Dithering | 2023 | IEEE Transactions on Signal Processing | 12 | 1 | open_alex |
| [67](https://doi.org/10.1109/isit54713.2023.10206722) | Strategic Quantization | 2023 | — | 11 | 1 | open_alex |
| [68](https://doi.org/10.18653/v1/2024.emnlp-main.197) | QUIK: Towards End-to-end 4-Bit Inference on Generative Large Language Models | 2024 | — | 10 | 1 | open_alex |
| [69](https://doi.org/10.52202/068431-1065) | FP8 Quantization: The Power of the Exponent | 2022 | — | 10 | 1 | open_alex |
| [70](https://doi.org/10.1109/cisat66811.2025.11181979) | Qwen3-Powered Log Classification for Improved SOC Decision-Making | 2025 | 2025 8th International Conference on Computer Information Science and Application Technology (CISAT) | 2 | 1 | crossref |
| [71](https://doi.org/10.57967/hf/10624) | Qwen3.8_UnCen | 2026 | Hugging Face | 0 | 1 | open_alex |
| [72](https://doi.org/10.57967/hf/10615) | Qwen3.8-27B | 2026 | Hugging Face | 0 | 1 | open_alex |
| [73](https://doi.org/10.5281/zenodo.18484777) | daviden1013/llm-ie: LLM_IE v1.4.1 | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 1 | open_alex |
| [74](https://doi.org/10.5281/zenodo.10655245) | milankl/LinLogQuantization.jl: v0.3.0 | 2024 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 1 | open_alex |
| [75](https://doi.org/10.1007/978-3-031-77575-8_5) | Quantization conditions | 2025 | — | 0 | 1 | open_alex |
| [76](https://doi.org/10.13140/rg.2.2.27879.62889) | Quantization, high-rate quantizers, and waveform encoding | 2023 | — | 0 | 1 | open_alex |
| [77](https://doi.org/10.13140/rg.2.2.30765.50406) | Full quantization vs partial quantization | 2024 | — | 0 | 1 | open_alex |
| [78](https://doi.org/10.1109/asens69964.2026.11605337) | DBGT: Dual-Branch Gated Transformer for Network Intrusion Detection | 2026 | — | 0 | 1 | open_alex |
| [79](https://doi.org/10.5281/zenodo.22970238) | A Shared Gated Expansion for Multi-Class Dendritic Gated Networks | 2026 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 1 | open_alex |
| [80](http://arxiv.org/abs/2506.08599v4) | Geometric Hyperscanning of Affect under Active Inference | 2025 | arXiv | 0 | 1 | arxiv |
| [81](http://arxiv.org/abs/2609.25611v1) | Qwen3.8-Omni: Towards Native Omni-Modal Agents | 2026 | arXiv | 0 | 1 | arxiv |
| [82](http://arxiv.org/abs/2409.15080v1) | Integrating Optimal Transport and Structural Inference Models for GRN Inference from Single-cell Data | 2024 | arXiv | 0 | 1 | arxiv |
| [83](http://arxiv.org/abs/2508.15773v1) | Scaling Group Inference for Diverse and High-Quality Generation | 2025 | arXiv | 0 | 1 | arxiv |
| [84](http://arxiv.org/abs/2208.10601v1) | Deriving time-averaged active inference from control principles | 2022 | arXiv | 0 | 1 | arxiv |
| [85](http://arxiv.org/abs/2207.06970v1) | Spin glass systems as collective active inference | 2022 | arXiv | 0 | 1 | arxiv |
| [86](http://arxiv.org/abs/2310.20058v3) | Generalized Asymptotic Limit Theory and Inference for Isotonic Regression | 2023 | arXiv | 0 | 1 | arxiv |
| [87](http://arxiv.org/abs/2504.09775v6) | MIST: A Co-Design Framework for Heterogeneous, Multi-Stage LLM Inference | 2025 | arXiv | 0 | 1 | arxiv |
| [88](http://arxiv.org/abs/2307.04421v3) | Towards Enabling Cardiac Digital Twins of Myocardial Infarction Using Deep Computational Models for Inverse Inference | 2023 | arXiv | 0 | 1 | arxiv |
| [89](http://arxiv.org/abs/2407.02078v1) | MARLIN: A Cloud Integrated Robotic Solution to Support Intralogistics in Retail | 2024 | arXiv | 0 | 1 | arxiv |
| [90](http://arxiv.org/abs/2407.15508v3) | Compensate Quantization Errors+: Quantized Models Are Inquisitive Learners | 2024 | arXiv | 0 | 1 | arxiv |
| [91](http://arxiv.org/abs/2406.16299v1) | Compensate Quantization Errors: Make Weights Hierarchical to Compensate Each Other | 2024 | arXiv | 0 | 1 | arxiv |
| [92](http://arxiv.org/abs/2505.14302v1) | Scaling Law for Quantization-Aware Training | 2025 | arXiv | 0 | 1 | arxiv |
| [93](http://arxiv.org/abs/2404.12759v1) | decoupleQ: Towards 2-bit Post-Training Uniform Quantization via decoupling Parameters into Integer and Floating Points | 2024 | arXiv | 0 | 1 | arxiv |
| [94](http://arxiv.org/abs/2206.07653v1) | A Valid Quantization of a Half-Harmonic Oscillator Field Theory | 2022 | arXiv | 0 | 1 | arxiv |
| [95](http://arxiv.org/abs/2508.01931v1) | Marlin: Efficient Coordination for Autoscaling Cloud DBMS (Extended Version) | 2025 | arXiv | 0 | 1 | arxiv |
| [96](http://arxiv.org/abs/2211.06627v3) | MARLIN: Masked Autoencoder for facial video Representation LearnINg | 2022 | arXiv | 0 | 1 | arxiv |
| [97](http://arxiv.org/abs/2206.10455v2) | Automated Coronary Calcium Scoring using U-Net Models through Semi-supervised Learning on Non-Gated CT Scans | 2022 | arXiv | 0 | 1 | arxiv |
| [98](http://arxiv.org/abs/2608.30695v1) | Liquid Gated Attention | 2026 | arXiv | 0 | 1 | arxiv |
| [99](https://doi.org/10.1007/978-981-92-3716-6_20) | Reconstructing Qwen3 into Qwen3-Protein: A Versatile Biophysics-Grounded Protein Language Foundation Model for PTMs and Downstream Tasks | 2027 | Lecture Notes in Computer Science Bioinformatics Research and Applications | 0 | 1 | crossref |
| [100](https://doi.org/10.54254/2753-8818/2026.33535) | Qwen3:4 Verification of the Feasibility of the PPO Strategy in Quantitative Trading | 2026 | Theoretical and Natural Science | 0 | 1 | crossref |
| [101](https://doi.org/10.18653/v1/2026.semeval-1.377) | ABARUAH at SemEval-2026 Task 9: Multilingual Polarization Detection across Seven Indic Languages using Qwen3 | 2026 | Proceedings of the 20th International Workshop on Semantic Evaluation (2026) | 0 | 1 | crossref |
| [102](https://doi.org/10.1117/12.3120243) | Social and behavioral determinants of health classification from clinical notes using Qwen3-8B with low-rank adaptation | 2026 | International Conference on Machine Vision and Deep Learning (MVDL 2026) | 0 | 1 | crossref |
| [103](https://doi.org/10.18653/v1/2026.chum-1.7) | Does Bigger Mean Funnier? Evaluating Humor Generation Across the Qwen3 Model Family | 2026 | Proceedings of the 2nd Workshop on Computational Humor (CHum 2026) | 0 | 1 | crossref |
| [104](https://doi.org/10.1109/eitce70137.2026.11634352) | Adapting FlexLLMGen to Qwen3 Dense and Mixture-of-Experts Models | 2026 | 2026 10th International Conference on Electronic Information Technology and Computer Engineering (EITCE) | 0 | 1 | crossref |
| [105](https://doi.org/10.18653/v1/2026.bionlp-2.18) | LinguIUTics at PsyDefDetect: Iterative Imbalance-Aware Fine-tuning of Qwen3-8B for Psychological Defense Mechanism Classification | 2026 | Proceedings of the BioNLP 2026 (Shared Tasks) | 0 | 1 | crossref |
| [106](https://doi.org/10.1093/acref/9780195301731.013.39033) | Briscoe, Marlin | 2023 | African American Studies Center | 0 | 1 | crossref |
| [107](https://doi.org/10.1093/oed/6405773695) | marlin, n.² | 2023 | Oxford English Dictionary | 0 | 1 | crossref |
| [108](https://doi.org/10.1093/oed/1798849608) | marlin, n.¹ | 2023 | Oxford English Dictionary | 0 | 1 | crossref |
| [109](https://doi.org/10.52202/079017-3157) | DeNetDM: Debiasing by Network Depth Modulation | 2024 | — | 3 | 0 | open_alex |
| [110](https://doi.org/10.15578/marlin.v3.i1.2022.55-66) | KAJIAN KARAKTERISTIK GELOMBANG  DI KECAMATAN BUMI WARAS, LAMPUNG | 2022 | Marlin | 1 | 0 | crossref |
| [111](https://doi.org/10.5281/zenodo.10655246) | milankl/LinLogQuantization.jl: v0.2.1 | 2024 | Zenodo (CERN European Organization for Nuclear Research) | 0 | 0 | open_alex |
| [112](https://doi.org/10.17632/v3x4782yd8.1) | Transfer-DeltaDeltaG | 2024 | Data Archiving and Networked Services (DANS) | 0 | 0 | open_alex |
| [113](https://doi.org/10.15578/marlin.v4i2) |  | 2023 | MARLIN | 0 | 0 | crossref |
| [114](https://doi.org/10.15578/marlin.v5i1) |  | 2024 | MARLIN | 0 | 0 | crossref |
| [115](https://doi.org/10.15578/marlin.v5.i2.2024.115-124) | POTENSI EKOWISATA WILAYAH PESISIR DESA PARANGTRITIS, KABUPATEN BANTUL | 2024 | MARLIN | 0 | 0 | crossref |
| [116](https://doi.org/10.15578/marlin.v3.i2.2022.77-85) | PROFIL USAHA PENGOLAHAN NUGGET IKAN GABUS  DI UMKM RINA | 2022 | Marlin | 0 | 0 | crossref |
| [117](https://doi.org/10.15578/marlin.v4.i1.2023.23-33) | IDENTIFIKASI POTENSI WILAYAH DAN USAHA PERIKANAN DI KECAMATAN KAPETAKAN, KABUPATEN CIREBON | 2023 | Marlin | 0 | 0 | crossref |
| [118](https://doi.org/10.30603/am.v19i2.3894) | Kriminalisasi Trading in Influence dalam Tindak Pidana Korupsi | 2023 | Al-Mizan | 0 | 0 | crossref |
| [119](https://doi.org/10.32388/w5gj1c) | [survey] Review of: "Draft Model Knows When to Stop: A Self-Verification Length Policy for Speculative Decoding" | 2025 | — | 0 | 2 | crossref |

## Installed skill完整结果

30条原始记录；此旧脚本按source分组，未做跨source去重。OpenAlex环境import失败、DBLP错误、OpenReview0。

### semantic_scholar (10 records)

| # | Title | API year | API venue | API citations | Score | Sources |
|---|---|---|---|---:|---:|---|
| [1](https://www.semanticscholar.org/paper/e2584f00b9d5c6263f5c201e53a1390c534aa436) | DecDEC: A Systems Approach to Advancing Low-Bit LLM Quantization | 2024 | USENIX Symposium on Operating Systems Design and Implementation | 11 | — | semantic_scholar |
| [2](https://www.semanticscholar.org/paper/e69310937deff1de01f24fe2b74114bf183c4814) | SingularBit: Exploiting Synergy of Singular Value Decomposition and Low-Bit Quantization for Weight and KV Compression in LLM Inference | 2026 | International Symposium on Computer Architecture | 0 | — | semantic_scholar |
| [3](https://www.semanticscholar.org/paper/f3028fb503a280c71df0e314cfd82c575f529dac) | 70% Size, 100% Accuracy: Lossless LLM Compression for Efficient GPU Inference via Dynamic-Length Float | 2025 | Neural Information Processing Systems | 33 | — | semantic_scholar |
| [4](https://www.semanticscholar.org/paper/21b5b26abba4b69a8e531c68ccde48d50041102e) | FlashQuant: Sparse-Dense Fusion for Memory-Efficient Outlier-Aware LLM Inference | 2026 | — | 0 | — | semantic_scholar |
| [5](https://www.semanticscholar.org/paper/f6efc61b2656d856b22c51e6564f091d8ae730d3) | TFLOP: Towards Energy-Efficient LLM Inference An FPGA-Affinity Accelerator with Unified LUT-based OPtimization | 2026 | Asia and South Pacific Design Automation Conference | 0 | — | semantic_scholar |
| [6](https://www.semanticscholar.org/paper/d16008cb55bd7b38e4ba8d13754926c9a8b37182) | Progressive Mixed-Precision Decoding for Efficient LLM Inference | 2024 | International Conference on Learning Representations | 19 | — | semantic_scholar |
| [7](https://www.semanticscholar.org/paper/95cbde8d97d87fa60a3e6749e467368452f7f050) | UnionSparse: An Index-Efficient Sparsity Framework for Low-Bit Sparse LLM Inference on Edge | 2026 | — | 0 | — | semantic_scholar |
| [8](https://www.semanticscholar.org/paper/51279fb5caaec6989f2acf25f71d11832e70bc38) | CubicQuant: Parametric Non-Uniform Codebooks for High-Throughput LLM Inference with 1-8-Bit Weights | 2026 | — | 0 | — | semantic_scholar |
| [9](https://www.semanticscholar.org/paper/50f250b0b41b0e7f55daadd4a231e7ad79c46b52) | DeFT: Decoding with Flash Tree-attention for Efficient Tree-structured LLM Inference | 2024 | International Conference on Learning Representations | 19 | — | semantic_scholar |
| [10](https://www.semanticscholar.org/paper/1281e1ffdce1bb6c6eb4180c6cb8aa00c5f69848) | MixPE: Quantization and Hardware Co-design for Efficient LLM Inference | 2024 | arXiv.org | 13 | — | semantic_scholar |

### open_alex (0 records)

本轮无结果；失败原因见下方原始错误。

### arxiv (10 records)

| # | Title | API year | API venue | API citations | Score | Sources |
|---|---|---|---|---:|---:|---|
| [1](http://arxiv.org/abs/2503.00491v1) | Tutorial Proposal: Speculative Decoding for Efficient LLM Inference | 2025 | arXiv | 0 | — | arxiv |
| [2](http://arxiv.org/abs/2508.17739v2) | Speculative Safety-Aware Decoding | 2025 | arXiv | 0 | — | arxiv |
| [3](http://arxiv.org/abs/2203.16487v6) | Speculative Decoding: Exploiting Speculative Execution for Accelerating Seq2seq Generation | 2022 | arXiv | 0 | — | arxiv |
| [4](http://arxiv.org/abs/2605.01106v1) | Component-Aware Self-Speculative Decoding in Hybrid Language Models | 2026 | arXiv | 0 | — | arxiv |
| [5](http://arxiv.org/abs/2609.21704v1) | SpecQuant: Speculative Decoding with Multi-Parent Quantization for Adaptive LLM Inference | 2026 | arXiv | 0 | — | arxiv |
| [6](http://arxiv.org/abs/2308.04623v1) | Accelerating LLM Inference with Staged Speculative Decoding | 2023 | arXiv | 0 | — | arxiv |
| [7](http://arxiv.org/abs/2406.02532v3) | SpecExec: Massively Parallel Speculative Decoding for Interactive LLM Inference on Consumer Devices | 2024 | arXiv | 0 | — | arxiv |
| [8](http://arxiv.org/abs/2507.02620v3) | FlowSpec: Continuous Pipelined Speculative Decoding for Efficient Distributed LLM Inference | 2025 | arXiv | 0 | — | arxiv |
| [9](http://arxiv.org/abs/2601.17768v2) | LLM-42: Enabling Determinism in LLM Inference with Verified Speculation | 2026 | arXiv | 0 | — | arxiv |
| [10](http://arxiv.org/abs/2412.18934v2) | Dovetail: A CPU/GPU Heterogeneous Speculative Decoding for LLM inference | 2024 | arXiv | 0 | — | arxiv |

### openreview (0 records)

本轮无结果；失败原因见下方原始错误。

### crossref (10 records)

| # | Title | API year | API venue | API citations | Score | Sources |
|---|---|---|---|---:|---:|---|
| [1](https://doi.org/10.21203/rs.3.rs-10319218/v1) | Multi-Tenant Edge-Cloud Hybrid LLM Serving using Speculative Decoding and Quantization | None | — | 0 | — | crossref |
| [2](https://doi.org/10.1109/icpc2t68221.2026.11646348) | SpecQuant – Speculative Decoding with Multi-Parent Quantization for Adaptive LLM Inference | 2026 | 2026 Fifth International Conference on Power, Control and Computing Technologies (ICPC2T) | 0 | — | crossref |
| [3](https://doi.org/10.18653/v1/2025.emnlp-main.879) | Dovetail: A CPU/GPU Heterogeneous Speculative Decoding for LLM inference | 2025 | Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing | 3 | — | crossref |
| [4](https://doi.org/10.2139/ssrn.6854700) | Weight-Only Quantization Does Not Always Save Energy: An Empirical Study of LLM Inference Across NVIDIA GPU Platforms | None | — | 0 | — | crossref |
| [5](https://doi.org/10.1109/wcsp68525.2025.1010651) | Communication-Efficient Collaborative LLM Inference via Distributed Speculative Decoding | 2025 | 2025 Seventeenth International Conference on Wireless Communications and Signal Processing (WCSP) | 7 | — | crossref |
| [6](https://doi.org/10.18653/v1/2026.acl-long.1454) | VecInfer: Efficient LLM Inference with Low-Bit KV Cache via Outlier-Suppressed Vector Quantization | 2026 | Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) | 0 | — | crossref |
| [7](https://doi.org/10.52202/079017-2923) | Speculative Decoding with CTC-based Draft Model for LLM Inference Acceleration | 2024 | Advances in Neural Information Processing Systems 37 | 0 | — | crossref |
| [8](https://doi.org/10.1109/iwqos70441.2026.11661086) | It Takes Two: Embracing Sparsity and Speculative Decoding for Efficient LLM Inference | 2026 | 2026 IEEE/ACM International Symposium on Quality of Service (IWQoS) | 0 | — | crossref |
| [9](https://doi.org/10.1145/3774906.3802783) | PELM: Power Efficient On-Device LLM Inference with Speculative Decoding and Dynamic Voltage Frequency Scaling | 2026 | Proceedings of the 2026 ACM/IEEE International Conference on Embedded Artificial Intelligence and Sensing Systems | 0 | — | crossref |
| [10](https://doi.org/10.1109/tcomm.2026.3712530) | Efficient LLM Inference Over Heterogeneous Edge Networks With Speculative Decoding | 2026 | IEEE Transactions on Communications | 0 | — | crossref |

### dblp (0 records)

本轮无结果；失败原因见下方原始错误。

## Model Knowledge补召回与primary核验

以下从历史知识补充，再查arXiv/官方代码确认；不重复上面的API记录。没有编造citation count。

| 论文 | 年 / venue | primary来源 | 用处 |
|---|---|---|---|
| GPTQ | ICLR2023 | [2210.17323](https://arxiv.org/abs/2210.17323) | W4/W3权重表示基础；已归档 |
| QTIP | NeurIPS2024 Spotlight | [2406.11235](https://arxiv.org/abs/2406.11235) | EXL3机制依据；已归档 |
| EAGLE3 | NeurIPS2025 | [2503.01840](https://arxiv.org/abs/2503.01840) | draft训练与多层feature融合；已归档 |
| Medusa | 2024 | [2401.10774](https://arxiv.org/abs/2401.10774) | multi-head/tree verify历史路线；目标专用head未核验 |
| Lean Attention | 2024 | [2405.10480](https://arxiv.org/abs/2405.10480) | long-context decode attention；目标GDN未覆盖 |

## 原生web补召回长名单与筛选

| 候选 / primary来源 | 方向 | 决策及原因 |
|---|---|---|
| [Qwen3.8官方config](https://huggingface.co/Qwen/Qwen3.8-27B/blob/main/config.json) | 目标身份 | model_type=qwen3_5；不能被第三方“纯GQA”描述误导，hybrid支持为硬门槛 |
| [ExLlamaV3](https://github.com/turboderp-org/exllamav3) | EXL3 consumer GPU | P0 engine；README明确EXL3基于QTIP、speculation和cache quant，具体目标看新commit |
| [DFlash2官方blog](https://inco.ai/blog/dflash2/) / [draft](https://huggingface.co/incoai/Qwen3.8-27B-DFlash2) | selector+conv parallel draft | P0，目标checkpoint与SGLang/vLLM/llama.cpp配方公开；需低bit才能适配24GB |
| [SGLang Qwen3.8 recipe](https://github.com/sgl-project/sglang/blob/main/docs/cookbook/autoregressive/Qwen/Qwen3.8-27B.mdx) | serving hybrid+draft | P0 engine路径，论文缓存不是当前runtime版本 |
| [r0b0tlab EXL3 recipe](https://github.com/r0b0tlab/qwen38-exl3-dflash2) | 24GB native DFlash2 | 优先复现候选，固定commit/模型；旧overlay已废弃 |
| [MiaAI-Lab EXL3 kit](https://github.com/MiaAI-Lab/Qwen3.8-27B-DFlash2-EXL3-5.0bpw) | EXL3 MTP/DFlash2 | 候选，5bpw显存需检查；fork特性不能算stock upstream |
| [thc1006 3090 study](https://github.com/thc1006/qwen3.8-speculative-decoding-rtx3090) | MTP/DFlash2 depth sweep | 保留速度/方法证据；仅2stars不作为流行度首选；跨GPU外推弱 |
| [Qwen3.8 ROCm](https://github.com/AIwork4me/Qwen3.8-27B-ROCm) | AMD DFlash2/MTP | 留长名单，硬件与4090不匹配 |
| [MARLIN](https://arxiv.org/abs/2408.11743) | W4A16 matmul | 已归档，作为支持目标的engine内核 |
| [FLUTE](https://arxiv.org/abs/2407.10960) | LUT低bit kernel | 保留内核长名单；未确认目标hybrid完整runtime |
| [GemLite](https://github.com/mobiusml/gemlite) | Triton低bit kernel | 保留候选；需要目标checkpoint/engine适配，不是完整服务端 |
| [BitBLAS](https://github.com/microsoft/BitBLAS) | mixed precision library | 保留内核路线，未把generic kernel当目标部署方案 |
| [QQQ](https://arxiv.org/abs/2406.09904) | W4A8 prefill/decode | 研究背景，旧Llama评估不能证明目标支持 |
| [QuIP#](https://arxiv.org/abs/2402.04396) | Hadamard+lattice quant | QTIP前驱；归档QTIP覆盖更直接EXL3机制，暂不重复新增 |
| [VPTQ](https://arxiv.org/abs/2409.17066) | vector PTQ | 保留低bit路线，目标artifact未核验 |
| [ParoQuant](https://arxiv.org/abs/2511.10645) | reasoning quant / rotation | 保留精度/latency研究，未观察目标27B直接支持 |
| [EAGLE](https://arxiv.org/abs/2401.15077) / [EAGLE2](https://arxiv.org/abs/2406.16858) | feature/tree draft | 历史背景，归档EAGLE3，不另复制同repo |
| [P-EAGLE](https://arxiv.org/abs/2602.01469) | parallel drafting | 保留近期方法，论文评估GPT-OSS/Qwen3-Coder；非目标27B |
| [Medusa](https://arxiv.org/abs/2401.10774) | multiple decoding heads | 历史路径，目标训练head不是现成通用开关 |
| [Lookahead](https://arxiv.org/abs/2402.02057) | model-free exact parallel decode | 保留不依赖draft的路径；hybrid目标支持未核验 |
| [FlashDecoding++](https://arxiv.org/abs/2311.01282) | attention+flat GEMM | 保留工程机制，不能将旧HF speedup当当前4090排序 |
| [Lean Attention](https://arxiv.org/abs/2405.10480) | decode stream-K | long-context内核，需检查目标full attention的实际dispatch |
| [TreeWY](https://arxiv.org/abs/2608.20961) | GDN recurrent-state tree verify | 高相关近期研究；测试Qwen3.5 35B/397B，节省state snapshots，未确认27B/4090 artifact，不抢部署优先级 |
| [DFlare](https://arxiv.org/abs/2606.02091) / [AdaFlash](https://arxiv.org/abs/2607.19223) | diffusion draft scaling | API新召回，未读全文或审计代码；后续候选 |
| [xPress](https://arxiv.org/abs/2608.02438) / [DARTree](https://arxiv.org/abs/2608.13524) / [BV Loss](https://arxiv.org/abs/2609.34832) | diffusion refine/tree/training loss | 全部保留新论文长名单，不能仅凭score转成可部署engine |

GDN/FLA既有资料链接：`research/linear-attention/papers/gated-deltanet-2025/index`、`research/linear-attention/papers/fla-2024/index`、`research/linear-attention/papers/linear-attn-gpu-kernel-2025/index`。Qwen3.8 hybrid attention还要求speculation时的recurrent-state rollback，不仅是普通KV cropping。

## Overview

2022–2026年，ResearchStudio五query召回119条去重记录，installed query召回30条；按规范化title合并两组得到140条（仅检索层去重，不代表手工确认的论文数）。很多Crossref同名“Marlin/EAGLE”或低相关结果仍保留，使召回可审计；新增正式笔记只针对5篇读过方法/实验的论文。

## Trends

本轮高相关记录集中于2024–2026。低bit权重表示从标量GPTQ/AWQ发展到小codebook/vector/trellis；speculation从autoregressive draft/tree转向parallel diffusion，2026新增selector、refinement及hybrid recurrent-state验证研究。API排序按词汇score，不能当论文影响力或速度排名；时间字段不完整，不据此量化领域增长。

## Key themes

- Weight traffic：GPTQ、Marlin、QTIP；压缩格式只有与kernel联合才变成速度。
- Draft–verify成本：EAGLE3、DFlash/DFlash2、MTP；acceptance、verify width与prompt内容共同决定速度。
- Hybrid recurrent states：GDN、TreeWY；回滚/快照显存会压缩batch和context容量。
- Long-context attention：LeanAttention、FlashDecoding++；目标只有部分层为full attention，不能照搬纯Transformer假设。
- Reproducibility：官方repo/checkpoint、consumer recipe及同机协议；大卡paper数字仅解释机制。

## Keywords frequency

按两套API记录title去重后计数，包含保留的噪音；每title出现与否各计1，未用不可见abstract补计。

| Keyword | Count |
|---|---:|
| speculative | 50 |
| decoding | 50 |
| gated | 22 |
| quantization | 20 |
| diffusion | 15 |

## Most cited by accepted paper

仅本轮API snapshot中可识别为accepted的相关工作，不是领域总榜；citation不是实时可靠计量。原始API混入arXiv首发年，因此下表分开显示发表年份。REST与Marlin的APIvenue空白/arxiv，但DOI提供venue线索；DeFT/PMPD的ICLR2025由官方proceedings核对。

| Rank | Title | Publication year / venue | API citations |
|---|---|---|---:|
| 1 | [70% Size, 100% Accuracy / DFloat11](https://arxiv.org/abs/2504.11651) | 2025 / NeurIPS（APIvenue） | 33 |
| 2 | [REST](https://aclanthology.org/2024.naacl-long.88/) | 2024 / NAACL（DOI） | 30 |
| 3 | [MARLIN](https://doi.org/10.1145/3710848.3710871) | 2025 / PPoPP（DOI；APIarxiv） | 23 |
| 4 | [Progressive Mixed-Precision Decoding](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5df4313ecd4875931fbdacc486cc1fcf-Abstract-Conference.html) | 2025 / ICLR | 19 |
| 5 | [DeFT](https://proceedings.iclr.cc/paper_files/paper/2025/file/a6df53f082619d02b9fad64a022e5de3-Paper-Conference.pdf) | 2025 / ICLR | 19 |

## Most cited by first author

规范化title去重，重复citation取两套API中的max；第一作者只取CLI作者列表首项。缺失/0 citation降低统计完整性，不能用于评价作者。

| Rank | Author | Papers in set | Total API citations |
|---|---|---:|---:|
| 1 | Tianyi Zhang | 1 | 33 |
| 2 | Zhenyu He | 1 | 30 |
| 3 | Elias Frantar | 1 | 23 |
| 4 | H. Chen | 1 | 19 |
| 5 | Jinwei Yao | 1 | 19 |

## Recommendations for reading

1. GPTQ：先分清量化算法、存储格式和runtime kernel。
2. Marlin：理解小/中batch如何把W4带宽节省转为实际速度，特别是spec verify。
3. QTIP：理解EXL3量化路线，阅读时区分paper kernel与ExLlamaV3当前实现。
4. EAGLE3：理解target-conditioned draft训练与verification成本，作为方法基线。
5. DFlash论文→DFlash2官方blog：从parallel drafting走到目标专用checkpoint，随后回到同机实测。

## 原始错误与覆盖缺口

下方保留错误原文；完整进度/warning stdout见原始日志。API失败不表示不存在工作；没有盲目反复重试或用模型回忆伪装成API命中。

### Installed skill

```text
/Users/LOCAL_USER/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
[open_alex] unavailable (import failed: unsupported operand type(s) for |: 'type' and 'NoneType'); skipping this source.
Rate limited. Waiting 3 seconds...
[dblp] Error: Expecting value: line 1 column 1 (char 0)
Rate limited. Waiting 3 seconds...
```

### ResearchStudio-Idea（Python3.11）

```text
[dblp] Error on query 'Qwen3.8 inference': HTTPSConnectionPool(host='dblp.org', port=443): Max retries exceeded with url: /search/publ/api?q=Qwen3.8+inference&format=json&h=10&f=0 (Caused by ProxyError('Unable to connect to proxy', RemoteDisconnected('Remote end closed connection without response')))
[dblp] Error on query 'Marlin quantization': Expecting value: line 1 column 1 (char 0)
[dblp] Error on query 'EAGLE speculative decoding': Expecting value: line 1 column 1 (char 0)
[dblp] Error on query 'DFlash diffusion speculative decoding': Expecting value: line 1 column 1 (char 0)
[dblp] Error on query 'Gated DeltaNet inference': 429 Client Error: Too Many Requests for url: https://dblp.org/search/publ/api?q=Gated+DeltaNet+inference&format=json&h=10&f=0
[semantic_scholar] Error on query 'Qwen3.8 inference': 429 Client Error:  for url: https://api.semanticscholar.org/graph/v1/paper/search?query=Qwen3.8+inference&offset=0&limit=10&fields=title%2Cauthors%2Cyear%2Cabstract%2CcitationCount%2Curl%2Cvenue%2CpublicationDate%2CexternalIds&year=2022-2026
[semantic_scholar] Error on query 'Marlin quantization': 429 Client Error:  for url: https://api.semanticscholar.org/graph/v1/paper/search?query=Marlin+quantization&offset=0&limit=10&fields=title%2Cauthors%2Cyear%2Cabstract%2CcitationCount%2Curl%2Cvenue%2CpublicationDate%2CexternalIds&year=2022-2026
[semantic_scholar] Error on query 'EAGLE speculative decoding': 429 Client Error:  for url: https://api.semanticscholar.org/graph/v1/paper/search?query=EAGLE+speculative+decoding&offset=0&limit=10&fields=title%2Cauthors%2Cyear%2Cabstract%2CcitationCount%2Curl%2Cvenue%2CpublicationDate%2CexternalIds&year=2022-2026
[semantic_scholar] Error on query 'DFlash diffusion speculative decoding': 429 Client Error:  for url: https://api.semanticscholar.org/graph/v1/paper/search?query=DFlash+diffusion+speculative+decoding&offset=0&limit=10&fields=title%2Cauthors%2Cyear%2Cabstract%2CcitationCount%2Curl%2Cvenue%2CpublicationDate%2CexternalIds&year=2022-2026
[semantic_scholar] Error on query 'Gated DeltaNet inference': 429 Client Error:  for url: https://api.semanticscholar.org/graph/v1/paper/search?query=Gated+DeltaNet+inference&offset=0&limit=10&fields=title%2Cauthors%2Cyear%2Cabstract%2CcitationCount%2Curl%2Cvenue%2CpublicationDate%2CexternalIds&year=2022-2026
  [90] (score 1) Compensate Quantization Errors+: Quantized Models Are Inquisitive Learners
  [91] (score 1) Compensate Quantization Errors: Make Weights Hierarchical to Compensate Each Other
```

ResearchStudio Py3.9的NotOpenSSLWarning、DBLP read-timeout/429和SS429也完整保留于asset日志。OpenReview两套均为0条，不是已确认该venue没有相关论文。

## 归档与验证状态

5篇均有原始source、PDF、safe-extracted独立source树与官方浅clone，metadata记录URL/version/hash/commit、精确阅读范围和not_run。source-first，无PDF fallback；PDF首页身份检查不等于PDF完整阅读。topic/global导航及log由父任务统一更新。
