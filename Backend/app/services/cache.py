"""
HRMS Cache Service
Redis caching with TTL, invalidation patterns, and typed helpers.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import get_settings
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)


class CacheService:
    """Typed cache helpers for HRMS modules."""

    def __init__(self) -> None:
        self._settings = None

    def _get_settings(self):
        """Lazy-load settings to avoid import-time crashes."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @staticmethod
    async def get_dashboard(user_id: str, role: str) -> dict[str, Any] | None:
        key = f"dashboard:{user_id}:{role}"
        return await redis_manager.get_json(key)

    async def set_dashboard(self, user_id: str, role: str, data: dict[str, Any]) -> bool:
        key = f"dashboard:{user_id}:{role}"
        settings = self._get_settings()
        return await redis_manager.set_json(key, data, ttl=settings.CACHE_DASHBOARD_TTL)

    @staticmethod
    async def invalidate_dashboard(user_id: str) -> None:
        await redis_manager.delete_pattern(f"dashboard:{user_id}:*")
        await redis_manager.delete_pattern("dashboard:*:admin")

    @staticmethod
    async def get_leave_balance(employee_id: str) -> dict[str, Any] | None:
        key = f"leave_balance:{employee_id}"
        return await redis_manager.get_json(key)

    @staticmethod
    async def set_leave_balance(employee_id: str, data: dict[str, Any]) -> bool:
        key = f"leave_balance:{employee_id}"
        return await redis_manager.set_json(key, data, ttl=300)

    @staticmethod
    async def invalidate_leave_balance(employee_id: str) -> None:
        await redis_manager.client.delete(f"leave_balance:{employee_id}")

    @staticmethod
    async def get_chatbot_context(user_id: str) -> dict[str, Any] | None:
        key = f"chatbot_context:{user_id}"
        return await redis_manager.get_json(key)

    async def set_chatbot_context(self, user_id: str, data: dict[str, Any]) -> bool:
        key = f"chatbot_context:{user_id}"
        settings = self._get_settings()
        return await redis_manager.set_json(key, data, ttl=settings.CACHE_CHATBOT_CONTEXT_TTL)

    @staticmethod
    async def get_leave_advisor(user_id: str, date_str: str) -> list | None:
        key = f"leave_advisor:{user_id}:{date_str}"
        cached = await redis_manager.get(key)
        if cached:
            try:
                return json.loads(cached) if isinstance(cached, str) else cached
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    async def set_leave_advisor(self, user_id: str, date_str: str, data: list) -> bool:
        key = f"leave_advisor:{user_id}:{date_str}"
        settings = self._get_settings()
        return await redis_manager.set_json(key, data, ttl=settings.CACHE_LEAVE_ADVISOR_TTL)

    @staticmethod
    async def get_heatmap(employee_id: str, year: int) -> dict | None:
        key = f"heatmap:{employee_id}:{year}"
        return await redis_manager.get_json(key)

    async def set_heatmap(self, employee_id: str, year: int, data: dict) -> bool:
        key = f"heatmap:{employee_id}:{year}"
        settings = self._get_settings()
        return await redis_manager.set_json(key, data, ttl=settings.CACHE_HEATMAP_TTL)

    @staticmethod
    async def check_attendance_lock(employee_id: str, date_str: str) -> bool:
        """Redis lock to prevent double check-in."""
        key = f"attendance:checkin:{employee_id}:{date_str}"
        return await redis_manager.exists(key)

    @staticmethod
    async def set_attendance_lock(employee_id: str, date_str: str, check_in_time: str) -> bool:
        key = f"attendance:checkin:{employee_id}:{date_str}"
        return await redis_manager.setex(key, 86400, check_in_time)

    @staticmethod
    async def get_role_cache(clerk_user_id: str) -> str | None:
        key = f"role_verified:{clerk_user_id}"
        return await redis_manager.get(key)

    async def set_role_cache(self, clerk_user_id: str, role: str) -> bool:
        key = f"role_verified:{clerk_user_id}"
        settings = self._get_settings()
        return await redis_manager.setex(key, settings.CACHE_ROLE_VERIFICATION_TTL, role)


cache_service = CacheService()
