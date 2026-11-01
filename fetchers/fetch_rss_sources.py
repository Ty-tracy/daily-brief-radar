"""
抓取指定信息源（大容量版）
"""
import feedparser
from datetime import datetime
import json
import urllib.parse

RSS_SOURCES = {
    "发改委与国务院": "site:ndrc.gov.cn OR site:gov.cn 政策 OR 资金",
    "财政与专项债": "专项债 OR 超长期特别国债 OR 中央预算内投资",
    "宏观经济数据": "国家统计局 OR 宏观经济数据 OR CPI OR PPI",
    "新质生产力": "新质生产力 OR 低空经济 OR 算力网 OR 卫星互联网",
    "AI与前沿科技": "AI4S OR 大模型 OR 人工智能应用",
    "地方经济动态": "湖北经济 OR 宜昌经济 OR 地方专项债",
}

def fetch_rss(name, query, max_items=10):  # 增加每次抓取的数量
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
    with open("rss_sources.json", "w", encoding="utf-8") as f:
        json.dump({"items": all_items}, f, ensure_ascii=False, indent=2)
