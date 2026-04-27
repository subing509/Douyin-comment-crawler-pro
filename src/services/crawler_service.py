# -*- coding: utf-8 -*-
"""
评论采集服务
"""

import random
import time
from typing import List, Dict, Optional
from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from ..models.comment import Comment
from ..models.video_info import VideoInfo
from ..utils.url_parser import extract_video_id, normalize_video_url
from .anti_detection import AntiDetectionEngine, RiskControlException
from .html_parser import HTMLCommentParser


class CrawlerService:
    """评论采集服务"""
    
    def __init__(self, anti_detection: Optional[AntiDetectionEngine] = None):
        """初始化采集服务
        
        Args:
            anti_detection: 反检测引擎实例
        """
        self.anti_detection = anti_detection or AntiDetectionEngine()
        self.html_parser = HTMLCommentParser()
    
    def get_video_info(self, page: Page, video_url: str) -> VideoInfo:
        """获取视频基本信息
        
        Args:
            page: Playwright Page对象
            video_url: 视频链接
            
        Returns:
            视频信息对象
        """
        normalized_url = normalize_video_url(video_url)
        video_id = extract_video_id(normalized_url) or ""
        
        try:
            current_id = extract_video_id(page.url or "") if hasattr(page, "url") else ""
            if not current_id or current_id != video_id:
                try:
                    page.goto(normalized_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)
                except Exception as nav_err:
                    print(f"⚠️ 视频信息加载失败: {nav_err}")
            
            # 提取视频标题
            title = ""
            try:
                title_elem = page.locator('[data-e2e="video-title"], h1').first
                if title_elem.count() > 0:
                    title = title_elem.inner_text()
            except:
                pass
            
            # 提取作者信息
            author_nickname = ""
            try:
                author_elem = page.locator('[data-e2e="video-author-name"], [class*="author"]').first
                if author_elem.count() > 0:
                    author_nickname = author_elem.inner_text()
            except:
                pass
            
            # 提取统计数据
            like_count = 0
            comment_count = 0
            
            return VideoInfo(
                video_id=video_id,
                title=title,
                author_nickname=author_nickname,
                video_url=normalized_url,
                like_count=like_count,
                comment_count=comment_count
            )
        except Exception as e:
            print(f"⚠️ 获取视频信息失败: {e}")
            return VideoInfo(video_id=video_id, video_url=video_url)

    def scroll_to_load_comments(self, page: Page, target_count: int, max_scrolls: int = 20) -> int:
        """滚动页面加载评论
        
        Args:
            page: Playwright Page对象
            target_count: 目标评论数量
            max_scrolls: 最大滚动次数
            
        Returns:
            实际加载的评论数量
        """
        print(f"📜 开始滚动加载评论（目标: {target_count}条）...")
        
        # 尝试多种选择器
        comment_selectors = [
            '[data-e2e="comment-item"]',
            '[class*="comment-item"]',
            '[class*="CommentItem"]',
            '.comment-item'
        ]
        
        # 找到有效的选择器
        active_selector = None
        for selector in comment_selectors:
            if page.locator(selector).count() > 0:
                active_selector = selector
                print(f"  使用选择器: {selector}")
                break
        
        if not active_selector:
            print("⚠️ 未找到评论元素，跳过滚动")
            return 0
        
        prev_count = 0
        no_change_count = 0
        
        for i in range(max_scrolls):
            # 获取当前评论数量
            current_count = page.locator(active_selector).count()
            
            print(f"  滚动 {i+1}/{max_scrolls}: 已加载 {current_count} 条评论")
            
            # 检查是否达到目标
            if current_count >= target_count:
                print(f"✅ 已达到目标评论数量: {current_count}")
                break
            
            # 检查是否没有新评论加载
            if current_count == prev_count:
                no_change_count += 1
                if no_change_count >= 3:
                    print(f"⚠️ 连续3次滚动无新评论，停止加载")
                    break
            else:
                no_change_count = 0
            
            prev_count = current_count
            
            # 使用自然滚动
            self.anti_detection.simulate_natural_scroll(page)
            
            # 偶尔模拟阅读评论
            if random.random() < 0.2:  # 20%概率
                self.anti_detection.simulate_reading(page, duration=random.uniform(1, 3))
            
            # 速率控制
            self.anti_detection.rate_control()
            
            # 检查会话健康度
            if self.anti_detection.check_session_health():
                print("⚠️ 检测到长时间运行，建议休息...")
                self.anti_detection.take_break()
            
            # 检查验证码
            if self.anti_detection.check_captcha(page):
                self.anti_detection.handle_detection("验证码")
                raise RiskControlException("验证码挑战")
            
            # 检查限流
            if self.anti_detection.check_rate_limit(page):
                self.anti_detection.handle_detection("限流提示")
                raise RiskControlException("限流提示")
        
        final_count = page.locator(active_selector).count()
        print(f"✅ 滚动完成，共加载 {final_count} 条评论")
        return final_count

    def crawl_video_comments(
        self,
        page: Page,
        video_url: str,
        max_comments: int = 300,
        include_replies: bool = False
    ) -> List[Dict]:
        """采集视频评论
        
        Args:
            page: Playwright Page对象
            video_url: 视频链接
            max_comments: 最大采集数量
            include_replies: 是否采集子评论
            
        Returns:
            评论数据列表
        """
        print(f"\n🎯 开始采集视频评论: {video_url}")

        normalized_url = normalize_video_url(video_url)
        if normalized_url != video_url:
            print(f"🔁 链接已规范化为: {normalized_url}")
        
        video_id = extract_video_id(normalized_url) or ""
        
        try:
            # 先访问首页，确保登录状态和Cookie有效
            print("🏠 先访问抖音首页，确保登录状态...")
            try:
                self.anti_detection.prepare_page(page)
                page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=15000)
                time.sleep(2)
                print("✅ 首页访问成功")
            except Exception as e:
                print(f"⚠️ 首页访问失败: {e}，继续尝试访问视频页面...")
            
            # 打开视频页面
            print("📖 正在加载视频页面...")
            page.goto(normalized_url, wait_until="domcontentloaded", timeout=30000)
            
            # 等待页面完全加载
            time.sleep(3)
            
            # 模拟阅读视频信息
            self.anti_detection.simulate_reading(page, duration=random.uniform(2, 4))
            
            # 尝试多种选择器等待评论区
            print("🔍 等待评论区加载...")
            comment_list_selectors = [
                '[data-e2e="comment-list"]',
                '[class*="comment-list"]',
                '[class*="CommentList"]',
                '#comment-list',
                '.comment-list'
            ]
            
            comment_list_found = False
            for selector in comment_list_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ 找到评论区: {selector}")
                    comment_list_found = True
                    break
                except PWTimeoutError:
                    continue
            
            if not comment_list_found:
                print("⚠️ 未找到评论区容器，尝试直接查找评论项...")
            
            # 智能延迟
            self.anti_detection.smart_delay(1, 2)
            
            # 滚动加载评论
            self.scroll_to_load_comments(page, max_comments)
            
            comments = self._extract_comments_from_page(
                page,
                video_id,
                include_replies=include_replies,
                max_comments=max_comments
            )
            
            if not comments:
                print("❌ 未找到评论数据，已保存页面HTML用于调试")
                try:
                    html = page.content()
                    debug_file = f"debug_no_comments_{int(time.time())}.html"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"   已保存到: {debug_file}")
                except Exception as save_err:
                    print(f"⚠️ 保存调试文件失败: {save_err}")
                return []
            
            print(f"✅ 成功采集 {len(comments)} 条有效评论")
            return comments
            
        except Exception as e:
            print(f"❌ 采集失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_comments_from_page(
        self,
        page: Page,
        video_id: str,
        include_replies: bool,
        max_comments: int
    ) -> List[Dict]:
        """使用HTML解析结果构建评论列表"""
        try:
            html = page.content()
        except Exception as e:
            print(f"⚠️ 读取页面HTML失败: {e}")
            return []
        
        parsed = self.html_parser.parse(html, video_id)
        if not include_replies:
            parsed = [c for c in parsed if not c.get("parent_comment_id")]
        
        comments: List[Dict] = []
        for record in parsed:
            try:
                comment = Comment(**record)
                if comment.validate():
                    comments.append(comment.to_dict())
            except TypeError:
                continue
            if len(comments) >= max_comments:
                break
        return comments
