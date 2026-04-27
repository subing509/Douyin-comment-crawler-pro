# -*- coding: utf-8 -*-
"""
错误处理器 - 异常捕获和日志记录
"""

import os
import logging
import traceback
from datetime import datetime
from typing import Optional
from playwright.sync_api import TimeoutError as PWTimeoutError


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, log_dir: str = "logs"):
        """初始化错误处理器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 配置日志
        log_file = os.path.join(
            self.log_dir,
            f"crawler_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def handle_exception(self, exc: Exception, context: str) -> bool:
        """处理异常
        
        Args:
            exc: 异常对象
            context: 异常上下文描述
            
        Returns:
            True表示可以重试，False表示不可恢复
        """
        error_type = type(exc).__name__
        error_msg = str(exc)
        
        # 可恢复错误
        recoverable_errors = [
            PWTimeoutError,
            ConnectionError,
            TimeoutError,
        ]
        
        is_recoverable = any(isinstance(exc, err_type) for err_type in recoverable_errors)
        
        if is_recoverable:
            self.logger.warning(f"[可恢复] {context}: {error_type} - {error_msg}")
            return True
        else:
            self.logger.error(f"[不可恢复] {context}: {error_type} - {error_msg}")
            self.log_error(f"{context} 发生错误", exc)
            return False
    
    def log_error(self, message: str, exc: Optional[Exception] = None):
        """记录错误日志
        
        Args:
            message: 错误消息
            exc: 异常对象
        """
        self.logger.error(message)
        
        if exc:
            self.logger.error(f"异常类型: {type(exc).__name__}")
            self.logger.error(f"异常信息: {str(exc)}")
            self.logger.error(f"堆栈跟踪:\n{traceback.format_exc()}")
    
    def log_info(self, message: str):
        """记录信息日志
        
        Args:
            message: 信息消息
        """
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """记录警告日志
        
        Args:
            message: 警告消息
        """
        self.logger.warning(message)
