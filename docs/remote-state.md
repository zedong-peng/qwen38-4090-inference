# 实验服务器状态：最后保存的观察

这是历史状态存档，不持续监控服务器。本次新建仓库没有连接服务器运行实验。

## 工作位置与服务

SSH alias：`g4090`。工作根目录：`~/qwen38-4090/`。模型、源码、环境、日志和结果仍在远端；本地保存下载/构建/运行 provenance 与原始结果。

2026-10-02 按用户要求停止并 disable `qwen38-cinference.service`，保存的状态为 `inactive/dead`、`disabled`、MainPID 0，原服务 PID 已退出。仅操作本用户 unit；没有终止他人任务。停止快照见 [原始停止证据的脱敏副本](../research/assets/g4090-qwen38-benchmark-2026/supplementary/remote-evidence/results/service-verification/stopped-at-user-request.json)。

## 实际运行的源码

| 远端相对路径 | 固定 commit | 实测 |
|---|---|---|
| `repos/qwen38-cinference-4090` | `70ebb1290dc7abe246c20696a24d21f77faee8d4` | HTTP AR、MTP3、MTP7 |
| `repos/qwen38-ninfer-4090` | `1bd56c9a1bdf457c6188391a9385d44d86e953aa` | HTTP AR、MTP3、MTP5；K7 不支持 |
| `repos/native-llama/llama.cpp` | `a4d880fd5c7f88713ded6db9f0111893bd78afa6` | HTTP CUDA AR、MTP3、MTP7 |
| `repos/exllamav3-git` | `d3739fd393337b1ff4d6c2a342b12f0c87a9592f` | 原生 AR、MTP4、DFlash2 K7；K15 超过该 draft block 容量 |

HyperQwen 已 clone、未 GPU 部署；TabbyAPI 的 HTTP 配置和依赖准备仅 CPU 检查。没有 vLLM/SGLang/Unsloth 原生测速。所有正式请求使用单张物理 GPU 3，串行执行。

保存的服务器构建环境为 driver 570.124.06、CUDA Toolkit 12.8、GCC 13，SM89 Release。已有独立 build/env 与模型校验记录。后续外部 CUDA 13 配方的可用性需要重新确认，不能把新报告的启动命令视为当前机器已经验证。

## 工具

| 工具 | 已安装/下载版本 |
|---|---|
| Node.js / npm | 24.21.0 / 11.19.0 |
| Claude Code | 2.1.286 |
| Codex CLI | 0.159.2 |
| OpenCode | 1.18.33 |
| CC Switch CLI | 5.10.5 |
| CC Switch desktop | 3.20.4 AppImage 已下载；无 DISPLAY，未启动 GUI |

CLI 的版本/帮助检查完成；没有配置账号、API key 或 provider。安装脚本、包 integrity 与 smoke 证据见 [工具资产](../research/assets/g4090-agent-tools-2026/index.md)及 [agent-tools.lock.json](../archives/agent-tools.lock.json)。
