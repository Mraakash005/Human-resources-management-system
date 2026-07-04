"""
HRMS Database Verification Script
Verifies all tables exist and migrations are applied.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

EXPECTED_TABLES = [
    "employees",
    "attendance_records",
    "leave_requests",
    "leave_balances",
    "salary_components",
    "payroll_runs",
    "burnout_config",
    "burnout_alerts",
    "audit_log",
    "nudges",
    "public_holidays",
    "office_config",
    "chat_channels",
    "chat_messages",
    "chat_reads",
    "meeting_rsvp",
]


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)

    print("═" * 50)
    print("  HRMS Database Verification")
    print("═" * 50)
    print()

    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = {row[0] for row in result.all()}

            print("  Expected tables:")
            missing = []
            for table in EXPECTED_TABLES:
                exists = table in tables
                status = "✅" if exists else "❌"
                print(f"    {status} {table}")
                if not exists:
                    missing.append(table)

            print()
            if missing:
                print(f"  ❌ {len(missing)} tables missing: {', '.join(missing)}")
                print("  Run: alembic upgrade head")
                sys.exit(1)
            else:
                print(f"  ✅ All {len(EXPECTED_TABLES)} tables exist!")

            # Check indexes
            result = await conn.execute(text(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'"
            ))
            indexes = {row[0] for row in result.all()}
            print(f"\n  Indexes found: {len(indexes)}")

            # Check constraints
            result = await conn.execute(text(
                "SELECT conname FROM pg_constraint WHERE connamespace = 'public'::regnamespace"
            ))
            constraints = {row[0] for row in result.all()}
            print(f"  Constraints found: {len(constraints)}")

    except Exception as exc:
        print(f"  ❌ Database connection failed: {exc}")
        sys.exit(1)
    finally:
        await engine.dispose()

    print("\n  ✅ Database verification complete!")


if __name__ == "__main__":
    asyncio.run(main())
