# -*- coding: utf-8 -*-
"""
分析评论HTML结构 - 用于调试和更新选择器
"""

import time
from playwright.sync_api import sync_playwright

def analyze_comments(url: str):
    """分析评论结构"""
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"❌ 无法连接到Chrome: {e}")
            print("💡 请先运行: python main.py --login")
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
        
        print(f"🔍 正在访问: {url}\n")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # 等待页面加载
        print("⏳ 等待页面加载...")
        time.sleep(5)
        
        print(f"📄 页面标题: {page.title()}\n")
        
        # 查找所有可能的评论容器
        print("="*60)
        print("🔍 查找评论容器...")
        print("="*60)
        
        container_patterns = [
            'comment-list',
            'CommentList',
            'comment_list',
            'comments',
            'Comments'
        ]
        
        for pattern in container_patterns:
            selectors = [
                f'[data-e2e*="{pattern}"]',
                f'[class*="{pattern}"]',
                f'#{pattern}',
                f'.{pattern}'
            ]
            for selector in selectors:
                count = page.locator(selector).count()
                if count > 0:
                    print(f"✅ {selector}: {count} 个")
        
        # 查找所有可能的评论项
        print("\n" + "="*60)
        print("💬 查找评论项...")
        print("="*60)
        
        item_patterns = [
            'comment-item',
            'CommentItem',
            'comment_item',
            'comment-card',
            'CommentCard'
        ]
        
        found_selector = None
        found_count = 0
        
        for pattern in item_patterns:
            selectors = [
                f'[data-e2e*="{pattern}"]',
                f'[class*="{pattern}"]',
                f'.{pattern}'
            ]
            for selector in selectors:
                count = page.locator(selector).count()
                if count > 0:
                    print(f"✅ {selector}: {count} 个")
                    if count > found_count:
                        found_selector = selector
                        found_count = count
        
        if not found_selector:
            print("\n❌ 未找到评论项！")
            print("💡 尝试保存页面HTML进行手动分析...")
            html = page.content()
            with open("debug_page_full.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("   已保存到: debug_page_full.html")
            page.close()
            return
        
        print(f"\n🎯 使用选择器: {found_selector}")
        print(f"📊 找到 {found_count} 条评论\n")
        
        # 分析第一条评论的结构
        print("="*60)
        print("🔬 分析第一条评论的结构...")
        print("="*60)
        
        first_comment = page.locator(found_selector).first
        
        # 获取HTML
        html = first_comment.inner_html()
        print(f"\n📝 HTML结构:\n{html[:1000]}...\n")
        
        # 尝试提取各个字段
        print("="*60)
        print("📋 字段提取测试...")
        print("="*60)
        
        # 用户名
        print("\n👤 用户名:")
        user_patterns = ['user', 'author', 'nickname', 'name']
        for pattern in user_patterns:
            selectors = [
                f'[class*="{pattern}"]',
                f'a[href*="/user/"]',
                f'span[class*="{pattern}"]'
            ]
            for selector in selectors:
                try:
                    elem = first_comment.locator(selector).first
                    if elem.count() > 0:
                        text = elem.inner_text().strip()
                        if text:
                            print(f"  ✅ {selector}: {text}")
                except:
                    pass
        
        # 评论内容
        print("\n💬 评论内容:")
        content_patterns = ['text', 'content', 'comment', 'desc']
        for pattern in content_patterns:
            selectors = [
                f'[class*="{pattern}"]',
                f'p[class*="{pattern}"]',
                f'span[class*="{pattern}"]',
                f'div[class*="{pattern}"]'
            ]
            for selector in selectors:
                try:
                    elem = first_comment.locator(selector).first
                    if elem.count() > 0:
                        text = elem.inner_text().strip()
                        if text and len(text) > 10:  # 过滤太短的文本
                            print(f"  ✅ {selector}: {text[:100]}...")
                except:
                    pass
        
        # 时间
        print("\n⏰ 时间:")
        time_patterns = ['time', 'date', 'create']
        for pattern in time_patterns:
            selectors = [
                f'[class*="{pattern}"]',
                f'span[class*="{pattern}"]'
            ]
            for selector in selectors:
                try:
                    elem = first_comment.locator(selector).first
                    if elem.count() > 0:
                        text = elem.inner_text().strip()
                        if text:
                            print(f"  ✅ {selector}: {text}")
                except:
                    pass
        
        # 点赞数
        print("\n👍 点赞数:")
        like_patterns = ['like', 'digg', 'praise', 'count']
        for pattern in like_patterns:
            selectors = [
                f'[class*="{pattern}"]',
                f'span[class*="{pattern}"]'
            ]
            for selector in selectors:
                try:
                    elem = first_comment.locator(selector).first
                    if elem.count() > 0:
                        text = elem.inner_text().strip()
                        if text and (text.isdigit() or '万' in text):
                            print(f"  ✅ {selector}: {text}")
                except:
                    pass
        
        # 保存完整HTML
        print("\n" + "="*60)
        print("💾 保存调试文件...")
        print("="*60)
        
        html_content = page.content()
        with open("debug_comments.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ 完整HTML: debug_comments.html")
        
        page.screenshot(path="debug_comments.png", full_page=True)
        print("✅ 页面截图: debug_comments.png")
        
        page.close()
        print("\n✅ 分析完成！")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        with open("urls.txt", "r", encoding="utf-8") as f:
            url = f.readline().strip()
    
    analyze_comments(url)
