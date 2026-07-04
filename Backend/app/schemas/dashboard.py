"""
HRMS Dashboard Schemas
Aggregated dashboard data schemas.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.schemas.common import HRMSBaseModel


class DashboardAttendance(HRMSBaseModel):
    """Today's attendance for dashboard."""
    status: str = "not_checked_in"
    check_in: str | None = None
    check_out: str | None = None
    duration_hours: float | None = None
    method: str | None = None


class DashboardLeaveBalance(HRMSBaseModel):
    """Leave balance summary for dashboard."""
    paid: dict[str, int]  # {"total": 12, "used": 4, "remaining": 8}
    sick: dict[str, int]
    unpaid: dict[str, int]
    bereavement: dict[str, int]
    medical: dict[str, int]


class DashboardRecentActivity(HRMSBaseModel):
    """Single activity item."""
    action: str
    description: str
    timestamp: str
    icon: str | None = None


class DashboardPendingLeave(HRMSBaseModel):
    """Pending leave for admin dashboard."""
    id: UUID
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    days: int
    remarks: str | None = None
    created_at: datetime


class DashboardBurnoutAlert(HRMSBaseModel):
    """Burnout alert for admin dashboard."""
    employee_id: UUID
    employee_name: str
    signal: str
    severity: str
    value: float | None = None
    created_at: datetime


class EmployeeDashboard(HRMSBaseModel):
    """Complete employee dashboard data."""
    attendance: DashboardAttendance
    leave_balance: DashboardLeaveBalance
    recent_activity: list[DashboardRecentActivity]
    pending_requests: int = 0
    total_employees: int = 0


class AdminDashboard(HRMSBaseModel):
    """Complete admin dashboard data."""
    total_employees: int
    active_employees: int
    attendance_today: DashboardAttendance
    pending_leaves: list[DashboardPendingLeave]
    pending_leave_count: int
    burnout_alerts: list[DashboardBurnoutAlert]
    department_health: dict[str, Any] | None = None


class DashboardResponse(HRMSBaseModel):
    """Unified dashboard response."""
    role: str
    data: EmployeeDashboard | AdminDashboard
