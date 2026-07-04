"""
HRMS Attendance Schemas
Request/response schemas for attendance operations.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import HRMSBaseModel


class CheckInRequest(HRMSBaseModel):
    """Check-in request with optional geolocation."""
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)
    method: str = Field(default="manual", pattern=r"^(manual|gps|wifi|voice)$")


class CheckOutRequest(HRMSBaseModel):
    """Check-out request."""
    pass


class AutoCheckinRequest(HRMSBaseModel):
    """Auto check-in request (GPS or WiFi)."""
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)
    method: str = Field(..., pattern=r"^(gps|wifi)$")
    ssid_hint: str | None = None


class AttendanceResponse(HRMSBaseModel):
    """Single attendance record response."""
    id: UUID
    employee_id: UUID
    date: date
    status: str
    check_in: datetime | None = None
    check_out: datetime | None = None
    duration_hours: float | None = None
    check_in_method: str | None = None


class AttendanceCheckinResponse(HRMSBaseModel):
    """Check-in success response."""
    status: str
    time: str
    method: str | None = None


class AttendanceCheckoutResponse(HRMSBaseModel):
    """Check-out success response."""
    status: str
    duration_hours: float


class TodayAttendance(HRMSBaseModel):
    """Today's attendance summary for dashboard."""
    status: str = "not_checked_in"
    check_in: datetime | None = None
    check_out: datetime | None = None
    duration_hours: float | None = None
    can_check_in: bool = True
    can_check_out: bool = False


class AttendanceCalendarDay(HRMSBaseModel):
    """Single day in attendance calendar."""
    date: date
    status: str  # present|absent|half-day|leave|weekend|holiday|not_recorded
    check_in: datetime | None = None
    check_out: datetime | None = None
    duration_hours: float | None = None


class AttendanceCalendarMonth(HRMSBaseModel):
    """Monthly attendance calendar."""
    year: int
    month: int
    days: list[AttendanceCalendarDay]
    summary: AttendanceMonthSummary | None = None


class AttendanceMonthSummary(HRMSBaseModel):
    """Monthly attendance summary."""
    total_working_days: int
    present: int
    absent: int
    half_day: int
    leave: int
    weekend: int
    holiday: int


class HeatmapResponse(HRMSBaseModel):
    """Yearly attendance heatmap data."""
    year: int
    data: dict[str, str]  # { "2025-01-15": "present", ... }


class WeeklyViewResponse(HRMSBaseModel):
    """Weekly attendance view."""
    week_start: date
    week_end: date
    days: list[AttendanceCalendarDay]
