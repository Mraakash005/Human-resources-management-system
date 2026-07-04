"""
HRMS Clerk Webhook Handler
Handles Clerk events: user creation, update, deletion, role changes.
Implements signature verification, replay protection, and idempotency.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.core.config import get_settings
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Replay protection: event IDs expire after 5 minutes
REPLAY_WINDOW_SECONDS = 300


def verify_clerk_webhook_signature(
    payload: bytes,
    svix_id: str,
    svix_timestamp: str,
    svix_signature: str,
) -> bool:
    """
    Verify Clerk webhook signature using Svix format.
    Clerk signs webhooks with HMAC-SHA256.
    Format: v1,<base64-encoded-signature>
    """
    settings = get_settings()
    if not settings.CLERK_WEBHOOK_SECRET:
        logger.warning("CLERK_WEBHOOK_SECRET not configured — skipping signature verification")
        return True

    to_sign = f"{svix_id}.{svix_timestamp}.{payload.decode('utf-8')}"
    secret_bytes = settings.CLERK_WEBHOOK_SECRET.replace("whsec_", "")

    try:
        import base64
        key = base64.b64decode(secret_bytes)
        expected = hmac.HMAC(key, to_sign.encode("utf-8"), hashlib.sha256).digest()
        expected_b64 = f"v1,{base64.b64encode(expected).decode('utf-8')}"
        return hmac.compare_digest(expected_b64, svix_signature)
    except Exception:
        logger.exception("Webhook signature verification failed")
        return False


async def check_replay_protection(event_id: str) -> bool:
    """
    Check if an event has been processed before (replay protection).
    Returns True if the event is new, False if it's a replay.
    """
    cache_key = f"webhook_event:{event_id}"
    exists = await redis_manager.exists(cache_key)
    if exists:
        return False
    await redis_manager.setex(cache_key, REPLAY_WINDOW_SECONDS, "1")
    return True


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(..., alias="svix-id"),
    svix_timestamp: str = Header(..., alias="svix-timestamp"),
    svix_signature: str = Header(..., alias="svix-signature"),
) -> dict[str, str]:
    """
    Handle Clerk webhook events.
    - Verifies Svix signature
    - Prevents replay attacks
    - Processes user CRUD and metadata changes
    """
    body = await request.body()

    # 1. Signature verification
    if not verify_clerk_webhook_signature(body, svix_id, svix_timestamp, svix_signature):
        logger.warning("Invalid webhook signature from svix_id=%s", svix_id)
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Replay protection
    if not await check_replay_protection(svix_id):
        logger.info("Replay detected for svix_id=%s — ignoring", svix_id)
        return {"status": "already_processed"}

    # 3. Parse event
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("type")
    data = event.get("data", {})
    logger.info("Clerk webhook received: type=%s, id=%s", event_type, svix_id)

    # 4. Route to handler
    try:
        if event_type == "user.created":
            await _handle_user_created(data)
        elif event_type == "user.updated":
            await _handle_user_updated(data)
        elif event_type == "user.deleted":
            await _handle_user_deleted(data)
        elif event_type == "session.created":
            logger.info("Session created for user %s", data.get("user_id"))
        elif event_type == "session.ended":
            logger.info("Session ended for user %s", data.get("user_id"))
        else:
            logger.info("Unhandled Clerk event type: %s", event_type)
    except Exception:
        logger.exception("Error processing Clerk event: %s", event_type)
        # Don't raise — webhook should return 200 to prevent retries
        # for events we intentionally don't handle

    return {"status": "processed"}


async def _handle_user_created(data: dict[str, Any]) -> None:
    """Handle user.created event — create employee record if not exists."""
    from app.models.employee import Employee
    from app.models.leave import LeaveBalance
    from app.core.config import get_settings as _gs

    settings = _gs()
    clerk_user_id = data.get("id")
    email_addresses = data.get("email_addresses", [])
    primary_email = next(
        (e["email_address"] for e in email_addresses if e.get("id") == data.get("primary_email_address_id")),
        email_addresses[0]["email_address"] if email_addresses else None,
    )
    if not primary_email:
        logger.warning("No email found for Clerk user %s", clerk_user_id)
        return

    metadata = data.get("public_metadata", {}) or {}
    role = metadata.get("role", "employee")
    name = data.get("first_name", "") or ""
    if data.get("last_name"):
        name = f"{name} {data['last_name']}".strip()
    if not name:
        name = primary_email.split("@")[0]

    # Use get_db dependency pattern for standalone async operations
    from app.core.database import db_manager
    session_factory = db_manager.get_session_factory()
    async with session_factory() as db:
        try:
            # Check if employee already exists
            existing = await db.execute(
                select(Employee).where(Employee.clerk_id == clerk_user_id)
            )
            if existing.scalar_one_or_none():
                logger.info("Employee already exists for Clerk user %s", clerk_user_id)
                return

            # Generate employee ID
            count_result = await db.execute(select(Employee))
            count = len(count_result.scalars().all())
            emp_id = f"EMP-{count + 1:04d}"

            employee = Employee(
                clerk_id=clerk_user_id,
                employee_id=emp_id,
                name=name,
                email=primary_email,
                role=role,
            )
            db.add(employee)
            await db.flush()

            # Initialize leave balances
            from datetime import date as _date
            year = _date.today().year
            for leave_type, default in [
                ("paid", settings.LEAVE_PAID_DEFAULT),
                ("sick", settings.LEAVE_SICK_DEFAULT),
                ("unpaid", settings.LEAVE_UNPAID_DEFAULT),
                ("bereavement", settings.LEAVE_BEREAVEMENT_DEFAULT),
            ]:
                db.add(LeaveBalance(
                    employee_id=employee.id,
                    year=year,
                    leave_type=leave_type,
                    total=default,
                ))

            await db.commit()
            logger.info("Created employee %s for Clerk user %s", emp_id, clerk_user_id)

        except Exception:
            await db.rollback()
            logger.exception("Failed to create employee for Clerk user %s", clerk_user_id)


async def _handle_user_updated(data: dict[str, Any]) -> None:
    """Handle user.updated event — sync role changes to employee record."""
    from app.models.employee import Employee
    from app.services.audit import log_action

    clerk_user_id = data.get("id")
    metadata = data.get("public_metadata", {}) or {}
    new_role = metadata.get("role", "employee")

    from app.core.database import db_manager
    session_factory = db_manager.get_session_factory()
    async with session_factory() as db:
        try:
            result = await db.execute(
                select(Employee).where(Employee.clerk_id == clerk_user_id)
            )
            employee = result.scalar_one_or_none()
            if not employee:
                logger.warning("No employee found for Clerk user %s", clerk_user_id)
                return

            old_role = employee.role
            if old_role != new_role:
                employee.role = new_role
                # Also sync is_active based on data
                if "deleted" in data or data.get("banned"):
                    employee.is_active = False

                # Sync name changes
                name = data.get("first_name", "") or ""
                if data.get("last_name"):
                    name = f"{name} {data['last_name']}".strip()
                if name and name != employee.name:
                    employee.name = name

                # Sync email changes
                email_addresses = data.get("email_addresses", [])
                primary_email = next(
                    (e["email_address"] for e in email_addresses if e.get("id") == data.get("primary_email_address_id")),
                    None,
                )
                if primary_email and primary_email != employee.email:
                    employee.email = primary_email

                await db.commit()

                # Invalidate role cache
                await redis_manager.client.delete(f"role_verified:{clerk_user_id}")

                # Audit log
                await log_action(
                    db=db,
                    actor_id=employee.id,
                    action="employee_role_changed",
                    entity_type="employee",
                    entity_id=employee.id,
                    metadata={"old_role": old_role, "new_role": new_role},
                )
                logger.info("Updated employee %s: role %s → %s", employee.employee_id, old_role, new_role)
            else:
                # Name/email sync without role change
                name = data.get("first_name", "") or ""
                if data.get("last_name"):
                    name = f"{name} {data['last_name']}".strip()
                if name:
                    employee.name = name
                email_addresses = data.get("email_addresses", [])
                primary_email = next(
                    (e["email_address"] for e in email_addresses if e.get("id") == data.get("primary_email_address_id")),
                    None,
                )
                if primary_email:
                    employee.email = primary_email
                await db.commit()

        except Exception:
            await db.rollback()
            logger.exception("Failed to update employee for Clerk user %s", clerk_user_id)


async def _handle_user_deleted(data: dict[str, Any]) -> None:
    """Handle user.deleted event — soft-delete employee (set is_active=False)."""
    from app.models.employee import Employee

    clerk_user_id = data.get("id")

    from app.core.database import db_manager
    session_factory = db_manager.get_session_factory()
    async with session_factory() as db:
        try:
            result = await db.execute(
                select(Employee).where(Employee.clerk_id == clerk_user_id)
            )
            employee = result.scalar_one_or_none()
            if employee:
                employee.is_active = False
                await db.commit()
                # Invalidate caches
                await redis_manager.client.delete(f"role_verified:{clerk_user_id}")
                await redis_manager.delete_pattern(f"dashboard:{clerk_user_id}:*")
                logger.info("Deactivated employee %s (Clerk user deleted)", employee.employee_id)
        except Exception:
            await db.rollback()
            logger.exception("Failed to deactivate employee for Clerk user %s", clerk_user_id)
