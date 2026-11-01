"""
抓取分类新闻（经济 / 政治 / 科学前沿）
基于 Google News RSS 进行关键词聚合，比直接爬网页更稳定
"""
import feedparser
from datetime import datetime
import json

# 针对你的需求定制的关键词
CATEGORIES = {
    "economy": [
        "宏观经济", "中央预算内投资", "地方政府专项债", "超长期特别国债", "新型政策性金融工具"
    ],
    "politics": [
        "国家发改委", "宏观政策", "国务院常务会议", "六张网", "基础设施投资"
    ],
    "science": [
        "AI4S", "低空经济", "北斗应用", "人工智能大模型"
    ]
}

def fetch_category_news(category_keywords, max_items=5):
    """按关键词搜索新闻"""
    results = []
    
    # 把关键词组合成 Google News 搜索语法 (OR 连接)
    query = "+OR+".join(category_keywords)
    # 限定过去 7 天内的中文新闻
    url = f"https://news.google.com/rss/search?q={query}+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    
    feed = feedparser.parse(url)
    
    if feed.bozo and not feed.entries:
        print(f"⚠️ 抓取分类 {category_keywords[0]} 失败")
        return []
        
    for entry in feed.entries[:max_items]:
        results.append({
            "source": "综合新闻",
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "")),
            "tags": category_keywords[0] # 打上标签
        })
    return results

if __name__ == "__main__":
    all_items = []
    
    for category, keywords in CATEGORIES.items():
        print(f"正在检索分类：{category} ...")
        items = fetch_category_news(keywords)
        print(f"  → 抓到 {len(items)} 条")
        all_items.extend(items)

    print(f"\n总共抓取到 {len(all_items)} 条分类新闻")
    
    output = {
        "fetched_at": datetime.now().isoformat(),
        "source": "category_news",
        "items": all_items,
    }
    with open("category_news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"已保存到 category_news.json")
