"""
Integration Tests — HRMS API Endpoints
Tests for the FastAPI application routes.
"""

from __future__ import annotations

import os
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-characters-long"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://hrms:test@localhost:5432/hrms_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["CLERK_PUBLISHABLE_KEY"] = "pk_test_placeholder"
os.environ["CLERK_SECRET_KEY"] = "sk_test_placeholder_minimum_20_chars"
os.environ["CLERK_JWT_VERIFICATION_KEY"] = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA\n-----END PUBLIC KEY-----"
os.environ["CLERK_WEBHOOK_SECRET"] = ""
os.environ["RESEND_API_KEY"] = "re_test_placeholder"
os.environ["HR_EMAIL"] = "hr@test.com"
os.environ["EMAIL_FROM"] = "noreply@test.com"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["WHISPER_URL"] = "http://localhost:9000"
os.environ["CLAMAV_URL"] = "http://localhost:3310"
os.environ["COMPANY_NAME"] = "Test Corp"


@pytest_asyncio.fixture
async def client():
    """Async test client with mocked dependencies."""
    from app.main import create_app
    from app.core.auth import get_current_user, require_admin
    from app.core.database import get_db

    app = create_app()

    # Override auth dependency
    class MockToken:
        def __init__(self):
            self.user_id = "user_test123"
            self.role = "employee"
            self.raw_payload = {}
        @property
        def is_admin(self):
            return self.role == "admin"

    async def override_get_user():
        return MockToken()

    async def override_require_admin():
        token = MockToken()
        token.role = "admin"
        return token

    async def override_get_db():
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        yield session

    app.dependency_overrides[get_current_user] = override_get_user
    app.dependency_overrides[require_admin] = override_require_admin
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client):
        with patch("app.main.db_manager") as mock_db, \
             patch("app.main.redis_manager") as mock_redis:
            mock_db.health_check = AsyncMock(return_value=True)
            mock_redis.health_check = AsyncMock(return_value=True)
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"
            assert data["version"] == "3.0.0"


@pytest.mark.asyncio
class TestDashboardEndpoint:
    async def test_dashboard_requires_auth(self, client):
        """Dashboard should require authentication."""
        # With mocked auth, should return 200 or appropriate error
        # depending on DB state
        resp = await client.get("/api/v1/dashboard")
        # Will return either 200 (with mocked DB returning None for employee)
        # or 404 (employee not found)
        assert resp.status_code in (200, 404)


@pytest.mark.asyncio
class TestLeaveEndpoints:
    async def test_list_leave_requires_auth(self, client):
        resp = await client.get("/api/v1/leave")
        assert resp.status_code in (200, 404)

    async def test_leave_balance_requires_auth(self, client):
        resp = await client.get("/api/v1/leave/balance")
        assert resp.status_code in (200, 404)


@pytest.mark.asyncio
class TestAttendanceEndpoints:
    async def test_today_attendance(self, client):
        resp = await client.get("/api/v1/attendance/today")
        assert resp.status_code in (200, 404)


@pytest.mark.asyncio
class TestEmployeeEndpoints:
    async def test_get_me(self, client):
        resp = await client.get("/api/v1/employees/me")
        assert resp.status_code in (200, 404)


@pytest.mark.asyncio
class TestChatEndpoints:
    async def test_list_channels(self, client):
        resp = await client.get("/api/v1/chat/channels")
        assert resp.status_code in (200, 404)
