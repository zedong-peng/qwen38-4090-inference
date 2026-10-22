# 接入个人网站

## 当前发布方式

个人网站部署时从本仓库拉取 `main`，运行 `tools/build_site.py`，把
`dist/benchmarks/qwen38-4090/` 和 `dist/assets/` 复制到站点输出目录。榜单页面是独立的
静态 HTML（自带页头、主题切换和页脚），不经过个人网站的 Jekyll layout。个人网站的
`/qwen38-4090/` 只是一个带导航的跳转页，指向 `/benchmarks/qwen38-4090/`。

下面保留最初的 Jekyll 草稿接入说明，仅用于追溯；当前部署不再把九个文件复制进 Jekyll 页面。


`site/` 保留九个榜单文件的原始 Jekyll 目录结构。它们在之前的个人网站草稿中完成完整 Jekyll 构建、浏览器筛选/排序、桌面/手机及明暗主题检查；证据在 [qa/](../qa/)。

| 从 `site/` 复制的路径 | 用途 |
|---|---|
| `_pages/qwen38-4090-leaderboard.md` | Jekyll page，permalink `/benchmarks/qwen38-4090/`，导航入口 |
| `assets/js/qwen38-4090-leaderboard.js` | 筛选、排序、分享 URL、覆盖度和外部报告 |
| `assets/css/qwen38-4090-leaderboard.css` | 作用域限定的页面样式 |
| `assets/benchmarks/qwen38-4090/results.json` | 36 条汇总与来源、协议、模型信息 |
| `assets/benchmarks/qwen38-4090/samples.json` | 108 条脱敏样本及 48 个原始来源哈希 |
| `assets/benchmarks/qwen38-4090/README.md` | 协议、限制与复现说明 |
| `assets/benchmarks/qwen38-4090/export_results.py` | 从原实验归档导出公开样本和汇总，CPU-only |
| `assets/benchmarks/qwen38-4090/benchmark_http.py` | HTTP 测速 harness；真正执行时需要已运行的 engine |
| `assets/benchmarks/qwen38-4090/benchmark_exl3.py` | EXL3 harness；dry-run 不加载模型，正式运行需要远端环境 |

复制时保持相对路径。原站的 `_config.yml`、page layout 和 Gemfile 不需要为这九个文件修改。发布前按站点自己的 `AGENTS.md` 运行格式和完整构建检查；本仓库的独立 renderer 只是预览，不冒充原站 Jekyll 构建。

原站推送主分支会触发 GitHub Pages，上线到 `zedongpeng.com`。新建这个公开归档仓库不触发原站发布，也没有为新仓库启用自动 Pages 部署。

## 独立预览

```bash
python3 tools/build_site.py
python3 -m http.server 8080 --directory dist --bind 127.0.0.1
```

`tools/build_site.py` 只扩展这份页面使用的 `relative_url` Liquid 表达式，并提供独立外壳。它保留同一套 JS/CSS 和数据，不需要 Ruby、npm、GPU 或 SSH。
