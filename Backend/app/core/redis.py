"""
HRMS Redis Configuration
Async Redis client with connection pooling, health checks, and typed helpers.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Manages async Redis connection pool and provides typed helpers."""

    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None
        self._settings = None

    def _get_settings(self):
        """Lazy-load settings to avoid import-time crashes."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        settings = self._get_settings()
        self._pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=settings.REDIS_DECODER_RESPONSES,
        )
        self._client = Redis(connection_pool=self._pool)
        logger.info("Redis connection pool created: max_connections=%d", settings.REDIS_MAX_CONNECTIONS)

    async def disconnect(self) -> None:
        """Close all Redis connections."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._pool = None
            logger.info("Redis connections closed")

    async def health_check(self) -> bool:
        """Verify Redis connectivity."""
        if not self._client:
            return False
        try:
            return await self._client.ping()
        except (RedisConnectionError, RedisTimeoutError):
            logger.exception("Redis health check failed")
            return False

    @property
    def client(self) -> Redis:
        if not self._client:
            raise RuntimeError("Redis not initialized. Call connect() first.")
        return self._client

    # ── Typed Helpers ────────────────────────────────────────────

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Get a JSON-serialized value from Redis."""
        try:
            data = await self.client.get(key)
            if data is None:
                return None
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return json.loads(data)
        except (RedisConnectionError, RedisTimeoutError, json.JSONDecodeError):
            return None

    async def set_json(self, key: str, value: dict[str, Any], ttl: int = 60) -> bool:
        """Set a JSON-serialized value in Redis with TTL."""
        try:
            await self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except (RedisConnectionError, RedisTimeoutError):
            logger.warning("Failed to set Redis key: %s", key)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern, count=100):
                keys.append(key)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except (RedisConnectionError, RedisTimeoutError):
            logger.warning("Failed to delete Redis pattern: %s", pattern)
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        try:
            return bool(await self.client.exists(key))
        except (RedisConnectionError, RedisTimeoutError):
            return False

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set a string value with TTL."""
        try:
            await self.client.setex(key, ttl, value)
            return True
        except (RedisConnectionError, RedisTimeoutError):
            return False

    async def get(self, key: str) -> str | None:
        """Get a string value."""
        try:
            val = await self.client.get(key)
            if isinstance(val, bytes):
                return val.decode("utf-8")
            return val
        except (RedisConnectionError, RedisTimeoutError):
            return None

    async def increment(self, key: str, ttl: int = 60) -> int:
        """Increment a counter key, setting TTL if new."""
        try:
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = await pipe.execute()
            return int(results[0])
        except (RedisConnectionError, RedisTimeoutError):
            return 0

    # ── Pub/Sub ──────────────────────────────────────────────────

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a Redis channel."""
        try:
            return await self.client.publish(channel, message)
        except (RedisConnectionError, RedisTimeoutError):
            logger.warning("Failed to publish to channel: %s", channel)
            return 0

    def pubsub(self) -> aioredis.client.PubSub:
        """Get a PubSub instance."""
        if not self._client:
            raise RuntimeError("Redis not initialized.")
        return self.client.pubsub()


redis_manager = RedisManager()


async def get_redis() -> Redis:
    """FastAPI dependency that yields the Redis client."""
    return redis_manager.client
