# -*- coding: utf-8 -*-
"""断点续爬状态管理"""

import json
from pathlib import Path
from typing import Dict, Optional


class ResumeManager:
    """记录已经完成的视频任务，避免重复采集"""

    def __init__(self, state_path: Optional[str] = None):
        self.path = Path(state_path or "outputs/resume_state.json")
        self.state: Dict[str, Dict] = {
            "completed": {},
            "failed": {}
        }
        self._ensure_file()
        self._load_state()

    def _ensure_file(self):
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_state(self):
        if not self.path.exists():
            self._flush_state()
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.state = {
                    "completed": data.get("completed", {}),
                    "failed": data.get("failed", {})
                }
        except Exception:
            self._flush_state()

    def _flush_state(self):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def is_completed(self, url: str) -> bool:
        return url in self.state.get("completed", {})

    def mark_completed(self, url: str, video_id: str, output_file: str):
        self.state.setdefault("completed", {})[url] = {
            "video_id": video_id,
            "output_file": output_file
        }
        self._flush_state()

    def mark_failed(self, url: str, reason: str):
        self.state.setdefault("failed", {})[url] = {
            "reason": reason
        }
        self._flush_state()


__all__ = ["ResumeManager"]
