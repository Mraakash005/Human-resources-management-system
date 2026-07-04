"""
HRMS Chat Service
Channel management, message delivery via Redis pub/sub + SSE.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatChannel, ChatMessage, ChatRead, MeetingRSVP
from app.models.employee import Employee
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)


async def get_or_create_channel(
    db: AsyncSession,
    channel_type: str,
    name: str | None = None,
    department: str | None = None,
    created_by: UUID | None = None,
) -> ChatChannel:
    """Get existing channel or create a new one."""
    query = select(ChatChannel).where(ChatChannel.type == channel_type)
    if department:
        query = query.where(ChatChannel.department == department)
    if name:
        query = query.where(ChatChannel.name == name)

    result = await db.execute(query)
    channel = result.scalar_one_or_none()
    if channel:
        return channel

    channel = ChatChannel(
        type=channel_type, name=name, department=department, created_by=created_by
    )
    db.add(channel)
    await db.flush()
    return channel


async def send_chat_message(
    db: AsyncSession,
    channel_id: UUID,
    sender_id: UUID,
    body: str,
    message_type: str = "text",
    meeting_meta: dict | None = None,
) -> ChatMessage:
    """Send a message to a channel and publish via Redis pub/sub."""
    msg = ChatMessage(
        channel_id=channel_id,
        sender_id=sender_id,
        body=body[:1000],
        message_type=message_type,
        meeting_meta=meeting_meta,
    )
    db.add(msg)
    await db.flush()

    # Get sender name
    sender_result = await db.execute(select(Employee).where(Employee.id == sender_id))
    sender = sender_result.scalar_one_or_none()
    sender_name = sender.name if sender else "Unknown"

    # Publish to Redis for SSE delivery
    message_data = {
        "id": str(msg.id),
        "sender_id": str(sender_id),
        "sender": sender_name,
        "body": msg.body,
        "type": msg.message_type,
        "meeting_meta": msg.meeting_meta,
        "time": msg.created_at.isoformat() if msg.created_at else "",
    }
    await redis_manager.publish(f"chat:{channel_id}", json.dumps(message_data))

    return msg


async def get_channel_messages(
    db: AsyncSession,
    channel_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Get messages for a channel with sender names."""
    result = await db.execute(
        select(ChatMessage, Employee.name)
        .join(Employee, ChatMessage.sender_id == Employee.id)
        .where(ChatMessage.channel_id == channel_id)
        .order_by(ChatMessage.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": msg.id,
            "channel_id": msg.channel_id,
            "sender_id": msg.sender_id,
            "sender_name": name,
            "body": msg.body,
            "message_type": msg.message_type,
            "meeting_meta": msg.meeting_meta,
            "created_at": msg.created_at,
        }
        for msg, name in reversed(rows)
    ]


async def get_unread_count(
    db: AsyncSession, channel_id: UUID, employee_id: UUID
) -> int:
    """Count unread messages in a channel for an employee."""
    last_read = await db.execute(
        select(ChatRead.read_at)
        .where(
            ChatRead.employee_id == employee_id,
            ChatRead.message_id.in_(
                select(ChatMessage.id).where(ChatMessage.channel_id == channel_id)
            ),
        )
        .order_by(ChatRead.read_at.desc())
        .limit(1)
    )
    last_read_time = last_read.scalar_one_or_none()

    query = select(func.count(ChatMessage.id)).where(
        ChatMessage.channel_id == channel_id
    )
    if last_read_time:
        query = query.where(ChatMessage.created_at > last_read_time)

    result = await db.execute(query)
    return result.scalar() or 0


async def mark_channel_read(
    db: AsyncSession, channel_id: UUID, employee_id: UUID
) -> None:
    """Mark all messages in a channel as read by an employee."""
    messages_result = await db.execute(
        select(ChatMessage.id)
        .where(ChatMessage.channel_id == channel_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    last_msg_id = messages_result.scalar_one_or_none()
    if last_msg_id:
        existing = await db.execute(
            select(ChatRead).where(
                ChatRead.employee_id == employee_id,
                ChatRead.message_id == last_msg_id,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(ChatRead(employee_id=employee_id, message_id=last_msg_id))


async def respond_to_meeting(
    db: AsyncSession,
    message_id: UUID,
    employee_id: UUID,
    response: str,
) -> MeetingRSVP:
    """Respond to a meeting invite."""
    existing = await db.execute(
        select(MeetingRSVP).where(
            MeetingRSVP.message_id == message_id,
            MeetingRSVP.employee_id == employee_id,
        )
    )
    rsvp = existing.scalar_one_or_none()
    if rsvp:
        rsvp.response = response
    else:
        rsvp = MeetingRSVP(
            message_id=message_id, employee_id=employee_id, response=response
        )
        db.add(rsvp)
    return rsvp


async def get_employee_channels(db: AsyncSession, employee_id: UUID) -> list[ChatChannel]:
    """Get all channels an employee has access to."""
    employee_result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = employee_result.scalar_one_or_none()
    if not employee:
        return []

    query = select(ChatChannel).where(
        (ChatChannel.type == "announcement")
        | ((ChatChannel.type == "department") & (ChatChannel.department == employee.department))
        | (ChatChannel.type == "direct")
    )
    result = await db.execute(query)
    return list(result.scalars().all())
