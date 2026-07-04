"""
HRMS Authentication
Clerk JWT RS256 verification, role extraction, and stale token protection.
Every API request is verified. Admin routes get real-time role validation.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def _parse_pem_key(raw: str) -> str:
    """Normalize Clerk PEM key — handle escaped newlines from .env."""
    key = raw.strip()
    if "\\n" in key and "\n" not in key:
        key = key.replace("\\n", "\n")
    return key


_CLERK_PEM_KEY: str | None = None


def _get_clerk_pem_key() -> str:
    """Lazy-load Clerk PEM key to avoid import-time crashes."""
    global _CLERK_PEM_KEY
    if _CLERK_PEM_KEY is None:
        settings = get_settings()
        _CLERK_PEM_KEY = _parse_pem_key(settings.CLERK_JWT_VERIFICATION_KEY)
    return _CLERK_PEM_KEY


class TokenPayload:
    """Typed representation of a decoded JWT payload."""

    __slots__ = ("user_id", "role", "raw_payload")

    def __init__(self, user_id: str, role: str, raw_payload: dict[str, Any]) -> None:
        self.user_id = user_id
        self.role = role
        self.raw_payload = raw_payload

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def decode_jwt(token: str) -> TokenPayload:
    """Decode and verify a Clerk JWT token."""
    try:
        payload = jwt.decode(
            token,
            _get_clerk_pem_key(),
            algorithms=["RS256"],
            options={"verify_aud": False, "verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid JWT: %s", exc)
        raise InvalidTokenError(str(exc))

    user_id = payload.get("sub", "")
    if not user_id:
        raise InvalidTokenError("Token missing subject claim")

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    role = metadata.get("role", "employee")

    if role not in ("admin", "employee"):
        role = "employee"

    return TokenPayload(user_id=user_id, role=role, raw_payload=payload)


async def verify_admin_role_live(clerk_user_id: str) -> bool:
    """
    Real-time role verification via Clerk API.
    Catches stale tokens for demoted admins.
    Result cached in Redis for 2 minutes.
    """
    settings = get_settings()
    cache_key = f"role_verified:{clerk_user_id}"
    cached = await redis_manager.get(cache_key)
    if cached is not None:
        return cached == "admin"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.clerk.com/v1/users/{clerk_user_id}",
                headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
            )
        if resp.status_code != 200:
            logger.warning("Clerk getUser() returned %d for %s", resp.status_code, clerk_user_id)
            return False

        user_data = resp.json()
        public_metadata = user_data.get("public_metadata", {})
        role = public_metadata.get("role", "employee")

        await redis_manager.setex(cache_key, settings.CACHE_ROLE_VERIFICATION_TTL, role)
        return role == "admin"

    except Exception:
        logger.exception("Failed to verify admin role via Clerk API for %s", clerk_user_id)
        # If Clerk is unreachable, use JWT role (fail-open for availability)
        return False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenPayload:
    """
    FastAPI dependency: extract and validate the current user from JWT.
    Returns a TokenPayload with user_id and role.
    """
    if not credentials:
        raise AuthenticationError("Missing authorization header")

    token = credentials.credentials
    if not token:
        raise AuthenticationError("Empty authorization token")

    return decode_jwt(token)


async def require_admin(
    user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    FastAPI dependency: require admin role.
    Performs real-time Clerk verification to catch stale JWTs.
    """
    if not user.is_admin:
        # Still verify via Clerk to be absolutely sure
        live_admin = await verify_admin_role_live(user.user_id)
        if not live_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        user.role = "admin"
        return user

    # Even if JWT says admin, verify via Clerk for stale token protection
    live_admin = await verify_admin_role_live(user.user_id)
    if not live_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access revoked. Please sign in again.",
        )

    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenPayload | None:
    """FastAPI dependency: extract user if present, return None if not."""
    if not credentials:
        return None
    try:
        return decode_jwt(credentials.credentials)
    except (AuthenticationError, InvalidTokenError, TokenExpiredError):
        return None
