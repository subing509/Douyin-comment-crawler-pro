"""
数据模型层 - 定义评论、视频信息、任务结果和配置数据结构
"""

from .comment import Comment
from .video_info import VideoInfo
from .task_result import TaskResult
from .config import CrawlerConfig

__all__ = [
    'Comment',
    'VideoInfo',
    'TaskResult',
    'CrawlerConfig',
]
