# 后续工作入口

## 接手时先确认的事实

- **用户要求先释放 GPU**，最后保存的状态为 `qwen38-cinference.service` 停止、disabled、MainPID 0。这是 2026-10-02 的历史观察，不是持续在线监测。
- 单机有 4 张 4090，但本次只串行使用物理 GPU 3。没有 tensor parallel，也没有四卡吞吐测量。
- 已实际运行四份代码：jram4 Cinference、Erik NInfer、llama.cpp、ExLlamaV3。Unsloth 原生、vLLM、SGLang 未实测；HyperQwen 仅克隆；TabbyAPI 仅完成 CPU 配置准备。
- HTTP 正式矩阵 81 个样本，原生 EXL3 27 个样本；每个配置/负载重复 3 次。不能把初始诊断、16K 服务 smoke、作者报告和这轮正式矩阵混在一起。
- 最多 512 输出 token 导致代码/散文截断；没有代码语义测试。旧速度 thread 的散文字数概括不准确，以公开 raw samples 中每条词数和质量说明为准。
- `site/` 的九个榜单文件可复制到个人网站；网站原仓库没有被本项目自动发布。

## 不占 GPU 就能继续做

1. 运行仓库校验和独立静态预览，检查筛选、排序、原始样本下载。
2. 阅读 [榜单检索](docs/leaderboard-research.md)、[公开协议](site/assets/benchmarks/qwen38-4090/README.md) 和 [归档范围](docs/archive.md)。
3. 为缺失方案固定 repo commit、模型 revision、量化、driver/CUDA、启动参数和结果 schema；先做 CPU 配置/源码检查。
4. 制订下一轮统一协议：真实输入长度、长上下文、单请求延迟与多请求吞吐分开；增加可执行的语义质量检查。3 个短 prompt 不足以概括真实 agent 工作负载。

## 用户恢复实验后

先检查服务器现有占用，再一次只启动自己负责的服务。保留他人任务。从普通 AR 基线开始，再测 MTP/DFlash 等 profile；不要同时跑多个 engine 或预先留下后台 GPU 服务。

优先补齐 **Unsloth 原生、vLLM、SGLang**。llama.cpp 使用 Unsloth 发布的 GGUF 只能算 llama.cpp 配置。Unsloth `fast_inference=True` 使用 vLLM 时，应标为该后端，避免重复计算独立引擎。

社区 vLLM 单卡 4090 报告有代码 237.9 token/s，但使用新的 driver/CUDA、量化和测试负载；需要独立复现，不能直接与本轮 213.9 排名。Artificial Analysis 的 agent replay 协议也与本轮不兼容，不要伪造 adapter 名称或提交兼容性。

## 远端恢复位置

SSH alias 是 `g4090`；工作根目录为 `~/qwen38-4090/`，内有 `models/`、`repos/`、`tools/`、`logs/`、`results/`。实际下载的模型和构建环境见 [远端状态](docs/remote-state.md)、公开实验资产及 `archives/models.lock.json`。完整原始记录在本地 `.local/originals/llm-inference/`。

服务器脚本的启动/停止命令属于历史操作记录，阅读文档并不意味着需要执行它们。
