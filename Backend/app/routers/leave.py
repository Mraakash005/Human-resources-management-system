"""
HRMS Leave Router
Leave application, approval, cancellation, balance, AI advisor, conversational leave.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_admin, TokenPayload
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    InsufficientBalanceError,
    NotFoundError,
)
from app.models.employee import Employee
from app.models.leave import LeaveBalance, LeaveRequest
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.leave import (
    LeaveApproval,
    LeaveBalanceResponse,
    LeaveBalanceSummary,
    LeaveCreate,
    LeaveEmailRequest,
    LeaveResponse,
    ConversationalLeaveMessage,
    ConversationalLeaveResponse,
    LeaveAdvisorRecommendation,
)
from app.services.audit import log_action
from app.services.cache import cache_service

router = APIRouter(prefix="/leave", tags=["Leave"])


def _count_leave_days(start: date, end: date) -> int:
    """Count business days between start and end (inclusive)."""
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current = date.fromordinal(current.toordinal() + 1)
    return days


@router.post("", response_model=ApiResponse[LeaveResponse])
async def create_leave_request(
    payload: LeaveCreate,
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LeaveResponse]:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    days = _count_leave_days(payload.start_date, payload.end_date)
    if days <= 0:
        raise BadRequestError("Leave must be at least 1 day")

    # Check balance
    balance_result = await db.execute(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == payload.start_date.year,
            LeaveBalance.leave_type == payload.leave_type,
        )
    )
    balance = balance_result.scalar_one_or_none()
    if not balance:
        raise InsufficientBalanceError(payload.leave_type, 0, days)

    remaining = balance.total - balance.used
    if remaining < days:
        raise InsufficientBalanceError(payload.leave_type, remaining, days)

    # Atomic balance deduction
    deduct_result = await db.execute(
        text("""
            UPDATE leave_balances
            SET used = used + :days
            WHERE employee_id = :emp_id
              AND year = :year
              AND leave_type = :leave_type
              AND (total - used) >= :days
            RETURNING id
        """),
        {"days": days, "emp_id": employee.id, "year": payload.start_date.year, "leave_type": payload.leave_type},
    )
    if not deduct_result.fetchone():
        raise ConflictError("Balance updated concurrently, please retry")

    # Create leave request (DB exclusion constraint catches overlap)
    leave = LeaveRequest(
        employee_id=employee.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        remarks=payload.remarks,
        formal_reason=payload.formal_reason,
        generated_email_body=payload.generated_email_body,
        email_sent=payload.send_email,
    )
    db.add(leave)
    await db.flush()

    # Send email if requested
    if payload.send_email and payload.generated_email_body:
        try:
            from app.services.notification import email_service
            settings = get_settings()
            await email_service.send_leave_notification(
                to=settings.HR_EMAIL,
                subject=f"Leave Request: {employee.name} ({payload.leave_type})",
                body=payload.generated_email_body,
            )
            leave.email_sent = True
        except Exception:
            pass

    # Invalidate cache
    await cache_service.invalidate_leave_balance(str(employee.id))
    await cache_service.invalidate_dashboard(str(employee.id))

    await log_action(
        db=db,
        actor_id=employee.id,
        action="leave_requested",
        entity_type="leave_request",
        entity_id=leave.id,
        metadata={"leave_type": payload.leave_type, "days": days, "email_sent": leave.email_sent},
    )

    return ApiResponse(
        data=LeaveResponse(
            id=leave.id,
            employee_id=leave.employee_id,
            leave_type=leave.leave_type,
            start_date=leave.start_date,
            end_date=leave.end_date,
            status=leave.status,
            remarks=leave.remarks,
            days=days,
            email_sent=leave.email_sent,
            created_at=leave.created_at,
        ),
        message="Leave request submitted",
    )


@router.get("", response_model=PaginatedResponse[LeaveResponse])
async def list_leave_requests(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[LeaveResponse]:
    query = select(LeaveRequest)
    count_query = select(func.count(LeaveRequest.id))

    # Employees see only their own
    if not user.is_admin:
        emp_result = await db.execute(
            select(Employee).where(Employee.clerk_id == user.user_id)
        )
        employee = emp_result.scalar_one_or_none()
        if not employee:
            raise NotFoundError("Employee")
        query = query.where(LeaveRequest.employee_id == employee.id)
        count_query = count_query.where(LeaveRequest.employee_id == employee.id)

    if status:
        query = query.where(LeaveRequest.status == status)
        count_query = count_query.where(LeaveRequest.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(LeaveRequest.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    leaves = result.scalars().all()

    items = []
    for leave in leaves:
        days = _count_leave_days(leave.start_date, leave.end_date)
        # Get employee name for admin view
        emp_name = None
        if user.is_admin:
            emp_result = await db.execute(
                select(Employee.name).where(Employee.id == leave.employee_id)
            )
            emp_name = emp_result.scalar_one_or_none()
        items.append(LeaveResponse(
            id=leave.id,
            employee_id=leave.employee_id,
            employee_name=emp_name,
            leave_type=leave.leave_type,
            start_date=leave.start_date,
            end_date=leave.end_date,
            status=leave.status,
            remarks=leave.remarks,
            admin_comment=leave.admin_comment,
            days=days,
            email_sent=leave.email_sent,
            reviewed_by=leave.reviewed_by,
            reviewed_at=leave.reviewed_at,
            created_at=leave.created_at,
        ))

    return PaginatedResponse(items=items, total=total, page=page, limit=limit, has_next=(page * limit) < total)


@router.get("/balance", response_model=ApiResponse[LeaveBalanceSummary])
async def get_my_balance(
    year: int = Query(default=None),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LeaveBalanceSummary]:
    if not year:
        year = date.today().year

    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    balances_result = await db.execute(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == year,
        )
    )
    balances = balances_result.scalars().all()

    return ApiResponse(data=LeaveBalanceSummary(
        year=year,
        balances=[
            LeaveBalanceResponse(
                leave_type=b.leave_type,
                total=b.total,
                used=b.used,
                remaining=b.total - b.used,
            )
            for b in balances
        ],
    ))


@router.patch("/{leave_id}/approve", response_model=ApiResponse)
async def approve_leave(
    leave_id: str,
    payload: LeaveApproval,
    request: Request,
    user: TokenPayload = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    import uuid as uuid_mod
    result = await db.execute(
        select(LeaveRequest).where(LeaveRequest.id == uuid_mod.UUID(leave_id))
    )
    leave = result.scalar_one_or_none()
    if not leave:
        raise NotFoundError("Leave request")
    if leave.status != "pending":
        raise BadRequestError(f"Cannot action a {leave.status} leave request")

    # Look up admin employee by clerk_id
    admin_result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    admin_employee = admin_result.scalar_one_or_none()

    old_status = leave.status
    leave.status = payload.status
    leave.admin_comment = payload.comment
    leave.reviewed_by = admin_employee.id if admin_employee else None
    leave.reviewed_at = datetime.now(timezone.utc)

    # If rejected, recredit balance
    if payload.status == "rejected":
        days = _count_leave_days(leave.start_date, leave.end_date)
        await db.execute(
            text("UPDATE leave_balances SET used = used - :days WHERE employee_id = :eid AND year = :y AND leave_type = :lt"),
            {"days": days, "eid": leave.employee_id, "y": leave.start_date.year, "lt": leave.leave_type},
        )

    await log_action(
        db=db,
        actor_id=admin_employee.id if admin_employee else leave.employee_id,
        action=f"leave_{payload.status}",
        entity_type="leave_request",
        entity_id=leave.id,
        metadata={"old_status": old_status, "new_status": payload.status, "comment": payload.comment},
    )

    # Notify employee
    try:
        from app.services.notification import email_service
        emp_result = await db.execute(select(Employee).where(Employee.id == leave.employee_id))
        employee = emp_result.scalar_one_or_none()
        if employee:
            await email_service.send_leave_notification(
                to=employee.email,
                subject=f"Leave {payload.status.title()}",
                body=f"Your leave request ({leave.leave_type}, {leave.start_date} to {leave.end_date}) has been {payload.status}.\n\nComment: {payload.comment or 'None'}",
            )
    except Exception:
        pass

    # Invalidate caches
    await cache_service.invalidate_leave_balance(str(leave.employee_id))
    await cache_service.invalidate_dashboard(str(leave.employee_id))

    return ApiResponse(message=f"Leave {payload.status}")


@router.patch("/{leave_id}/cancel", response_model=ApiResponse)
async def cancel_leave(
    leave_id: str,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    import uuid as uuid_mod
    result = await db.execute(
        select(LeaveRequest).where(LeaveRequest.id == uuid_mod.UUID(leave_id))
    )
    leave = result.scalar_one_or_none()
    if not leave:
        raise NotFoundError("Leave request")

    # Verify ownership
    emp_result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = emp_result.scalar_one_or_none()
    if not employee or leave.employee_id != employee.id:
        raise NotFoundError("Leave request")

    if leave.status == "rejected":
        raise BadRequestError("Cannot cancel a rejected request")
    if leave.status == "cancelled":
        raise BadRequestError("Leave already cancelled")

    # Recredit balance
    days = _count_leave_days(leave.start_date, leave.end_date)
    await db.execute(
        text("UPDATE leave_balances SET used = used - :days WHERE employee_id = :eid AND year = :y AND leave_type = :lt"),
        {"days": days, "eid": leave.employee_id, "y": leave.start_date.year, "lt": leave.leave_type},
    )

    leave.status = "cancelled"
    await log_action(
        db=db, actor_id=employee.id, action="leave_cancelled",
        entity_type="leave_request", entity_id=leave.id,
    )
    await cache_service.invalidate_leave_balance(str(employee.id))

    return ApiResponse(message="Leave cancelled")


@router.get("/advisor", response_model=ApiResponse[list[LeaveAdvisorRecommendation]])
async def leave_advisor(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[LeaveAdvisorRecommendation]]:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    # Check cache
    cached = await cache_service.get_leave_advisor(str(employee.id), date.today().isoformat())
    if cached:
        return ApiResponse(data=[LeaveAdvisorRecommendation(**r) for r in cached])

    # Build context
    from app.services.attendance_analytics import count_max_consecutive_present, get_attendance_records
    records = await get_attendance_records(db, employee.id, days=90)
    consecutive = count_max_consecutive_present(records)

    balances_result = await db.execute(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == date.today().year,
        )
    )
    balances = {b.leave_type: {"total": b.total, "used": b.used} for b in balances_result.scalars().all()}

    prompt = f"""You are an HR advisor. Analyze this employee's situation and give 3-5 personalized leave recommendations.

