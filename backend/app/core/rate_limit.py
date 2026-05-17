from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        now = time.time()
        earliest_allowed = now - window_seconds

        with self._lock:
            bucket = self._events[key]

            while bucket and bucket[0] < earliest_allowed:
                bucket.popleft()

            if len(bucket) >= limit:
                return False

            bucket.append(now)
            return True


rate_limiter = InMemoryRateLimiter()
