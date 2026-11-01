"""
抓取指定信息源（使用 Google News 聚合，解决国内网站屏蔽海外 IP 的问题）
"""
import feedparser
from datetime import datetime
import json
import urllib.parse

# 这里我们不再直连国内网站，而是让 Google 帮我们去抓取
RSS_SOURCES = {
    "发改委最新政策": "site:ndrc.gov.cn",
    "专项债与国债动态": "专项债 OR 超长期特别国债",
    "AI4S与低空经济": "AI4S OR 低空经济 OR 北斗",
    "宏观财经": "宏观经济 OR 财新网",
}

def fetch_rss(name, query, max_items=5):
    # 核心修复：对中文关键词进行 URL 编码
    encoded_query = urllib.parse.quote(f"{query} when:7d")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    
    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        print(f"⚠️ {name} 抓取可能有问题，跳过")
        return []

    results = []
    for entry in feed.entries[:max_items]:
        results.append({
            "source": name,
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "")),
        })
    return results

if __name__ == "__main__":
    all_items = []
    for name, query in RSS_SOURCES.items():
        print(f"正在抓取 {name} ...")
        items = fetch_rss(name, query)
        print(f"  → 抓到 {len(items)} 条")
        all_items.extend(items)

    print(f"\n总共抓取到 {len(all_items)} 条")
    output = {
        "fetched_at": datetime.now().isoformat(),
        "source": "rss_mixed",
        "items": all_items,
    }
    with open("rss_sources.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"已保存到 rss_sources.json")
