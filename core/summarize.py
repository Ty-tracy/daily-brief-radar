"""
把已经抓好的 JSON 丢给 DeepSeek，生成结构化政务/宏观中文简报
"""
import json
import os
import sys
import time
import requests
from datetime import datetime

# ============ DeepSeek API Key ============
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# 适配早晚班
def get_slot():
    if len(sys.argv) > 1 and sys.argv[1] in ("morning", "evening"):
        return sys.argv[1]
    return "morning" if datetime.now().hour < 12 else "evening"

# ============ 你的专属发改画像 ============
USER_NAME = "领导"
USER_PROFILE_TEXT = """身份：地方发改部门公职人员。
核心目标：跟踪国家宏观政策、国债、中央预算内投资、专项债及新型政策性金融工具。
重点关注领域：国家及湖北省、宜昌市经济指标；AI4S、低空经济、北斗等前沿技术；六张网基建。
行动建议偏好：需要具体的项目谋划建议、资金争取思路和政策研判。"""

NO_RHETORIC_RULE = "语言要求：绝对不要使用任何比喻、修辞手法，直奔主题。要用标准的政务与宏观经济术语，越专业越好。"

def call_deepseek(prompt, max_retries=4, temperature=0.3):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位资深的发改委宏观政策研究员与项目谋划专家。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
    }
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(DEEPSEEK_URL, headers=headers, json=body, timeout=120)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(attempt * 5)
            else:
                print(f"  ⚠️ DeepSeek 请求放弃: {e}")
    raise last_error

def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# ============ 生成各模块 ============

def generate_overview(all_news_text):
    prompt = f"""下面是今天抓取到的宏观、经济与科技政策新闻，请写一段“今日总览”，格式严格如下：

【今日一句话】
抽象概括今天宏观政策、资金动向或产业趋势的主题，不超过25字。不要罗列一堆公司名，要提炼出核心定调。
【AI观察】
1-2句话，分析今天资讯中释放的政策信号、资金流向或产业逻辑。
【趋势预测】
1-2句话，基于今天的信息，预判接下来的政策风向或市场影响。
【最该做的】
如果新闻中有紧急或重要的资金申报、政策落地，挑最核心的一条写（不超过20字）；如果没有，写“暂无紧急待办，建议研读最新政策动向”。

{NO_RHETORIC_RULE}
新闻原文：
{all_news_text}"""
    return call_deepseek(prompt)

def generate_top_picks(all_news_text):
    prompt = f"""从以下新闻中，挑选出今天最核心、最重要的一条宏观政策或重大产业动向，进行七段式深度解读。

格式严格按（每条一行，用 ||| 分隔七段，不要加序号）：
来源名|||中文标题|||链接|||发生了什么|||处理情况|||原理科普|||对你的意义

要求：
- 中文标题：准确翻译或提炼
- 链接：原样使用我给的链接
- 发生了什么：一句话说清核心政策事实
- 处理情况：政策推进到哪一步了
- 原理科普：用通俗的话解释政策背后的机制（如专项债怎么运作的）
- 对你的意义：结合地方发改的工作，指出该政策在项目谋划、资金争取上的意义。

{NO_RHETORIC_RULE}
新闻原文：
{all_news_text}"""
    return call_deepseek(prompt)

def generate_category_cards(all_news_text, category_name, count=2):
    prompt = f"""从以下新闻中，挑选出 {count} 条最符合【{category_name}】类别的资讯，进行六段式解读。
如果找不到符合该类别的高质量内容，宁可返回空，也不要用无关内容凑数。

格式严格按（每条一行，用 ||| 分隔六段，不要加序号）：
来源名|||中文标题|||链接|||关键词标签|||深度摘要|||一句话点评

要求：
- 关键词标签：2-3个词，逗号分隔
- 深度摘要：用大白话讲清楚是什么事，18-20字
- 一句话点评：分析背后的政策逻辑、潜在影响，20-25字

{NO_RHETORIC_RULE}
新闻原文：
{all_news_text}"""
    return call_deepseek(prompt)

