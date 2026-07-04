"""
HRMS Analytics Router
Team attendance health score and burnout dashboard.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin, TokenPayload
from app.core.database import get_db
from app.models.attendance import AttendanceRecord
from app.models.burnout import BurnoutAlert
from app.models.employee import Employee

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/team-health")
async def team_health_score(
    department: str = Query(...),
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None),
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not month:
        month = date.today().month
    if not year:
        year = date.today().year

    # Get all employees in department
    employees_result = await db.execute(
        select(Employee).where(
            Employee.department == department,
            Employee.is_active,
        )
    )
    employees = employees_result.scalars().all()
    if not employees:
        return {"department": department, "score": 0, "message": "No employees found"}

    total_score = 0
    risk_employees = []

    for emp in employees:
        # Get attendance for month
        from datetime import date as date_type
        import calendar
        last_day = calendar.monthrange(year, month)[1]

        att_result = await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.date >= date_type(year, month, 1),
                AttendanceRecord.date <= date_type(year, month, last_day),
            )
        )
        records = att_result.scalars().all()

        working_days = sum(1 for d in range(1, last_day + 1) if date_type(year, month, d).weekday() < 5)
        present = sum(1 for r in records if r.status == "present")
        absent = sum(1 for r in records if r.status == "absent")
        leave_days = sum(1 for r in records if r.status == "leave")

        # Score components
        present_rate = (present / working_days * 100) if working_days > 0 else 0
        leave_util = min(leave_days / 12 * 100, 100) if leave_days > 0 else 0
        absence_penalty = (absent / working_days * 100) if working_days > 0 else 0

        # Burnout penalty
        burnout_result = await db.execute(
            select(func.count(BurnoutAlert.id)).where(
                BurnoutAlert.employee_id == emp.id,
                BurnoutAlert.resolved == False,
            )
        )
        burnout_count = burnout_result.scalar() or 0
        burnout_penalty = min(burnout_count * 20, 100)

        emp_score = max(0, min(100, int(
            present_rate * 0.4
            + (100 - absence_penalty) * 0.2
            + (100 - burnout_penalty) * 0.2
            + leave_util * 0.2
        )))
        total_score += emp_score

        if emp_score < 50:
            risk_employees.append({"name": emp.name, "score": emp_score})

    avg_score = total_score // len(employees) if employees else 0
    color = "green" if avg_score >= 90 else "yellow" if avg_score >= 70 else "orange" if avg_score >= 50 else "red"

    return {
        "department": department,
        "score": avg_score,
        "color": color,
        "employee_count": len(employees),
        "risk_employees": risk_employees,
        "month": month,
        "year": year,
    }


@router.get("/burnout-dashboard")
async def burnout_dashboard(
    department: str | None = None,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = (
        select(BurnoutAlert, Employee.name, Employee.department)
        .join(Employee, BurnoutAlert.employee_id == Employee.id)
        .where(BurnoutAlert.resolved == False)
    )
    if department:
        query = query.where(Employee.department == department)
    query = query.order_by(BurnoutAlert.created_at.desc())

    result = await db.execute(query)
    alerts = [
        {
            "id": str(a.id),
            "employee_name": name,
            "department": dept,
            "signal": a.signal,
            "severity": a.severity,
            "value": float(a.value) if a.value else None,
            "threshold": float(a.threshold) if a.threshold else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a, name, dept in result.all()
    ]

    return {"alerts": alerts, "total": len(alerts)}
