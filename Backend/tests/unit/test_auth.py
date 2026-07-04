"""
Unit Tests — HRMS Authentication
Tests for JWT decoding, role extraction, and token payload.
"""

from __future__ import annotations

import pytest

from app.core.auth import TokenPayload, _parse_pem_key


class TestTokenPayload:
    def test_employee_role(self):
        payload = TokenPayload(user_id="user_123", role="employee", raw_payload={})
        assert payload.user_id == "user_123"
        assert payload.role == "employee"
        assert payload.is_admin is False

    def test_admin_role(self):
        payload = TokenPayload(user_id="user_admin", role="admin", raw_payload={})
        assert payload.is_admin is True

    def test_raw_payload_preserved(self):
        raw = {"sub": "user_123", "metadata": {"role": "admin"}}
        payload = TokenPayload(user_id="user_123", role="admin", raw_payload=raw)
        assert payload.raw_payload == raw


class TestParsePemKey:
    def test_normal_pem(self):
        key = "-----BEGIN PUBLIC KEY-----\nMIIB...\n-----END PUBLIC KEY-----"
        result = _parse_pem_key(key)
        assert "\n" in result

    def test_escaped_newlines(self):
        key = "-----BEGIN PUBLIC KEY-----\\nMIIB...\\n-----END PUBLIC KEY-----"
        result = _parse_pem_key(key)
        assert "\n" in result
        assert "\\n" not in result

    def test_strips_whitespace(self):
        key = "  -----BEGIN PUBLIC KEY-----  "
        result = _parse_pem_key(key)
        assert result == "-----BEGIN PUBLIC KEY-----"