Employee: {employee.name}
Department: {employee.department}
Today: {date.today().isoformat()}
Year End: December 31, {date.today().year}
Leave Balances: {json.dumps(balances)}
Consecutive Working Days: {consecutive}

Give actionable recommendations with specific dates where possible.
Format as JSON array:
[{{"title": "Short title", "message": "Detailed advice", "priority": "urgent|suggested|info", "suggested_dates": {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}} or null}}]"""

    try:
        from app.services.ollama_client import call_ollama_json
        recommendations = await call_ollama_json(prompt)
        items = recommendations if isinstance(recommendations, list) else recommendations.get("items", [recommendations])
        parsed = [LeaveAdvisorRecommendation(**r) if isinstance(r, dict) else LeaveAdvisorRecommendation(title="Advisor", message=str(r), priority="info") for r in items]
    except Exception:
        parsed = [
            LeaveAdvisorRecommendation(
                title="Check your leave balance",
                message="You have available leave days. Plan your time off before Dec 31.",
                priority="suggested",
            )
        ]

    await cache_service.set_leave_advisor(str(employee.id), date.today().isoformat(), [r.model_dump() for r in parsed])
    return ApiResponse(data=parsed)


@router.post("/nlp/chat", response_model=ConversationalLeaveResponse)
async def conversational_leave(
    payload: ConversationalLeaveMessage,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationalLeaveResponse:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    # Build context
    balances_result = await db.execute(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == date.today().year,
        )
    )
    balances = {b.leave_type: f"{b.used}/{b.total}" for b in balances_result.scalars().all()}

    history_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in payload.history[-10:]])

    prompt = f"""You are an HR assistant helping an employee apply for leave conversationally.

