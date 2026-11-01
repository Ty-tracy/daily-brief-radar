"""
抓取分类新闻（经济 / 政策 / 科技前沿）
基于 Google News RSS 进行关键词聚合
"""
import feedparser
from datetime import datetime
import json
import urllib.parse

CATEGORIES = {
    "经济": ["中央预算内投资", "地方政府专项债", "新型政策性金融工具"],
    "政策": ["国家发改委", "宏观政策", "国务院常务会议", "六张网"],
    "科技": ["AI4S", "低空经济", "人工智能大模型"]
}

def fetch_category_news(category_name, keywords, max_items=5):
    query = " OR ".join(keywords)
    encoded_query = urllib.parse.quote(f"{query} when:7d")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        print(f"⚠️ 抓取分类 {category_name} 失败")
        return []
        
    results = []
    for entry in feed.entries[:max_items]:
        results.append({
            "source": f"综合新闻-{category_name}",
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "")),
            "tags": keywords[0]
        })
    return results

if __name__ == "__main__":
    all_items = []
    for category, keywords in CATEGORIES.items():
        print(f"正在检索分类：{category} ...")
        items = fetch_category_news(category, keywords)
        print(f"  → 抓到 {len(items)} 条")
        all_items.extend(items)

    output = {
        "fetched_at": datetime.now().isoformat(),
        "source": "category_news",
        "items": all_items,
    }
    with open("category_news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"已保存到 category_news.json")
