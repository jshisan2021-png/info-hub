#!/bin/bash
# Info Hub v2 更新脚本
# 新流程: fetch_feeds → fetch_twitter → curate → build_html

cd "$(dirname "$0")"

echo "🚀 开始更新 Info Hub v2..."
echo ""

# 1. 抓取 RSS 和 YouTube
echo "📡 [1/4] 抓取 RSS 和 YouTube..."
venv/bin/python scripts/fetch_feeds.py
if [ $? -ne 0 ]; then
    echo "❌ RSS/YouTube 抓取失败"
    exit 1
fi
echo ""

# 2. 抓取 Twitter
echo "🐦 [2/4] 抓取 Twitter 推文..."
venv/bin/python scripts/fetch_twitter.py
if [ $? -ne 0 ]; then
    echo "❌ Twitter 抓取失败"
    exit 1
fi
echo ""

# 3. AI 筛选和分类
echo "🤖 [3/4] AI 筛选和点评..."
venv/bin/python scripts/curate.py
if [ $? -ne 0 ]; then
    echo "❌ AI 处理失败"
    exit 1
fi
echo ""

# 4. 生成 HTML
echo "🔨 [4/4] 生成 HTML..."
venv/bin/python scripts/build_html.py
if [ $? -ne 0 ]; then
    echo "❌ HTML 生成失败"
    exit 1
fi

echo ""

# 5. 复制到根目录并推送到 GitHub
echo "🚀 [5/5] 推送到 GitHub Pages..."
cp site/index.html index.html
cd "$(dirname "$0")"
git add index.html site/index.html
git commit -m "Daily update: $(date +%Y-%m-%d)" 2>/dev/null
git push 2>/dev/null
echo ""

echo "✅ 更新完成！"
echo "📂 本地: site/index.html"
echo "🌐 在线: https://jshisan2021-png.github.io/info-hub/"
