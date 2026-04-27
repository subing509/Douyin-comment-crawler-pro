# -*- coding: utf-8 -*-
"""
视频信息数据模型
"""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class VideoInfo:
    """视频信息模型"""
    video_id: str
    title: str = ""
    author_nickname: str = ""
    author_id: str = ""
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    collect_count: int = 0
    publish_time: str = ""
    video_url: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            视频信息字典
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VideoInfo':
        """从字典创建VideoInfo对象
        
        Args:
            data: 视频信息字典
            
        Returns:
            VideoInfo对象
        """
        return cls(**data)
