# Alembic Migrations

Async migration support for PostgreSQL via SQLAlchemy. Manages schema versioning for all 16 HRMS tables.

## Alembic Configuration

`alembic.ini` at project root:

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = postgresql+asyncpg://hrms:password@localhost:5432/hrms_db
```

The `sqlalchemy.url` is overridden at runtime by `migrations/env.py` using `settings.DATABASE_URL` from the application config.

### Logging

```ini
[loggers]
keys = root,sqlalchemy,alembic

[logger_alembic]
level = INFO
```

---

## Async Migration Support

`migrations/env.py` uses `async_engine_from_config` for async migration execution:

```python
from sqlalchemy.ext.asyncio import async_engine_from_config

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()
```

- Uses `NullPool` for migrations (no connection pooling needed)
- `asyncio.run()` called from `run_migrations_online()` to bridge sync/async

### Model Auto-Discovery

```python
from app.models import *  # noqa: F401, F403
```

All models are imported in `env.py` so Alembic can autodetect schema changes.

---

## Initial Migration

`migrations/versions/001_initial_schema.py` — Creates all 16 HRMS tables.

**Revision**: `001_initial`  
**Down revision**: `None` (root migration)  
**Date**: 2026-07-04

### Tables Created

| Table | Key Features |
|---|---|
| `employees` | UUID PK, `clerk_id` unique index, `role` index |
| `attendance_records` | FK → employees, unique constraint (emp+date), composite index |
| `leave_requests` | FK → employees, EXCLUDE constraint for overlapping dates |
| `leave_balances` | FK → employees, unique constraint (emp+year+type) |
| `salary_components` | FK → employees, effective_from date |
| `payroll_runs` | FK → employees, JSONB `components_snapshot`, unique constraint |
| `audit_log` | FK → employees (SET NULL), JSONB `metadata` |
| `burnout_config` | Unique department, configurable thresholds |
| `burnout_alerts` | FK → employees, severity levels |
| `nudges` | FK → employees, read/unread tracking |
| `public_holidays` | Unique date, year index |
| `office_config` | Geofence settings, IP subnet |
| `chat_channels` | Type-based (announcement, department, direct, meeting) |
| `chat_messages` | FK → channels + employees, JSONB `meeting_meta` |
| `chat_reads` | Composite PK (employee + message) |
| `meeting_rsvp` | FK → messages + employees, unique constraint |

### Extensions

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist
```

Required for the `EXCLUDE` constraint on `leave_requests` (prevents overlapping approved leaves).

### Composite Indexes

10 performance indexes created for common query patterns:

- `ix_attendance_emp_date_status` — attendance lookups
- `ix_leave_emp_status`, `ix_leave_status_created` — leave filtering
- `ix_payroll_emp_period` — payroll period queries
- `ix_audit_actor_created`, `ix_audit_entity` — audit log searches
- `ix_chat_messages_channel_created` — chat message ordering
- `ix_nudges_emp_read` — unread nudge counts
- `ix_burnout_alerts_emp_resolved` — burnout alert filtering
- `ix_salary_components_emp_effective` — salary history

---

## How to Create New Migrations

### Auto-generate from model changes

```bash
alembic revision --autogenerate -m "description_of_change"
```

This compares current models against the database and generates a migration script.

### Create empty migration (manual)

```bash
alembic revision -m "description_of_change"
```

Edit the generated file in `migrations/versions/` to add `upgrade()` and `downgrade()` logic.

---

## How to Apply / Rollback

### Apply all pending migrations

```bash
alembic upgrade head
```

### Apply to a specific revision

```bash
alembic upgrade 001_initial
```

### Rollback one step

```bash
alembic downgrade -1
```

### Rollback to a specific revision

```bash
alembic downgrade 001_initial
```

### Rollback everything

```bash
alembic downgrade base
```

### Check current version

```bash
alembic current
```

### View migration history

```bash
alembic history
```

---

## Migration Safety

### Production Checklist

1. **Never** run `alembic upgrade head` in production without reviewing the migration first
2. Always test migrations on a staging database before production
3. Use `--sql` mode to preview generated SQL:
   ```bash
   alembic upgrade head --sql > migration.sql
   ```
4. Back up the database before applying destructive migrations
5. The initial migration is non-destructive (CREATE TABLE only)

### Downgrade Support

Every migration includes a `downgrade()` function. The initial migration drops all tables and constraints in reverse dependency order:

```python
def downgrade() -> None:
    op.drop_table("meeting_rsvp")
    op.drop_table("chat_reads")
    # ... (reverse order)
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
```

### Schema Validation

After migrations, run the verification script:

```bash
python scripts/verify_database.py
```

Checks that all 16 expected tables exist in the database.
