# -*- coding: utf-8 -*-
"""
抖音视频 & 评论采集（Windows / macOS 通用最终版）
------------------------------------------------
✅ 特性：
- 自动识别 /video/ 与 jingxuan?modal_id 链接
- 若未传入 --url 参数，则自动读取 urls.txt 批量采集
- 每个视频单独导出 Excel
- 自动滚动、延时、人类化操作防封
"""

import argparse, os, random, re, time
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import pyautogui
import subprocess



def manual_login(profile, chrome_path, proxy, timeout_sec=30):
    """人工登录（本地浏览器，保存cookie）"""
    with sync_playwright() as p:
        ctx = open_context(p, profile, chrome_path, proxy, True, timeout_sec)
        print("💡 Chrome 已连接，你现在可以扫码登录抖音，登录后不要关浏览器。")
        while True:
            time.sleep(3)



# 兼容链接：/video/123456789 或 ?modal_id=123456789
def aweme_id_from_url(url: str):
    m = re.search(r"(?:/video/|modal_id=)(\d+)", url)
    return m.group(1) if m else None

def jitter(a=0.25, b=0.75):
    return random.uniform(a, b)

def run_once(url, out, profile, chrome_path, proxy, headful, timeout, max_comments):
    from playwright.sync_api import TimeoutError as PWTimeoutError
    with sync_playwright() as p:
        ctx = open_context(p, profile, chrome_path, proxy, headful, timeout)

        # ✅ 获取所有 tab 页，优先选择当前活动页
        pages = ctx.pages
        page = pages[-1] if pages else ctx.new_page()
        print(f"🌐 正在打开链接: {url}")
        page.bring_to_front()
        page.goto(url, wait_until='domcontentloaded')

        try:
            page.wait_for_selector('[data-e2e="comment-list"], p[data-e2e^="comment"]', timeout=20000)
        except PWTimeoutError:
            print("⚠️ 未检测到评论区，请确认页面已登录并加载完成。")

        # ✅ 开始抓取
        comments = crawl_comments(page, max_comments)
        df = pd.DataFrame(comments)
        df.to_excel(out, index=False)
        print(f"✅ 已导出 {len(df)} 条评论 -> {out}")

        ctx.close()

def open_context(p, profile, chrome_path=None, proxy=None, headful=True, timeout_sec=30):
    """
    Mac Intel: 使用本地 Chrome 浏览器并附加调试端口
    """
    chrome_path = chrome_path or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    profile_dir = os.path.expanduser(profile)
    os.makedirs(profile_dir, exist_ok=True)
    port = 9222
    print(f"🧭 请稍等，正在打开本地 Chrome（调试端口 {port}）...")

    # 启动本地 Chrome
    subprocess.Popen([
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized"
    ])
    print("\n🧍 请在 Chrome 中手动打开 https://www.douyin.com 并扫码登录抖音。\n"
          "✅ 登录成功后保持窗口打开，脚本将自动连接。\n")

    time.sleep(10)
    print("⏳ 正在尝试附加浏览器...")

    # 连接调试端口
    browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    print("✅ 已附加到本地浏览器，会话连接成功！")
    return context

def run_once(url, out, profile, chrome_path=None, proxy=None, headful=True, timeout=30, max_comments=300):
    with sync_playwright() as p:
        ctx = open_context(p, profile, chrome_path, proxy, headful, timeout)
        page = ctx.new_page()
        print(f"🌐 正在打开链接: {url}")
        page.goto(url, wait_until="domcontentloaded")

        vid = aweme_id_from_url(url)
        if not vid:
            print(f"⚠️ 该链接无法识别视频ID，已跳过：{url}")
            ctx.close()
            return

        time.sleep(2)
        data = crawl_comments(page, max_comments)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        pd.DataFrame(data).to_excel(out, index=False)
        print(f"✅ 已导出 {len(data)} 条评论 -> {out}")
        ctx.close()

if __name__ == "__main__":
    import sys

    # 自动定位脚本所在目录（macOS 关键）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print(f"📁 当前运行目录: {os.getcwd()}")

    ap = argparse.ArgumentParser(description="抖音评论采集器")
    ap.add_argument("--init", action="store_true", help="首次登录模式（人工扫码）")

    ap.add_argument("--url", help="单个视频链接")
    ap.add_argument("--out", default="outputs/result.xlsx", help="输出文件路径")
    ap.add_argument("--profile", default="~/douyin_profile", help="浏览器配置目录")
    ap.add_argument("--max", type=int, default=300, help="最大评论数")
    ap.add_argument("--chrome-path", help="浏览器路径")
    ap.add_argument("--proxy", help="代理地址")
    ap.add_argument("--headful", action="store_true", help="是否显示浏览器")
    args = ap.parse_args()
    # ✅ 首次扫码登录模式
    if args.init:
        manual_login(args.profile, args.chrome_path, args.proxy)
        sys.exit(0)


    # ✅ 新逻辑：支持 urls.txt 批量读取
    urls = []

    # 优先使用 --url 参数
    if args.url:
        urls = [args.url.strip()]
    else:
        urls_path = os.path.join(base_dir, "urls.txt")
        print(f"🔍 正在检测: {urls_path}")
        if os.path.exists(urls_path):
            with open(urls_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
            if not urls:
                print("❌ urls.txt 文件为空，请填写视频链接后重试。")
                sys.exit(0)
        else:
            print("❌ 未检测到 --url 参数或 urls.txt 文件，请放在同目录下。")
            sys.exit(0)

    for idx, link in enumerate(urls, 1):
        vid = aweme_id_from_url(link)
        if not vid:
            print(f"⚠️ 第 {idx} 条链接无法识别视频ID，已跳过：{link}")
            continue
        out_dir = os.path.join(base_dir, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        out_name = os.path.join(out_dir, f"video_{vid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        print(f"\n▶️ [{idx}/{len(urls)}] 正在采集 {link}")
        run_once(link, out_name, args.profile, args.chrome_path, args.proxy, args.headful, 30, args.max)
