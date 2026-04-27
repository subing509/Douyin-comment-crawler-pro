# -*- coding: utf-8 -*-
"""
任务管理器 - 批量任务调度和执行
"""

import os
import time
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Callable

from ..services.browser_service import BrowserService
from ..services.crawler_service import CrawlerService
from ..services.data_service import DataService
from ..services.proxy_manager import ProxyManager
from ..services.resume_manager import ResumeManager
from ..services.status_reporter import StatusReporter
from ..models.config import CrawlerConfig
from ..models.task_result import TaskResult
from ..utils.url_parser import extract_video_id, is_video_url
from .error_handler import ErrorHandler
from ..services.anti_detection import RiskControlException


class TaskManager:
    """任务管理器"""
    
    def __init__(
        self,
        browser_service: BrowserService,
        crawler_service: CrawlerService,
        data_service: DataService,
        proxy_manager: ProxyManager,
        resume_manager: ResumeManager,
        error_handler: Optional[ErrorHandler] = None,
        status_reporter: Optional[StatusReporter] = None
    ):
        """初始化任务管理器
        
        Args:
            browser_service: 浏览器服务
            crawler_service: 采集服务
            data_service: 数据服务
            error_handler: 错误处理器
        """
        self.browser_service = browser_service
        self.crawler_service = crawler_service
        self.data_service = data_service
        self.proxy_manager = proxy_manager
        self.resume_manager = resume_manager
        self.error_handler = error_handler or ErrorHandler()
        summary_path = os.path.join(
            self.data_service.output_dir or "outputs",
            "status_summary.json"
        )
        self.status_reporter = status_reporter or StatusReporter(summary_path)
    
    def execute_single_task(
        self,
        url: str,
        config: CrawlerConfig
    ) -> TaskResult:
        """执行单个采集任务
        
        Args:
            url: 视频链接
            config: 配置对象
            
        Returns:
            任务结果对象
        """
        start_time = datetime.now()
        if not is_video_url(url):
            result = TaskResult(
                video_url=url,
                video_id="unknown",
                status="skipped",
                start_time=start_time
            )
            result.error_message = "链接不是标准的视频页面"
            result.failure_phase = "validation"
            result.end_time = datetime.now()
            result.calculate_duration()
            self.error_handler.log_warning(f"跳过无效链接: {url}")
            return result

        video_id = extract_video_id(url) or "unknown"
        
        result = TaskResult(
            video_url=url,
            video_id=video_id,
            status="failed",
            start_time=start_time
        )
        
        try:
            self.error_handler.log_info(f"开始采集任务: {url}")
            
            # 确保登录状态
            if not self.browser_service.ensure_logged_in():
                result.status = "failed"
                result.error_message = "未登录或登录失败"
                result.failure_phase = "login"
                self.error_handler.log_error(f"登录检查失败: {url}")
                return result
            
            attempts = config.max_retry_attempts + 1
            comments: Optional[List[Dict]] = None
            last_error = None
            last_proxy: Optional[str] = None

            for attempt in range(1, attempts + 1):
                proxy = self.proxy_manager.next_proxy()
                last_proxy = proxy
                self.error_handler.log_info(
                    f"使用代理: {proxy or '直连'}（尝试 {attempt}/{attempts}）"
                )
                context = self.browser_service.prepare_context(config.debug_port, proxy)
                page = context.new_page()
                try:
                    comments = self.crawler_service.crawl_video_comments(
                        page,
                        url,
                        max_comments=config.max_comments,
                        include_replies=config.include_replies
                    )
                    self.proxy_manager.record_success(proxy)
                    break
                except RiskControlException as risk:
                    last_error = risk
                    result.failure_phase = "crawl"
                    result.failure_details = traceback.format_exc()
                    self.proxy_manager.record_failure(proxy)
                    self.browser_service.close_browser()
                    self.browser_service.clear_profile_cache()
                    self.error_handler.log_warning(
                        f"风控触发 ({risk.reason})，准备下一轮重试"
                    )
                    continue
                except Exception as e:
                    last_error = e
                    result.failure_phase = "crawl"
                    result.failure_details = traceback.format_exc()
                    self.proxy_manager.record_failure(proxy)
                    self.error_handler.log_warning(
                        f"采集异常 ({type(e).__name__})，准备重试: {e}"
                    )
                    self.browser_service.close_browser()
                    continue
                finally:
                    try:
                        page.close()
                    except Exception:
                        pass

            if comments is None:
                result.status = "failed"
                result.error_message = str(last_error or "风控导致采集失败")
                self.error_handler.log_error(f"风控/异常导致失败: {url}", last_error)
                self.resume_manager.mark_failed(url, result.error_message)
                return result

            if not comments:
                result.status = "skipped"
                result.error_message = "未采集到评论"
                result.failure_phase = "crawl"
                result.failure_details = "未解析到有效评论"
                self.error_handler.log_warning(f"未采集到评论: {url}")
                self.resume_manager.mark_failed(url, result.error_message)
                return result

            # 获取视频信息
            info_page = self.browser_service.context.new_page()
            try:
                video_info = self.crawler_service.get_video_info(info_page, url).to_dict()
            finally:
                info_page.close()
            
            # 处理增量采集
            new_comments_count = len(comments)
            if config.enable_incremental:
                existing_df = self.data_service.load_existing_data(video_id)
                if existing_df is not None:
                    merged_df = self.data_service.merge_incremental_data(
                        existing_df,
                        comments
                    )
                    new_comments_count = len(merged_df) - len(existing_df)
                    comments = merged_df.to_dict('records')

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{video_id}_{timestamp}.xlsx"

            self.error_handler.log_info(f"准备导出 {len(comments)} 条评论到 {filename}")
            try:
                self.data_service.export_to_excel(comments, video_info, filename)
            except Exception as export_error:
                result.error_message = f"导出失败: {export_error}"
                result.failure_phase = "export"
                result.failure_details = traceback.format_exc()
                self.error_handler.log_error(f"导出失败: {url}", export_error)
                self.resume_manager.mark_failed(url, result.error_message)
                return result

            result.status = "success"
            result.comments_count = len(comments)
            result.new_comments_count = new_comments_count
            result.output_file = filename
            self.resume_manager.mark_completed(url, video_id, filename)
            self.error_handler.log_info(f"任务完成: {url} ({len(comments)} 条评论)")
            
        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            if not result.failure_phase:
                result.failure_phase = "unknown"
            result.failure_details = traceback.format_exc()
            self.error_handler.log_error(f"任务失败: {url}", e)
            self.resume_manager.mark_failed(url, result.error_message)

        finally:
            result.end_time = datetime.now()
            result.calculate_duration()
        
        return result

    def execute_batch_tasks(
        self,
        urls: List[str],
        config: CrawlerConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[TaskResult]:
        """执行批量采集任务
        
        Args:
            urls: 视频链接列表
            config: 配置对象
            progress_callback: 进度回调函数 callback(current, total, result)
            
        Returns:
            任务结果列表
        """
        results = []
        total = len(urls)
        
        self.error_handler.log_info(f"开始批量采集: {total} 个视频")
        
        for idx, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"进度: [{idx}/{total}] {url}")
            print(f"{'='*60}")
            
            if self.resume_manager.is_completed(url):
                self.error_handler.log_info(f"跳过已完成任务: {url}")
                skip_result = TaskResult(
                    video_url=url,
                    video_id=extract_video_id(url) or "unknown",
                    status="skipped",
                    start_time=datetime.now()
                )
                skip_result.error_message = "断点续爬已完成"
                skip_result.failure_phase = "resume"
                skip_result.end_time = skip_result.start_time
                skip_result.calculate_duration()
                results.append(skip_result)
                self.status_reporter.record(skip_result)
                continue

            # 执行单个任务
            result = self.execute_single_task(url, config)
            results.append(result)
            self.status_reporter.record(result)
            
            # 调用进度回调
            if progress_callback:
                try:
                    progress_callback(idx, total, result)
                except Exception as e:
                    self.error_handler.log_warning(f"进度回调失败: {e}")
            
            # 任务间延迟
            if idx < total:
                delay = 2
                print(f"\n⏳ 等待 {delay} 秒后继续下一个任务...")
                time.sleep(delay)
        
        # 生成报告
        report = self.data_service.generate_report([r.to_dict() for r in results])
        print(f"\n{report}")
        self.error_handler.log_info(f"批量采集完成: {total} 个任务")
        
        return results
