"""
HRMS Rate Limiting Middleware
Redis-backed sliding window rate limiter.
Protects all endpoints from abuse with per-IP and per-user limits.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis import redis_manager

logger = logging.getLogger(__name__)


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter using Redis sorted sets.
    - General API: 60 requests per minute per IP
    - AI endpoints: 10 requests per minute per IP
    """

    def __init__(self, app, general_limit: int = 60, ai_limit: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.general_limit = general_limit
        self.ai_limit = ai_limit
        self.window_seconds = window_seconds
        self._ai_paths = {"/nlp/", "/voice/", "/chatbot/", "/advisor"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = _get_client_ip(request)
        path = request.url.path

        # Skip rate limiting for health checks and docs
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Determine rate limit based on path
        is_ai_path = any(p in path for p in self._ai_paths)
        limit = self.ai_limit if is_ai_path else self.general_limit
        category = "ai" if is_ai_path else "general"

        # Sliding window using Redis sorted sets
        key = f"ratelimit:{category}:{client_ip}"
        now = time.time()
        window_start = now - self.window_seconds

        try:
            pipe = redis_manager.client.pipeline()
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Add current request
            pipe.zadd(key, {f"{now}": now})
            # Count requests in window
            pipe.zcard(key)
            # Set expiry on the key
            pipe.expire(key, self.window_seconds)
            results = await pipe.execute()

            request_count = results[2]

            if request_count > limit:
                retry_after = self.window_seconds
                logger.warning(
                    "Rate limit exceeded: ip=%s path=%s count=%d limit=%d",
                    client_ip, path, request_count, limit,
                )
                return Response(
                    content='{"success":false,"error":"Rate limit exceeded. Try again later.","status_code":429}',
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now + self.window_seconds)),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - request_count))
            response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))
            return response

        except Exception:
            # If Redis is down, allow the request through (fail-open)
            logger.warning("Rate limiter Redis error — allowing request through")
            return await call_next(request)
