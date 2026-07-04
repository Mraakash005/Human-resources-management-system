"""
HRMS Chat Router
Internal team chat, SSE streaming, meeting invites.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, TokenPayload
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.redis import redis_manager
from app.models.chat import ChatChannel
from app.models.employee import Employee
from app.schemas.chat import (
    ChatChannelResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    MeetingRSVPResponse,
    MeetingRSVPUpdate,
    UnreadCountResponse,
)
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/channels", response_model=list[ChatChannelResponse])
async def list_channels(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatChannelResponse]:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    channels = await chat_service.get_employee_channels(db, employee.id)
    return [ChatChannelResponse.model_validate(c) for c in channels]


@router.get("/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    channel_id: UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessageResponse]:
    messages = await chat_service.get_channel_messages(db, channel_id, limit, offset)
    return [ChatMessageResponse(**m) for m in messages]


@router.post("/messages", response_model=ChatMessageResponse)
async def send_message(
    payload: ChatMessageCreate,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    # Permission check
    channel_result = await db.execute(
        select(ChatChannel).where(ChatChannel.id == payload.channel_id)
    )
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise NotFoundError("Chat channel")

    if channel.type in ("announcement", "department", "meeting") and employee.role != "admin":
        raise ForbiddenError("Only HR/Admin can send to this channel")

    msg = await chat_service.send_chat_message(
        db=db,
        channel_id=payload.channel_id,
        sender_id=employee.id,
        body=payload.body,
        message_type=payload.message_type,
        meeting_meta=payload.meeting_meta,
    )

    return ChatMessageResponse(
        id=msg.id,
        channel_id=msg.channel_id,
        sender_id=msg.sender_id,
        sender_name=employee.name,
        body=msg.body,
        message_type=msg.message_type,
        meeting_meta=msg.meeting_meta,
        created_at=msg.created_at,
    )


@router.get("/unread", response_model=list[UnreadCountResponse])
async def get_unread_counts(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UnreadCountResponse]:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    channels = await chat_service.get_employee_channels(db, employee.id)
    counts = []
    for ch in channels:
        count = await chat_service.get_unread_count(db, ch.id, employee.id)
        counts.append(UnreadCountResponse(channel_id=ch.id, unread_count=count))
    return counts


@router.post("/read/{channel_id}")
async def mark_read(
    channel_id: UUID,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")
    await chat_service.mark_channel_read(db, channel_id, employee.id)
    return {"success": True}


@router.post("/rsvp/{message_id}")
async def rsvp_meeting(
    message_id: UUID,
    payload: MeetingRSVPUpdate,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingRSVPResponse:
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFoundError("Employee")

    rsvp = await chat_service.respond_to_meeting(db, message_id, employee.id, payload.response)
    return MeetingRSVPResponse(
        id=rsvp.id, message_id=rsvp.message_id, employee_id=rsvp.employee_id,
        response=rsvp.response, created_at=rsvp.created_at,
    )


@router.get("/stream/{channel_id}")
async def chat_stream(
    channel_id: UUID,
    user: TokenPayload = Depends(get_current_user),
) -> StreamingResponse:
    async def event_generator():
        pubsub = redis_manager.pubsub()
        await pubsub.subscribe(f"chat:{channel_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data'].decode()}\n\n"
        finally:
            await pubsub.unsubscribe(f"chat:{channel_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
