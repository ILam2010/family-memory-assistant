"""Simple in-memory rate limiting (resets when the bot restarts)."""

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_events: int, per_seconds: float) -> None:
        self.max_events = max_events
        self.per_seconds = per_seconds
        self._events: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, key: int) -> bool:
        now = time.monotonic()
        events = self._events[key]
        while events and now - events[0] > self.per_seconds:
            events.popleft()
        if len(events) >= self.max_events:
            return False
        events.append(now)
        return True


question_limiter = RateLimiter(max_events=5, per_seconds=60)
upload_limiter = RateLimiter(max_events=10, per_seconds=60)