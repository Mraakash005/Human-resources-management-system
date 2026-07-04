"""
HRMS Test Configuration
Shared fixtures for unit and integration tests.
"""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Set test environment before any app imports
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-characters-long"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://hrms:test@localhost:5432/hrms_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["CLERK_PUBLISHABLE_KEY"] = "pk_test_placeholder"
os.environ["CLERK_SECRET_KEY"] = "sk_test_placeholder_minimum_20_chars"
os.environ["CLERK_JWT_VERIFICATION_KEY"] = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z3VS5JJcds3xfn/ygWy\nF01P8cCX0sD1YkP4PF0Z0VBt8D7bF0N7+Y0I2e0I5c9K5K5K5K5K5K5K5K5K5K5K\n5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K\n5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K\n5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K\n5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K\n5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K\n5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K5K\nQIDAQAB\n-----END PUBLIC KEY-----"
os.environ["CLERK_WEBHOOK_SECRET"] = ""
os.environ["RESEND_API_KEY"] = "re_test_placeholder"
os.environ["HR_EMAIL"] = "hr@test.com"
os.environ["EMAIL_FROM"] = "noreply@test.com"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["WHISPER_URL"] = "http://localhost:9000"
os.environ["CLAMAV_URL"] = "http://localhost:3310"
os.environ["COMPANY_NAME"] = "Test Corp"


# ── Token Mocking ──────────────────────────────────────────────


class MockTokenPayload:
    """Mock TokenPayload for testing."""

    def __init__(self, user_id: str = "user_test123", role: str = "employee"):
        self.user_id = user_id
        self.role = role
        self.raw_payload = {"sub": user_id, "metadata": {"role": role}}

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@pytest.fixture
def employee_token() -> MockTokenPayload:
    return MockTokenPayload(user_id="user_employee1", role="employee")


@pytest.fixture
def admin_token() -> MockTokenPayload:
    return MockTokenPayload(user_id="user_admin1", role="admin")


@pytest.fixture
def mock_uuid() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def mock_employee_id() -> uuid.UUID:
    return uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture
def mock_leave_id() -> uuid.UUID:
    return uuid.UUID("11111111-2222-3333-4444-555555555555")


# ── Database Fixtures ──────────────────────────────────────────


@pytest_asyncio.fixture
async def mock_db_session():
    """Mock AsyncSession for unit tests."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


# ── Redis Fixtures ─────────────────────────────────────────────


@pytest.fixture
def mock_redis():
    """Mock Redis manager for unit tests."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=False)
    redis.delete_pattern = AsyncMock(return_value=0)
    redis.get_json = AsyncMock(return_value=None)
    redis.set_json = AsyncMock(return_value=True)
    redis.increment = AsyncMock(return_value=1)
    redis.publish = AsyncMock(return_value=0)
    return redis
