"""
抓取指定信息源（国内真实链接版）
使用带 User-Agent 的镜像节点，绕过反爬，拿真实原文链接
"""
import feedparser
from datetime import datetime
import json
import urllib.request

# 伪装成浏览器，防止被国内网站直接拦截
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

RSS_SOURCES = {
    # 官方直连
    "国家统计局": "http://www.stats.gov.cn/tjsj/zxfb/rss.xml",
    "财新网": "https://gateway.caixin.com/api/data/global/feedlyRss.xml",
    "36氪": "https://36kr.com/feed",
    
    # 发改委与国务院（使用 RSSHub 镜像，如果这个镜像挂了，可以换成 rsshub.app）
    "发改委最新政策": "https://rsshub.rssforever.com/gov/ndrc/zcfb",
    "国务院最新政策": "https://rsshub.rssforever.com/gov/zhengce/zuixin",
    "财政部动态": "https://rsshub.rssforever.com/gov/mof/gzdt"
}

def fetch_rss(name, url, max_items=5):
    try:
        # 核心修复：手动带上 User-Agent 请求数据
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read()
            
        feed = feedparser.parse(content)

        if feed.bozo and not feed.entries:
            print(f"⚠️ {name} 抓取可能有问题，跳过")
            return []

        results = []
        for entry in feed.entries[:max_items]:
            results.append({
                "source": name,
                "title": entry.get("title", ""),
                "url": entry.get("link", ""), # 这里的链接就是真实的国内官网链接了
                "published": entry.get("published", entry.get("updated", "")),
            })
        return results
    except Exception as e:
        print(f"❌ {name} 抓取失败: {e}")
        return []

if __name__ == "__main__":
    all_items = []
    for name, url in RSS_SOURCES.items():
        print(f"正在抓取 {name} ...")
        items = fetch_rss(name, url)
        print(f"  → 抓到 {len(items)} 条")
        all_items.extend(items)

    print(f"\n总共抓取到 {len(all_items)} 条")
    with open("rss_sources.json", "w", encoding="utf-8") as f:
        json.dump({"items": all_items}, f, ensure_ascii=False, indent=2)
    print(f"已保存到 rss_sources.json")
