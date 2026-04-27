# -*- coding: utf-8 -*-
"""
抖音评论采集助手 - 主程序入口
"""

import os
import sys
import argparse
import textwrap
from pathlib import Path

from src.services.browser_service import BrowserService
from src.services.crawler_service import CrawlerService
from src.services.data_service import DataService
from src.services.anti_detection import AntiDetectionEngine
from src.services.proxy_manager import ProxyManager
from src.services.resume_manager import ResumeManager
from src.managers.task_manager import TaskManager
from src.managers.config_manager import ConfigManager
from src.managers.error_handler import ErrorHandler


def _resolve_path(path: str, base_dir: Path) -> str:
    """根据调用方路径优先级解析配置路径"""
    candidate = Path(path)
    if candidate.is_absolute():
        return str(candidate)
    if candidate.exists():
        return str(candidate)
    return str(base_dir / path)


def _bootstrap_urls_file(urls_file: Path):
    """若urls.txt不存在则创建示例模板"""
    if urls_file.exists():
        return
    template = textwrap.dedent(
        """\
        # 每行一个抖音视频链接，示例：
        # https://www.douyin.com/video/123456789
        # 也可以运行: python main.py --url <链接>
        """
    ).rstrip() + "\n"
    urls_file.write_text(template, encoding="utf-8")
    print(f"🆕 已创建示例 urls.txt -> {urls_file}")


def _prompt_for_urls() -> list:
    """交互式收集URL"""
    if not sys.stdin.isatty():
        return []
    print("\n🔗 未检测到链接，输入完成后直接回车留空即可。")
    print("   可逐条粘贴，也可复制多条依次回车。")
    urls = []
    while True:
        try:
            line = input("  粘贴抖音链接: ").strip()
        except EOFError:
            break
        if not line:
            break
        urls.append(line)
    return urls


def manual_login(config_manager: ConfigManager):
    """手动登录模式"""
    config = config_manager.load_config()
    
    print("\n" + "="*60)
    print("  抖音评论采集助手 - 登录模式")
    print("="*60)
    
    browser_service = BrowserService(
        profile_path=config.profile_path,
        chrome_path=config.chrome_path
    )
    
    try:
        # 启动浏览器
        context = browser_service.prepare_context(config.debug_port)
        
        # 打开抖音首页
        page = context.new_page()
        page.goto("https://www.douyin.com", wait_until="domcontentloaded")
        
        print("\n💡 请在浏览器中扫码登录抖音")
        print("✅ 登录成功后，关闭浏览器窗口即可")
        print("⚠️  登录状态将自动保存，下次无需重新登录\n")
        
        # 等待用户操作
        input("按 Enter 键完成登录...")
        
        # 检查登录状态
        if browser_service.is_logged_in(context):
            print("\n✅ 登录成功！登录状态已保存")
        else:
            print("\n⚠️  未检测到登录状态，请确认是否已完成登录")
        
    finally:
        browser_service.close_browser()


def run_crawler(config_manager: ConfigManager, urls: list):
    """运行采集任务"""
    config = config_manager.load_config()
    error_handler = ErrorHandler()
    
    print("\n" + "="*60)
    print("  抖音评论采集助手 - 采集模式")
    print("="*60)
    print(f"📋 任务数量: {len(urls)}")
    print(f"📊 最大评论数: {config.max_comments}")
    print(f"🔄 增量模式: {'开启' if config.enable_incremental else '关闭'}")
    print("="*60 + "\n")
    
    browser_service = BrowserService(
        profile_path=config.profile_path,
        chrome_path=config.chrome_path
    )
    
    try:
        proxies = []
        if config.enable_proxy:
            if config.proxy_list:
                proxies.extend(config.proxy_list)
            elif config.proxy:
                proxies.append(config.proxy)
        proxy_manager = ProxyManager(proxies)
        initial_proxy = proxies[0] if proxies else None

        # 启动并连接浏览器
        context = browser_service.prepare_context(config.debug_port, initial_proxy)
        
        # 确保登录状态（如果未登录会提示用户登录）
        if not browser_service.ensure_logged_in(context):
            print("❌ 登录失败，无法继续采集")
            print("💡 提示：请确保能够正常访问抖音网站")
            return
        
        print("✅ 登录状态有效\n")
        
        # 创建服务实例
        anti_detection = AntiDetectionEngine(config)
        crawler_service = CrawlerService(anti_detection)
        data_service = DataService(config.output_dir)

        resume_file = config.resume_state_file or os.path.join(config.output_dir, "resume_state.json")
        resume_manager = ResumeManager(resume_file)
        
        # 创建任务管理器
        task_manager = TaskManager(
            browser_service,
            crawler_service,
            data_service,
            proxy_manager,
            resume_manager,
            error_handler
        )
        
        # 执行批量任务
        results = task_manager.execute_batch_tasks(urls, config)
        
        print("\n" + "="*60)
        print("  采集完成！")
        print("="*60)
        print(f"📁 输出目录: {config.output_dir}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断采集")
    except Exception as e:
        error_handler.log_error("采集过程发生错误", e)
    finally:
        browser_service.close_browser()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="抖音评论采集助手")
    parser.add_argument("--login", action="store_true", help="登录模式（扫码登录）")
    parser.add_argument("--url", help="单个视频链接")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    
    args = parser.parse_args()
    
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # 配置管理器
    config_path = _resolve_path(args.config, script_dir)
    template_path = str(script_dir / "config.json.example")
    config_manager = ConfigManager(config_path, default_template_path=template_path)
    
    # 登录模式
    if args.login:
        manual_login(config_manager)
        return
    
    # 采集模式
    urls = []
    urls_file = script_dir / "urls.txt"
    _bootstrap_urls_file(urls_file)
    
    # 从命令行参数获取URL
    if args.url:
        urls = [args.url]
    # 从urls.txt读取
    elif urls_file.exists():
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    
    if not urls:
        pasted = _prompt_for_urls()
        if pasted:
            urls = pasted
            content = "\n".join(urls) + "\n"
            urls_file.write_text(content, encoding="utf-8")
            print(f"📝 已将 {len(urls)} 条链接写入 {urls_file}")
    
    if not urls:
        print("❌ 未找到视频链接")
        print("   方式1: python main.py --url <视频链接>")
        print("   方式2: 在 urls.txt 文件中添加视频链接")
        return
    
    run_crawler(config_manager, urls)


if __name__ == "__main__":
    main()
