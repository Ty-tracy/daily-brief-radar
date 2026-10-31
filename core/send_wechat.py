"""
把 daily_brief.md 解析成结构化数据，生成精致的 HTML 卡片推送出去
（已修改为通过 PushPlus 推送到微信）
"""
import os
import re
import html as html_lib
import urllib.parse
import requests
import time

import seen_records

# 从环境变量读取 PushPlus 的 Token
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

COLOR_DARK = "#2c3e50"
COLOR_ACCENT = "#3f6b8f"
COLOR_MUTED = "#8a95a3"
COLOR_BG_ACCENT = "#eaf0f5"
COLOR_BG_MUTED = "#f4f5f6"

EXTRA_SECTIONS = [
    ("economy", "💰 经济"),
    ("politics", "🏛 政治"),
    ("science", "🔬 科学突破"),
]

_LEADING_MARKER_RE = re.compile(r"^[\s\-\*•·]*(\d+[\.\、\)]\s+)?")


def _split_line(line, min_parts):
    line = _LEADING_MARKER_RE.sub("", line).strip()
    if "|||" not in line:
        return None
    parts = [p.strip() for p in line.split("|||")]
    if len(parts) < min_parts:
        parts += [""] * (min_parts - len(parts))
    return parts


def _safe_href(url):
    """将原始 URL 安全地放入 HTML href 属性，避免客户端截断链接。"""
    url = (url or "").strip().strip("<>\"'")
    decoded = urllib.parse.unquote(url)
    if "|||" in decoded:
        url = decoded.split("|||", 1)[0].strip()
    return html_lib.escape(url, quote=True)


def parse_brief(content):
    date = ""
    slot = "morning"
    keys = ["overview", "jwc", "top_picks", "tech", "economy", "politics", "science", "action", "greeting"]
    sections = {k: "" for k in keys}
    current = None
    for line in content.split("\n"):
        if line.startswith("DATE|||"):
            date = line.split("|||", 1)[1]
        elif line.startswith("SLOT|||"):
            slot = line.split("|||", 1)[1]
        elif line.startswith("SECTION|||"):
            current = line.split("|||", 1)[1]
        elif current in sections:
            sections[current] += line + "\n"
    return date, slot, sections

def collect_seen_items(sections):
    """把展示的新闻（标题+链接）收集起来，供当天晚上去重用"""
    seen = []
    seen_urls = set()
    for key in ("jwc", "top_picks", "tech", "economy", "politics", "science"):
        for raw_line in sections.get(key, "").split("\n"):
            parts = _split_line(raw_line, 3)
            if not parts:
                continue
            title, url = (parts[0], parts[1]) if key == "jwc" else (parts[1], parts[2])
            if title and url and url not in seen_urls:
                seen_urls.add(url)
                seen.append({"title": title, "url": url})
    return seen


def render_overview(text):
    one_liner, ai_view, trend, todo = "", "", "", ""
    mode = None
    for line in text.split("\n"):
        line = line.strip()
        if not line: continue
        if "今日一句话" in line: mode = "one_liner"; continue
        if "AI观察" in line: mode = "ai_view"; continue
        if "趋势预测" in line: mode = "trend"; continue
        if "最该做的" in line: mode = "todo"; continue
        if mode == "one_liner": one_liner += line
        elif mode == "ai_view": ai_view += line + " "
        elif mode == "trend": trend += line + " "
        elif mode == "todo": todo += line

    trend_html = f'''<div style="font-size:15px; color:#cfd8e3; line-height:1.7; margin-top:12px; border-top:1px solid rgba(255,255,255,0.2); padding-top:12px;">🔮 {trend}</div>''' if trend else ""

    html = f'''<div style="background:{COLOR_DARK}; border-radius:8px; padding:22px; margin-bottom:20px; color:#fff;">
        <div style="font-size:19px; font-weight:700; line-height:1.6;">{one_liner}</div>
        <div style="font-size:15px; color:#cfd8e3; line-height:1.7; margin-top:14px; border-top:1px solid rgba(255,255,255,0.2); padding-top:14px;">💭 {ai_view}</div>
        {trend_html}
    </div>'''
    return html, todo


