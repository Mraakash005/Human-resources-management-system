"""
HRMS Nudge Schemas
Request/response schemas for proactive nudge system.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID


from app.schemas.common import HRMSBaseModel


class NudgeResponse(HRMSBaseModel):
    """Single nudge response."""
    id: UUID
    message: str
    type: str
    read: bool
    created_at: datetime


class NudgeListResponse(HRMSBaseModel):
    """List of nudges."""
    nudges: list[NudgeResponse]
    unread_count: int


class NudgeMarkRead(HRMSBaseModel):
    """Mark nudge as read."""
    pass
