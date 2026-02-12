#!/opt/homebrew/bin/python3.12
"""
AI 内容筛选与点评脚本
读取 data/feeds.json + data/twitter.json，用 Gemini API 做：
1. 筛选出 15-25 条最有价值的内容
2. 按主题分类
3. 为每条配一句话中文点评
4. 识别今日热门话题
输出到 data/curated.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import requests

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
FEEDS_FILE = ROOT_DIR / "data" / "feeds.json"
TWITTER_FILE = ROOT_DIR / "data" / "twitter.json"
OUTPUT_FILE = ROOT_DIR / "data" / "curated.json"

# Gemini API 配置
GEMINI_API_KEY = "AIzaSyCI3nuV7ii7JA8xdxDBEs9IsUBolJbJ6sA"
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def load_all_items():
    """加载所有数据源"""
    all_items = []
    
    # 加载 RSS/YouTube
    if FEEDS_FILE.exists():
        with open(FEEDS_FILE, 'r', encoding='utf-8') as f:
            feeds_data = json.load(f)
            all_items.extend(feeds_data.get('items', []))
    
    # 加载 Twitter
    if TWITTER_FILE.exists():
        with open(TWITTER_FILE, 'r', encoding='utf-8') as f:
            twitter_data = json.load(f)
            all_items.extend(twitter_data.get('items', []))
    
    return all_items


def prepare_content_for_ai(items):
    """准备内容给 AI 分析"""
    content_list = []
    
    for i, item in enumerate(items):
        # 为每条内容准备摘要
        source = item.get('source_name', 'Unknown')
        title = item.get('title', 'No Title')
        text = item.get('text', item.get('summary', ''))[:500]  # 限制长度
        
        content_list.append({
            'id': i,
            'source': source,
            'title': title,
            'text': text,
            'type': item.get('type', 'unknown')
        })
    
    return content_list


def call_gemini_api(prompt, temperature=0.3):
    """调用 Gemini API"""
    headers = {
        'Content-Type': 'application/json',
    }
    
    payload = {
        'contents': [{
            'parts': [{
                'text': prompt
            }]
        }],
        'generationConfig': {
            'temperature': temperature,
            'topP': 0.95,
            'topK': 40,
            'maxOutputTokens': 8192,
        }
    }
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        text = result['candidates'][0]['content']['parts'][0]['text']
        return text
        
    except Exception as e:
        print(f"❌ Gemini API 调用失败: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"响应: {e.response.text}")
        return None


def curate_content(all_items):
    """使用 AI 筛选和分类内容"""
    
    # 准备内容
    content_list = prepare_content_for_ai(all_items)
    
    print(f"📊 共 {len(content_list)} 条原始内容")
    print("\n🤖 调用 Gemini API 进行筛选和分类...")
    
    # 构建 prompt
    prompt = f"""你是一个科技内容策展人。我有以下 {len(content_list)} 条来自 RSS、YouTube 和 Twitter 的内容。

内容列表（JSON格式）：
{json.dumps(content_list, ensure_ascii=False, indent=2)}

请完成以下任务：

1. **筛选出 15-25 条最有价值的内容**（标准：信息密度高、观点独特、实用性强、时效性强）

2. **按主题分类**，使用以下类别：
   - 🧠 AI 研究前沿（论文、模型、技术突破）
   - 🤖 AI Agent & 工具（应用、产品、开发工具）
   - 🎨 AI 创作 & 视频（生成式 AI、创意应用）
   - 💰 创业 & 商业（商业模式、融资、市场分析）
   - 🔬 科学（非 AI 的科学研究）
   - 🔧 技术（编程、工程、基础设施）

3. **为每条内容写一句话中文点评**（不超过50字，突出核心价值或亮点）

4. **识别今日热门话题**（3-5个）：多个来源讨论同一话题的，提取为热点

请以 JSON 格式返回，结构如下：
{{
  "selected": [
    {{
      "id": 原始内容的id,
      "category": "分类emoji和名称（如 '🧠 AI 研究前沿'）",
      "comment": "中文点评（不超过50字）"
    }}
  ],
  "hot_topics": [
    {{
      "topic": "话题名称",
      "description": "一句话描述",
      "related_ids": [相关内容的id列表]
    }}
  ]
}}

只返回 JSON，不要其他文字。"""
    
    # 调用 API
    response_text = call_gemini_api(prompt, temperature=0.3)
    
    if not response_text:
        print("❌ AI 处理失败")
        return None
    
    # 解析 JSON（去除可能的 markdown 代码块标记）
    response_text = response_text.strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    try:
        ai_result = json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"AI 返回内容：\n{response_text[:500]}")
        return None
    
    # 组装最终结果
    curated_items = []
    for selection in ai_result.get('selected', []):
        item_id = selection['id']
        if 0 <= item_id < len(all_items):
            item = all_items[item_id].copy()
            item['ai_category'] = selection['category']
            item['ai_comment'] = selection['comment']
            curated_items.append(item)
    
    hot_topics = ai_result.get('hot_topics', [])
    
    print(f"✓ AI 筛选完成：{len(curated_items)} 条精选内容")
    print(f"✓ 识别热门话题：{len(hot_topics)} 个")
    
    return {
        'items': curated_items,
        'hot_topics': hot_topics
    }


def main():
    """主函数"""
    print("=" * 60)
    print("Info Hub - AI 内容策展")
    print("=" * 60)
    
    # 加载数据
    print("\n📂 加载数据...")
    all_items = load_all_items()
    
    if not all_items:
        print("❌ 没有找到任何内容")
        sys.exit(1)
    
    print(f"✓ 加载完成，共 {len(all_items)} 条原始内容")
    
    # AI 筛选和分类
    print("\n" + "=" * 60)
    result = curate_content(all_items)
    
    if not result:
        sys.exit(1)
    
    # 保存结果
    output = {
        'updated_at': datetime.now().isoformat(),
        'total': len(result['items']),
        'items': result['items'],
        'hot_topics': result['hot_topics']
    }
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✓ 完成！精选 {len(result['items'])} 条内容")
    print(f"✓ 热门话题 {len(result['hot_topics'])} 个")
    print(f"✓ 输出文件: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
