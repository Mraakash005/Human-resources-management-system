# HRMS Database Reference

## Overview

- **Engine:** PostgreSQL (async via `asyncpg`)
- **ORM:** SQLAlchemy 2.0 async with Alembic migrations
- **Tables:** 16 total
- **UUID Primary Keys:** All tables use `gen_random_uuid()` server defaults
- **Timezone-aware timestamps:** All `DateTime` columns use `timezone=True`

---

## Tables

### 1. `employees`

Core entity for all HRMS operations.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` |
| `clerk_id` | `VARCHAR(255)` | UNIQUE, NOT NULL, indexed |
| `employee_id` | `VARCHAR(50)` | UNIQUE, NOT NULL, indexed |
| `name` | `VARCHAR(255)` | NOT NULL |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, indexed |
| `department` | `VARCHAR(100)` | nullable, indexed |
| `designation` | `VARCHAR(100)` | nullable |
| `phone` | `VARCHAR(20)` | nullable |
| `address` | `TEXT` | nullable |
| `profile_pic` | `VARCHAR(500)` | nullable |
| `role` | `VARCHAR(20)` | NOT NULL, default `'employee'`, indexed |
| `date_joined` | `DATE` | NOT NULL, default `CURRENT_DATE` |
| `is_active` | `BOOLEAN` | NOT NULL, default `true`, indexed |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

---

### 2. `attendance_records`

Daily attendance records with check-in/out, geolocation, and duration.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, NOT NULL, indexed |
| `date` | `DATE` | NOT NULL, indexed |
| `status` | `VARCHAR(20)` | NOT NULL, default `'present'` |
| `check_in` | `TIMESTAMPTZ` | nullable |
| `check_out` | `TIMESTAMPTZ` | nullable |
| `duration_hours` | `NUMERIC(6,2)` | nullable |
| `location_lat` | `NUMERIC(10,8)` | nullable |
| `location_lng` | `NUMERIC(11,8)` | nullable |
| `check_in_method` | `VARCHAR(20)` | nullable (`manual\|gps\|wifi\|voice`) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

**Constraints:**
- `UNIQUE (employee_id, date)` — named `uq_attendance_emp_date`

---

### 3. `leave_requests`

Leave applications with approval workflow.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, NOT NULL, indexed |
| `leave_type` | `VARCHAR(20)` | NOT NULL (`paid\|sick\|unpaid\|bereavement\|medical`) |
| `start_date` | `DATE` | NOT NULL |
| `end_date` | `DATE` | NOT NULL |
| `status` | `VARCHAR(20)` | NOT NULL, default `'pending'`, indexed |
| `remarks` | `TEXT` | nullable |
| `admin_comment` | `TEXT` | nullable |
| `formal_reason` | `VARCHAR(100)` | nullable |
| `generated_email_body` | `TEXT` | nullable |
| `email_sent` | `BOOLEAN` | default `false` |
| `reviewed_by` | `UUID` | FK → `employees.id` ON DELETE SET NULL |
| `reviewed_at` | `TIMESTAMPTZ` | nullable |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

**Constraints:**
- `EXCLUDE USING gist (employee_id WITH =, daterange(start_date, end_date, '[]') WITH &&) WHERE (status != 'rejected')` — named `EXCL_leave_overlap`. Prevents overlapping approved/pending leaves for the same employee.

---

### 4. `leave_balances`

Annual leave entitlements per employee per leave type.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, NOT NULL, indexed |
| `year` | `INTEGER` | NOT NULL |
| `leave_type` | `VARCHAR(20)` | NOT NULL |
| `total` | `INTEGER` | NOT NULL, default `0` |
| `used` | `INTEGER` | NOT NULL, default `0` |

**Constraints:**
- `UNIQUE (employee_id, year, leave_type)` — named `uq_leave_balance_emp_year_type`

---

### 5. `salary_components`

Salary breakdown by component (basic, HRA, transport, etc.).

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, NOT NULL, indexed |
| `component` | `VARCHAR(100)` | NOT NULL |
| `amount` | `NUMERIC(12,2)` | NOT NULL |
| `effective_from` | `DATE` | NOT NULL |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

---

### 6. `payroll_runs`

Immutable monthly payroll snapshots.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, NOT NULL, indexed |
| `month` | `INTEGER` | NOT NULL |
| `year` | `INTEGER` | NOT NULL |
| `gross_pay` | `NUMERIC(12,2)` | NOT NULL |
| `deductions` | `NUMERIC(12,2)` | NOT NULL, default `0` |
| `net_pay` | `NUMERIC(12,2)` | NOT NULL |
| `pay_stub_url` | `VARCHAR(500)` | nullable |
| `components_snapshot` | `JSONB` | NOT NULL |
| `finalized_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

**Constraints:**
- `UNIQUE (employee_id, month, year)` — named `uq_payroll_emp_period`

---

### 7. `audit_log`

