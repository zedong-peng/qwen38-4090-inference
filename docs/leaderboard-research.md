# 本地推理榜单检索：2026-10-02 快照

已有本地推理榜单，但本轮检查没有找到覆盖完整「Qwen3.8-27B × 单张 RTX 4090 × 多引擎统一测试」的专门榜单。此结论只覆盖检查到的来源和日期，不能写成整个互联网没有相关工作。

| 来源 | 检查结果 | 对本专题的作用 |
|---|---|---|
| [Artificial Analysis](https://artificialanalysis.ai/hardware-inference-stack/laptops-workstations) | 有 Qwen3.8-27B；最初硬件为 RTX 5090、DGX Spark、Ryzen AI Halo、M5 Pro，检查的配置没有 RTX 4090 | 使用它的多轮 agent 协议可做后续外部对照 |
| [Inference Atlas](https://0xbakeer.github.io/inference-atlas/) | 多引擎贡献型数据库；检查 commit `b93f6281f150788d53c05600725b63f8febddd1e` 的 569 条结果含 127 条 Qwen3.8-27B，硬件为 DGX Spark/M2 Max，没有 4090 | 可考虑按其协议贡献新测量 |
| [Qwen Local-Run Directory](https://local.host.impossibuild.ai/) | 有 4090 部署 recipes；速度混合作者实测、论坛报告、厂商数据和未核验项 | 搜索部署线索，不能作为统一协议排行 |
| [Poor Paul's Benchmark](https://poorpaul.dev/) | 提供 llama-bench/server/loadtest 数据；检查时的结果没有 Qwen3.8/4090 | 参考 TTFT、ITL、显存和质量字段设计 |

## Artificial Analysis 协议

2026-09-29 [发布说明](https://artificialanalysis.ai/articles/aa-agentperf-local)与 [aa-agentperf-local](https://github.com/ArtificialAnalysis/aa-agentperf-local) 描述真实多轮 agent 请求回放。其初始协议有 8 个任务、168 turns、172 tool actions，历史增长约 56K、配置 64K，单并发；在每次隔离回放中保留正常 prefix reuse，按原输出长度生成，默认采样也不是本轮 greedy。

因此本仓库 34–77-token 短输入、4K 容量、3 个 prompt 的数据不是 AA-compatible，不能改标签直接提交。AA runner 的 attached-framework 枚举与具体 adapter 也要匹配；Cinference/NInfer/EXL3 不能冒充 llama.cpp。

它的 [提交说明](https://github.com/ArtificialAnalysis/aa-agentperf-local/blob/main/docs/SUBMITTING.md) 和 API 有准备/上传/状态流程，但接受上传不保证公开榜单收录。本轮没有上传测量。

## 新发现的公开 4090 报告

[sidnaZ/qwen38-27b-rtx4090](https://github.com/sidnaZ/qwen38-27b-rtx4090/blob/main/RELEASE.md) 报告 vLLM 0.27.1、CUDA 13、driver 595.84、AutoRound W4A16、DFlash2 K7 与 lookup 的组合：代码 decode 237.9 token/s，context-copy 337.8；C32 aggregate 1318 属于多请求吞吐，不能当作单流速度。作者还提供量化/质量报告、固定 corpus 与 runner；本轮没有在 g4090 复现。

[kuotunyu/qwen38-speculative-decoding-benchmark](https://github.com/kuotunyu/qwen38-speculative-decoding-benchmark/blob/main/QWEN38_REPORT.md) 则提供单 4090/WSL2 的 llama.cpp speculation 研究：8K 主实验和 16K/32K probes、原始 JSONL/CSV、paired 比较与 bootstrap CI。它是更丰富的单引擎协议，不是我们的同卡多引擎复测。

这些报告说明「最快」需要限定负载、driver、量化、计时和质量。榜单将外部报告单列，不把它们与本轮短请求取最大值混排。

完整广检与论文搜索见 [research/threads/](../research/threads/)；本页是最近的榜单增量检索，不取代旧的工程长名单。
