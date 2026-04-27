# -*- coding: utf-8 -*-
"""
URL解析工具
"""

import re
from urllib.parse import urlparse
from typing import Optional


def extract_video_id(url: str) -> Optional[str]:
    """从URL中提取视频ID
    
    Args:
        url: 视频链接
        
    Returns:
        视频ID，如果无法提取则返回None
    """
    # 匹配 /video/123456789 或 modal_id=123456789
    match = re.search(r"(?:/video/|modal_id=)(\d+)", url)
    return match.group(1) if match else None


def is_video_url(url: str) -> bool:
    """判断链接是否为抖音视频页"""

    if extract_video_id(url):
        return True

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if "douyin.com" not in domain and "iesdouyin.com" not in domain:
        return False

    path = parsed.path
    query = parsed.query
    if "/video/" in path or "modal_id=" in query:
        return True

    return False


def normalize_video_url(url: str) -> str:
    """将任意可识别的视频链接转换为标准 /video/{id} 形式

    例如:
        https://www.douyin.com/jingxuan?modal_id=123 -> https://www.douyin.com/video/123

    Args:
        url: 原始链接

    Returns:
        规范化后可直接打开评论区的链接；如果无法识别则原样返回
    """
    video_id = extract_video_id(url)
    if not video_id:
        return url

    parsed = urlparse(url)
    path = parsed.path or ""

    # 已经是标准视频路径则直接返回
    if re.search(r"/video/\d+", path):
        return url

    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or "www.douyin.com"

    # 对短链或其它域名统一切换到主站，避免功能受限
    if "douyin.com" not in netloc:
        netloc = "www.douyin.com"

    return f"{scheme}://{netloc}/video/{video_id}"