def render_jwc_cards(text):
    html = ""
    mode = None
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line: continue
        if "需要行动" in line:
            mode = "action"
            html += f'<div style="font-size:15px; color:{COLOR_ACCENT}; font-weight:bold; margin:16px 0 10px;">● 需要行动</div>'
            continue
        if "仅需" in line:
            mode = "info"
            html += f'<div style="font-size:15px; color:{COLOR_MUTED}; font-weight:bold; margin:16px 0 10px;">○ 仅需了解</div>'
            continue
        parts = _split_line(line, 3)
        if not parts: continue
        title, url, desc = parts[0], parts[1], parts[2]
        if not title: continue
        title_html = f'<a href="{_safe_href(url)}" style="color:inherit; text-decoration:none; border-bottom:1px dotted currentColor;">{html_lib.escape(title)}</a>' if url else html_lib.escape(title)
        if mode == "action":
            html += f'''<div style="background:{COLOR_BG_ACCENT}; border-left:3px solid {COLOR_ACCENT}; border-radius:4px; padding:14px 18px; margin-bottom:10px;">
                <div style="font-size:17px; font-weight:600; color:#222;">{title_html}</div>
                <div style="font-size:15px; color:#555; margin-top:6px; line-height:1.5;">{desc}</div>
            </div>'''
        else:
            html += f'''<div style="background:{COLOR_BG_MUTED}; border-radius:4px; padding:14px 18px; margin-bottom:10px;">
                <div style="font-size:16px; color:#444;">{title_html}</div>
                <div style="font-size:14px; color:#999; margin-top:6px; line-height:1.5;">{desc}</div>
            </div>'''
    return html


def render_top_picks(text):
    html = ""
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line: continue
        parts = _split_line(line, 7)
        if not parts: continue
        label, title, url, happened, progress, principle, meaning = parts[:7]
        if not title: continue
        title_html = f'<a href="{_safe_href(url)}" style="color:#222; text-decoration:none; border-bottom:1px dotted #222;">{html_lib.escape(title)}</a>' if url else html_lib.escape(title)
        html += f'''<div style="background:#fff; border:1px solid {COLOR_ACCENT}; border-radius:6px; padding:18px 20px; margin-bottom:14px;">
            <div style="display:inline-block; background:{COLOR_ACCENT}; color:#fff; font-size:12px; padding:3px 10px; border-radius:10px; margin-bottom:8px;">{label}</div>
            <div style="font-size:18px; font-weight:600; color:#222; margin-top:6px;">{title_html}</div>
            <div style="font-size:14.5px; color:#666; margin-top:10px; line-height:1.6;"><b style="color:{COLOR_ACCENT};">发生了什么：</b>{happened}</div>
            <div style="font-size:14.5px; color:#666; margin-top:6px; line-height:1.6;"><b style="color:{COLOR_ACCENT};">处理情况：</b>{progress}</div>
            <div style="font-size:14.5px; color:#666; margin-top:6px; line-height:1.6;"><b style="color:{COLOR_ACCENT};">原理科普：</b>{principle}</div>
            <div style="font-size:14.5px; color:#333; margin-top:8px; line-height:1.6; background:{COLOR_BG_ACCENT}; padding:8px 10px; border-radius:4px;"><b style="color:{COLOR_ACCENT};">对你的意义：</b>{meaning}</div>
        </div>'''
    return html


