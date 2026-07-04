"""
HRMS Nudges Router
Proactive notification system for employees.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenPayload
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.employee import Employee
from app.models.nudges import Nudge
from app.schemas.nudge import NudgeListResponse, NudgeResponse
from app.services.nudge_service import mark_nudge_read

router = APIRouter(prefix="/nudges", tags=["Nudges"])


@router.get("", response_model=NudgeListResponse)
async def list_nudges(
    unread_only: bool = False,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NudgeListResponse:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    query = select(Nudge).where(Nudge.employee_id == employee.id)
    if unread_only:
        query = query.where(Nudge.read == False)
    query = query.order_by(Nudge.created_at.desc()).limit(50)

    nudges_result = await db.execute(query)
    nudges = nudges_result.scalars().all()

    unread_count_result = await db.execute(
        select(func.count(Nudge.id)).where(
            Nudge.employee_id == employee.id, Nudge.read == False
        )
    )
    unread_count = unread_count_result.scalar() or 0

    return NudgeListResponse(
        nudges=[
            NudgeResponse(
                id=n.id, message=n.message, type=n.type,
                read=n.read, created_at=n.created_at,
            )
            for n in nudges
        ],
        unread_count=unread_count,
    )


@router.patch("/{nudge_id}/read")
async def mark_as_read(
    nudge_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    success = await mark_nudge_read(db, nudge_id, employee.id)
    if not success:
        raise NotFoundError("Nudge")

    return {"success": True}