def generate_action_advice(all_news_text):
    prompt = f"""你是一位资深的发改部门导师，指导这位公职人员的工作。
下面是今天的简报内容，请基于此生成“今日行动建议”，格式如下：

【可能的方向】
列出2-3个今天政策中延伸出的具体方向，必须是发改部门能实际着手的工作，比如“围绕XX政策，梳理本地XX项目的申报切入点”。
格式：方向名称|||具体做法（20-30字）

【不建议投入】
指出1个不值得现在投入精力的伪需求或方向，并说明原因。

【今日推荐行动】
从上面方向中选1个，给出一个今天就能开始做的具体动作，比如“打开XX文件，研究XX部分”。

{NO_RHETORIC_RULE}
新闻原文：
{all_news_text}"""
    return call_deepseek(prompt)

def generate_greeting(slot):
    mood = "早安" if slot == "morning" else "晚安"
    prompt = f"""给这位地方发改部门的公职人员写一段{mood}问候和结尾。
【开头】
（结合发改工作性质，写2句话，40字以内，不要客套话，要激励或提醒工作重点）
【结尾】
（1句话，20字以内，让他放松或注意休息）
{NO_RHETORIC_RULE}"""
    return call_deepseek(prompt, temperature=0.8)


if __name__ == "__main__":
    slot = get_slot()
    slot_label = "早班" if slot == "morning" else "晚班"
    print(f"正在生成今日简报（{slot_label}）...\n")

    today = datetime.now().strftime("%Y-%m-%d")
    sections = {}

    # 1. 收集所有抓取到的新闻
    all_items = []
    
    rss_data = load_json("rss_sources.json")
    if rss_data and rss_data.get("items"):
        all_items.extend(rss_data["items"])
        
    category_data = load_json("category_news.json")
    if category_data and category_data.get("items"):
        all_items.extend(category_data["items"])

    if not all_items:
        print("❌ 没有抓取到任何新闻，退出。")
        sys.exit(1)

    # 拼装给 AI 阅读的文本
    all_news_text = ""
    for i, item in enumerate(all_items):
        all_news_text += f"[{i}] 来源:{item.get('source')} | 标题:{item.get('title')} | 链接:{item.get('url')}\n"

    print(f"共收集到 {len(all_items)} 条新闻，开始请求 DeepSeek 生成摘要...")

    # 2. 按模块生成
    print("正在生成今日总览...")
    sections["overview"] = generate_overview(all_news_text)
    
    print("正在提取核心头条...")
    sections["top_picks"] = generate_top_picks(all_news_text)
    
    print("正在筛选【经济与资金】...")
    sections["economy"] = generate_category_cards(all_news_text, "经济与资金（如专项债、预算内投资）", 2)
    
    print("正在筛选【宏观政策】...")
    sections["politics"] = generate_category_cards(all_news_text, "宏观政策（如发改委发文、六张网）", 2)
    
    print("正在筛选【前沿科技】...")
    sections["science"] = generate_category_cards(all_news_text, "前沿科技（如AI4S、低空经济、北斗）", 2)
    
    print("正在生成行动建议...")
    sections["action"] = generate_action_advice(all_news_text)
    
    print("正在生成问候语...")
    sections["greeting"] = generate_greeting(slot)

    # 3. 严格按照 send_wechat.py 要求的格式写入文件
    with open("daily_brief.md", "w", encoding="utf-8") as f:
        f.write(f"DATE|||{today}\n")
        f.write(f"SLOT|||{slot}\n")
        f.write("SECTION|||overview\n")
        f.write(sections.get("overview", "") + "\n")
        f.write("SECTION|||top_picks\n")
        f.write(sections.get("top_picks", "") + "\n")
        f.write("SECTION|||economy\n")
        f.write(sections.get("economy", "") + "\n")
        f.write("SECTION|||politics\n")
        f.write(sections.get("politics", "") + "\n")
        f.write("SECTION|||science\n")
        f.write(sections.get("science", "") + "\n")
        f.write("SECTION|||action\n")
        f.write(sections.get("action", "") + "\n")
        f.write("SECTION|||greeting\n")
        f.write(sections.get("greeting", "") + "\n")

    print("✅ 简报已生成：daily_brief.md")