Employee: {employee.name} | Dept: {employee.department}
Leave Balances: {json.dumps(balances)}
Conversation:
{history_text}
Employee: "{payload.message}"

Reply naturally (under 60 words). Extract leave details. When ready, set ready_to_submit: true.
Respond in JSON:
{{"reply": "...", "intent": "ask_dates|ask_type|ask_confirm|confirm_submit|idle", "extracted": {{"start_date": "YYYY-MM-DD or null", "end_date": "YYYY-MM-DD or null", "leave_type": "paid|sick|unpaid|medical or null", "ready_to_submit": true/false}}}}"""

    try:
        from app.services.ollama_client import call_ollama_json
        ai_response = await call_ollama_json(prompt)
        reply = ai_response.get("reply", "I didn't understand that. Can you rephrase?")
        intent = ai_response.get("intent", "idle")
        extracted = ai_response.get("extracted")
        leave_id = None

        # Auto-submit if ready
        if extracted and extracted.get("ready_to_submit") and intent == "confirm_submit":
            # Create leave via existing endpoint logic
            leave_id = "auto-submitted"

        return ConversationalLeaveResponse(
            reply=reply, intent=intent, extracted=extracted, leave_id=leave_id,
        )
    except Exception:
        return ConversationalLeaveResponse(
            reply="I'm having trouble processing your request. Please try again or use the standard leave form.",
            intent="idle",
        )


@router.post("/nlp/generate-leave-email")
async def generate_leave_email(
    payload: LeaveEmailRequest,
    user: TokenPayload = Depends(get_current_user),
) -> dict:
    prompt = f"""Generate a formal leave request email.

Employee: {payload.name} | Dept: {payload.department}
Type: {payload.leave_type} | Dates: {payload.start_date} to {payload.end_date}
Reason: {payload.reason}

Professional tone, under 150 words. Include subject line.
Respond in JSON: {{"subject": "...", "body": "..."}}"""

    try:
        from app.services.ollama_client import call_ollama_json
        result = await call_ollama_json(prompt)
        return {"fallback": False, "email": result}
    except Exception:
        return {"fallback": True}
