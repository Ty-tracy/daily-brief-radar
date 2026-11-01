import os
import requests

PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

def send_brief_wechat():
    try:
        with open("daily_brief.md", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return

    # 解析出纯文本内容，方便直接推 Markdown
    lines = content.split("\n")
    date, slot = "", "morning"
    sections = {}
    current = None
    
    for line in lines:
        if line.startswith("DATE|||"): date = line.split("|||")[1]
        elif line.startswith("SLOT|||"): slot = line.split("|||")[1]
        elif line.startswith("SECTION|||"): current = line.split("|||")[1]; sections[current] = ""
        elif current: sections[current] += line + "\n"

    # 用最极简的 Markdown 语法拼装
    md = f"# 🏛️ 宏观政策情报通报\n**日期:** {date} | **类型:** {'早报' if slot=='morning' else '晚报'}\n\n"
    
    md += "## 🎯 今日宏观总览\n" + sections.get("overview", "").replace("【", "### 【").replace("】", "】\n") + "\n"
    
    md += "## 🔥 核心头条\n"
    for line in sections.get("top_picks", "").split("\n"):
        if "|||" in line:
            p = line.split("|||")
            if len(p) >= 7:
                md += f"**[{p[0]}] {p[1]}**\n"
                md += f"- 事件：{p[3]}\n- 进展：{p[4]}\n- 原理：{p[5]}\n- **启示：{p[6]}**\n[阅读原文]({p[2]})\n\n"

    def add_cards(sec_name, title):
        text = sections.get(sec_name, "")
        res = f"## {title}\n"
        has_content = False
        for line in text.split("\n"):
            if "|||" in line:
                p = line.split("|||")
                if len(p) >= 6:
                    has_content = True
                    res += f"### [{p[0]}] {p[1]}\n"
                    res += f"🏷️ `{p[3]}`\n"
                    res += f"**摘要：**{p[4]}\n"
                    res += f"**点评：**{p[5]}\n"
                    res += f"[原文链接]({p[2]})\n\n---\n"
        return res if has_content else ""

    md += add_cards("economy", "💰 资金与专项债")
    md += add_cards("politics", "🏛 宏观政策与基建")
    md += add_cards("science", "🔬 前沿科技与新质生产力")
    
    md += "## 🎯 今日工作建议\n" + sections.get("action", "").replace("【", "### 【").replace("】", "】\n")
    md += "\n" + sections.get("greeting", "").replace("【", "### 【").replace("】", "】\n")

    if not PUSHPLUS_TOKEN:
        print("❌ 错误: 未找到 PUSHPLUS_TOKEN")
        return

    url = "https://www.pushplus.plus/send"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": f"【{ '早报' if slot=='morning' else '晚报' }】{date} 发改宏观政策通报",
        "content": md,
        "template": "markdown"  # 👈 改用纯 Markdown 模板
    }

    print(f"📡 正在通过 PushPlus 推送到微信...")
    res = requests.post(url, json=payload, timeout=15)
    if res.status_code == 200 and '"code":200' in res.text:
        print(f"✅ 推送成功！请查看微信长文。")
    else:
        print(f"⚠️ 推送失败：{res.text}")

if __name__ == "__main__":
    send_brief_wechat()
