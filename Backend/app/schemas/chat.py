"""
HRMS Chat Schemas
Request/response schemas for internal team chat.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import HRMSBaseModel


class ChatChannelResponse(HRMSBaseModel):
    """Chat channel response."""
    id: UUID
    type: str
    name: str | None = None
    department: str | None = None
    created_at: datetime


class ChatMessageResponse(HRMSBaseModel):
    """Chat message response."""
    id: UUID
    channel_id: UUID
    sender_id: UUID
    sender_name: str | None = None
    body: str
    message_type: str
    meeting_meta: dict | None = None
    created_at: datetime


class ChatMessageCreate(HRMSBaseModel):
    """Request to send a chat message."""
    channel_id: UUID
    body: str = Field(..., min_length=1, max_length=1000)
    message_type: str = Field(default="text", pattern=r"^(text|meeting_invite|announcement)$")
    meeting_meta: dict | None = None


class MeetingInviteMeta(HRMSBaseModel):
    """Meeting invite metadata."""
    title: str
    date: str
    time: str
    duration_minutes: int = 60
    location: str
    agenda: str | None = None
    rsvp_required: bool = True


class MeetingRSVPResponse(HRMSBaseModel):
    """Meeting RSVP response."""
    id: UUID
    message_id: UUID
    employee_id: UUID
    employee_name: str | None = None
    response: str
    created_at: datetime


class MeetingRSVPUpdate(HRMSBaseModel):
    """Request to update meeting RSVP."""
    response: str = Field(..., pattern=r"^(accept|decline|maybe)$")


class UnreadCountResponse(HRMSBaseModel):
    """Unread message count."""
    channel_id: UUID
    unread_count: int
