"""
backend/rate_limit.py — Simple in-memory token-bucket rate limiter.

No Redis required — state resets on server restart (acceptable for hackathon).
Swap to a Redis-backed solution for production.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, status


class _TokenBucket:
    """Per-key token bucket."""

    def __init__(self, max_tokens: int, refill_rate: float):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self._buckets: dict[str, tuple[float, float]] = {}  # key → (tokens, last_refill)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        tokens, last_refill = self._buckets.get(key, (self.max_tokens, now))

        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        tokens = min(self.max_tokens, tokens + elapsed * self.refill_rate)

        if tokens >= 1.0:
            self._buckets[key] = (tokens - 1.0, now)
            return True

        self._buckets[key] = (tokens, now)
        return False


# Pre-configured buckets
_advisor_bucket = _TokenBucket(max_tokens=10, refill_rate=10 / 60)  # 10 req/min
_login_bucket = _TokenBucket(max_tokens=5, refill_rate=5 / 60)      # 5 req/min


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def create_rate_limit_dependency(bucket: _TokenBucket) -> Callable:
    """Factory that returns a FastAPI dependency for the given bucket."""

    async def _check(request: Request) -> None:
        key = _get_client_ip(request)
        if not bucket.allow(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before trying again.",
            )

    return _check


# Ready-to-use dependencies
advisor_rate_limit = create_rate_limit_dependency(_advisor_bucket)
login_rate_limit = create_rate_limit_dependency(_login_bucket)
