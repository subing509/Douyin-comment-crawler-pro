# -*- coding: utf-8 -*-
"""
调试选择器 - 检查抖音页面实际DOM结构
"""

import time
from playwright.sync_api import sync_playwright

def debug_page_structure(url: str):
    """调试页面结构"""
    with sync_playwright() as p:
        # 连接到已启动的Chrome
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except:
            print("❌ 无法连接到Chrome，请先运行: python main.py --login")
            return
        
        context = browser.contexts[0]
        page = context.new_page()
        
        # 先访问首页确保登录
        print("🏠 先访问抖音首页，确保登录状态...")
        try:
            page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            print("✅ 首页访问成功\n")
        except Exception as e:
            print(f"⚠️ 首页访问失败: {e}\n")
        
        print(f"🔍 正在访问: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # 等待页面加载
        time.sleep(5)
        
        print("\n" + "="*60)
        print("页面标题:", page.title())
        print("="*60)
        
        # 检查评论区容器
        print("\n📦 检查评论区容器...")
        selectors_to_check = [
            '[data-e2e="comment-list"]',
            '[class*="comment-list"]',
            '[class*="CommentList"]',
            '#comment-list',
            '.comment-list',
        ]
        
        for selector in selectors_to_check:
            count = page.locator(selector).count()
            print(f"  {selector}: {count} 个元素")
            if count > 0:
                try:
                    html = page.locator(selector).first.inner_html()
                    print(f"    HTML预览: {html[:200]}...")
                except:
                    pass
        
        # 检查评论项
        print("\n💬 检查评论项...")
        comment_selectors = [
            '[data-e2e="comment-item"]',
            '[class*="comment-item"]',
            '[class*="CommentItem"]',
            '.comment-item',
        ]
        
        for selector in comment_selectors:
            count = page.locator(selector).count()
            print(f"  {selector}: {count} 个元素")
            if count > 0:
                try:
                    # 获取第一个评论的HTML
                    first_comment = page.locator(selector).first
                    html = first_comment.inner_html()
                    print(f"    第一条评论HTML:\n{html[:500]}...")
                except:
                    pass
        
        # 保存完整HTML
        print("\n💾 保存完整页面HTML...")
        html_content = page.content()
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("  已保存到: debug_page.html")
        
        # 截图
        print("\n📸 保存页面截图...")
        page.screenshot(path="debug_screenshot.png", full_page=True)
        print("  已保存到: debug_screenshot.png")
        
        page.close()
        print("\n✅ 调试完成！")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # 使用urls.txt中的第一个链接
        with open("urls.txt", "r", encoding="utf-8") as f:
            url = f.readline().strip()
    
    debug_page_structure(url)
