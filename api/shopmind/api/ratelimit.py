"""In-process sliding window. Enough for one instance; a fleet would use Redis."""

from __future__ import annotations

import threading
import time


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock:
            recent = [
                stamp for stamp in self._hits.get(key, []) if now - stamp < self.window_seconds
            ]
            if len(recent) >= self.limit:
                self._hits[key] = recent
                return False, 0
            recent.append(now)
            self._hits[key] = recent
            return True, self.limit - len(recent)
