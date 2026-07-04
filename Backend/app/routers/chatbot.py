"""
HRMS HR Chatbot Router
RAG-lite Q&A grounded in employee's actual DB data.
"""

from __future__ import annotations


from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenPayload
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.employee import Employee
from app.models.leave import LeaveBalance, LeaveRequest
from app.schemas.common import ApiResponse
from app.services.cache import cache_service

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatbotQuestion(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class ChatbotAnswer(BaseModel):
    answer: str


HR_CHATBOT_PROMPT = """You are a helpful HR assistant. Answer the employee's question using ONLY
the data provided below. If the answer is not in the data, say
"I don't have that information — please contact HR directly."

Employee: {name} | Dept: {department}

Leave Balances This Year:
{leave_balances}

Recent Leave Requests:
{leave_requests}

Company Leave Policy:
- Paid Leave: 12 days/year
- Sick Leave: 10 days/year
- Unpaid Leave: unlimited (unpaid)
- Bereavement: 5 days/year
- Balances reset every January 1

Employee's Question: "{question}"

Answer in 2-3 sentences max. Be direct and friendly."""


@router.post("/ask", response_model=ApiResponse[ChatbotAnswer])
async def chatbot_ask(
    payload: ChatbotQuestion,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ChatbotAnswer]:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    # Check cache
    cached = await cache_service.get_chatbot_context(user.user_id)
    if not cached:
        # Build context from DB
        from datetime import date as _date
        balances_result = await db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee.id,
                LeaveBalance.year == _date.today().year,
            )
        )
        balances_text = "\n".join(
            f"- {b.leave_type}: {b.used} used / {b.total} total"
            for b in balances_result.scalars().all()
        )

        leaves_result = await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee.id)
            .order_by(LeaveRequest.created_at.desc())
            .limit(5)
        )
        leaves_text = "\n".join(
            f"- {leave.leave_type} ({leave.start_date} to {leave.end_date}): {leave.status}"
            for leave in leaves_result.scalars().all()
        ) or "No recent leave requests"

        context = {
            "name": employee.name,
            "department": employee.department or "N/A",
            "leave_balances": balances_text,
            "leave_requests": leaves_text,
        }
        await cache_service.set_chatbot_context(user.user_id, context)
    else:
        context = cached

    prompt = HR_CHATBOT_PROMPT.format(**context, question=payload.question)

    try:
        from app.services.ollama_client import call_ollama
        answer = await call_ollama(prompt, model="mistral")
        return ApiResponse(data=ChatbotAnswer(answer=answer))
    except Exception:
        return ApiResponse(
            data=ChatbotAnswer(
                answer="I'm having trouble processing your question right now. Please try again later or contact HR directly."
            )
        )
