# Qwen3.8-27B × RTX 4090 inference

单张 RTX 4090 上的推理方案研究、速度证据和专题榜单。这个独立仓库保存研究与实验现场，便于后续继续；快照日期为 **2026-10-02**。

## 从这里继续

先读 [CONTINUE.md](CONTINUE.md)，再读 [实验协议](site/assets/benchmarks/qwen38-4090/README.md)。

```bash
python3 tools/verify_repo.py
python3 tools/build_site.py
python3 -m http.server 8080 --directory dist --bind 127.0.0.1
```

浏览器打开 <http://127.0.0.1:8080/benchmarks/qwen38-4090/>。上述命令只校验存档并生成静态页面，不连接实验服务器、不加载模型。Python 3.9+ 标准库即可运行。

## 已有结果

全部测量串行使用同一张物理 RTX 4090，而非四卡并行。HTTP 的 Cinference、NInfer、llama.cpp，以及原生 Python 的 ExLlamaV3，共 **108 个正式样本、36 条配置与负载汇总**。HTTP 和原生调用使用不同计时口径，在榜单中分别展示。

这轮真实输入只有 **34–77 token**；4K 是配置容量。并发为 1，贪心解码，最多输出 512 token，每个负载 3 次取中位数。量化与 KV 格式不同，因此比较的是部署配置。代码和散文截断；JSON 结构检查通过；代码语义测试未运行。

Cinference MTP7 在已测 HTTP 配置的代码/JSON 上分别为 **213.9 / 238.6 decode token/s**。散文的最优草稿长度不同。不能据此宣布所有方案的通用冠军：**Unsloth 原生、vLLM、SGLang 尚未实测**，社区报告另列。

## 保存的内容

| 位置 | 内容 |
|---|---|
| [site/](site/) | 可继续编辑的榜单页面、JS/CSS、结果、108 条脱敏样本、复现脚本；保留原站 Jekyll 文件结构 |
| [research/](research/) | 推理专题笔记、论文与工程资产的来源/固定版本、检索记录、测速和工具安装 threads |
| [archives/](archives/) | 完整原始缓存文件清单与 SHA-256、仓库/论文/模型锁定信息、复制范围说明 |
| [qa/](qa/) | 已完成的网站构建、浏览器交互检查、截图与数据审计证据 |
| [docs/](docs/) | 现有榜单调查、远端实验状态、个人网站接入方法与归档说明 |
| `.local/originals/` | 此工作目录内的完整原始研究缓存、日志和源码参考，保留原样；由 Git 忽略 |

公开仓库含脱敏证据。公开清单中的 `original_sha256` 指原始缓存的哈希；公开副本的哈希由 [archives/public-files.json](archives/public-files.json) 单独记录。上游源码和论文全文保存在本地缓存，公开仓库提供 canonical URL、固定版本与校验值；模型大文件仍保存在实验服务器。

## 当前状态

实验服务器的推理服务已按用户要求停止并禁用自动启动；本次归档没有重新启动 GPU 任务。CLI 工具安装记录已保存。个人网站榜单通过完整 Jekyll 构建及桌面/手机检查，尚未推送到个人站点。

现有 [Artificial Analysis](https://artificialanalysis.ai/hardware-inference-stack/laptops-workstations)、[Inference Atlas](https://0xbakeer.github.io/inference-atlas/) 已做本地推理比较；截至快照日期，检查的数据没有 RTX 4090 条目。这个专题补充单卡 4090 证据，不宣称整个领域没有其他榜单。

## 来源与权利

上游代码、论文、模型和外部 benchmark 保留各自的许可证、作者及条件；存档或提供链接不改变这些条件。参见 [NOTICE.md](NOTICE.md)。
