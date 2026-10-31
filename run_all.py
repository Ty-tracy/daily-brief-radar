"""
一键运行：依次执行抓取 → AI摘要 → 发送简报微信（强制日志增强版）
"""
import subprocess
import sys
import os
import time
from datetime import datetime

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 5 # 测试期间缩短重试等待时间

FETCH_STEPS = [
    ("抓取 GitHub Trending", "fetchers/fetch_github_trending.py"),
    ("抓取教务网通知", "fetchers/fetch_jwc_news.py"),
    ("抓取 Hacker News", "fetchers/fetch_hacker_news.py"),
    ("抓取科技/AI媒体RSS", "fetchers/fetch_rss_sources.py"),
    ("抓取经济/政治/科学突破新闻", "fetchers/fetch_category_news.py"),
]

if len(sys.argv) > 1 and sys.argv[1] in ("morning", "evening"):
    slot = sys.argv[1]
else:
    slot = "morning" if datetime.now().hour < 12 else "evening"

slot_label = "早班" if slot == "morning" else "晚班"
print(f"本次运行班次：{slot_label}（{slot}）")

daily_frequency = os.environ.get("DAILY_FREQUENCY", "2").strip()
if daily_frequency == "1" and slot == "evening":
    print("你在问卷里选的是「一天1次」，晚班这次直接跳过。")
    sys.exit(0)

steps = FETCH_STEPS + [
    ("生成AI摘要", "core/summarize.py", slot),
    ("发送简报微信", "core/send_wechat.py", slot),
]

def run_step_with_retry(step_name, script, extra_args):
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n{'='*40}")
        print(f"▶ 正在执行：{step_name}（第{attempt}次尝试）")
        print(f"执行命令：{sys.executable} {script} {' '.join(extra_args)}")
        print('='*40)
        
        # 【核心修改】强制捕获子进程的输出和报错，不让他偷偷溜走
        result = subprocess.run(
            [sys.executable, script] + extra_args,
            capture_output=True,
            text=True
        )
        
        # 打印脚本里的正常输出
        if result.stdout:
            print(result.stdout)
        # 打印脚本里的报错信息
        if result.stderr:
            print(f"❌ 错误输出: {result.stderr}")

        if result.returncode == 0:
            return True
            
        print(f"⚠️ {step_name} 第{attempt}次失败（退出码 {result.returncode}）")
        if attempt < MAX_RETRIES:
            print(f"   等待 {RETRY_WAIT_SECONDS} 秒后重试...")
            time.sleep(RETRY_WAIT_SECONDS)
            
    print(f"❌ {step_name} 重试{MAX_RETRIES}次仍然失败，停止后续步骤")
    return False

all_ok = True
for step in steps:
    step_name, script = step[0], step[1]
    extra_args = list(step[2:])
    if not run_step_with_retry(step_name, script, extra_args):
        all_ok = False
        break

if all_ok:
    print(f"\n✅ 全部完成！{slot_label}简报已生成并推送")
else:
    print(f"\n❌ 运行中断，请检查上面的报错信息。")
