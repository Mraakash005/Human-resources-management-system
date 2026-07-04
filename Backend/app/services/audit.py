"""
HRMS Audit Service
Immutable audit logging for all mutations.
Every admin action writes to audit_log with old/new values.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    actor_id: UUID | None,
    action: str,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    """
    Write an immutable audit log entry.
    Called within the same transaction as the mutation for atomicity.
    """
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        action_metadata=metadata,
        ip_address=ip_address,
    )
    db.add(entry)
    logger.info(
        "Audit: action=%s actor=%s entity=%s/%s",
        action,
        actor_id,
        entity_type,
        entity_id,
    )


async def get_audit_logs(
    db: AsyncSession,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    actor_id: UUID | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Query audit logs with filters."""
    from sqlalchemy import select

    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    if action:
        query = query.where(AuditLog.action == action)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_audit_logs(
    db: AsyncSession,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
) -> int:
    """Count audit logs with optional filters."""
    from sqlalchemy import func, select

    query = select(func.count(AuditLog.id))
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    result = await db.execute(query)
    return result.scalar() or 0
