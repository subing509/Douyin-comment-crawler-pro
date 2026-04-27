# -*- coding: utf-8 -*-
"""
浏览器服务 - 管理浏览器生命周期和CDP连接
"""

import os
import time
import shutil
import subprocess
from typing import Optional
from playwright.sync_api import sync_playwright, BrowserContext, Browser


class BrowserService:
    """浏览器管理服务"""
    
    def __init__(self, profile_path: str, chrome_path: Optional[str] = None):
        """初始化浏览器服务
        
        Args:
            profile_path: 浏览器配置文件路径
            chrome_path: Chrome可执行文件路径
        """
        self.profile_path = os.path.expanduser(profile_path)
        self.chrome_path = chrome_path or self._get_default_chrome_path()
        self.browser_process: Optional[subprocess.Popen] = None
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.current_proxy: Optional[str] = None
        
        # 确保profile目录存在
        os.makedirs(self.profile_path, exist_ok=True)
    
    def _get_default_chrome_path(self) -> str:
        """获取默认Chrome路径
        
        Returns:
            Chrome可执行文件路径
        """
        import platform
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif system == "Windows":
            return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        else:  # Linux
            return "/usr/bin/google-chrome"
    
    def launch_browser(self, debug_port: int = 9222, proxy: Optional[str] = None) -> subprocess.Popen:
        """启动本地Chrome浏览器
        
        Args:
            debug_port: 调试端口
            
        Returns:
            浏览器进程对象
        """
        print(f"🚀 正在启动Chrome浏览器（调试端口: {debug_port}）...")
        
        # 启动Chrome with CDP
        args = [
            self.chrome_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={self.profile_path}",
            "--no-first-run",
            "--no-default-browser-check",
            "--start-maximized"
        ]
        if proxy:
            args.append(f"--proxy-server={proxy}")
            self.current_proxy = proxy
        else:
            self.current_proxy = None

        self.browser_process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待浏览器启动
        time.sleep(3)
        print("✅ Chrome浏览器已启动")
        
        return self.browser_process
    
    def connect_browser(self, debug_port: int = 9222) -> BrowserContext:
        """通过CDP连接到浏览器
        
        Args:
            debug_port: 调试端口
            
        Returns:
            Playwright BrowserContext对象
        """
        print(f"🔗 正在连接到浏览器...")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp(
            f"http://localhost:{debug_port}"
        )
        
        # 获取或创建context
        if self.browser.contexts:
            self.context = self.browser.contexts[0]
        else:
            self.context = self.browser.new_context()
        
        print("✅ 已成功连接到浏览器")
        return self.context
    
    def close_browser(self):
        """关闭浏览器和连接"""
        print("🔒 正在关闭浏览器...")
        
        if self.context:
            try:
                self.context.close()
            except:
                pass
            finally:
                self.context = None
        
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
            finally:
                self.browser = None
        
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
            finally:
                self.playwright = None
        
        if self.browser_process:
            try:
                self.browser_process.terminate()
                self.browser_process.wait(timeout=5)
            except:
                try:
                    self.browser_process.kill()
                except:
                    pass
            finally:
                self.browser_process = None
        self.current_proxy = None
        
        print("✅ 浏览器已关闭")

    def clear_profile_cache(self):
        """清理用户数据中的缓存以规避长时间运行的风险反馈"""
        if self.browser_process:
            print("⚠️ 清理缓存前需要先关闭浏览器，操作已跳过")
            return
        cache_dirs = [
            "Cache",
            "GPUCache",
            "Code Cache",
            os.path.join("Default", "Cache"),
            os.path.join("Default", "Cache_Data"),
            os.path.join("Default", "Code Cache"),
        ]

        for sub in cache_dirs:
            path = os.path.join(self.profile_path, sub)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
    
    def is_logged_in(self, context: Optional[BrowserContext] = None) -> bool:
        """检查登录状态
        
        Args:
            context: BrowserContext对象，如果为None则使用self.context
            
        Returns:
            True表示已登录，False表示未登录
        """
        ctx = context or self.context
        if not ctx:
            return False
        
        try:
            # 先访问首页，确保Cookie加载
            page = ctx.new_page()
            try:
                print("🔍 检查登录状态...")
                page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=15000)
                time.sleep(2)
                
                # 检查是否有登录按钮（未登录的标志）
                login_button_selectors = [
                    'text="登录"',
                    '[class*="login"]',
                    'button:has-text("登录")',
                    'a:has-text("登录")'
                ]
                
                for selector in login_button_selectors:
                    if page.locator(selector).count() > 0:
                        print("⚠️ 检测到登录按钮，可能未登录")
                        return False
                
                # 检查是否有用户头像或用户信息（已登录的标志）
                user_info_selectors = [
                    '[class*="avatar"]',
                    '[class*="user-info"]',
                    '[class*="header-user"]',
                    'img[alt*="头像"]'
                ]
                
                for selector in user_info_selectors:
                    if page.locator(selector).count() > 0:
                        print("✅ 检测到用户信息，已登录")
                        return True
                
                # 检查Cookie作为备用方案
                cookies = ctx.cookies("https://www.douyin.com")
                for cookie in cookies:
                    if cookie.get('name') in ['sessionid', 'sid_guard', 'uid_tt']:
                        print("✅ 检测到登录Cookie")
                        return True
                
                return False
                
            finally:
                page.close()
                
        except Exception as e:
            print(f"⚠️ 检查登录状态失败: {e}")
            return False
    
    def ensure_logged_in(self, context: Optional[BrowserContext] = None) -> bool:
        """确保已登录，如果未登录则打开首页等待用户登录
        
        Args:
            context: BrowserContext对象
            
        Returns:
            True表示已登录，False表示未登录
        """
        ctx = context or self.context
        if not ctx:
            return False
        
        if self.is_logged_in(ctx):
            return True
        
        print("\n" + "="*60)
        print("  需要登录")
        print("="*60)
        print("💡 正在打开抖音首页，请扫码登录...")
        
        page = ctx.new_page()
        try:
            page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=30000)
            
            print("\n请在浏览器中完成以下操作：")
            print("1. 点击登录按钮")
            print("2. 使用抖音APP扫码登录")
            print("3. 登录成功后，按Enter键继续\n")
            
            input("按 Enter 键继续...")
            
            # 再次检查登录状态
            page.close()
            return self.is_logged_in(ctx)
            
        except Exception as e:
            print(f"❌ 登录过程出错: {e}")
            page.close()
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_browser()

    def prepare_context(self, debug_port: int, proxy: Optional[str] = None) -> BrowserContext:
        """确保当前浏览器使用指定代理并返回新的上下文"""

        if self.context and proxy == self.current_proxy:
            return self.context

        self.close_browser()
        self.launch_browser(debug_port, proxy)
        return self.connect_browser(debug_port)
