"""
HRMS Nudge Service
Proactive nudge generation for employees.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.leave import LeaveBalance
from app.models.nudges import Nudge

logger = logging.getLogger(__name__)


async def create_nudge(
    db: AsyncSession,
    employee_id: UUID,
    message: str,
    nudge_type: str,
) -> Nudge:
    """Create a new nudge for an employee."""
    nudge = Nudge(employee_id=employee_id, message=message, type=nudge_type)
    db.add(nudge)
    return nudge


async def get_unread_nudges(db: AsyncSession, employee_id: UUID) -> list[Nudge]:
    """Get all unread nudges for an employee."""
    result = await db.execute(
        select(Nudge)
        .where(Nudge.employee_id == employee_id, Nudge.read == False)
        .order_by(Nudge.created_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())


async def mark_nudge_read(db: AsyncSession, nudge_id: UUID, employee_id: UUID) -> bool:
    """Mark a nudge as read."""
    result = await db.execute(
        select(Nudge).where(Nudge.id == nudge_id, Nudge.employee_id == employee_id)
    )
    nudge = result.scalar_one_or_none()
    if not nudge:
        return False
    nudge.read = True
    return True


async def generate_leave_lapse_nudges() -> None:
    """Check for employees with leave balances about to lapse."""
    from app.core.database import db_manager

    async with db_manager.get_session_factory()() as db:
        today = date.today()
        year_end = date(today.year, 12, 31)
        days_left = (year_end - today).days

        if days_left > 60:
            return  # Only start nudging within 60 days of year end

        result = await db.execute(
            select(LeaveBalance).where(
                LeaveBalance.year == today.year,
                LeaveBalance.leave_type.in_(["paid", "sick"]),
            )
        )
        balances = result.scalars().all()

        for balance in balances:
            remaining = balance.total - balance.used
            if remaining > 0:
                # Check if nudge already sent today
                existing = await db.execute(
                    select(Nudge).where(
                        Nudge.employee_id == balance.employee_id,
                        Nudge.type == "leave_lapse",
                        func.date(Nudge.created_at) == today,
                    )
                )
                if not existing.scalar_one_or_none():
                    await create_nudge(
                        db=db,
                        employee_id=balance.employee_id,
                        message=f"You have {remaining} {balance.leave_type} leave days expiring Dec 31. Plan your time off before they lapse.",
                        nudge_type="leave_lapse",
                    )

        await db.commit()


async def generate_missed_checkout_nudges() -> None:
    """Check for employees who checked in but didn't check out yesterday."""
    from app.core.database import db_manager

    async with db_manager.get_session_factory()() as db:
        yesterday = date.today() - timedelta(days=1)
        result = await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.date == yesterday,
                AttendanceRecord.check_in.isnot(None),
                AttendanceRecord.check_out.is_(None),
            )
        )
        records = result.scalars().all()

        for record in records:
            existing = await db.execute(
                select(Nudge).where(
                    Nudge.employee_id == record.employee_id,
                    Nudge.type == "missed_checkout",
                    func.date(Nudge.created_at) == date.today(),
                )
            )
            if not existing.scalar_one_or_none():
                await create_nudge(
                    db=db,
                    employee_id=record.employee_id,
                    message="Looks like you didn't check out yesterday. Did you work late? Tap to log your check-out time.",
                    nudge_type="missed_checkout",
                )

        await db.commit()


async def run_nudge_checks() -> None:
    """APScheduler job: run all nudge checks."""
    logger.info("Running nudge checks")
    await generate_leave_lapse_nudges()
    await generate_missed_checkout_nudges()
    logger.info("Nudge checks completed")
