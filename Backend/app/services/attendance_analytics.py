"""
HRMS Attendance Analytics Service
Burnout detection, consecutive workday counting, overtime computation.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.burnout import BurnoutAlert, BurnoutConfig
from app.models.employee import Employee
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def get_attendance_records(
    db: AsyncSession, employee_id: UUID, days: int = 90
) -> list[AttendanceRecord]:
    """Fetch attendance records for the last N days."""
    cutoff = date.today() - timedelta(days=days)
    result = await db.execute(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date >= cutoff,
        )
        .order_by(AttendanceRecord.date.desc())
    )
    return list(result.scalars().all())


def count_max_consecutive_present(records: list[AttendanceRecord]) -> int:
    """Count the maximum streak of consecutive present days."""
    if not records:
        return 0

    sorted_records = sorted(records, key=lambda r: r.date)
    max_streak = 0
    current_streak = 0
    prev_date: date | None = None

    for record in sorted_records:
        if record.status == "present":
            if prev_date and record.date == prev_date + timedelta(days=1):
                current_streak += 1
            else:
                current_streak = 1
            max_streak = max(max_streak, current_streak)
            prev_date = record.date
        elif record.status in ("absent", "leave"):
            current_streak = 0
            prev_date = None
        # half-day continues the streak

    return max_streak


def compute_weekly_overtime(records: list[AttendanceRecord]) -> list[float]:
    """Compute overtime hours per week (weeks where total > 40h)."""
    if not records:
        return []

    from collections import defaultdict
    weekly_hours: dict[str, float] = defaultdict(float)

    for record in records:
        if record.duration_hours and record.status == "present":
            # ISO week key
            week_key = record.date.isocalendar()[:2]
            weekly_hours[f"{week_key[0]}-W{week_key[1]:02d}"] += float(record.duration_hours)

    overtime = []
    for total in weekly_hours.values():
        if total > 40:
            overtime.append(round(total - 40, 2))
    return overtime


def count_extreme_hour_days(
    records: list[AttendanceRecord], before_hour: int = 7, after_hour: int = 21
) -> int:
    """Count days where check-in is before before_hour OR check-out is after after_hour."""
    count = 0
    for record in records:
        if record.check_in and record.check_in.hour < before_hour:
            count += 1
        elif record.check_out and record.check_out.hour >= after_hour:
            count += 1
    return count


def count_half_days_in_month(records: list[AttendanceRecord], year: int, month: int) -> int:
    """Count half-day records in a given month."""
    return sum(
        1 for r in records
        if r.status == "half-day" and r.date.year == year and r.date.month == month
    )


def compute_absence_spike(records: list[AttendanceRecord]) -> bool:
    """Detect sudden absence after a long streak of attendance."""
    if len(records) < 5:
        return False

    sorted_records = sorted(records, key=lambda r: r.date)
    streak = 0
    for record in reversed(sorted_records):
        if record.status == "present":
            streak += 1
        else:
            break

    if streak < 10:
        return False

    # Check if there's a sudden absence right before the streak
    idx = len(sorted_records) - streak - 1
    if idx >= 0 and sorted_records[idx].status in ("absent", "leave"):
        return True
    return False


async def compute_burnout_signals(
    db: AsyncSession, employee_id: UUID, config: BurnoutConfig
) -> list[dict[str, Any]]:
    """Compute all burnout signals for an employee."""
    records = await get_attendance_records(db, employee_id, days=90)
    alerts: list[dict[str, Any]] = []

    # Signal 1: Consecutive working days
    consecutive = count_max_consecutive_present(records)
    if consecutive >= config.max_consecutive_days:
        alerts.append({
            "signal": "consecutive_days",
            "value": consecutive,
            "threshold": config.max_consecutive_days,
            "severity": "high",
        })

    # Signal 2: Weekly overtime
    overtime_weeks = compute_weekly_overtime(records)
    for ot in overtime_weeks:
        if ot > config.max_weekly_overtime_hrs:
            alerts.append({
                "signal": "weekly_overtime",
                "value": ot,
                "threshold": config.max_weekly_overtime_hrs,
                "severity": "medium",
            })
            break  # One alert per employee per run

    # Signal 3: Extreme hours pattern
    extreme_days = count_extreme_hour_days(records)
    settings = get_settings()
    if extreme_days >= settings.BURNOUT_EXTREME_HOURS_THRESHOLD:
        alerts.append({
            "signal": "extreme_hours",
            "value": extreme_days,
            "threshold": settings.BURNOUT_EXTREME_HOURS_THRESHOLD,
            "severity": "high",
        })

    # Signal 4: Absence spike after long streak
    if compute_absence_spike(records):
        alerts.append({
            "signal": "absence_spike",
            "value": 1,
            "threshold": 1,
            "severity": "watch",
        })

    # Signal 5: Repeated half-days
    today = date.today()
    half_days = count_half_days_in_month(records, today.year, today.month)
    if half_days >= 6:
        alerts.append({
            "signal": "half_day_pattern",
            "value": half_days,
            "threshold": 6,
            "severity": "medium",
        })

    return alerts


async def check_burnout() -> None:
    """
    APScheduler job: nightly burnout detection for all departments.
    """
    from app.core.database import db_manager

    logger.info("Starting nightly burnout check")
    async with db_manager.get_session_factory()() as db:
        # Get all department configs
        configs_result = await db.execute(select(BurnoutConfig))
        configs = configs_result.scalars().all()

        for config in configs:
            employees_result = await db.execute(
                select(Employee).where(
                    Employee.department == config.department,
                    Employee.is_active,
                )
            )
            employees = employees_result.scalars().all()

            for emp in employees:
                alerts = await compute_burnout_signals(db, emp.id, config)
                if alerts:
                    for alert_data in alerts:
                        alert = BurnoutAlert(
                            employee_id=emp.id,
                            signal=alert_data["signal"],
                            value=alert_data["value"],
                            threshold=alert_data["threshold"],
                            severity=alert_data["severity"],
                        )
                        db.add(alert)

                    # Send email notification to HR
                    if config.alert_email:
                        from app.services.notification import email_service
                        for alert_data in alerts:
                            try:
                                await email_service.send_burnout_alert(
                                    to=config.alert_email,
                                    employee_name=emp.name,
                                    signal=alert_data["signal"],
                                    severity=alert_data["severity"],
                                )
                            except Exception:
                                logger.exception(
                                    "Failed to send burnout email for %s", emp.name
                                )

        await db.commit()
    logger.info("Nightly burnout check completed")
