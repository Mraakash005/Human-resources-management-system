"""
HRMS Employee Schemas
Request/response schemas for employee management.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import HRMSBaseModel


class EmployeeProfile(HRMSBaseModel):
    """Employee profile response (limited fields for employee self-view)."""
    id: UUID
    clerk_id: str
    employee_id: str
    name: str
    email: str
    department: str | None = None
    designation: str | None = None
    phone: str | None = None
    address: str | None = None
    profile_pic: str | None = None
    role: str
    date_joined: date
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EmployeeSelfUpdate(HRMSBaseModel):
    """Fields an employee can update on their own profile."""
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=1000)
    profile_pic: str | None = Field(None, max_length=500)


class EmployeeAdminUpdate(HRMSBaseModel):
    """Fields an admin can update on any employee profile."""
    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    department: str | None = Field(None, max_length=100)
    designation: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=1000)
    profile_pic: str | None = Field(None, max_length=500)
    role: str | None = Field(None, pattern=r"^(admin|employee)$")
    is_active: bool | None = None


class EmployeeCreate(HRMSBaseModel):
    """Schema for admin creating a new employee."""
    employee_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    department: str | None = Field(None, max_length=100)
    designation: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    role: str = Field(default="employee", pattern=r"^(admin|employee)$")


class EmployeeListFilter(HRMSBaseModel):
    """Query parameters for listing employees."""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    department: str | None = None
    search: str | None = None
    is_active: bool | None = None


class AvatarPresignResponse(HRMSBaseModel):
    """Response for avatar upload presigned URL."""
    upload_url: str
    public_url: str