Immutable audit trail for all admin actions and mutations.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `actor_id` | `UUID` | FK → `employees.id` ON DELETE SET NULL, indexed |
| `action` | `VARCHAR(100)` | NOT NULL, indexed |
| `entity_type` | `VARCHAR(50)` | nullable, indexed |
| `entity_id` | `UUID` | nullable |
| `metadata` | `JSONB` | nullable |
| `ip_address` | `VARCHAR(50)` | nullable |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()`, indexed |

---

### 8. `burnout_config`

Per-department burnout detection thresholds.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `department` | `VARCHAR(100)` | UNIQUE, NOT NULL |
| `max_consecutive_days` | `INTEGER` | NOT NULL, default `14` |
| `max_weekly_overtime_hrs` | `INTEGER` | NOT NULL, default `10` |
| `alert_email` | `VARCHAR(255)` | nullable |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

---

### 9. `burnout_alerts`

Generated burnout warning records.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, NOT NULL, indexed |
| `signal` | `VARCHAR(50)` | NOT NULL (`consecutive_days\|weekly_overtime\|extreme_hours\|leave_not_taken\|absence_spike\|half_day_pattern`) |
| `value` | `NUMERIC` | nullable |
| `threshold` | `NUMERIC` | nullable |
| `severity` | `VARCHAR(20)` | NOT NULL (`high\|medium\|watch`) |
| `resolved` | `BOOLEAN` | default `false`, indexed |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

---

### 10. `nudges`

Proactive notification queue for employees.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, NOT NULL, indexed |
| `message` | `TEXT` | NOT NULL |
| `type` | `VARCHAR(50)` | NOT NULL, indexed (`burnout\|leave_lapse\|missed_checkout\|approval\|rejection\|birthday\|pending_approval`) |
| `read` | `BOOLEAN` | default `false`, indexed |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

---

### 11. `public_holidays`

Company-wide public holidays.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `name` | `VARCHAR(100)` | NOT NULL |
| `date` | `DATE` | NOT NULL, UNIQUE |
| `year` | `INTEGER` | NOT NULL, indexed |

---

### 12. `office_config`

Geofence and WiFi check-in configuration.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `office_lat` | `NUMERIC(10,8)` | nullable |
| `office_lng` | `NUMERIC(11,8)` | nullable |
| `geofence_radius_m` | `INTEGER` | default `150` |
| `office_ip_subnet` | `VARCHAR(20)` | nullable |
| `wifi_checkin_enabled` | `BOOLEAN` | default `false` |
| `gps_checkin_enabled` | `BOOLEAN` | default `true` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

---

### 13. `chat_channels`

Internal team chat channels.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `type` | `VARCHAR(30)` | NOT NULL (`announcement\|department\|direct\|meeting`) |
| `name` | `VARCHAR(100)` | nullable |
| `department` | `VARCHAR(100)` | nullable |
| `created_by` | `UUID` | FK → `employees.id` ON DELETE SET NULL |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

---

### 14. `chat_messages`

Chat message content.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `channel_id` | `UUID` | FK → `chat_channels.id` ON DELETE CASCADE, NOT NULL, indexed |
| `sender_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, NOT NULL, indexed |
| `body` | `TEXT` | NOT NULL |
| `message_type` | `VARCHAR(20)` | default `'text'` (`text\|meeting_invite\|announcement`) |
| `meeting_meta` | `JSONB` | nullable |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()`, indexed |

---

### 15. `chat_reads`

Read receipts per employee per message.

| Column | Type | Constraints |
|---|---|---|
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, composite PK |
| `message_id` | `UUID` | FK → `chat_messages.id` ON DELETE CASCADE, composite PK |
| `read_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

**Constraints:**
- `UNIQUE (employee_id, message_id)` — named `uq_chat_read_emp_msg`

---

### 16. `meeting_rsvp`

