"""
Unit Tests — HRMS Cache Service
Tests for Redis cache operations.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.cache import CacheService


class TestCacheService:
    @pytest.fixture
    def cache(self):
        with patch("app.services.cache.redis_manager") as mock_redis:
            mock_settings = type('MockSettings', (), {
                'CACHE_DASHBOARD_TTL': 300,
                'CACHE_CHATBOT_CONTEXT_TTL': 300,
                'CACHE_LEAVE_ADVISOR_TTL': 300,
                'CACHE_HEATMAP_TTL': 300,
                'CACHE_ROLE_VERIFICATION_TTL': 120,
            })()
            with patch("app.services.cache.get_settings", return_value=mock_settings):
                service = CacheService()
                yield service, mock_redis

    @pytest.mark.asyncio
    async def test_get_dashboard_hit(self, cache):
        service, mock_redis = cache
        mock_redis.get_json = AsyncMock(return_value={"role": "employee", "data": {}})
        result = await service.get_dashboard("user1", "employee")
        assert result is not None
        assert result["role"] == "employee"

    @pytest.mark.asyncio
    async def test_get_dashboard_miss(self, cache):
        service, mock_redis = cache
        mock_redis.get_json = AsyncMock(return_value=None)
        result = await service.get_dashboard("user1", "employee")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_dashboard(self, cache):
        service, mock_redis = cache
        mock_redis.set_json = AsyncMock(return_value=True)
        await service.set_dashboard("user1", "employee", {"data": "test"})
        mock_redis.set_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_leave_balance(self, cache):
        service, mock_redis = cache
        # The invalidate_leave_balance method uses redis_manager.client.delete() directly
        mock_redis.client = MagicMock()
        mock_redis.client.delete = AsyncMock(return_value=1)
        await service.invalidate_leave_balance("emp123")
        mock_redis.client.delete.assert_called_once_with("leave_balance:emp123")
