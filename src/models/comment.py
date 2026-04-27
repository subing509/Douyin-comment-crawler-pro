# -*- coding: utf-8 -*-
"""
评论数据模型
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
from datetime import datetime


@dataclass
class Comment:
    """评论数据模型"""
    comment_id: str
    video_id: str
    content: str
    user_nickname: str
    user_id: str = ""
    like_count: int = 0
    reply_count: int = 0
    create_time: str = ""
    ip_location: str = ""
    is_author: bool = False
    parent_comment_id: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            评论数据字典
            
    """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Comment':
        """从字典创建Comment对象
        
        Args:
            data: 评论数据字典
            
        Returns:
            Comment对象
        """
        return cls(**data)
    
    def validate(self) -> bool:
        """验证评论数据有效性
        
        Returns:
            True表示数据有效
        """
        if not self.comment_id or not self.video_id:
            return False
        if not self.content or not self.user_nickname:
            return False
        if self.like_count < 0 or self.reply_count < 0:
            return False
        return True
