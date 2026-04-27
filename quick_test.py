# -*- coding: utf-8 -*-
"""
快速测试 - 验证评论采集功能
"""

import os
import sys
from pathlib import Path
from src.services.browser_service import BrowserService
from src.services.crawler_service import CrawlerService
from src.services.anti_detection import AntiDetectionEngine
from src.managers.config_manager import ConfigManager

def quick_test(url: str):
    """快速测试单个URL"""
    print("="*60)
    print("  快速测试 - 评论采集")
    print("="*60)
    print(f"🎯 测试URL: {url}\n")
    
    # 加载配置
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    template_path = base_dir / "config.json.example"
    config_manager = ConfigManager("config.json", default_template_path=str(template_path))
    config = config_manager.load_config()
    
    # 创建服务
    browser_service = BrowserService(
        profile_path=config.profile_path,
        chrome_path=config.chrome_path
    )
    
    try:
        # 启动浏览器
        print("🚀 启动浏览器...")
        browser_service.launch_browser(config.debug_port)
        context = browser_service.connect_browser(config.debug_port)
        
        # 确保登录
        if not browser_service.ensure_logged_in(context):
            print("❌ 登录失败，无法继续测试")
            return
        
        print("✅ 登录状态有效\n")
        
        # 创建采集服务
        anti_detection = AntiDetectionEngine(config)
        crawler_service = CrawlerService(anti_detection)
        
        # 创建页面
        page = context.new_page()
        
        try:
            # 采集评论
            comments = crawler_service.crawl_video_comments(
                page,
                url,
                max_comments=50,  # 测试只采集50条
                include_replies=False
            )
            
            print("\n" + "="*60)
            print("  测试结果")
            print("="*60)
            print(f"📊 采集到 {len(comments)} 条评论\n")
            
            if comments:
                print("前3条评论预览:")
                for i, comment in enumerate(comments[:3], 1):
                    print(f"\n{i}. {comment.get('user_nickname', '未知用户')}")
                    print(f"   内容: {comment.get('content', '')[:50]}...")
                    print(f"   点赞: {comment.get('like_count', 0)}")
                    print(f"   时间: {comment.get('create_time', '')}")
            else:
                print("❌ 未采集到评论")
                print("\n💡 建议:")
                print("1. 运行分析工具: python analyze_comments.py")
                print("2. 检查页面是否需要登录")
                print("3. 检查URL是否正确")
            
        finally:
            page.close()
        
    finally:
        browser_service.close_browser()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        with open("urls.txt", "r", encoding="utf-8") as f:
            url = f.readline().strip()
    
    quick_test(url)
