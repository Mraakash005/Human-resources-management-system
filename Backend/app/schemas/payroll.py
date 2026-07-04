"""
HRMS Payroll Schemas
Request/response schemas for payroll operations.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import HRMSBaseModel


class SalaryComponentResponse(HRMSBaseModel):
    """Single salary component."""
    name: str
    amount: float


class SalaryStructureResponse(HRMSBaseModel):
    """Full salary structure for employee."""
    employee_id: UUID
    components: list[SalaryComponentResponse]
    effective_from: date | None = None


class SalaryUpdateRequest(HRMSBaseModel):
    """Admin request to update salary structure."""
    components: list[SalaryComponentUpdate]


class SalaryComponentUpdate(HRMSBaseModel):
    """Single salary component update."""
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., ge=0)


# Fix forward reference
SalaryUpdateRequest.model_rebuild()


class PayrollRunResponse(HRMSBaseModel):
    """Payroll run response for employee."""
    id: UUID
    employee_id: UUID
    month: int
    year: int
    gross_pay: float
    deductions: float
    net_pay: float
    pay_stub_url: str | None = None
    components_snapshot: dict
    finalized_at: datetime


class PayrollAdminResponse(PayrollRunResponse):
    """Extended payroll response for admin."""
    employee_name: str | None = None
    employee_id_code: str | None = None
    department: str | None = None


class PayrollListFilter(HRMSBaseModel):
    """Query parameters for listing payroll runs."""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    month: int | None = Field(None, ge=1, le=12)
    year: int | None = None
    employee_id: UUID | None = None


class SalarySimulatorInput(HRMSBaseModel):
    """Client-side salary simulation input (documented for completeness)."""
    basic_salary: float = Field(..., ge=0)
    hra: float = Field(default=0, ge=0)
    transport: float = Field(default=0, ge=0)
    bonus: float = Field(default=0, ge=0)
    pf_enabled: bool = True
    tax_slab: str | None = None


class PayStubDownloadResponse(HRMSBaseModel):
    """Pay stub download URL response."""
    download_url: str
    month: int
    year: int
    filename: str
