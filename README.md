# Info Hub - 个人信息聚合仪表板

## 快速开始

### 1. 首次设置（已完成）
```bash
# 创建虚拟环境并安装依赖
/opt/homebrew/bin/python3.12 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

### 2. 更新内容
```bash
# 方法1：使用便捷脚本（推荐）
./update.sh

# 方法2：手动运行
venv/bin/python scripts/fetch_feeds.py  # 抓取数据
venv/bin/python scripts/build_html.py   # 生成HTML
```

### 3. 查看结果
在浏览器中打开 `site/index.html`

## 目录结构
```
info-hub/
├── PRD.md              # 产品需求文档
├── README.md           # 本文件
├── config.yaml         # 数据源配置（RSS源、YouTube频道）
├── update.sh           # 一键更新脚本
├── venv/               # Python虚拟环境
├── scripts/
│   ├── fetch_feeds.py  # RSS/YouTube 抓取脚本
│   ├── build_html.py   # HTML 生成器
│   └── requirements.txt
├── data/
│   └── feeds.json      # 抓取的数据（中间文件）
└── site/
    └── index.html      # 生成的静态页面
```

## 配置说明

### 添加RSS源
编辑 `config.yaml`，在 `rss:` 下添加：
```yaml
- name: 来源名称
  url: https://example.com/feed.xml
  category: tech  # tech/ai/science/education/news/other
```

### 添加YouTube频道
编辑 `config.yaml`，在 `youtube:` 下添加：
```yaml
- name: 频道名称
  channel_id: UCxxxxxxxxxxxxx
  category: education
```

**获取YouTube频道ID**: 访问频道页面，URL中的 `/channel/` 或 `/c/` 后面的就是频道ID

## 功能特性

### fetch_feeds.py
- ✅ 读取 config.yaml 获取数据源
- ✅ 抓取RSS/Atom feeds
- ✅ 支持YouTube频道（需安装yt-dlp）
- ✅ 错误容错：单个源失败不影响其他源
- ✅ 输出JSON到 data/feeds.json
- ✅ 记录抓取时间戳

### build_html.py
- ✅ 读取 feeds.json
- ✅ 生成响应式HTML页面
- ✅ Tailwind CSS 暗色主题
- ✅ 按category分栏显示
- ✅ 显示标题、来源、时间、摘要
- ✅ 顶部显示最后更新时间

## 下一步计划

1. **部署到GitHub Pages**
   - 创建GitHub仓库
   - 配置GitHub Actions自动构建
   - 或者手动push更新

2. **Mac mini 自动更新**
   - 配置crontab定时运行（每天3次）
   ```bash
   # 编辑crontab
   crontab -e
   
   # 添加任务（早8点/午12点/晚8点）
   0 8,12,20 * * * cd /path/to/info-hub && ./update.sh
   ```

3. **优化Anthropic RSS**
   - Anthropic的RSS源目前解析有警告，可能需要特殊处理

## 故障排除

### yt-dlp 相关错误
如果YouTube抓取失败，确保安装了yt-dlp：
```bash
brew install yt-dlp
# 或
venv/bin/pip install yt-dlp
```

### 模块未找到错误
确保使用虚拟环境的Python：
```bash
venv/bin/python scripts/fetch_feeds.py  # ✓ 正确
/opt/homebrew/bin/python3.12 scripts/fetch_feeds.py  # ✗ 错误
```

## 测试结果

✅ 第一次运行成功：
- 抓取了60条RSS内容（Hacker News、TechCrunch、Nature News）
- 生成了29KB的HTML文件
- 页面包含3个分类（tech、science、ai）
- 响应式设计、暗色主题正常工作
