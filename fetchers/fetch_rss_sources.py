"""
抓取多个RSS信息源（宏观政策 / 经济数据 / 发改动态 / 前沿科技）
用 feedparser 这个专门解析RSS的工具库，比自己写XML解析省事很多

运行前需要先装：pip install feedparser
"""
import feedparser
from datetime import datetime
import json

# 信息源清单：名字 + RSS地址
RSS_SOURCES = {
    # ==========================================
    # 核心宏观与政策（原生稳定源）
    # ==========================================
    "国家统计局": "http://www.stats.gov.cn/tjsj/zxfb/rss.xml",
    "财新网-要闻": "https://gateway.caixin.com/api/data/global/feedlyRss.xml",
    
    # ==========================================
    # 发改与专项债（Google News 聚合，防止官网反爬失效）
    # ==========================================
    "发改委最新政策": "https://news.google.com/rss/search?q=site:ndrc.gov.cn+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "专项债与国债动态": "https://news.google.com/rss/search?q=专项债+OR+超长期特别国债+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    
    # ==========================================
    # 科技前沿与产业（AI4S / 低空 / 北斗）
    # ==========================================
    "前沿科技风向": "https://news.google.com/rss/search?q=AI4S+OR+低空经济+OR+北斗+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    
    # ==========================================
    # 补充一点商业科技视点
    # ==========================================
    "36氪": "https://36kr.com/feed",
}

def fetch_rss(name, url, max_items=8):
    """抓取单个RSS源，返回最新几条"""
    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        # bozo=1 通常表示解析出了点问题，如果还完全没抓到内容，说明这个源可能失效了
        print(f"⚠️ {name} 抓取可能有问题，跳过（{url}）")
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

    for name, url in RSS_SOURCES.items():
        print(f"正在抓取 {name} ...")
        items = fetch_rss(name, url)
        print(f"  → 抓到 {len(items)} 条")
        all_items.extend(items)

    print(f"\n总共抓取到 {len(all_items)} 条")
    for i, item in enumerate(all_items, 1):
        print(f"{i}. [{item['source']}] {item['title']}")
        print(f"   {item['url']}\n")

    output = {
        "fetched_at": datetime.now().isoformat(),
        "source": "rss_mixed",
        "items": all_items,
    }
    with open("rss_sources.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"已保存到 rss_sources.json（共 {len(all_items)} 条）")
