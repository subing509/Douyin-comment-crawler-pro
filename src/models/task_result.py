# -*- coding: utf-8 -*-
"""
任务结果数据模型
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional
from datetime import datetime


@dataclass
class TaskResult:
    """任务结果模型"""
    video_url: str
    video_id: str
    status: str  # success/failed/skipped
    comments_count: int = 0
    new_comments_count: int = 0
    output_file: str = ""
    error_message: str = ""
    failure_phase: str = ""
    failure_details: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            任务结果字典
        """
        data = asdict(self)
        # 转换datetime为字符串
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    def calculate_duration(self):
        """计算任务耗时"""
        if self.start_time and self.end_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TaskResult':
        """从字典创建TaskResult对象
        
        Args:
            data: 任务结果字典
            
        Returns:
            TaskResult对象
        """
        # 转换字符串为datetime
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)
