"""
HRMS Config Models
Public holidays and office configuration (geofence, WiFi, GPS).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<PublicHoliday {self.name} {self.date}>"


class OfficeConfig(Base):
    __tablename__ = "office_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    office_lat: Mapped[float | None] = mapped_column(Numeric(10, 8))
    office_lng: Mapped[float | None] = mapped_column(Numeric(11, 8))
    geofence_radius_m: Mapped[int] = mapped_column(Integer, default=150)
    office_ip_subnet: Mapped[str | None] = mapped_column(String(20))
    wifi_checkin_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    gps_checkin_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<OfficeConfig gps={self.gps_checkin_enabled} wifi={self.wifi_checkin_enabled}>"
