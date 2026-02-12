#!/opt/homebrew/bin/python3.12
"""
RSS/YouTube 抓取脚本
读取 config.yaml，抓取所有源的最新内容，输出到 data/feeds.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import signal
import feedparser
import yaml

# 超时处理
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Request timed out")


# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "config.yaml"
OUTPUT_FILE = ROOT_DIR / "data" / "feeds.json"


def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def fetch_rss(url, source_name, category):
    """
    抓取单个RSS源
    返回 list of dict，每个dict包含: title, link, published, summary, source_name, category
    """
    items = []
    try:
        print(f"[RSS] 抓取 {source_name} ({url})...")
        import requests
        resp = requests.get(url, timeout=15, headers={"User-Agent": "InfoHub/1.0"})
        feed = feedparser.parse(resp.content)
        
        # 如果 feedparser 解析失败且是 XML 格式错误，尝试 BeautifulSoup 容错解析
        if feed.bozo and feed.bozo_exception:
            print(f"  ⚠️  feedparser 解析警告: {feed.bozo_exception}")
            if 'not well-formed' in str(feed.bozo_exception).lower() or not feed.entries:
                print(f"  🔄 尝试 BeautifulSoup 容错解析...")
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.content, 'xml')
                    entries = soup.find_all('item') or soup.find_all('entry')
                    
                    for entry in entries[:20]:
                        title = entry.find('title')
                        link = entry.find('link')
                        pub_date = entry.find('pubDate') or entry.find('published') or entry.find('updated')
                        summary = entry.find('description') or entry.find('summary') or entry.find('content')
                        
                        # 解析时间
                        published = None
                        if pub_date and pub_date.text:
                            try:
                                from email.utils import parsedate_to_datetime
                                published = parsedate_to_datetime(pub_date.text).isoformat()
                            except:
                                published = pub_date.text
                        
                        item = {
                            'title': title.text.strip() if title else '无标题',
                            'link': link.text.strip() if link and link.text else (link.get('href', '') if link else ''),
                            'published': published,
                            'summary': (summary.text.strip()[:300] if summary else '')[:300],
                            'source_name': source_name,
                            'category': category,
                            'type': 'rss'
                        }
                        items.append(item)
                    
                    print(f"  ✓ BeautifulSoup 成功抓取 {len(items)} 条")
                    return items
                except Exception as bs_error:
                    print(f"  ✗ BeautifulSoup 也失败: {bs_error}")
        
        # 使用 feedparser 的正常结果
        for entry in feed.entries[:20]:  # 只取最新20条
            # 统一时间格式
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6]).isoformat()
            
            item = {
                'title': entry.get('title', '无标题'),
                'link': entry.get('link', ''),
                'published': published,
                'summary': entry.get('summary', entry.get('description', ''))[:300],  # 限制摘要长度
                'source_name': source_name,
                'category': category,
                'type': 'rss'
            }
            items.append(item)
        
        print(f"  ✓ 成功抓取 {len(items)} 条")
        
    except TimeoutError:
        signal.alarm(0)
        print(f"  ✗ 超时（15秒）")
    except Exception as e:
        signal.alarm(0)
        print(f"  ✗ 失败: {e}")
    
    return items


def fetch_youtube(channel_id, channel_name, category):
    """
    抓取YouTube频道最新视频
    使用 yt-dlp 获取视频列表
    """
    items = []
    try:
        import subprocess
        
        print(f"[YouTube] 抓取 {channel_name} ({channel_id})...")
        
        # 使用 yt-dlp 获取频道最新视频（使用 venv 中的 yt-dlp）
        yt_dlp_path = str(ROOT_DIR / 'venv' / 'bin' / 'yt-dlp')
        cmd = [
            yt_dlp_path,
            '--flat-playlist',
            '--playlist-end', '20',  # 只获取最新20个
            '--dump-json',
            f'https://www.youtube.com/channel/{channel_id}/videos'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"  ✗ yt-dlp 失败: {result.stderr}")
            return items
        
        # 解析每一行JSON
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                video = json.loads(line)
                item = {
                    'title': video.get('title', '无标题'),
                    'link': f"https://www.youtube.com/watch?v={video.get('id', '')}",
                    'published': video.get('upload_date'),  # YYYYMMDD格式，需要转换
                    'summary': video.get('description', '')[:300],
                    'source_name': channel_name,
                    'category': category,
                    'type': 'youtube',
                    'thumbnail': video.get('thumbnail', '')
                }
                
                # 转换时间格式
                if item['published']:
                    date_str = item['published']
                    item['published'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T00:00:00"
                
                items.append(item)
            except json.JSONDecodeError:
                continue
        
        print(f"  ✓ 成功抓取 {len(items)} 条")
        
    except subprocess.TimeoutExpired:
        print(f"  ✗ 超时")
    except FileNotFoundError:
        print(f"  ✗ yt-dlp 未安装，跳过YouTube抓取")
    except Exception as e:
        print(f"  ✗ 失败: {e}")
    
    return items


def main():
    """主函数"""
    print("=" * 60)
    print("Info Hub - RSS/YouTube 抓取器")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    all_items = []
    
    # 抓取RSS源
    print("\n📰 RSS 源:")
    for source in config.get('rss', []):
        items = fetch_rss(source['url'], source['name'], source['category'])
        all_items.extend(items)
    
    # 抓取YouTube频道
    print("\n📺 YouTube 频道:")
    youtube_sources = config.get('youtube', [])
    if youtube_sources:
        for source in youtube_sources:
            items = fetch_youtube(source['channel_id'], source['name'], source['category'])
            all_items.extend(items)
    else:
        print("  （未配置）")
    
    # 按时间排序（最新的在前）
    all_items.sort(
        key=lambda x: x.get('published') or '',
        reverse=True
    )
    
    # 翻译为中文
    print("\n🌐 翻译:")
    try:
        from translate import batch_translate
        all_items = batch_translate(all_items)
    except Exception as e:
        print(f"  ⚠️  翻译模块加载失败: {e}")
    
    # 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output = {
        'updated_at': datetime.now().isoformat(),
        'total': len(all_items),
        'items': all_items
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✓ 完成！共抓取 {len(all_items)} 条内容")
    print(f"✓ 输出文件: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
