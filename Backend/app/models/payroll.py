"""
HRMS Payroll Models
Salary components and immutable payroll run snapshots.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SalaryComponent(Base):
    __tablename__ = "salary_components"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # basic_salary, hra, transport, performance_bonus, etc.
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SalaryComponent {self.component}={self.amount}>"


class PayrollRun(Base):
    __tablename__ = "payroll_runs"
    __table_args__ = (
        UniqueConstraint("employee_id", "month", "year", name="uq_payroll_emp_period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    gross_pay: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    deductions: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    net_pay: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    pay_stub_url: Mapped[str | None] = mapped_column(String(500))
    components_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    finalized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<PayrollRun {self.employee_id} {self.month}/{self.year} net={self.net_pay}>"
