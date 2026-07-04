"""Initial schema — all 16 HRMS tables

Revision ID: 001_initial
Revises:
Create Date: 2026-07-04

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable btree_gist for EXCLUDE constraint
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # ── employees ─────────────────────────────────────────────────
    op.create_table(
        "employees",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("clerk_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("employee_id", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("department", sa.String(100), index=True),
        sa.Column("designation", sa.String(100)),
        sa.Column("phone", sa.String(20)),
        sa.Column("address", sa.Text),
        sa.Column("profile_pic", sa.String(500)),
        sa.Column("role", sa.String(20), nullable=False, server_default="employee", index=True),
        sa.Column("date_joined", sa.Date, nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── attendance_records ─────────────────────────────────────────
    op.create_table(
        "attendance_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.Date, nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="present"),
        sa.Column("check_in", sa.DateTime(timezone=True)),
        sa.Column("check_out", sa.DateTime(timezone=True)),
        sa.Column("duration_hours", sa.Numeric(6, 2)),
        sa.Column("location_lat", sa.Numeric(10, 8)),
        sa.Column("location_lng", sa.Numeric(11, 8)),
        sa.Column("check_in_method", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("employee_id", "date", name="uq_attendance_emp_date"),
    )

    # ── leave_requests ────────────────────────────────────────────
    op.create_table(
        "leave_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("leave_type", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("remarks", sa.Text),
        sa.Column("admin_comment", sa.Text),
        sa.Column("formal_reason", sa.String(100)),
        sa.Column("generated_email_body", sa.Text),
        sa.Column("email_sent", sa.Boolean, server_default=sa.text("false")),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    # EXCLUDE constraint: prevents overlapping approved/pending leaves for same employee
    op.execute("""
        ALTER TABLE leave_requests ADD CONSTRAINT EXCL_leave_overlap
        EXCLUDE USING gist (
            employee_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&
        ) WHERE (status != 'rejected')
    """)

    # ── leave_balances ────────────────────────────────────────────
    op.create_table(
        "leave_balances",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("leave_type", sa.String(20), nullable=False),
        sa.Column("total", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("used", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("employee_id", "year", "leave_type", name="uq_leave_balance_emp_year_type"),
    )

    # ── salary_components ─────────────────────────────────────────
    op.create_table(
        "salary_components",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("component", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── payroll_runs ──────────────────────────────────────────────
    op.create_table(
        "payroll_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("gross_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("deductions", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("net_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("pay_stub_url", sa.String(500)),
        sa.Column("components_snapshot", JSONB, nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("employee_id", "month", "year", name="uq_payroll_emp_period"),
    )

    # ── audit_log ─────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="SET NULL"), index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), index=True),
        sa.Column("entity_id", UUID(as_uuid=True)),
        sa.Column("metadata", JSONB),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
    )

    # ── burnout_config ────────────────────────────────────────────
    op.create_table(
        "burnout_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("department", sa.String(100), unique=True, nullable=False),
        sa.Column("max_consecutive_days", sa.Integer, nullable=False, server_default=sa.text("14")),
        sa.Column("max_weekly_overtime_hrs", sa.Integer, nullable=False, server_default=sa.text("10")),
        sa.Column("alert_email", sa.String(255)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── burnout_alerts ────────────────────────────────────────────
    op.create_table(
        "burnout_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("signal", sa.String(50), nullable=False),
        sa.Column("value", sa.Numeric),
        sa.Column("threshold", sa.Numeric),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("resolved", sa.Boolean, server_default=sa.text("false"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── nudges ────────────────────────────────────────────────────
    op.create_table(
        "nudges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("type", sa.String(50), nullable=False, index=True),
        sa.Column("read", sa.Boolean, server_default=sa.text("false"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── public_holidays ───────────────────────────────────────────
    op.create_table(
        "public_holidays",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("date", sa.Date, nullable=False, unique=True),
        sa.Column("year", sa.Integer, nullable=False, index=True),
    )

    # ── office_config ─────────────────────────────────────────────
    op.create_table(
        "office_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("office_lat", sa.Numeric(10, 8)),
        sa.Column("office_lng", sa.Numeric(11, 8)),
        sa.Column("geofence_radius_m", sa.Integer, server_default=sa.text("150")),
        sa.Column("office_ip_subnet", sa.String(20)),
        sa.Column("wifi_checkin_enabled", sa.Boolean, server_default=sa.text("false")),
        sa.Column("gps_checkin_enabled", sa.Boolean, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── chat_channels ─────────────────────────────────────────────
    op.create_table(
        "chat_channels",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("name", sa.String(100)),
        sa.Column("department", sa.String(100)),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── chat_messages ─────────────────────────────────────────────
    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("channel_id", UUID(as_uuid=True), sa.ForeignKey("chat_channels.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sender_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("message_type", sa.String(20), server_default="text"),
        sa.Column("meeting_meta", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
    )

    # ── chat_reads ────────────────────────────────────────────────
    op.create_table(
        "chat_reads",
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("message_id", UUID(as_uuid=True), sa.ForeignKey("chat_messages.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("employee_id", "message_id", name="uq_chat_read_emp_msg"),
    )

    # ── meeting_rsvp ──────────────────────────────────────────────
    op.create_table(
        "meeting_rsvp",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("message_id", UUID(as_uuid=True), sa.ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True),
        sa.Column("employee_id", UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), index=True),
        sa.Column("response", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("message_id", "employee_id", name="uq_meeting_rsvp_emp_msg"),
    )

    # ── Composite indexes for performance ─────────────────────────
    op.create_index("ix_attendance_emp_date_status", "attendance_records", ["employee_id", "date", "status"])
    op.create_index("ix_leave_emp_status", "leave_requests", ["employee_id", "status"])
    op.create_index("ix_leave_status_created", "leave_requests", ["status", "created_at"])
    op.create_index("ix_payroll_emp_period", "payroll_runs", ["employee_id", "year", "month"])
    op.create_index("ix_audit_actor_created", "audit_log", ["actor_id", "created_at"])
    op.create_index("ix_audit_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_chat_messages_channel_created", "chat_messages", ["channel_id", "created_at"])
    op.create_index("ix_nudges_emp_read", "nudges", ["employee_id", "read"])
    op.create_index("ix_burnout_alerts_emp_resolved", "burnout_alerts", ["employee_id", "resolved"])
    op.create_index("ix_salary_components_emp_effective", "salary_components", ["employee_id", "effective_from"])


def downgrade() -> None:
    op.drop_table("meeting_rsvp")
    op.drop_table("chat_reads")
    op.drop_table("chat_messages")
    op.drop_table("chat_channels")
    op.drop_table("office_config")
    op.drop_table("public_holidays")
    op.drop_table("nudges")
    op.drop_table("burnout_alerts")
    op.drop_table("burnout_config")
    op.drop_table("audit_log")
    op.drop_table("payroll_runs")
    op.drop_table("salary_components")
    op.drop_table("leave_balances")
    op.execute("ALTER TABLE leave_requests DROP CONSTRAINT IF EXISTS EXCL_leave_overlap")
    op.drop_table("leave_requests")
    op.drop_table("attendance_records")
    op.drop_table("employees")
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
