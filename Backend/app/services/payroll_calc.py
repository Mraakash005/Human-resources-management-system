"""
HRMS Payroll Calculation Service
Monthly payroll run with immutable snapshots and PDF generation.
"""

from __future__ import annotations

import calendar
import logging
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.attendance import AttendanceRecord
from app.models.employee import Employee
from app.models.payroll import PayrollRun, SalaryComponent
from app.services.audit import log_action

logger = logging.getLogger(__name__)


async def get_current_salary_components(
    db: AsyncSession, employee_id: UUID
) -> list[SalaryComponent]:
    """Get the current effective salary components for an employee."""
    result = await db.execute(
        select(SalaryComponent)
        .where(
            SalaryComponent.employee_id == employee_id,
            SalaryComponent.effective_from <= date.today(),
        )
        .order_by(SalaryComponent.effective_from.desc())
    )
    all_components = result.scalars().all()

    # Keep only the latest value for each component name
    seen: dict[str, SalaryComponent] = {}
    for comp in all_components:
        if comp.component not in seen:
            seen[comp.component] = comp
    return list(seen.values())


async def get_month_attendance_summary(
    db: AsyncSession, employee_id: UUID, year: int, month: int
) -> dict[str, Any]:
    """Get attendance summary for a specific month."""
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date,
        )
    )
    records = result.scalars().all()

    present = sum(1 for r in records if r.status == "present")
    absent = sum(1 for r in records if r.status == "absent")
    half_day = sum(1 for r in records if r.status == "half-day")
    leave_days = sum(1 for r in records if r.status == "leave")
    unpaid_days = absent + leave_days  # Unpaid deduction days

    working_days = 0
    for day in range(1, last_day + 1):
        d = date(year, month, day)
        if d.weekday() < 5:  # Monday=0 to Friday=4
            working_days += 1

    return {
        "working_days": working_days,
        "present": present,
        "absent": absent,
        "half_day": half_day,
        "leave_days": leave_days,
        "unpaid_days": unpaid_days,
    }


def compute_tax(taxable_income: float) -> float:
    """Compute Indian income tax (simplified slabs)."""
    if taxable_income <= 300000:
        return 0
    if taxable_income <= 600000:
        return (taxable_income - 300000) * 0.05
    if taxable_income <= 900000:
        return 15000 + (taxable_income - 600000) * 0.10
    if taxable_income <= 1200000:
        return 45000 + (taxable_income - 900000) * 0.15
    if taxable_income <= 1500000:
        return 90000 + (taxable_income - 1200000) * 0.20
    return 150000 + (taxable_income - 1500000) * 0.30


async def compute_payroll(
    db: AsyncSession, employee: Employee, year: int, month: int
) -> dict[str, Any]:
    """Compute payroll for a single employee for a given month."""
    components = await get_current_salary_components(db, employee.id)

    if not components:
        logger.warning("No salary components found for %s", employee.employee_id)
        return {
            "gross_pay": 0, "deductions": 0, "net_pay": 0,
            "components_snapshot": {},
        }

    # Build component amounts
    comp_dict = {c.component: float(c.amount) for c in components}
    basic = comp_dict.get("basic_salary", 0)
    hra = comp_dict.get("hra", 0)
    transport = comp_dict.get("transport", 0)
    performance_bonus = comp_dict.get("performance_bonus", 0)

    gross = basic + hra + transport + performance_bonus

    # Deductions
    settings = get_settings()
    attendance = await get_month_attendance_summary(db, employee.id, year, month)
    unpaid_deduction = attendance["unpaid_days"] * (basic / 22) if basic else 0

    pf = basic * settings.PAYROLL_PF_RATE if settings.PAYROLL_PF_RATE else 0
    taxable = max(0, gross - settings.PAYROLL_STANDARD_DEDUCTION - pf)
    tax = compute_tax(taxable)

    total_deductions = pf + tax + unpaid_deduction
    net = gross - total_deductions

    snapshot = {c.component: float(c.amount) for c in components}

    return {
        "gross_pay": round(gross, 2),
        "deductions": round(total_deductions, 2),
        "net_pay": round(net, 2),
        "components_snapshot": snapshot,
    }


async def run_monthly_payroll() -> None:
    """
    APScheduler job: runs at end of each month.
    Generates immutable payroll snapshots for all active employees.
    """
    from app.core.database import db_manager

    today = date.today()
    year = today.year
    month = today.month

    logger.info("Starting monthly payroll run for %d/%d", month, year)

    async with db_manager.get_session_factory()() as db:
        employees_result = await db.execute(
            select(Employee).where(Employee.is_active)
        )
        employees = employees_result.scalars().all()

        for emp in employees:
            # Check if payroll already generated
            existing = await db.execute(
                select(PayrollRun).where(
                    PayrollRun.employee_id == emp.id,
                    PayrollRun.month == month,
                    PayrollRun.year == year,
                )
            )
            if existing.scalar_one_or_none():
                logger.info("Payroll already exists for %s %d/%d", emp.employee_id, month, year)
                continue

            payroll_data = await compute_payroll(db, emp, year, month)

            run = PayrollRun(
                employee_id=emp.id,
                month=month,
                year=year,
                gross_pay=payroll_data["gross_pay"],
                deductions=payroll_data["deductions"],
                net_pay=payroll_data["net_pay"],
                components_snapshot=payroll_data["components_snapshot"],
            )
            db.add(run)
            await db.flush()

            # Generate PDF pay stub
            try:
                from app.services.payroll_pdf import generate_pay_stub
                pdf_path = await generate_pay_stub(emp, run)
                run.pay_stub_url = pdf_path
            except Exception:
                logger.exception("Failed to generate pay stub for %s", emp.employee_id)

            await log_action(
                db=db,
                actor_id=None,
                action="payroll_generated",
                entity_type="payroll_run",
                entity_id=run.id,
                metadata={
                    "employee_id": str(emp.id),
                    "month": month,
                    "year": year,
                    "net_pay": payroll_data["net_pay"],
                },
            )

            # Send email notification
            try:
                from app.services.notification import email_service
                await email_service.send_pay_stub_email(
                    to=emp.email, name=emp.name, month=month, year=year
                )
            except Exception:
                logger.exception("Failed to send pay stub email to %s", emp.email)

        await db.commit()

    logger.info("Monthly payroll run completed for %d/%d", month, year)
