"""
HRMS Leave Schemas
Request/response schemas for leave operations.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import HRMSBaseModel


LeaveType = Literal["paid", "sick", "unpaid", "bereavement", "medical"]


class LeaveCreate(HRMSBaseModel):
    """Schema for creating a leave request."""
    leave_type: LeaveType
    start_date: date
    end_date: date
    remarks: str | None = Field(None, max_length=500)
    formal_reason: str | None = Field(None, max_length=100)
    generated_email_body: str | None = None
    send_email: bool = False

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator("remarks")
    @classmethod
    def no_html_tags(cls, v: str | None) -> str | None:
        if v and ("<script" in v.lower() or "<" in v):
            raise ValueError("HTML tags not allowed")
        return v


class LeaveApproval(HRMSBaseModel):
    """Schema for admin approving/rejecting leave."""
    status: Literal["approved", "rejected"]
    comment: str | None = Field(None, max_length=1000)


class LeaveResponse(HRMSBaseModel):
    """Leave request response."""
    id: UUID
    employee_id: UUID
    employee_name: str | None = None
    leave_type: str
    start_date: date
    end_date: date
    status: str
    remarks: str | None = None
    admin_comment: str | None = None
    days: int = 0
    email_sent: bool = False
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime


class LeaveBalanceResponse(HRMSBaseModel):
    """Leave balance for one type."""
    leave_type: str
    total: int
    used: int
    remaining: int


class LeaveBalanceSummary(HRMSBaseModel):
    """Full leave balance summary for employee."""
    year: int
    balances: list[LeaveBalanceResponse]


class LeaveCalendarDay(HRMSBaseModel):
    """Day in leave application calendar."""
    date: date
    status: str  # present|absent|leave|weekend|holiday|not_recorded


class LeaveListFilter(HRMSBaseModel):
    """Query parameters for listing leave requests."""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    status: str | None = Field(None, pattern=r"^(pending|approved|rejected|cancelled)$")
    employee_id: UUID | None = None
    leave_type: LeaveType | None = None
    start_date: date | None = None
    end_date: date | None = None


class ConversationalLeaveMessage(HRMSBaseModel):
    """Message in conversational leave chat."""
    message: str = Field(..., min_length=1, max_length=500)
    history: list[dict[str, str]] = Field(default_factory=list)


class ConversationalLeaveResponse(HRMSBaseModel):
    """AI response in conversational leave."""
    reply: str
    intent: str  # ask_dates|ask_type|ask_confirm|confirm_submit|idle
    extracted: dict | None = None
    leave_id: str | None = None


class LeaveAdvisorRecommendation(HRMSBaseModel):
    """Single recommendation from AI leave advisor."""
    title: str
    message: str
    priority: str  # urgent|suggested|info
    suggested_dates: dict | None = None


class LeaveEmailRequest(HRMSBaseModel):
    """Request for AI leave email generation."""
    name: str
    department: str | None = None
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
