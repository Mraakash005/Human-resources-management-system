"""
HRMS Burnout Models
Burnout config per department and burnout alert logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BurnoutConfig(Base):
    __tablename__ = "burnout_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    department: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    max_consecutive_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    max_weekly_overtime_hrs: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    alert_email: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<BurnoutConfig {self.department} consec={self.max_consecutive_days}>"


class BurnoutAlert(Base):
    __tablename__ = "burnout_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    signal: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # consecutive_days|weekly_overtime|extreme_hours|leave_not_taken|absence_spike|half_day_pattern
    value: Mapped[float | None] = mapped_column(Numeric)
    threshold: Mapped[float | None] = mapped_column(Numeric)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # high|medium|watch
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<BurnoutAlert {self.signal} severity={self.severity}>"
