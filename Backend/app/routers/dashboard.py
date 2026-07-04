"""
HRMS Dashboard Router
Aggregated dashboard endpoint — single call returns everything.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenPayload
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.attendance import AttendanceRecord
from app.models.burnout import BurnoutAlert
from app.models.employee import Employee
from app.models.leave import LeaveBalance, LeaveRequest
from app.schemas.dashboard import (
    AdminDashboard,
    DashboardAttendance,
    DashboardBurnoutAlert,
    DashboardLeaveBalance,
    DashboardPendingLeave,
    DashboardRecentActivity,
    EmployeeDashboard,
)
from app.services.cache import cache_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


async def _get_attendance_summary(db: AsyncSession, employee_id) -> DashboardAttendance:
    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date == date.today(),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        return DashboardAttendance(status="not_checked_in")
    return DashboardAttendance(
        status=record.status,
        check_in=record.check_in.isoformat() if record.check_in else None,
        check_out=record.check_out.isoformat() if record.check_out else None,
        duration_hours=float(record.duration_hours) if record.duration_hours else None,
        method=record.check_in_method,
    )


async def _get_leave_balance(db: AsyncSession, employee_id) -> DashboardLeaveBalance:
    result = await db.execute(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == date.today().year,
        )
    )
    balances = {b.leave_type: b for b in result.scalars().all()}

    def _make(bt: str) -> dict[str, int]:
        b = balances.get(bt)
        if b:
            return {"total": b.total, "used": b.used, "remaining": b.total - b.used}
        return {"total": 0, "used": 0, "remaining": 0}

    return DashboardLeaveBalance(
        paid=_make("paid"), sick=_make("sick"), unpaid=_make("unpaid"),
        bereavement=_make("bereavement"), medical=_make("medical"),
    )


async def _get_recent_activity(db: AsyncSession, employee_id) -> list[DashboardRecentActivity]:
    from app.models.audit_log import AuditLog
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.actor_id == employee_id)
        .order_by(AuditLog.created_at.desc())
        .limit(5)
    )
    logs = result.scalars().all()
    activities = []
    for log in logs:
        activities.append(DashboardRecentActivity(
            action=log.action,
            description=log.action.replace("_", " ").title(),
            timestamp=log.created_at.isoformat() if log.created_at else "",
        ))
    return activities


@router.get("/dashboard")
async def get_dashboard(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Check cache
    cached = await cache_service.get_dashboard(user.user_id, user.role)
    if cached:
        return cached

    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    if user.is_admin:
        # Admin dashboard
        active_count_result = await db.execute(
            select(func.count(Employee.id)).where(Employee.is_active)
        )
        active_count = active_count_result.scalar() or 0

        pending_result = await db.execute(
            select(LeaveRequest).where(LeaveRequest.status == "pending").order_by(LeaveRequest.created_at.desc()).limit(10)
        )
        pending_leaves = pending_result.scalars().all()

        pending_items = []
        for pl in pending_leaves:
            emp_result = await db.execute(select(Employee.name).where(Employee.id == pl.employee_id))
            emp_name = emp_result.scalar_one_or_none() or "Unknown"
            days = (pl.end_date - pl.start_date).days + 1
            pending_items.append(DashboardPendingLeave(
                id=pl.id, employee_name=emp_name, leave_type=pl.leave_type,
                start_date=pl.start_date, end_date=pl.end_date, days=days,
                remarks=pl.remarks, created_at=pl.created_at,
            ))

        burnout_result = await db.execute(
            select(BurnoutAlert, Employee.name)
            .join(Employee, BurnoutAlert.employee_id == Employee.id)
            .where(BurnoutAlert.resolved == False)
            .order_by(BurnoutAlert.created_at.desc())
            .limit(10)
        )
        burnout_alerts = [
            DashboardBurnoutAlert(
                employee_id=a.employee_id, employee_name=name,
                signal=a.signal, severity=a.severity,
                value=float(a.value) if a.value else None,
                created_at=a.created_at,
            )
            for a, name in burnout_result.all()
        ]

        data = AdminDashboard(
            total_employees=active_count + 0,  # Could count inactive separately
            active_employees=active_count,
            attendance_today=await _get_attendance_summary(db, employee.id),
            pending_leaves=pending_items,
            pending_leave_count=len(pending_items),
            burnout_alerts=burnout_alerts,
        )
    else:
        # Employee dashboard
        pending_result = await db.execute(
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.status == "pending",
            )
        )
        pending_count = pending_result.scalar() or 0

        data = EmployeeDashboard(
            attendance=await _get_attendance_summary(db, employee.id),
            leave_balance=await _get_leave_balance(db, employee.id),
            recent_activity=await _get_recent_activity(db, employee.id),
            pending_requests=pending_count,
        )

    response = {"role": user.role, "data": data.model_dump()}

    # Cache the result
    await cache_service.set_dashboard(user.user_id, user.role, response)

    return response
