#!/opt/homebrew/bin/python3.12
"""
翻译模块：将英文标题和摘要翻译为中文
使用 Google Gemini Flash（免费额度，速度快）
"""

import json
import os
import re
from pathlib import Path

GEMINI_KEY = "AIzaSyCI3nuV7ii7JA8xdxDBEs9IsUBolJbJ6sA"


def is_chinese(text):
    """检测文本是否主要是中文"""
    if not text:
        return True
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese_chars / max(len(text), 1) > 0.3


def batch_translate(items, batch_size=15):
    """批量翻译标题和摘要"""
    import urllib.request

    # 筛选需要翻译的项目
    to_translate = []
    for i, item in enumerate(items):
        title = item.get('title', '')
        summary = item.get('summary', '')
        if not is_chinese(title) or not is_chinese(summary):
            to_translate.append((i, title, summary))

    if not to_translate:
        print("  ✓ 所有内容已是中文，无需翻译")
        return items

    print(f"  📝 需要翻译 {len(to_translate)} 条...")

    # 分批翻译
    for batch_start in range(0, len(to_translate), batch_size):
        batch = to_translate[batch_start:batch_start + batch_size]

        # 构造 prompt
        texts = []
        for idx, (i, title, summary) in enumerate(batch):
            clean_summary = re.sub(r'<[^>]+>', '', summary)[:200]
            texts.append(f"[{idx}] Title: {title}\nSummary: {clean_summary}")

        prompt = f"""将以下文章标题和摘要翻译为简体中文。保持自然简洁。
返回 JSON 数组格式：[{{"id": 0, "title": "中文标题", "summary": "中文摘要"}}]
只返回 JSON 数组，不要其他文字。

{chr(10).join(texts)}"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1}
            }).encode()

            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())

            text = result["candidates"][0]["content"]["parts"][0]["text"]
            # 提取 JSON
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                translations = json.loads(json_match.group())
                for t in translations:
                    idx = t.get("id", -1)
                    if 0 <= idx < len(batch):
                        orig_idx = batch[idx][0]
                        if t.get("title"):
                            items[orig_idx]["title_orig"] = items[orig_idx]["title"]
                            items[orig_idx]["title"] = t["title"]
                        if t.get("summary"):
                            items[orig_idx]["summary_orig"] = items[orig_idx]["summary"]
                            items[orig_idx]["summary"] = t["summary"]

                print(f"  ✓ 翻译完成 {batch_start + 1}-{batch_start + len(batch)}/{len(to_translate)}")
            else:
                print(f"  ⚠️  无法解析翻译结果")

        except Exception as e:
            print(f"  ⚠️  翻译批次失败: {e}")

    return items
