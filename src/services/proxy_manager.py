# -*- coding: utf-8 -*-
"""代理轮换管理器"""

from typing import List, Optional


class ProxyManager:
    """管理多代理轮换"""
    
    def __init__(self, proxies: Optional[List[str]] = None, max_failures: int = 3):
        self.proxies = [p.strip() for p in (proxies or []) if p and p.strip()]
        self.index = -1
        self.max_failures = max_failures
        self.fail_counts = {p: 0 for p in self.proxies}

    def has_proxy(self) -> bool:
        return bool(self.proxies)

    def next_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None

        candidates = [
            p for p in self.proxies
            if self.fail_counts.get(p, 0) < self.max_failures
        ]

        if not candidates:
            for p in self.proxies:
                self.fail_counts[p] = 0
            candidates = list(self.proxies)

        self.index = (self.index + 1) % len(candidates)
        return candidates[self.index]

    def record_success(self, proxy: Optional[str]) -> None:
        if proxy and proxy in self.fail_counts:
            self.fail_counts[proxy] = 0

    def record_failure(self, proxy: Optional[str]) -> None:
        if proxy and proxy in self.fail_counts:
            self.fail_counts[proxy] += 1


__all__ = ["ProxyManager"]
