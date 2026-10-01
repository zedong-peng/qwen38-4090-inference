---
title: g4090 编程助手工具安装资产
domain: research
area: llm-inference
type: engineering
status: stable
updated: 2026-10-01
tags: [g4090, tooling, codex, claude-code, opencode, cc-switch]
---

# g4090 编程助手工具安装资产

2026-10-01 在 `g4090` 的普通用户目录安装开发工具，支持推理实验的后续操作。实际安装、命令验证和使用方式见 [2026-10-01-g4090-agent-tools](../../threads/2026-10-01-g4090-agent-tools.md)。本资产不是推理 engine，也没有 token/s 结果。

| 工具 | 固定版本 | 交付 / 验证 |
|---|---|---|
| Node.js | 24.21.0；npm 11.19.0 | 官方 Linux x64 LTS 包；SHA-256、版本检查 |
| Claude Code | 2.1.286 | 官方 npm 包；`--version` / `--help` 均退出 0 |
| Codex CLI | 0.159.2 | 官方 npm 包；`--version` / `--help` 均退出 0 |
| OpenCode | 1.18.33 | 官方 npm 包；`--version` / `--help` 均退出 0 |
| CC Switch CLI | 5.10.5 | 官方桌面项目推荐的社区 CLI；musl 包，SHA-256、版本及帮助检查 |
| CC Switch 桌面版 | 3.20.4 | 官方 AppImage 已下载；SHA-256、AppImage runtime 检查；无 DISPLAY，未启动图形界面 |

可复现脚本是 [install_agent_tools.py](supplementary/install_agent_tools.py)。安装到 `~/.local/share/g4090-agent-tools/`，启动命令链接到 `~/.local/bin/`，无需 sudo。脚本固定版本、校验下载、检查归档边界，并保留已有 launcher。现有 `.bashrc` / `.profile` 内容先备份，再增加 PATH 段；不配置账号、API key 或 provider。

证据文件：

- [install-manifest.json](supplementary/install-manifest.json)：远端生成的固定版本、GUI/CLI 下载来源、SHA-256 和实际版本。
- [smoke-results.json](supplementary/smoke-results.json)：新 SSH 会话的命令路径、版本和帮助退出码；GUI runtime 状态。
- [npm-package-manifest.json](supplementary/npm-package-manifest.json)：六个确切 npm 包版本及 registry SHA-512 integrity / provenance，涵盖三个工具及 Linux x64 依赖。
- [agent_tools_install_20261001_retry.log](supplementary/agent_tools_install_20261001_retry.log)：最终安装日志。首轮遇到 npm 的脚本许可和 GitHub 下载网络问题，最终脚本已加入一次性 `--allow-scripts` 参数，下载包已重新校验。

来源：[Claude Code 官方安装文档](https://code.claude.com/docs/en/setup#install-with-npm)、[OpenAI 官方 Codex CLI 文档](https://learn.chatgpt.com/docs/codex/cli)、[官方 npm 安装示例](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)、[OpenCode 官方文档](https://opencode.ai/docs/)、[CC Switch 官方仓库的 headless 说明](https://github.com/farion1231/cc-switch#faq)、[CC Switch CLI 项目](https://github.com/SaladDay/cc-switch-cli)。均于 2026-10-01 核对。
