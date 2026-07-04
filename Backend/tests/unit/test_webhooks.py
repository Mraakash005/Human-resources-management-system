"""
Unit Tests — HRMS Clerk Webhook Handler
Tests for signature verification, replay protection, event routing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from app.routers.webhooks import (
    check_replay_protection,
    verify_clerk_webhook_signature,
)


class TestSignatureVerification:
    def test_valid_signature(self):
        payload = b'{"type":"user.created","data":{}}'
        svix_id = "msg_test123"
        svix_timestamp = "1234567890"
        # Use a valid base64 secret
        secret_bytes = b"testsecret12345678"
        secret = f"whsec_{base64.b64encode(secret_bytes).decode('utf-8')}"

        to_sign = f"{svix_id}.{svix_timestamp}.{payload.decode('utf-8')}"
        expected = hmac.new(secret_bytes, to_sign.encode("utf-8"), hashlib.sha256).digest()
        signature = f"v1,{base64.b64encode(expected).decode('utf-8')}"

        mock_settings = type('MockSettings', (), {'CLERK_WEBHOOK_SECRET': secret})()
        with patch("app.routers.webhooks.get_settings", return_value=mock_settings):
            result = verify_clerk_webhook_signature(payload, svix_id, svix_timestamp, signature)
            assert result is True

    def test_invalid_signature(self):
        payload = b'{"type":"user.created"}'
        mock_settings = type('MockSettings', (), {'CLERK_WEBHOOK_SECRET': 'whsec_testsecret12345678'})()
        with patch("app.routers.webhooks.get_settings", return_value=mock_settings):
            result = verify_clerk_webhook_signature(payload, "msg_1", "123", "v1,invalidsig")
            assert result is False

    def test_no_secret_configured(self):
        """When no webhook secret is configured, skip verification (dev mode)."""
        mock_settings = type('MockSettings', (), {'CLERK_WEBHOOK_SECRET': ''})()
        with patch("app.routers.webhooks.get_settings", return_value=mock_settings):
            result = verify_clerk_webhook_signature(b"test", "msg_1", "123", "v1,anything")
            assert result is True


class TestReplayProtection:
    @pytest.mark.asyncio
    async def test_new_event_passes(self):
        with patch("app.routers.webhooks.redis_manager") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=False)
            mock_redis.setex = AsyncMock(return_value=True)
            result = await check_replay_protection("msg_new123")
            assert result is True

    @pytest.mark.asyncio
    async def test_replay_blocked(self):
        with patch("app.routers.webhooks.redis_manager") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=True)
            result = await check_replay_protection("msg_replay123")
            assert result is False
