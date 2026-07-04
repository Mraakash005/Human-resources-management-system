"""
HRMS Attendance Router
Check-in/out, geofence validation, auto check-in, calendar views, heatmap.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone

import uuid as _uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_admin, TokenPayload
from app.core.database import get_db
from app.core.exceptions import (
    BadRequestError,
    DoubleCheckInError,
    DoubleCheckOutError,
    GeofenceViolationError,
    NotFoundError,
)
from app.models.attendance import AttendanceRecord
from app.models.config import OfficeConfig
from app.models.employee import Employee
from app.schemas.attendance import (
    AttendanceCalendarDay,
    AttendanceCalendarMonth,
    AttendanceCheckinResponse,
    AttendanceCheckoutResponse,
    AttendanceMonthSummary,
    AutoCheckinRequest,
    CheckInRequest,
    HeatmapResponse,
    TodayAttendance,
    WeeklyViewResponse,
    AttendanceResponse,
)
from app.services.audit import log_action
from app.services.cache import cache_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _ip_in_subnet(ip: str, subnet: str) -> bool:
    """Check if an IP is within a subnet (simplified)."""
    import ipaddress
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(subnet, strict=False)
    except ValueError:
        return False


@router.post("/checkin", response_model=AttendanceCheckinResponse)
async def check_in(
    payload: CheckInRequest,
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttendanceCheckinResponse:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    today = date.today().isoformat()

    # Redis double check-in prevention
    if await cache_service.check_attendance_lock(str(employee.id), today):
        raise DoubleCheckInError()

    # Geofence validation
    config_result = await db.execute(select(OfficeConfig).limit(1))
    config = config_result.scalar_one_or_none()

    if config and config.gps_checkin_enabled and payload.lat is not None and payload.lng is not None:
        distance = _haversine(
            payload.lat, payload.lng,
            float(config.office_lat), float(config.office_lng),
        )
        if distance > config.geofence_radius_m:
            raise GeofenceViolationError()

    record = AttendanceRecord(
        employee_id=employee.id,
        date=date.today(),
        status="present",
        check_in=datetime.now(timezone.utc),
        location_lat=payload.lat,
        location_lng=payload.lng,
        check_in_method=payload.method,
    )
    db.add(record)
    await db.flush()

    # Set Redis lock
    await cache_service.set_attendance_lock(
        str(employee.id), today, record.check_in.isoformat()
    )

    await log_action(
        db=db,
        actor_id=employee.id,
        action="check_in",
        entity_type="attendance",
        entity_id=record.id,
        metadata={"lat": payload.lat, "lng": payload.lng, "method": payload.method},
        ip_address=request.client.host,
    )

    return AttendanceCheckinResponse(
        status="checked_in",
        time=record.check_in.isoformat(),
        method=payload.method,
    )


@router.post("/checkout", response_model=AttendanceCheckoutResponse)
async def check_out(
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttendanceCheckoutResponse:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    today_result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == date.today(),
        )
    )
    record = today_result.scalar_one_or_none()
    if not record or not record.check_in:
        raise BadRequestError("No check-in found for today")
    if record.check_out:
        raise DoubleCheckOutError()

    record.check_out = datetime.now(timezone.utc)
    record.duration_hours = round(
        (record.check_out - record.check_in).total_seconds() / 3600, 2
    )

    await log_action(
        db=db,
        actor_id=employee.id,
        action="check_out",
        entity_type="attendance",
        entity_id=record.id,
        metadata={"duration_hours": record.duration_hours},
    )

    return AttendanceCheckoutResponse(
        status="checked_out",
        duration_hours=record.duration_hours,
    )


@router.post("/auto-checkin", response_model=AttendanceCheckinResponse)
async def auto_checkin(
    payload: AutoCheckinRequest,
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttendanceCheckinResponse:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    today = date.today().isoformat()
    if await cache_service.check_attendance_lock(str(employee.id), today):
        # Already checked in — return success but don't create duplicate
        today_record = await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date == date.today(),
            )
        )
        rec = today_record.scalar_one_or_none()
        return AttendanceCheckinResponse(
            status="already_checked_in",
            time=rec.check_in.isoformat() if rec and rec.check_in else "",
        )

    verified = False

    if payload.method == "gps" and payload.lat is not None and payload.lng is not None:
        config_result = await db.execute(select(OfficeConfig).limit(1))
        config = config_result.scalar_one_or_none()
        if config and config.office_lat and config.office_lng:
            distance = _haversine(
                payload.lat, payload.lng,
                float(config.office_lat), float(config.office_lng),
            )
            verified = distance <= config.geofence_radius_m

    elif payload.method == "wifi":
        client_ip = request.client.host if request else ""
        config_result = await db.execute(select(OfficeConfig).limit(1))
        config = config_result.scalar_one_or_none()
        if config and config.office_ip_subnet:
            verified = _ip_in_subnet(client_ip, config.office_ip_subnet)

    if not verified:
        return AttendanceCheckinResponse(status="not_in_office", time="", method=payload.method)

    record = AttendanceRecord(
        employee_id=employee.id,
        date=date.today(),
        status="present",
        check_in=datetime.now(timezone.utc),
        check_in_method=payload.method,
    )
    db.add(record)
    await db.flush()

    await cache_service.set_attendance_lock(str(employee.id), today, record.check_in.isoformat())

    return AttendanceCheckinResponse(
        status="checked_in",
        time=record.check_in.isoformat(),
        method=payload.method,
    )


@router.get("/today", response_model=TodayAttendance)
async def get_today_attendance(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TodayAttendance:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    record_result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == date.today(),
        )
    )
    record = record_result.scalar_one_or_none()

    if not record:
        return TodayAttendance(status="not_checked_in", can_check_in=True, can_check_out=False)

    return TodayAttendance(
        status=record.status,
        check_in=record.check_in,
        check_out=record.check_out,
        duration_hours=float(record.duration_hours) if record.duration_hours else None,
        can_check_in=record.check_in is None,
        can_check_out=record.check_in is not None and record.check_out is None,
    )


@router.get("/calendar", response_model=AttendanceCalendarMonth)
async def get_attendance_calendar(
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AttendanceCalendarMonth:
    import calendar as cal

    if not year:
        year = date.today().year
    if not month:
        month = date.today().month

    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    start_date = date(year, month, 1)
    last_day = cal.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    records_result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date,
        )
    )
    records = {r.date: r for r in records_result.scalars().all()}

    days = []
    present = absent = half_day = leave_count = weekend = holiday = 0

    for day in range(1, last_day + 1):
        d = date(year, month, day)
        record = records.get(d)

        if d.weekday() >= 5:
            status = "weekend"
            weekend += 1
        elif record:
            status = record.status
            if status == "present":
                present += 1
            elif status == "absent":
                absent += 1
            elif status == "half-day":
                half_day += 1
            elif status == "leave":
                leave_count += 1
        else:
            status = "not_recorded"

        days.append(AttendanceCalendarDay(
            date=d,
            status=status,
            check_in=record.check_in if record else None,
            check_out=record.check_out if record else None,
            duration_hours=float(record.duration_hours) if record and record.duration_hours else None,
        ))

    return AttendanceCalendarMonth(
        year=year,
        month=month,
        days=days,
        summary=AttendanceMonthSummary(
            total_working_days=last_day - weekend,
            present=present,
            absent=absent,
            half_day=half_day,
            leave=leave_count,
            weekend=weekend,
            holiday=holiday,
        ),
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_attendance_heatmap(
    year: int = Query(default=None),
    employee_id: str | None = None,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HeatmapResponse:
    if not year:
        year = date.today().year

    # Get employee
    if user.is_admin and employee_id:
        emp_result = await db.execute(
            select(Employee).where(Employee.id == _uuid.UUID(employee_id))
        )
    else:
        emp_result = await db.execute(
            select(Employee).where(Employee.clerk_id == user.user_id)
        )
    employee = emp_result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    # Check cache
    cached = await cache_service.get_heatmap(str(employee.id), year)
    if cached:
        return HeatmapResponse(year=year, data=cached)

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    records_result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date,
        )
    )

    data: dict[str, str] = {}
    for record in records_result.scalars().all():
        data[record.date.isoformat()] = record.status

    await cache_service.set_heatmap(str(employee.id), year, data)

    return HeatmapResponse(year=year, data=data)


@router.get("/weekly", response_model=WeeklyViewResponse)
async def get_weekly_view(
    week_start: date | None = None,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyViewResponse:
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    week_end = week_start + timedelta(days=6)

    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    records_result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= week_start,
            AttendanceRecord.date <= week_end,
        )
    )
    records = {r.date: r for r in records_result.scalars().all()}

    days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        record = records.get(d)
        if d.weekday() >= 5:
            status = "weekend"
        elif record:
            status = record.status
        else:
            status = "not_recorded"

        days.append(AttendanceCalendarDay(
            date=d,
            status=status,
            check_in=record.check_in if record else None,
            check_out=record.check_out if record else None,
            duration_hours=float(record.duration_hours) if record and record.duration_hours else None,
        ))

    return WeeklyViewResponse(week_start=week_start, week_end=week_end, days=days)


@router.get("/all", response_model=list[AttendanceResponse])
async def admin_list_attendance(
    employee_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AttendanceResponse]:
    query = select(AttendanceRecord)
    if employee_id:
        query = query.where(AttendanceRecord.employee_id == employee_id)
    if start_date:
        query = query.where(AttendanceRecord.date >= start_date)
    if end_date:
        query = query.where(AttendanceRecord.date <= end_date)
    query = query.order_by(AttendanceRecord.date.desc()).limit(limit)
    result = await db.execute(query)
    return [AttendanceResponse.model_validate(r) for r in result.scalars().all()]
