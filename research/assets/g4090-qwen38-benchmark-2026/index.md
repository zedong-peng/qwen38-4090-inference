---
title: g4090 Qwen3.8-27B 原生部署与实测资产
domain: research
area: llm-inference
type: engineering
status: active
updated: '2026-10-02'
tags: [qwen3.8, rtx4090, inference, reproduction, benchmark]
---

# g4090 Qwen3.8-27B

本目录保存 2026-10-01 在 g4090 的真实安装与推理证据。公开作者数据另见 [2026-10-01-qwen38-4090-landscape](../../threads/2026-10-01-qwen38-4090-landscape.md)，两者不混合排名。

## 模型与构建

- RTX 4090，Ubuntu 22.04，NVIDIA driver 570.124.06，系统 CUDA Toolkit 12.8。用户目录中的独立编译环境提供 GCC 13、CMake、Ninja、FFmpeg 7、libcurl；未更改系统驱动。
- 机器有 4 张 4090，开始时都有其他用户任务；本次固定 GPU 3，保留所有其他进程。机器人任务在编译/测量间自然退出并重新启动；每个请求前后记录显存、利用率、功率和温度，不能把整轮结果称为独占卡性能。
- 实际GPU测试为Cinference、Erik NInfer、llama.cpp、ExLlamaV3，模式与请求全部在单张物理GPU3串行执行，没有四卡并行或tensor parallel。
- NInfer v2: `neroued/Qwen3.8-27B-NInfer` revision `3526913004b1cf552cb57b88d6a5c6f5e4a89a70`，18,210,531,328 bytes，SHA-256 `eec39564993d6e9c7d5e383382a760f093465c9d163ec9a1bd6b80199514bf3e`。
- GGUF: `unsloth/Qwen3.8-27B-GGUF` revision `4ca720788d1e01f1bff70c033e0d0028fd02e502`，`UD-Q4_K_M` 16,464,440,224 bytes，SHA-256 `322e194ff79741c7baa497c240f677f54b201b0efab44ca8e50f122b39123482`。
- 同 revision 的 MTP sidecar `mtp-Qwen3.8-27B-Q4_0.gguf`，1,369,590,656 bytes，SHA-256 `50d9ce5a6da381bbcfb31061cf73df94a90e6faf8efeddee379a9cb8f1501c6e`。
- g4090 无法解析 `huggingface.co`；下载走 `hf-mirror.com`，内容按官方 LFS SHA-256 校验。GitHub 直连克隆多次失败；固定 commit 的只读 Git 参考通过 Git 文件协议在 g4090 真正独立克隆，canonical origin、detached HEAD、git fsck 和无 alternates 均核对。所有构建、代码调整和服务启动在远端克隆进行；Mac llmwiki 中的缓存源码只作参考，未修改。
- 远端工作目录：`~/qwen38-4090/`；weights 在 `models/`，源码在 `repos/`，日志在 `logs/`，测量在 `results/`。

## 指标与检查

[benchmark_http.py](supplementary/benchmark_http.py) 只依赖 Python 标准库。固定 temperature=0、seed=42、presence/frequency penalty=0、thinking 关闭、单请求，分别测 JSON、Python 代码和 prose；记录完整请求、完整回复、服务器 timings 与客户端墙钟时间。代码只做 AST 语法检查，不执行模型生成代码；不将语法通过称为语义正确。

服务器 decode token/s 采用 `(已提交 output tokens - 1) / decode_seconds`，两 engine 的 `predicted_per_second` 都排除由 prefill 产生的首个 token，也不计 draft/rejected tokens；另报告含 prefill 的 E2E output token/s。`prompt_ms` 含首 token 的服务器计算时间，不是纯 GPU kernel 时间或客户端 TTFT；本脚本不测 streaming TTFT。warmup 不计入统计；每种负载取三次中位数。服务器禁用 prefix reuse，llama 请求设置 `cache_prompt=false`。HTTP 成功次数与质量检查结果分列。

