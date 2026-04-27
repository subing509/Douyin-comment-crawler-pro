# -*- coding: utf-8 -*-
"""
采集配置数据模型
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, List


@dataclass
class CrawlerConfig:
    """采集配置模型"""
    max_comments: int = 300
    include_replies: bool = False
    scroll_delay_min: float = 0.5
    scroll_delay_max: float = 2.0
    page_load_timeout: int = 30
    max_retry_attempts: int = 3
    enable_incremental: bool = False
    enable_proxy: bool = False
    proxy: Optional[str] = None
    proxy_list: Optional[List[str]] = None
    resume_state_file: Optional[str] = None
    chrome_path: Optional[str] = None
    profile_path: str = "douyin_profile"
    output_dir: str = "outputs"
    debug_port: int = 9222
    
    # 防反爬配置
    enable_stealth: bool = True  # 启用隐身模式
    simulate_reading: bool = True  # 模拟阅读行为
    reading_time_min: float = 2.0  # 最小阅读时间
    reading_time_max: float = 8.0  # 最大阅读时间
    enable_smart_delay: bool = True  # 启用智能延迟
    enable_session_break: bool = True  # 启用会话休息
    session_max_duration: int = 1800  # 会话最大时长（秒）
    session_max_actions: int = 500  # 会话最大操作数
    break_duration_min: int = 60  # 最小休息时长（秒）
    break_duration_max: int = 300  # 最大休息时长（秒）
    
    def validate(self) -> bool:
        """验证配置有效性
        
        Returns:
            True表示配置有效
        """
        if self.max_comments <= 0:
            return False
        if self.scroll_delay_min < 0 or self.scroll_delay_max < self.scroll_delay_min:
            return False
        if self.page_load_timeout <= 0:
            return False
        if self.max_retry_attempts < 0:
            return False
        if self.debug_port < 1024 or self.debug_port > 65535:
            return False
        return True
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            配置字典
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CrawlerConfig':
        """从字典创建CrawlerConfig对象
        
        Args:
            data: 配置字典
            
        Returns:
            CrawlerConfig对象
        """
        # 只使用已定义的字段
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)
