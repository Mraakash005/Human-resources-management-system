"""
HRMS Employee Router
Employee profile management, CRUD, avatar upload.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_admin, TokenPayload
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.employee import Employee
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.employee import (
    EmployeeAdminUpdate,
    EmployeeCreate,
    EmployeeProfile,
    EmployeeSelfUpdate,
    AvatarPresignResponse,
)
from app.services.audit import log_action

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/me", response_model=ApiResponse[EmployeeProfile])
async def get_my_profile(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[EmployeeProfile]:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee profile")
    return ApiResponse(data=EmployeeProfile.model_validate(employee))


@router.patch("/me", response_model=ApiResponse[EmployeeProfile])
async def update_my_profile(
    payload: EmployeeSelfUpdate,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ApiResponse[EmployeeProfile]:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee profile")

    old_values = {"phone": employee.phone, "address": employee.address}
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    await log_action(
        db=db,
        actor_id=employee.id,
        action="profile_updated",
        entity_type="employee",
        entity_id=employee.id,
        metadata={"old_values": old_values, "new_values": update_data},
        ip_address=request.client.host if request else None,
    )

    return ApiResponse(data=EmployeeProfile.model_validate(employee))


@router.post("/me/avatar/presign", response_model=ApiResponse[AvatarPresignResponse])
async def get_avatar_upload_url(
    filename: str = Query(..., min_length=1),
    user: TokenPayload = Depends(get_current_user),
) -> ApiResponse[AvatarPresignResponse]:

    from app.core.config import get_settings
    settings = get_settings()

    key = f"avatars/{user.user_id}/{filename}"
    public_url = f"{settings.R2_PUBLIC_BASE_URL}/{key}"

    # Generate presigned URL (simplified — in production use boto3)
    upload_url = (
        f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/"
        f"{settings.R2_BUCKET_NAME}/{key}"
    )

    return ApiResponse(data=AvatarPresignResponse(upload_url=upload_url, public_url=public_url))


@router.get("", response_model=PaginatedResponse[EmployeeProfile])
async def list_employees(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    department: str | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[EmployeeProfile]:
    query = select(Employee)
    count_query = select(func.count(Employee.id))

    if is_active is not None:
        query = query.where(Employee.is_active == is_active)
        count_query = count_query.where(Employee.is_active == is_active)
    else:
        query = query.where(Employee.is_active)
        count_query = count_query.where(Employee.is_active)

    if department:
        query = query.where(Employee.department == department)
        count_query = count_query.where(Employee.department == department)

    if search:
        search_filter = Employee.name.ilike(f"%{search}%") | Employee.email.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Employee.name).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    employees = result.scalars().all()

    return PaginatedResponse(
        items=[EmployeeProfile.model_validate(e) for e in employees],
        total=total,
        page=page,
        limit=limit,
        has_next=(page * limit) < total,
    )


@router.get("/{employee_id}", response_model=ApiResponse[EmployeeProfile])
async def get_employee(
    employee_id: uuid.UUID,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[EmployeeProfile]:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee", employee_id)
    return ApiResponse(data=EmployeeProfile.model_validate(employee))


@router.post("", response_model=ApiResponse[EmployeeProfile])
async def create_employee(
    payload: EmployeeCreate,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ApiResponse[EmployeeProfile]:
    # Check uniqueness
    existing = await db.execute(
        select(Employee).where(
            (Employee.email == payload.email) | (Employee.employee_id == payload.employee_id)
        )
    )
    if existing.scalar_one_or_none():
        from app.core.exceptions import ConflictError
        raise ConflictError("Employee with this email or ID already exists")

    import secrets
    temp_password = secrets.token_urlsafe(16)

    # Create Clerk user via API
    import httpx
    from app.core.config import get_settings
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        clerk_resp = await client.post(
            "https://api.clerk.com/v1/users",
            headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
            json={
                "email_address": [payload.email],
                "password": temp_password,
                "public_metadata": {"role": payload.role},
            },
        )
    if clerk_resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Failed to create Clerk user")

    clerk_data = clerk_resp.json()
    clerk_id = clerk_data["id"]

    employee = Employee(
        clerk_id=clerk_id,
        employee_id=payload.employee_id,
        name=payload.name,
        email=payload.email,
        department=payload.department,
        designation=payload.designation,
        phone=payload.phone,
        role=payload.role,
    )
    db.add(employee)
    await db.flush()

    # Initialize leave balances
    from app.models.leave import LeaveBalance
    from datetime import date as _date
    for leave_type, default in [
        ("paid", settings.LEAVE_PAID_DEFAULT),
        ("sick", settings.LEAVE_SICK_DEFAULT),
        ("unpaid", settings.LEAVE_UNPAID_DEFAULT),
        ("bereavement", settings.LEAVE_BEREAVEMENT_DEFAULT),
    ]:
        db.add(LeaveBalance(
            employee_id=employee.id,
            year=_date.today().year,
            leave_type=leave_type,
            total=default,
        ))

    await log_action(
        db=db,
        actor_id=employee.id,
        action="employee_created",
        entity_type="employee",
        entity_id=employee.id,
        metadata={"employee_id": payload.employee_id, "department": payload.department},
    )

    # Send welcome email
    try:
        from app.services.notification import email_service
        await email_service.send_welcome_email(to=payload.email, name=payload.name)
    except Exception:
        pass  # Don't fail employee creation if email fails

    return ApiResponse(data=EmployeeProfile.model_validate(employee), message="Employee created successfully")


@router.patch("/{employee_id}", response_model=ApiResponse[EmployeeProfile])
async def admin_update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeAdminUpdate,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ApiResponse[EmployeeProfile]:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee", employee_id)

    old_values = {k: getattr(employee, k) for k in payload.model_fields if getattr(employee, k, None) is not None}
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    await log_action(
        db=db,
        actor_id=employee.id,
        action="admin_profile_edit",
        entity_type="employee",
        entity_id=employee.id,
        metadata={"old_values": old_values, "new_values": update_data},
        ip_address=request.client.host if request else None,
    )

    return ApiResponse(data=EmployeeProfile.model_validate(employee))


@router.patch("/{employee_id}/deactivate", response_model=ApiResponse)
async def deactivate_employee(
    employee_id: uuid.UUID,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee", employee_id)

    employee.is_active = False
    await log_action(
        db=db,
        actor_id=employee.id,
        action="employee_deactivated",
        entity_type="employee",
        entity_id=employee.id,
    )
    return ApiResponse(message="Employee deactivated")


@router.patch("/{employee_id}/reactivate", response_model=ApiResponse)
async def reactivate_employee(
    employee_id: uuid.UUID,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee", employee_id)

    employee.is_active = True
    await log_action(
        db=db,
        actor_id=employee.id,
        action="employee_reactivated",
        entity_type="employee",
        entity_id=employee.id,
    )
    return ApiResponse(message="Employee reactivated")