def render_content_cards(text):
    html = ""
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line: continue
        parts = _split_line(line, 5)
        if not parts: continue
        if len(parts) >= 6:
            source, title, url, tags, digest, comment = parts[:6]
        else:
            source = ""
            title, url, tags, digest, comment = parts[:5]
        if not title: continue
        title_html = f'<a href="{_safe_href(url)}" style="color:#222; text-decoration:none; border-bottom:1px dotted #222;">{html_lib.escape(title)}</a>' if url else html_lib.escape(title)
        tag_badges = "".join([
            f'<span style="display:inline-block; background:{COLOR_BG_ACCENT}; color:{COLOR_ACCENT}; font-size:12px; padding:3px 8px; border-radius:8px; margin-right:5px;">{t.strip()}</span>'
            for t in tags.split(",") if t.strip()
        ])
        source_badge = f'<span style="display:inline-block; background:{COLOR_ACCENT}; color:#fff; font-size:12px; padding:3px 10px; border-radius:10px; margin-right:6px; vertical-align:2px;">{source}</span>' if source else ""
        html += f'''<div style="background:{COLOR_BG_MUTED}; border-radius:6px; padding:16px 18px; margin-bottom:12px;">
            <div style="font-size:16.5px; font-weight:600; color:#222;">{source_badge}{title_html}</div>
            <div style="margin-top:8px;">{tag_badges}</div>
            <div style="font-size:14.5px; color:#555; margin-top:8px; line-height:1.6;">{digest}</div>
            <div style="font-size:13.5px; color:#888; margin-top:8px; line-height:1.6;">💬 {comment}</div>
        </div>'''
    return html


def render_action_advice(text):
    directions, not_worth, recommend = [], "", ""
    mode = None
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line: continue
        if "可能的方向" in line: mode = "directions"; continue
        if "不建议投入" in line: mode = "not_worth"; continue
        if "今日推荐行动" in line: mode = "recommend"; continue
        if mode == "directions":
            parts = _split_line(line, 2)
            if parts and parts[0]: directions.append((parts[0], parts[1]))
        elif mode == "not_worth": not_worth += line
        elif mode == "recommend": recommend += line

    if not directions and not not_worth and not recommend: return ""

    directions_html = "".join([
        f'''<div style="padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.15);">
            <div style="font-size:15px; font-weight:600; color:#fff;">🧭 {name}</div>
            <div style="font-size:14px; color:#cfd8e3; margin-top:4px; line-height:1.6;">{detail}</div>
        </div>'''
        for name, detail in directions
    ])

    not_worth_html = f'''<div style="margin-top:14px; padding:12px 14px; background:rgba(255,255,255,0.08); border-radius:6px;">
        <div style="font-size:13px; color:#a8b4c2;">⚠️ 不建议现在投入</div>
        <div style="font-size:14px; color:#e5eaf0; margin-top:4px; line-height:1.6;">{not_worth}</div>
    </div>''' if not_worth else ""

    recommend_html = f'''<div style="margin-top:14px; padding:14px 16px; background:{COLOR_ACCENT}; border-radius:6px;">
        <div style="font-size:13px; color:#dce6f0;">✅ 今日推荐行动</div>
        <div style="font-size:15.5px; color:#fff; font-weight:600; margin-top:4px; line-height:1.6;">{recommend}</div>
    </div>''' if recommend else ""

    return f'''<h2 style="font-size:18px; color:{COLOR_DARK}; margin-top:26px;">🎯 今日行动建议</h2>
    <div style="background:{COLOR_DARK}; border-radius:8px; padding:18px 20px;">
        {directions_html}
        {not_worth_html}
        {recommend_html}
    </div>'''


def render_greeting(text):
    opening, closing = "", ""
    mode = None
    for line in text.split("\n"):
        line = line.strip()
        if not line: continue
        if "开头" in line and line.startswith("【"): mode = "opening"; continue
        if "结尾" in line and line.startswith("【"): mode = "closing"; continue
        if mode == "opening": opening += line
        elif mode == "closing": closing += line
    return opening, closing


