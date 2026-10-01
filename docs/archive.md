# 归档范围与恢复

本仓库由本次研究、服务器实验和榜单实现整理而来。复制不修改原 llmwiki 或原站点；本次也没有 SSH 启动服务或运行 GPU。

## 本地完整副本

`.local/originals/llm-inference/` 保存完整推理专题的 `assets/`、`threads/` 和导航，包含既有背景论文与本轮新增工作。原始源码缓存、Git 历史、论文 PDF/TeX、脚本、日志和结果都保留原样。每个普通文件在复制后与来源逐一比较 SHA-256；清单为 [original-files.json](../archives/original-files.json)。

`.local/originals/site/` 保存榜单九个交付文件的原始版本；`.local/originals/temporary/` 保存本轮 `/tmp` 中的研究观察、代码归档包、操作脚本、构建日志和 QA 截图等。清单为 [session-artifacts.json](../archives/session-artifacts.json)。没有复制个人网站的其他文章、照片或整个私人 wiki。

`.local/` 被 Git 忽略，因此 GitHub 上的 clone 不含完整本地缓存。要迁移这台机器的完整工作现场，除 Git clone 外再复制 `.local/originals/`。

```bash
# 在原始工作目录验证完整本地缓存，过程中不联网、不查询 GPU。
python3 tools/verify_repo.py --local-originals
```

## 公开副本

公开仓库保存研究笔记、来源与版本元数据、检索观察、脱敏历史实验/工具安装证据、可编辑榜单和复现脚本。原环境的用户名路径、GPU UUID、内网地址等在公开副本中使用占位符。下载或启动脚本中的占位符需要按实际环境填写；历史脚本不会被校验或预览命令自动执行。

历史 `metadata.yaml`、raw sample `source_files` 和 `original-files.json` 的哈希仍指原始文件，不能当作脱敏副本的哈希。公开文件自己的 bytes/SHA-256 统一在 [public-files.json](../archives/public-files.json)。原始来源和公开副本的计时、输出、重复数和统计值仍可交叉核对。

上游源码与论文全文不作为新仓库的 Git 文件重复分发。它们的完整本地副本仍在 `.local/`；另一台机器可按 [repos.lock.json](../archives/repos.lock.json) 和 [papers.lock.json](../archives/papers.lock.json) 的 canonical URL、固定 commit/版本恢复。阅读状态仍是原来的 partial/read，不因复制变成新的复现结论。

模型权重没有从实验服务器重新复制到 Mac，也不进入 Git。下载地址、固定 revision、文件 SHA 和 EXL3 分片清单保存在 [models.lock.json](../archives/models.lock.json) 及原始下载证据中。远端 `~/qwen38-4090/models/` 保留已下载文件。

## 修改后更新清单

```bash
python3 tools/verify_repo.py --update-manifest
python3 tools/verify_repo.py
python3 tools/build_site.py
```

`--update-manifest` 会先重算速度与检查公开内容，再更新清单；不会修改原始缓存的哈希或加载模型。
