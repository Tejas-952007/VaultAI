import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple


class LocalRateLimiter:
    """Very small in-process rate limiter for prototype deployments."""

    def __init__(self, limit_per_minute: int = 60, burst: int = 10):
        self.limit_per_minute = limit_per_minute
        self.burst = burst
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        window = 60.0
        with self._lock:
            bucket = self._buckets[key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()

            if len(bucket) >= self.limit_per_minute and len(bucket) >= self.burst:
                return False

            bucket.append(now)
            return True


router_limiter = LocalRateLimiter(limit_per_minute=60, burst=10)
upload_limiter = LocalRateLimiter(limit_per_minute=20, burst=5)
sandbox_limiter = LocalRateLimiter(limit_per_minute=10, burst=2)
auth_limiter = LocalRateLimiter(limit_per_minute=10, burst=10)