def build_html(date, slot, sections):
    overview_html, todo = render_overview(sections["overview"])
    jwc_html = render_jwc_cards(sections["jwc"])
    top_picks_html = render_top_picks(sections["top_picks"])
    tech_html = render_content_cards(sections["tech"])

    extra_sections_html = ""
    for key, title in EXTRA_SECTIONS:
        content = render_content_cards(sections.get(key, ""))
        if content:
            extra_sections_html += f'''<h2 style="font-size:18px; color:{COLOR_DARK}; margin-top:26px;">{title}</h2>{content}'''

    action_html = render_action_advice(sections.get("action", ""))
    opening, closing = render_greeting(sections.get("greeting", ""))

    slot_label = "早安" if slot == "morning" else "晚安"
    opening_html = f'''<div style="font-size:15px; color:{COLOR_DARK}; background:{COLOR_BG_ACCENT}; border-radius:8px; padding:14px 18px; margin-bottom:16px; line-height:1.6;">{slot_label}👋 {opening}</div>''' if opening else ""
    closing_in_footer = f'''<div style="font-size:15px; font-weight:600; color:{COLOR_DARK}; margin-top:12px; border-top:1px solid rgba(63,107,143,0.25); padding-top:12px; line-height:1.6;">💌 {closing}</div>''' if closing else ""

    tab_bar = f'''
    <div style="display:table; width:100%; margin-bottom:18px; border-bottom:2px solid #eee;">
        <div style="display:table-cell; width:50%; text-align:center; padding:12px 0; background:{COLOR_DARK}; color:#fff; font-size:16px; font-weight:600; border-radius:6px 0 0 0;">🏫 学校教务</div>
        <div style="display:table-cell; width:50%; text-align:center; padding:12px 0; background:{COLOR_ACCENT}; color:#fff; font-size:16px; font-weight:600; border-radius:0 6px 0 0;">💻 科技资讯</div>
    </div>
    '''

    footer = f'''<div style="background:{COLOR_BG_ACCENT}; border-radius:8px; padding:18px 22px; margin-top:30px; text-align:center;">
        <div style="font-size:14px; color:{COLOR_MUTED};">今日最该做的一件事</div>
        <div style="font-size:17px; font-weight:600; color:{COLOR_DARK}; margin-top:6px;">✅ {todo}</div>
        {closing_in_footer}
    </div>'''

    return f"""
    <div style="max-width:620px; margin:0 auto; font-family:-apple-system,'PingFang SC',sans-serif;">
        <h1 style="font-size:23px; color:{COLOR_DARK}; margin-bottom:6px;">📋 每日简报</h1>
        <div style="font-size:15px; color:{COLOR_MUTED}; margin-bottom:18px;">{date}</div>
        {opening_html}
        {overview_html}
        {tab_bar}
        <h2 style="font-size:18px; color:{COLOR_DARK}; margin-top:8px;">学校教务</h2>
        {jwc_html}
        <h2 style="font-size:18px; color:{COLOR_DARK}; margin-top:26px;">🏆 各榜单头名</h2>
        {top_picks_html}
        <h2 style="font-size:18px; color:{COLOR_DARK}; margin-top:26px;">科技资讯全览</h2>
        {tech_html}
        {extra_sections_html}
        {action_html}
        {footer}
    </div>
    """


def send_brief_wechat():
    """已修改：使用 PushPlus 发送到微信"""
    if not PUSHPLUS_TOKEN:
        print("❌ 错误: 未找到 PUSHPLUS_TOKEN 环境变量，请检查 GitHub Secrets")
        return

    try:
        with open("daily_brief.md", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("⚠️ 没找到 daily_brief.md，先跑 run_all.py 生成简报")
        return

    date, slot, sections = parse_brief(content)
    html_content = build_html(date, slot, sections)

    slot_tag = "早报" if slot == "morning" else "晚报"
    title = f"每日简报·{slot_tag} {date}"

    url = "https://www.pushplus.plus/send"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": html_content,
        "template": "html" # 使用 HTML 模板保留精美排版
    }

    max_retries = 3
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📡 正在通过 PushPlus 推送到微信 (第{attempt}次尝试)...")
            res = requests.post(url, json=payload, timeout=15)
            
            # PushPlus 成功返回 200 且包含 "code":200
            if res.status_code == 200 and '"code":200' in res.text:
                print(f"✅ 简报已成功推送到微信！")
                # 早报发送成功后，记录已看新闻，供晚报去重
                if slot == "morning":
                    seen_items = collect_seen_items(sections)
                    seen_records.record_today(date, seen_items)
                return
            else:
                last_error = res.text
                print(f"⚠️ 第{attempt}次推送失败：{res.text}")
        except Exception as e:
            last_error = str(e)
            print(f"⚠️ 第{attempt}次请求异常：{e}")
        
        if attempt < max_retries:
            time.sleep(5)

    print(f"❌ 推送彻底失败（已重试{max_retries}次）：{last_error}")


if __name__ == "__main__":
    # 兼容原来的函数名，以防其他地方调用了它
    send_brief_wechat()