模型量化不同、请求长度由实际 tokenizer 决定；本轮属于同卡部署选型，不是同精度的 engine-only 科学比较。公开论文的 kernel speedup 不作为本机 E2E 倍率。

完整数据、当前服务与命令见 [2026-10-01-g4090-qwen38-speed](../../threads/2026-10-01-g4090-qwen38-speed.md)。

## 完成结果

正式HTTP矩阵覆盖Cinference MTP0/3/7、Erik NInfer MTP0/3/5、llama.cpp MTP0/3/7，81个请求与9个warmup；正式请求显式penalty0、cold prefix，全部成功。JSON解析/三个districts通过；512-token code/prose样本截断，不属于完整任务质量通过。EXL3 native AR/MTP4/DFlash2K7另有27个成功请求，cache0；两类时间与token计数口径分别记录。

Cinference MTP7本轮JSON/code medians为238.6/213.9 decode token/s、208.5/205.4 HTTP E2E output token/s；散文MTP3约100.2 decode token/s。此前在g4090启动并验证 `qwen38-cinference.service`，16K context、int8 KV、MTP7、prefix reuse、single lane，监听localhost18038。完整LRU代码smoke生成1449token、自然stop、AST通过；语义测试未执行。health/models/SSE/Responses/Anthropic smoke通过。

**当前状态：2026-10-02 01:48按用户要求停止服务并禁用自动启动。** 停止后MainPID=0、inactive/dead、disabled，原PID2332782已退出；GPU3快照为17MiB已用、24076MiB空闲、利用率0%，NVIDIA计算进程列表为空。仅操作本用户的unit。模型、构建和历史测速全部保留，见 [停止验证](supplementary/remote-evidence/results/service-verification/stopped-at-user-request.json)。

- [HTTP原始结果与构建证据](supplementary/remote-evidence/results/primary-benchmark-audit.json)，[服务验证](supplementary/remote-evidence/results/service-verification/summary.json)，[构建配置](supplementary/remote-evidence/results/cmake-build-provenance.json)。
- [EXL3全部原始记录](supplementary/exl3-bench/README.md)，[部署/模型验证](supplementary/exl3-deployment-notes.md)。Native速度与HTTP速度分列，首请求初始化开销保留。
- [正式HTTP脚本快照](supplementary/benchmark_http.py)，[NInfer模式launcher](supplementary/run_ninfer_modes.py)，[llama模式launcher](supplementary/run_llama_modes.py)。它们都是远端实际工作代码的归档，不在本地wiki执行模型。
- [保留的服务launcher](supplementary/run_qwen38_service.sh)，[unit](supplementary/qwen38-cinference.service)，[管理wrapper](supplementary/service_ctl.sh)，[验证脚本](supplementary/verify_qwen38_service.py)。服务当前已停止。
- [TabbyAPI预备配置](supplementary/tabby-http-preparation/README.md)仅完成CPU schema/依赖验证，未运行GPU；HyperQwen仅clone并固定来源，CUDA13 runtime未部署。

失败/修正均保留：Erik MTP7超出[1,5]合法范围，改测K5；DFlash2固定draft的block_size8只能到K7，K15请求失败后增加CPU guard；HTTP runner TIME_WAIT检查已修复；Responses请求使用reasoning.effort而不是Chat专有enable_thinking字段。模型与系统驱动保持原始版本，所有运行进程只由本用户的测试launcher或service unit管理。

远端download模型都保留在 `~/qwen38-4090/models/`。v2→v3容器转换的SHA变化来自metadata/template/identity，原始payload逐字一致，见 [验证证据](supplementary/remote-evidence/results/ninfer-v3-payload-verification.json)。v3文件18,210,750,082 bytes，实际SHA256 `efec7393d517dc3cdda1f8fa0f3333bd03ffe61610418f059d6758afcaece006`；不能套用旧README的另一份转换文件hash。
