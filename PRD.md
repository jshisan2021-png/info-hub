# Info Hub — 个人信息聚合仪表板

## 概述
一个纯静态的信息聚合页面，汇集 RSS 源和 YouTube 频道的最新内容，部署在 GitHub Pages 上，Mac mini 通过 cron 定时更新。

## 核心功能
1. **RSS 聚合**：抓取多个 RSS/Atom 源，展示最新文章（**中文标题、中文摘要**、来源、时间、链接）
2. **YouTube 聚合**：抓取指定频道的最新视频（**中文标题**、缩略图、发布时间、链接）
3. **分类展示**：按来源/类别分组，支持筛选
4. **时间线视图**：所有内容按时间倒序混合展示
5. **响应式设计**：手机和桌面都能看

## 技术方案
- **前端**：纯 HTML + Tailwind CSS（无框架），静态页面
- **数据抓取**：Python 脚本，抓 RSS（feedparser）+ YouTube（yt-dlp 或 YouTube Data API）
- **构建流程**：Python 脚本抓数据 → 生成 JSON → 用模板渲染静态 HTML
- **部署**：GitHub Pages，免费
- **更新**：Mac mini cron 每天 3 次（早8点/午12点/晚8点）→ git push 触发 Pages 更新

## 数据源（待十三提供完整列表，先用以下占位）
### RSS 源
- Hacker News: https://news.ycombinator.com/rss
- TechCrunch: https://techcrunch.com/feed/
- Nature News: https://www.nature.com/nature.rss
- Anthropic Blog: https://www.anthropic.com/rss.xml

### YouTube 频道
- （待十三提供）

## 目录结构
```
info-hub/
├── PRD.md              # 本文件
├── scripts/
│   ├── fetch_feeds.py  # 抓取 RSS + YouTube
│   ├── build_html.py   # 生成静态页面
│   └── requirements.txt
├── data/
│   └── feeds.json      # 抓取的数据（中间产物）
├── site/
│   ├── index.html      # 主页面
│   └── assets/         # CSS等
└── config.yaml         # 数据源配置（RSS URLs + YouTube channels）
```

## 非功能需求
- 页面加载快（纯静态，无 JS 框架）
- 代码简洁，十三能看懂和改
- config.yaml 易于添加新源
- **所有标题和摘要翻译为中文**（英文源用 LLM 翻译，中文源保持原样）

## 里程碑
1. ✅ 需求文档
2. 🔄 Python 抓取脚本（RSS 部分先做）
3. HTML 模板 + Tailwind 样式
4. YouTube 抓取
5. 本地测试通过
6. GitHub repo + Pages 部署
7. Mac mini cron 配置
