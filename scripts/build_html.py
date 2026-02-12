#!/opt/homebrew/bin/python3.12
"""
HTML 生成器 v2
读取 data/curated.json（AI 筛选后的内容），生成日报风格的静态页面
"""

import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DATA_FILE = ROOT_DIR / "data" / "curated.json"
OUTPUT_FILE = ROOT_DIR / "site" / "index.html"


def generate_html(data):
    """生成 HTML 内容"""
    
    updated_at = data.get('updated_at', '')
    items = data.get('items', [])
    hot_topics = data.get('hot_topics', [])
    
    # 格式化日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 按 AI 分类分组
    categories = defaultdict(list)
    for item in items:
        cat = item.get('ai_category', '其他')
        categories[cat].append(item)
    
    # 生成热门话题区块
    hot_topics_html = ""
    if hot_topics:
        for topic in hot_topics[:5]:  # 最多显示5个
            hot_topics_html += f"""
            <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                <h3 class="font-bold text-red-900 mb-1">🔥 {topic.get('topic', '')}</h3>
                <p class="text-sm text-red-700">{topic.get('description', '')}</p>
            </div>
            """
    else:
        hot_topics_html = '<p class="text-gray-500">今日暂无热门话题</p>'
    
    # 生成分类内容区块
    categories_html = ""
    
    # 固定分类顺序
    category_order = [
        '🧠 AI 研究前沿',
        '🤖 AI Agent & 工具',
        '🎨 AI 创作 & 视频',
        '💰 创业 & 商业',
        '🔬 科学',
        '🔧 技术'
    ]
    
    for cat_name in category_order:
        cat_items = categories.get(cat_name, [])
        if not cat_items:
            continue
        
        items_html = ""
        for item in cat_items:
            # 来源标识
            source_type = item.get('type', 'rss')
            if source_type == 'twitter':
                source_icon = '🐦'
                source_name = item.get('source_name', '')
            elif source_type == 'youtube':
                source_icon = '📺'
                source_name = item.get('source_name', '')
            else:
                source_icon = '📰'
                source_name = item.get('source_name', '')
            
            # AI 点评
            comment = item.get('ai_comment', '')
            
            items_html += f"""
            <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <h3 class="font-semibold text-gray-900 mb-2 leading-snug">
                    <a href="{item.get('link', '#')}" target="_blank" class="hover:text-blue-600">
                        {item.get('title', '无标题')}
                    </a>
                </h3>
                <div class="flex items-center text-sm text-gray-500 mb-2">
                    <span class="mr-3">{source_icon} {source_name}</span>
                </div>
                <p class="text-sm text-gray-700 italic border-l-2 border-blue-500 pl-3">
                    💬 {comment}
                </p>
            </div>
            """
        
        categories_html += f"""
        <section class="mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-4 pb-2 border-b-2 border-gray-300">
                {cat_name}
            </h2>
            <div class="space-y-3">
                {items_html}
            </div>
        </section>
        """
    
    # 统计信息
    total_items = len(items)
    sources_count = len(set(item.get('source_name', '') for item in items))
    
    # 完整 HTML 模板
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily News | {today}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #ffffff;
        }}
    </style>
</head>
<body class="bg-white text-gray-900">
    <!-- 头部 -->
    <header class="bg-white border-b border-gray-300 py-6">
        <div class="container mx-auto px-4 max-w-4xl">
            <h1 class="text-4xl font-bold text-gray-900">Daily News</h1>
            <p class="text-gray-600 mt-2 text-lg">{today}</p>
        </div>
    </header>

    <!-- 主内容 -->
    <main class="container mx-auto px-4 py-8 max-w-4xl">
        <!-- 今日热门话题 -->
        <section class="mb-10">
            <h2 class="text-2xl font-bold text-gray-800 mb-4 pb-2 border-b-2 border-gray-300">
                📌 今日热门话题
            </h2>
            <div class="space-y-3">
                {hot_topics_html}
            </div>
        </section>

        <!-- 分类内容 -->
        {categories_html}
    </main>

    <!-- 页脚 -->
    <footer class="bg-gray-50 border-t border-gray-200 py-6 mt-12">
        <div class="container mx-auto px-4 max-w-4xl text-center text-gray-600 text-sm">
            <p class="mb-2">
                最后更新: {updated_at[:19].replace('T', ' ')} · 
                精选 {total_items} 条内容 · 
                来自 {sources_count} 个数据源
            </p>
            <p class="text-gray-500">
                由 AI 自动筛选和点评 · Powered by Gemini 2.0 Flash
            </p>
        </div>
    </footer>
</body>
</html>
"""
    
    return html


def main():
    """主函数"""
    print("=" * 60)
    print("Info Hub - HTML 生成器 v2")
    print("=" * 60)
    
    # 读取数据
    if not DATA_FILE.exists():
        print(f"❌ 数据文件不存在: {DATA_FILE}")
        print("请先运行 curate.py 生成精选内容")
        return
    
    print(f"\n📂 读取数据: {DATA_FILE}")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ 数据加载完成")
    print(f"  - 精选内容: {data.get('total', 0)} 条")
    print(f"  - 热门话题: {len(data.get('hot_topics', []))} 个")
    
    # 生成 HTML
    print("\n🔨 生成 HTML...")
    html = generate_html(data)
    
    # 保存文件
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ HTML 生成完成: {OUTPUT_FILE}")
    print(f"✓ 文件大小: {len(html) / 1024:.1f} KB")
    print("\n" + "=" * 60)
    print("✓ 完成！可以用浏览器打开 site/index.html 查看")
    print("=" * 60)


if __name__ == "__main__":
    main()
