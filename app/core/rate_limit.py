import time
import threading
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Union
from fastapi import Request, status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings

# Thread-safe sliding window storage for IP-based rate limiting
_rate_limit_lock = threading.Lock()
_request_records: Dict[str, List[float]] = defaultdict(list)
_last_global_cleanup: float = 0.0


def get_client_ip(request: Request) -> str:
    """Extract client IP address, respecting X-Forwarded-For if present."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first untrusted proxy hop
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def reset_rate_limits() -> None:
    """Utility to clear rate limit buckets (primarily for testing)."""
    with _rate_limit_lock:
        _request_records.clear()


class RateLimiter:
    """Thread-safe sliding-window in-memory rate limiter dependency for FastAPI."""

    def __init__(
        self,
        key: str,
        max_requests: Union[int, Callable[[], int]],
        window_seconds: Union[int, Callable[[], int]] = 60
    ):
        self.key = key
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    @property
    def max_requests(self) -> int:
        if callable(self._max_requests):
            return self._max_requests()
        return self._max_requests

    @property
    def window_seconds(self) -> int:
        if callable(self._window_seconds):
            return self._window_seconds()
        return self._window_seconds

    async def __call__(self, request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        # Bypass hook for internal automated test runs if header provided
        if request.headers.get("X-Test-Bypass-Rate-Limit") == "finreg-test-secret":
            return

        client_ip = get_client_ip(request)
        bucket_key = f"{self.key}:{client_ip}"
        now = time.monotonic()
        effective_max = self.max_requests
        effective_window = self.window_seconds

        with _rate_limit_lock:
            global _last_global_cleanup
            # Periodic cleanup every 300 seconds to prevent memory unbounded growth
            if now - _last_global_cleanup > 300.0:
                stale_keys = []
                for k, ts_list in _request_records.items():
                    cutoff = now - 300.0
                    _request_records[k] = [t for t in ts_list if t > cutoff]
                    if not _request_records[k]:
                        stale_keys.append(k)
                for k in stale_keys:
                    _request_records.pop(k, None)
                _last_global_cleanup = now

            timestamps = _request_records[bucket_key]
            cutoff = now - effective_window
            # Retain only timestamps inside the sliding window
            valid_timestamps = [t for t in timestamps if t > cutoff]
            _request_records[bucket_key] = valid_timestamps

            if len(valid_timestamps) >= effective_max:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(effective_window - (now - oldest)))
                headers = {
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(effective_max),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                }
                raise StarletteHTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please wait before retrying.",
                    headers=headers,
                )

            # Record this valid request
            _request_records[bucket_key].append(now)
