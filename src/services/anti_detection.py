# -*- coding: utf-8 -*-
"""
反检测引擎 - 模拟真实用户行为
"""

import time
import random
from typing import Optional, Set, TYPE_CHECKING
from playwright.sync_api import Page

if TYPE_CHECKING:
    from ..models.config import CrawlerConfig


class RiskControlException(Exception):
    """封装风控/验证码检测异常"""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class AntiDetectionEngine:
    """反检测引擎"""
    
    def __init__(self, config: Optional["CrawlerConfig"] = None):
        """初始化反检测引擎"""
        self.action_count = 0
        self.start_time = time.time()
        self.risk_hits = 0
        self.session_start = time.time()
        self.total_actions = 0
        self.last_action_time = time.time()
        self.config = config
        self._stealth_contexts: Set[int] = set()
    
    def random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """随机延迟
        
        Args:
            min_sec: 最小延迟秒数
            max_sec: 最大延迟秒数
        """
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def human_scroll(self, page: Page, distance: int = 800):
        """模拟人类滚动行为
        
        Args:
            page: Playwright Page对象
            distance: 滚动距离（像素）
        """
        # 随机化滚动距离
        actual_distance = distance + random.randint(-100, 100)
        
        # 使用平滑滚动
        page.evaluate(f"""
            window.scrollBy({{
                top: {actual_distance},
                behavior: 'smooth'
            }});
        """)
        
        # 随机停顿
        self.random_delay(0.8, 1.5)
    
    def random_mouse_move(self, page: Page):
        """随机鼠标移动
        
        Args:
            page: Playwright Page对象
        """
        try:
            # 获取页面尺寸
            viewport = page.viewport_size
            if not viewport:
                return
            
            # 随机目标位置
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            
            # 移动鼠标
            page.mouse.move(x, y)
            self.random_delay(0.1, 0.3)
        except Exception as e:
            # 忽略鼠标移动错误
            pass
    
    def check_captcha(self, page: Page) -> bool:
        """检测是否出现验证码
        
        Args:
            page: Playwright Page对象
            
        Returns:
            True表示检测到验证码
        """
        try:
            # 检测常见验证码元素
            captcha_selectors = [
                '[class*="captcha"]',
                '[id*="captcha"]',
                '[class*="verify"]',
                'iframe[src*="captcha"]',
            ]
            
            for selector in captcha_selectors:
                if page.locator(selector).count() > 0:
                    return True
            
            return False
        except Exception:
            return False
    
    def check_rate_limit(self, page: Page) -> bool:
        """检测是否触发速率限制
        
        Args:
            page: Playwright Page对象
            
        Returns:
            True表示触发限制
        """
        try:
            # 检测限流提示文本
            rate_limit_texts = [
                "访问过于频繁",
                "请稍后再试",
                "操作太快",
                "系统繁忙",
            ]
            
            page_content = page.content()
            for text in rate_limit_texts:
                if text in page_content:
                    return True
            
            return False
        except Exception:
            return False
    
    def rate_control(self, max_actions_per_minute: int = 50):
        """速率控制
        
        Args:
            max_actions_per_minute: 每分钟最大操作数
        """
        self.action_count += 1
        elapsed = time.time() - self.start_time
        
        # 如果在1分钟内超过限制，则等待
        if elapsed < 60 and self.action_count >= max_actions_per_minute:
            wait_time = 60 - elapsed
            print(f"⏳ 速率控制：等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
            self.action_count = 0
            self.start_time = time.time()
        
        # 重置计数器（每分钟）
        if elapsed >= 60:
            self.action_count = 0
            self.start_time = time.time()

    def handle_detection(self, reason: str) -> float:
        """记录风控事件并返回建议的等待时间"""
        self.risk_hits += 1
        wait_time = min(30, 2 ** min(self.risk_hits, 5))
        print(f"⚠️ 风控提示: {reason}，等待 {wait_time:.1f} 秒后重试")
        time.sleep(wait_time)
        return wait_time
    
    def simulate_reading(self, page: Page, duration: float = None):
        """模拟阅读行为
        
        Args:
            page: Playwright Page对象
            duration: 阅读时长（秒），None则随机
        """
        if self.config and not self.config.simulate_reading:
            return
        min_read = (self.config.reading_time_min
                    if self.config and self.config.reading_time_min > 0 else 2.0)
        max_read = (self.config.reading_time_max
                    if self.config and self.config.reading_time_max >= min_read else max(min_read, 8.0))
        if duration is None:
            duration = random.uniform(min_read, max_read)
        
        print(f"📖 模拟阅读 {duration:.1f} 秒...")
        
        # 在阅读期间随机移动鼠标
        steps = int(duration / 2)
        for _ in range(max(1, steps)):
            self.random_mouse_move(page)
            time.sleep(duration / max(1, steps))
    
    def simulate_natural_scroll(self, page: Page, target_distance: int = 800):
        """模拟自然滚动 - 分段滚动，带停顿
        
        Args:
            page: Playwright Page对象
            target_distance: 目标滚动距离
        """
        # 分成3-5段滚动
        segments = random.randint(3, 5)
        segment_distance = target_distance / segments
        
        for i in range(segments):
            # 每段距离随机化
            distance = segment_distance + random.randint(-50, 50)
            
            page.evaluate(f"""
                window.scrollBy({{
                    top: {distance},
                    behavior: 'smooth'
                }});
            """)
            
            # 段间停顿
            if i < segments - 1:
                pause = random.uniform(0.3, 0.8)
                time.sleep(pause)
        
        # 滚动后短暂停顿（模拟查看内容）
        time.sleep(random.uniform(0.5, 1.5))
    
    def check_session_health(self) -> bool:
        """检查会话健康度
        
        Returns:
            True表示需要休息
        """
        if self.config and not self.config.enable_session_break:
            return False
        session_duration = time.time() - self.session_start
        max_duration = self.config.session_max_duration if self.config else 1800
        max_actions = self.config.session_max_actions if self.config else 500
        risk_threshold = 3
        
        if session_duration > max_duration:
            return True
        
        if self.total_actions > max_actions:
            return True
        
        if self.risk_hits > risk_threshold:
            return True
        
        return False
    
    def take_break(self, duration: int = None):
        """休息一段时间
        
        Args:
            duration: 休息时长（秒），None则根据情况自动计算
        """
        if self.config and not self.config.enable_session_break:
            return
        if duration is None:
            min_break = self.config.break_duration_min if self.config else 60
            max_break = self.config.break_duration_max if self.config else 300
            base_duration = min_break * (1 + self.risk_hits * 0.5)
            duration = min(max_break, max(min_break, base_duration))
        
        print(f"\n☕ 休息 {duration:.0f} 秒，模拟真实用户行为...")
        time.sleep(duration)
        
        # 重置计数器
        self.session_start = time.time()
        self.total_actions = 0
        self.risk_hits = max(0, self.risk_hits - 1)  # 减少风控计数
        print("✅ 休息完成，继续采集\n")
    
    def prepare_page(self, page: Page):
        """在导航前注入隐身脚本"""
        self.inject_stealth_scripts(page)
    
    def inject_stealth_scripts(self, page: Page):
        """注入隐身脚本 - 隐藏自动化特征
        
        Args:
            page: Playwright Page对象
        """
        if self.config and not self.config.enable_stealth:
            return
        try:
            context = page.context
            if not context:
                return
            context_id = id(context)
            if context_id in self._stealth_contexts:
                return
            
            def _add_script(script: str):
                context.add_init_script(script)
            
            _add_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            _add_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            _add_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)
            
            self._stealth_contexts.add(context_id)
        except Exception as e:
            print(f"⚠️ 注入隐身脚本失败: {e}")

    def smart_delay(self, base_min: float = 0.5, base_max: float = 2.0):
        """智能延迟 - 根据行为模式动态调整
        
        Args:
            base_min: 基础最小延迟
            base_max: 基础最大延迟
        """
        if self.config and not self.config.enable_smart_delay:
            return
        # 计算距离上次操作的时间
        time_since_last = time.time() - self.last_action_time
        
        # 如果操作太频繁，增加延迟
        if time_since_last < 1.0:
            multiplier = 1.5
        else:
            multiplier = 1.0
        
        # 根据风控次数调整
        if self.risk_hits > 0:
            multiplier *= (1 + self.risk_hits * 0.2)
        
        # 随机延迟
        delay = random.uniform(base_min * multiplier, base_max * multiplier)
        
        # 偶尔加入长时间停顿（模拟用户思考）
        if random.random() < 0.1:  # 10%概率
            delay += random.uniform(2, 5)
            print(f"💭 模拟用户思考，停顿 {delay:.1f} 秒...")
        
        time.sleep(delay)
        self.last_action_time = time.time()
        self.total_actions += 1
