"""
HRMS Payroll Router
Payroll visibility, salary management, pay stub download.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_admin, TokenPayload
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.employee import Employee
from app.models.payroll import PayrollRun, SalaryComponent
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.payroll import (
    PayrollRunResponse,
    PayrollAdminResponse,
    SalaryComponentResponse,
    SalaryStructureResponse,
    SalaryUpdateRequest,
    PayStubDownloadResponse,
)
from app.services.audit import log_action
from app.services.payroll_calc import get_current_salary_components

router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.get("/me", response_model=ApiResponse[PayrollRunResponse])
async def get_my_payroll(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PayrollRunResponse]:
    if not month:
        month = date.today().month
    if not year:
        year = date.today().year

    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    payroll_result = await db.execute(
        select(PayrollRun).where(
            PayrollRun.employee_id == employee.id,
            PayrollRun.month == month,
            PayrollRun.year == year,
        )
    )
    payroll = payroll_result.scalar_one_or_none()
    if not payroll:
        raise NotFoundError("Payroll record for this period")

    return ApiResponse(data=PayrollRunResponse.model_validate(payroll))


@router.get("/me/salary", response_model=ApiResponse[SalaryStructureResponse])
async def get_my_salary(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SalaryStructureResponse]:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    components = await get_current_salary_components(db, employee.id)
    return ApiResponse(data=SalaryStructureResponse(
        employee_id=employee.id,
        components=[SalaryComponentResponse(name=c.component, amount=float(c.amount)) for c in components],
    ))


@router.get("/me/stub", response_model=ApiResponse[PayStubDownloadResponse])
async def download_pay_stub(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PayStubDownloadResponse]:
    if not month:
        month = date.today().month
    if not year:
        year = date.today().year

    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    payroll_result = await db.execute(
        select(PayrollRun).where(
            PayrollRun.employee_id == employee.id,
            PayrollRun.month == month,
            PayrollRun.year == year,
        )
    )
    payroll = payroll_result.scalar_one_or_none()
    if not payroll or not payroll.pay_stub_url:
        raise NotFoundError("Pay stub for this period")

    import calendar
    return ApiResponse(data=PayStubDownloadResponse(
        download_url=payroll.pay_stub_url,
        month=month,
        year=year,
        filename=f"paystub-{calendar.month_name[month]}-{year}.pdf",
    ))


@router.get("/all", response_model=PaginatedResponse[PayrollAdminResponse])
async def admin_list_payroll(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = None,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PayrollAdminResponse]:
    query = select(PayrollRun)
    count_query = select(func.count(PayrollRun.id))

    if month:
        query = query.where(PayrollRun.month == month)
        count_query = count_query.where(PayrollRun.month == month)
    if year:
        query = query.where(PayrollRun.year == year)
        count_query = count_query.where(PayrollRun.year == year)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(PayrollRun.finalized_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    runs = result.scalars().all()

    items = []
    for run in runs:
        emp_result = await db.execute(
            select(Employee.name, Employee.employee_id, Employee.department).where(Employee.id == run.employee_id)
        )
        emp_data = emp_result.one_or_none()
        items.append(PayrollAdminResponse(
            id=run.id,
            employee_id=run.employee_id,
            employee_name=emp_data[0] if emp_data else None,
            employee_id_code=emp_data[1] if emp_data else None,
            department=emp_data[2] if emp_data else None,
            month=run.month,
            year=run.year,
            gross_pay=float(run.gross_pay),
            deductions=float(run.deductions),
            net_pay=float(run.net_pay),
            pay_stub_url=run.pay_stub_url,
            components_snapshot=run.components_snapshot,
            finalized_at=run.finalized_at,
        ))

    return PaginatedResponse(items=items, total=total, page=page, limit=limit, has_next=(page * limit) < total)


@router.patch("/employees/{employee_id}/salary")
async def update_salary_structure(
    employee_id: str,
    payload: SalaryUpdateRequest,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    emp_result = await db.execute(
        select(Employee).where(Employee.id == _uuid.UUID(employee_id))
    )
    employee = emp_result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    old_components = await get_current_salary_components(db, employee.id)
    old_values = {c.component: float(c.amount) for c in old_components}

    for comp in payload.components:
        new_entry = SalaryComponent(
            employee_id=employee.id,
            component=comp.name,
            amount=comp.amount,
            effective_from=date.today(),
        )
        db.add(new_entry)

    await log_action(
        db=db,
        actor_id=employee.id,
        action="salary_updated",
        entity_type="employee",
        entity_id=employee.id,
        metadata={"old_values": old_values, "new_components": {c.name: c.amount for c in payload.components}},
    )

    return ApiResponse(message="Salary structure updated")
