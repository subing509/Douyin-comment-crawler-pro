# -*- coding: utf-8 -*-
"""HTML评论解析工具"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag


class HTMLCommentParser:
    """将抖音评论区HTML解析为结构化数据"""

    def parse(self, html: str, video_id: str = "") -> List[Dict]:
        """解析整段HTML

        Args:
            html: 抖音评论区域的HTML字符串
            video_id: 可选的视频ID

        Returns:
            评论字典列表
        """

        soup = BeautifulSoup(html, "html.parser")
        comment_elements = soup.select('[data-e2e="comment-item"]')

        comments: List[Dict] = []
        tag_to_comment_id: Dict[int, str] = {}
        comments_by_id: Dict[str, Dict] = {}

        for element in comment_elements:
            comment_data = self._parse_comment_element(element, video_id)
            if not comment_data:
                continue

            comments.append(comment_data)
            comments_by_id[comment_data["comment_id"]] = comment_data
            tag_to_comment_id[id(element)] = comment_data["comment_id"]

            if self._is_reply(element):
                parent_tag = self._find_parent_comment_tag(element)
                if parent_tag:
                    parent_id = tag_to_comment_id.get(id(parent_tag))
                    if parent_id and parent_id in comments_by_id:
                        comment_data["parent_comment_id"] = parent_id
                        parent_comment = comments_by_id[parent_id]
                        parent_comment["reply_count"] = parent_comment.get("reply_count", 0) + 1

        return comments

    # ------------------------------------------------------------------
    # 内部解析函数
    # ------------------------------------------------------------------

    def _parse_comment_element(self, element: Tag, video_id: str) -> Optional[Dict]:
        user_nickname = self._extract_user_nickname(element)
        content = self._extract_comment_content(element)

        if not user_nickname or not content:
            return None

        user_id = self._extract_user_id(element)
        create_time, ip_location = self._extract_time_and_location(element)
        like_count = self._extract_like_count(element)
        is_author = self._has_author_badge(element)

        comment_id = self._generate_comment_id(
            video_id=video_id,
            user_id=user_id,
            user_nickname=user_nickname,
            content=content,
            create_time=create_time,
        )

        return {
            "comment_id": comment_id,
            "video_id": video_id,
            "content": content,
            "user_nickname": user_nickname,
            "user_id": user_id,
            "like_count": like_count,
            "reply_count": 0,
            "create_time": create_time,
            "ip_location": ip_location,
            "is_author": is_author,
            "parent_comment_id": "",
        }

    def _extract_user_nickname(self, element: Tag) -> str:
        nick_elem = element.select_one('.BT7MlqJC a, .arnSiSbK.xtTwhlGw')
        if not nick_elem:
            return ""
        self._inject_inline_alt_text(nick_elem)
        return nick_elem.get_text(strip=True)

    def _extract_user_id(self, element: Tag) -> str:
        link = element.select_one('.BT7MlqJC a[href], a[href*="/user/"]')
        if not link:
            return ""

        href = link.get("href", "")
        if href.startswith("//"):
            href = "https:" + href

        parsed = urlparse(href)
        path = parsed.path.rstrip('/')
        if not path:
            return ""
        parts = path.split('/')
        return parts[-1] if parts else ""

    def _extract_comment_content(self, element: Tag) -> str:
        content_elem = element.select_one('.C7LroK_h, .WFJiGxr7')
        if not content_elem:
            return ""
        self._inject_inline_alt_text(content_elem)
        text = content_elem.get_text("\n", strip=True)
        # 去掉多余空行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _extract_time_and_location(self, element: Tag) -> Tuple[str, str]:
        time_elem = element.select_one('.fJhvAqos span')
        if not time_elem:
            return "", ""
        text = time_elem.get_text(strip=True)
        if '·' in text:
            time_text, location = text.split('·', 1)
            return time_text.strip(), location.strip()
        return text, ""

    def _extract_like_count(self, element: Tag) -> int:
        like_elem = element.select_one('.xZhLomAs span')
        if not like_elem:
            return 0
        raw_text = like_elem.get_text(strip=True)
        return self._parse_count_text(raw_text)

    def _has_author_badge(self, element: Tag) -> bool:
        badge = element.select_one('.comment-item-tag')
        if not badge:
            return False
        text = badge.get_text(strip=True)
        return "作者" in text

    def _is_reply(self, element: Tag) -> bool:
        return element.find_parent('div', class_='replyContainer') is not None

    def _find_parent_comment_tag(self, element: Tag) -> Optional[Tag]:
        container = element.find_parent('div', class_='replyContainer')
        if not container:
            return None

        def is_top_level(tag: Tag) -> bool:
            return (
                isinstance(tag, Tag)
                and tag.name == 'div'
                and tag.get('data-e2e') == 'comment-item'
                and tag.find_parent('div', class_='replyContainer') is None
            )

        return container.find_previous(is_top_level)

    def _generate_comment_id(
        self,
        video_id: str,
        user_id: str,
        user_nickname: str,
        content: str,
        create_time: str,
    ) -> str:
        raw = "|".join([video_id or "html", user_id or user_nickname, content, create_time])
        digest = hashlib.md5(raw.encode("utf-8")).hexdigest()
        return f"html_{digest}"

    def _inject_inline_alt_text(self, element: Tag) -> None:
        for img in element.find_all('img'):
            alt_text = img.get('alt')
            if alt_text:
                img.replace_with(alt_text)

    def _parse_count_text(self, text: str) -> int:
        if not text:
            return 0
        text = text.replace(',', '').strip()
        if not text:
            return 0
        if text.endswith('万'):
            number_text = text[:-1]
            try:
                return int(float(number_text) * 10000)
            except ValueError:
                return 0
        try:
            return int(text)
        except ValueError:
            return 0


__all__ = ["HTMLCommentParser"]
