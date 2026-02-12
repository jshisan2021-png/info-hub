#!/opt/homebrew/bin/python3.12
"""
Twitter/X 推文抓取脚本
使用 bird CLI 抓取 config.yaml 中配置的 Twitter 账号最新推文
输出到 data/twitter.json
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import yaml

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "config.yaml"
OUTPUT_FILE = ROOT_DIR / "data" / "twitter.json"

# Twitter 认证环境变量
AUTH_TOKEN = "d6c2b88b12e3a0b95dd0aff068ce2ca4674b3aef"
CT0 = "9b6309d10218adac541d6486c1b98b1cbf248a478dc14ff7d828ef41a32744f00f6ed385246147af08b2f82b0ffaa263151c2dd9dfc6f9386ae61ba9b36ab70497fc8aa745765074f0f5b765c350a5b4"


def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def fetch_user_tweets(handle, user_name, category):
    """
    使用 bird CLI 抓取某个用户的推文
    返回最近24小时的推文列表
    """
    items = []
    
    try:
        print(f"[Twitter] 抓取 @{handle} ({user_name})...")
        
        # 设置环境变量
        env = os.environ.copy()
        env['AUTH_TOKEN'] = AUTH_TOKEN
        env['CT0'] = CT0
        
        # 调用 bird CLI（使用 --json 输出）
        cmd = ['bird', 'user-tweets', handle, '--count', '5', '--json']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        if result.returncode != 0:
            print(f"  ✗ bird CLI 失败: {result.stderr}")
            return items
        
        # 过滤掉 info 行，找到 JSON 内容
        output_lines = result.stdout.strip().split('\n')
        json_start = -1
        for i, line in enumerate(output_lines):
            if line.strip().startswith('['):
                json_start = i
                break
        
        if json_start == -1:
            print(f"  ✗ 未找到 JSON 输出")
            return items
        
        # 解析 JSON 数组
        json_text = '\n'.join(output_lines[json_start:])
        try:
            tweets = json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON 解析失败: {e}")
            return items
        
        # 处理每条推文
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)
        
        for tweet in tweets:
            try:
                
                # 解析时间（bird 的格式：Wed Feb 11 21:14:49 +0000 2026）
                created_at = tweet.get('createdAt', '')
                if not created_at:
                    continue
                
                # 转换时间格式
                from datetime import datetime as dt_parser
                tweet_time = dt_parser.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                
                # 过滤24小时外的推文
                if tweet_time < cutoff:
                    continue
                
                # 提取推文信息
                item = {
                    'title': tweet.get('text', '')[:200],  # 标题用前200字符
                    'text': tweet.get('text', ''),
                    'link': f"https://twitter.com/{handle}/status/{tweet.get('id', '')}",
                    'published': tweet_time.isoformat(),
                    'source_name': f"@{handle}",
                    'author': user_name,
                    'category': category,
                    'type': 'twitter',
                    'likes': tweet.get('likeCount', 0),
                    'retweets': tweet.get('retweetCount', 0),
                    'replies': tweet.get('replyCount', 0)
                }
                
                items.append(item)
                
            except Exception as e:
                print(f"  ⚠️  处理推文失败: {e}")
                continue
        
        print(f"  ✓ 成功抓取 {len(items)} 条（24小时内）")
        
    except subprocess.TimeoutExpired:
        print(f"  ✗ 超时（30秒）")
    except FileNotFoundError:
        print(f"  ✗ bird CLI 未找到，请确认已安装")
        sys.exit(1)
    except Exception as e:
        print(f"  ✗ 失败: {e}")
    
    return items


def main():
    """主函数"""
    print("=" * 60)
    print("Info Hub - Twitter 推文抓取器")
    print("=" * 60)
    
    # 检查 bird CLI
    try:
        subprocess.run(['bird', '--version'], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ bird CLI 未找到或无法运行")
        print("请确认 bird 已安装并在 PATH 中")
        sys.exit(1)
    
    # 加载配置
    config = load_config()
    twitter_accounts = config.get('twitter', [])
    
    if not twitter_accounts:
        print("⚠️  config.yaml 中未配置 twitter 账号")
        sys.exit(0)
    
    print(f"\n📱 共配置 {len(twitter_accounts)} 个 Twitter 账号\n")
    
    # 抓取所有账号（加延时防 rate limit）
    import time
    all_items = []
    for i, account in enumerate(twitter_accounts):
        handle = account.get('handle', '')
        name = account.get('name', handle)
        category = account.get('category', 'tech')
        
        if not handle:
            continue
        
        items = fetch_user_tweets(handle, name, category)
        all_items.extend(items)
        
        # 每抓 3 个账号暂停 5 秒，防止 rate limit
        if (i + 1) % 3 == 0 and i < len(twitter_accounts) - 1:
            print(f"  ⏳ 暂停 5 秒（防限流）...")
            time.sleep(5)
    
    # 按时间排序（最新的在前）
    all_items.sort(
        key=lambda x: x.get('published', ''),
        reverse=True
    )
    
    # 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output = {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'total': len(all_items),
        'items': all_items
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✓ 完成！共抓取 {len(all_items)} 条推文（24小时内）")
    print(f"✓ 输出文件: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
