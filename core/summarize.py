"""
生成结构化政务/宏观中文简报（高密度内容版）
"""
import json
import os
import sys
import time
import requests
from datetime import datetime

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

def get_slot():
    return sys.argv[1] if len(sys.argv) > 1 else "morning"

def call_deepseek(prompt, max_retries=4, temperature=0.3):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": "你是一位资深的发改委宏观政策研究员。"}, {"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(DEEPSEEK_URL, headers=headers, json=body, timeout=120)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == max_retries: raise e
            time.sleep(attempt * 5)

def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError: return None

def generate_overview(all_news_text):
    prompt = f"""下面是今天抓取的宏观、经济新闻。请写一段深度的【今日宏观总览】。
格式：
【今日定调】一句话高度概括今天的政策与资金主线（30字内）。
【核心观察】用3-4句话，详细分析今天资讯中释放的政策信号、资金流向或产业逻辑，要有政策深度。
【趋势预判】用2-3句话，预判接下来的政策走向或对地方发改工作的影响。

新闻素材：
{all_news_text}"""
    return call_deepseek(prompt)

def generate_top_picks(all_news_text):
    prompt = f"""从以下新闻中，挑选出今天最核心的1条重大政策或资金动向，进行深度解读。
格式（严格用 ||| 分隔）：
来源名|||标题|||链接|||发生了什么（详细50字）|||处理情况（30字）|||原理科普（30字）|||对你的意义（结合实际工作，50字）

新闻素材：
{all_news_text}"""
    return call_deepseek(prompt)

def generate_category_cards(all_news_text, category_name, count=4):
    # 强制要求数量，并拉长字数
    prompt = f"""从以下新闻中，挑选出 {count} 条最符合【{category_name}】类别的资讯。如果新闻素材不够，请把新闻中涉及此类的宏观背景一并揉进去总结。
格式（严格用 ||| 分隔六段）：
来源名|||标题|||链接|||关键词标签|||深度摘要（必须达到40字，讲清背景和事实）|||一句话点评（必须达到30字，分析影响）

新闻素材：
{all_news_text}"""
    return call_deepseek(prompt)

def generate_action_advice(all_news_text):
    prompt = f"""基于今天的海量政策新闻，为地方发改公职人员生成【今日工作建议】。
格式：
【可能的方向】
列出3个具体的谋划方向（格式：方向名称|||具体做法，至少30字，要能落地）
【避坑提示】
指出1个目前不值得投入的伪需求（30字）
【今日行动】
今天最该去查什么文件、看什么数据（30字）
"""
    return call_deepseek(prompt)

if __name__ == "__main__":
    slot = get_slot()
    today = datetime.now().strftime("%Y-%m-%d")
    sections = {}
    all_items = []
    
    rss_data = load_json("rss_sources.json")
    if rss_data and rss_data.get("items"): all_items.extend(rss_data["items"])

    if not all_items:
        print("❌ 没有抓取到新闻。")
        sys.exit(1)

    # 把文章正文截取前200字作为素材，或者直接把标题塞进去（这里直接塞标题和链接）
    all_news_text = "\n".join([f"[{x.get('source')}] {x.get('title')} (链接:{x.get('url')})" for x in all_items])

    print("生成宏观总览...")
    sections["overview"] = generate_overview(all_news_text)
    print("提取核心头条...")
    sections["top_picks"] = generate_top_picks(all_news_text)
    
    print("生成【资金与专项债】板块...")
    sections["economy"] = generate_category_cards(all_news_text, "资金与专项债", 4)
    print("生成【宏观政策与基建】板块...")
    sections["politics"] = generate_category_cards(all_news_text, "宏观政策与基建", 4)
    print("生成【前沿科技与新质】板块...")
    sections["science"] = generate_category_cards(all_news_text, "前沿科技与新质生产力", 4)
    
    print("生成行动建议...")
    sections["action"] = generate_action_advice(all_news_text)
    
    sections["greeting"] = "【开头】\n领导早安，这是今日宏观政策与资金动向密集通报。\n【结尾】\n请查收。"

    with open("daily_brief.md", "w", encoding="utf-8") as f:
        f.write(f"DATE|||{today}\nSLOT|||{slot}\n")
        for k in ["overview", "top_picks", "economy", "politics", "science", "action", "greeting"]:
            f.write(f"SECTION|||{k}\n{sections.get(k, '')}\n")

    print("✅ 高密度简报已生成！")