Meeting invite RSVP tracking.

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK |
| `message_id` | `UUID` | FK → `chat_messages.id` ON DELETE CASCADE, indexed |
| `employee_id` | `UUID` | FK → `employees.id` ON DELETE CASCADE, indexed |
| `response` | `VARCHAR(10)` | NOT NULL (`accept\|decline\|maybe`) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` |

**Constraints:**
- `UNIQUE (message_id, employee_id)` — named `uq_meeting_rsvp_emp_msg`

---

## Relationships & Foreign Keys

```
employees (1) ──→ (N) attendance_records      [employee_id, CASCADE]
employees (1) ──→ (N) leave_requests           [employee_id, CASCADE]
employees (1) ──→ (N) leave_balances           [employee_id, CASCADE]
employees (1) ──→ (N) salary_components        [employee_id, CASCADE]
employees (1) ──→ (N) payroll_runs             [employee_id, CASCADE]
employees (1) ──→ (N) burnout_alerts           [employee_id, CASCADE]
employees (1) ──→ (N) nudges                   [employee_id, CASCADE]
employees (1) ──→ (N) chat_messages            [sender_id, CASCADE]
employees (1) ──→ (N) meeting_rsvp             [employee_id, CASCADE]
employees (1) ──→ (N) chat_reads               [employee_id, CASCADE]
employees (1) ──→ (N) audit_log                [actor_id, SET NULL]
employees (1) ──→ (N) leave_requests           [reviewed_by, SET NULL]
employees (1) ──→ (N) chat_channels            [created_by, SET NULL]
chat_channels (1) ──→ (N) chat_messages        [channel_id, CASCADE]
chat_messages (1) ──→ (N) chat_reads           [message_id, CASCADE]
chat_messages (1) ──→ (N) meeting_rsvp         [message_id, CASCADE]
```

---

## Key Indexes

| Index | Table | Columns | Purpose |
|---|---|---|---|
| `ix_attendance_emp_date_status` | `attendance_records` | `employee_id, date, status` | Calendar/heatmap queries |
| `ix_leave_emp_status` | `leave_requests` | `employee_id, status` | My pending leaves |
| `ix_leave_status_created` | `leave_requests` | `status, created_at` | Admin leave queue |
| `ix_payroll_emp_period` | `payroll_runs` | `employee_id, year, month` | Payroll lookup |
| `ix_audit_actor_created` | `audit_log` | `actor_id, created_at` | Activity feed |
| `ix_audit_entity` | `audit_log` | `entity_type, entity_id` | Entity history |
| `ix_chat_messages_channel_created` | `chat_messages` | `channel_id, created_at` | Channel message list |
| `ix_nudges_emp_read` | `nudges` | `employee_id, read` | Unread nudge count |
| `ix_burnout_alerts_emp_resolved` | `burnout_alerts` | `employee_id, resolved` | Active alerts |
| `ix_salary_components_emp_effective` | `salary_components` | `employee_id, effective_from` | Current salary lookup |

---

## EXCLUDE Constraint — Leave Overlap Prevention

```sql
ALTER TABLE leave_requests ADD CONSTRAINT EXCL_leave_overlap
EXCLUDE USING gist (
    employee_id WITH =,
    daterange(start_date, end_date, '[]') WITH &&
) WHERE (status != 'rejected')
```

**How it works:**
- Uses PostgreSQL GiST index with `btree_gist` extension
- The `daterange(start_date, end_date, '[]')` creates an inclusive range
- `&&` operator detects any overlap between date ranges
- `WHERE (status != 'rejected')` — rejected leaves are excluded from the constraint
- Prevents an employee from having two overlapping approved/pending leaves

**Application-layer defense (additional):**
- Before inserting a leave request, the service checks `LeaveBalance` via an atomic SQL `UPDATE ... WHERE (total - used) >= :days` to prevent double-spending

---

## Atomic Balance Deduction Pattern

```sql
UPDATE leave_balances
SET used = used + :days
WHERE employee_id = :emp_id
  AND year = :year
  AND leave_type = :leave_type
  AND (total - used) >= :days
RETURNING id
```

**Why atomic:**
- The `WHERE (total - used) >= :days` condition ensures the deduction only succeeds if sufficient balance exists
- If two concurrent requests try to deduct the same balance, only one will succeed (the other gets 0 rows back)
- The `RETURNING id` allows the application to detect the race condition and return a `409 Conflict`

**Balance recrediting on rejection/cancellation:**
```sql
UPDATE leave_balances
SET used = used - :days
WHERE employee_id = :eid AND year = :y AND leave_type = :lt
```

---

## Connection Pooling Configuration

**Async engine settings** (from `app/core/config.py`):

| Setting | Default | Description |
|---|---|---|
| `DB_POOL_SIZE` | `20` | Base number of connections (1–100) |
| `DB_MAX_OVERFLOW` | `10` | Extra connections beyond pool_size (0–50) |
| `DB_POOL_TIMEOUT` | `30` | Seconds to wait for a connection |
| `DB_POOL_RECYCLE` | `1800` | Seconds before a connection is recycled |
| `pool_pre_ping` | `True` | Validates connections before use |

**Testing mode:** Uses `NullPool` (no pooling, each request opens a new connection).

**Session lifecycle:**
```python
async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
```

Each request gets a session via `get_db()` dependency with automatic commit/rollback:
```python
async with session_factory() as session:
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

**Redis connection pool** (used for caching, rate limiting, pub/sub):

| Setting | Default | Description |
|---|---|---|
| `REDIS_MAX_CONNECTIONS` | `20` | Max pooled Redis connections |
| `REDIS_DECODER_RESPONSES` | `True` | Auto-decode bytes to strings |

---

## Redis Cache Keys

| Pattern | TTL | Purpose |
|---|---|---|
| `role_verified:{clerk_id}` | 120s | Clerk role verification cache |
| `dashboard:{clerk_id}:{role}` | 60s | Dashboard response cache |
| `attendance:{emp_id}:{date}` | 3600s | Double check-in prevention lock |
| `leave_balance:{emp_id}` | 300s | Leave balance cache |
| `heatmap:{emp_id}:{year}` | 3600s | Attendance heatmap cache |
| `leave_advisor:{emp_id}:{date}` | 3600s | AI leave advisor cache |
| `chatbot:{clerk_id}` | 300s | Chatbot context cache |
| `ratelimit:{category}:{ip}` | 60s | Sliding window rate limiter |
| `webhook_event:{svix_id}` | 300s | Webhook replay protection |
