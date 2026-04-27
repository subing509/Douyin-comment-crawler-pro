# -*- coding: utf-8 -*-
"""任务状态汇总输出"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models.task_result import TaskResult


class StatusReporter:
    """将每次任务结果额外输出为 JSON 报表"""

    def __init__(self, output_path: Optional[str] = None):
        self.path = Path(output_path or "outputs/status_summary.json")
        self._ensure_parent()
        self.entries: List[Dict] = []
        self._load_existing_entries()

    def _ensure_parent(self):
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, result: TaskResult) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "video_url": result.video_url,
            "video_id": result.video_id,
            "status": result.status,
            "failure_phase": result.failure_phase,
            "error_message": result.error_message,
            "failure_details": result.failure_details,
            "output_file": result.output_file,
            "duration": result.duration,
        }
        self.entries.append(entry)
        self._flush()

    def _flush(self) -> None:
        with self.path.open("w", encoding="utf-8") as fp:
            json.dump({"results": self.entries}, fp, ensure_ascii=False, indent=2)

    def _load_existing_entries(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
            results = data.get("results", [])
            if isinstance(results, list):
                self.entries.extend(results)
        except Exception:
            # 旧文件损坏时重置
            self.entries = []


__all__ = ["StatusReporter"]
