# HRMS Entity-Relationship Diagram

## Text-Based ER Diagram

```
                            ┌─────────────────────┐
                            │     employees        │
                            │─────────────────────│
                            │ PK id (UUID)        │
                            │    clerk_id (UQ)    │
                            │    employee_id (UQ) │
                            │    name             │
                            │    email (UQ)       │
                            │    department       │
                            │    designation      │
                            │    phone            │
                            │    address          │
                            │    profile_pic      │
                            │    role             │
                            │    date_joined      │
                            │    is_active        │
                            │    created_at       │
                            │    updated_at       │
                            └────────┬────────────┘
                                     │
            ┌────────────────────────┼────────────────────────────────────┐
            │                        │                                    │
            │ 1:N                   1:N                                  1:N
            ▼                        ▼                                    ▼
┌──────────────────────┐  ┌──────────────────────┐          ┌──────────────────────┐
│  attendance_records   │  │    leave_requests     │          │    salary_components  │
│──────────────────────│  │──────────────────────│          │──────────────────────│
│ PK id               │  │ PK id                │          │ PK id                │
│ FK employee_id ──────│  │ FK employee_id ──────│          │ FK employee_id ──────│
│    date              │  │    leave_type        │          │    component         │
│    status            │  │    start_date        │          │    amount            │
│    check_in          │  │    end_date          │          │    effective_from    │
│    check_out         │  │    status            │          │    created_at        │
│    duration_hours    │  │    remarks           │          └──────────────────────┘
│    location_lat      │  │    admin_comment     │
│    location_lng      │  │    formal_reason     │
│    check_in_method   │  │    generated_email   │
│    created_at        │  │    email_sent        │
│                      │  │ FK reviewed_by ──────│──→ employees.id (SET NULL)
│ UQ (employee_id,date)│  │    reviewed_at       │
└──────────────────────┘  │    created_at        │
                          │    updated_at        │
                          │                      │
                          │ EXCL: no overlap     │
                          │ (employee_id,        │
                          │  daterange) WHERE    │
                          │  status != 'rejected'│
                          └──────────┬───────────┘
                                     │
                          ┌──────────┴───────────┐
                          │ 1:N                  │
                          ▼                      ▼
              ┌──────────────────────┐  ┌──────────────────────┐
              │   leave_balances      │  │                      │
              │──────────────────────│  │                      │
              │ PK id               │  │                      │
              │ FK employee_id ──────│  │                      │
              │    year             │  │                      │
              │    leave_type       │  │                      │
              │    total            │  │                      │
              │    used             │  │                      │
              │                     │  │                      │
              │ UQ (employee_id,    │  │                      │
              │     year,           │  │                      │
              │     leave_type)     │  │                      │
              └─────────────────────┘  │                      │
                                       │                      │
            ┌──────────────────────────┤                      │
            │ 1:N                     1:N                     │
            ▼                          ▼                      │
┌──────────────────────┐  ┌──────────────────────┐           │
│    payroll_runs       │  │     audit_log         │           │
│──────────────────────│  │──────────────────────│           │
│ PK id               │  │ PK id                │           │
│ FK employee_id ──────│  │ FK actor_id ─────────│──┐        │
│    month            │  │    action            │  │        │
│    year             │  │    entity_type       │  │        │
│    gross_pay        │  │    entity_id         │  │        │
│    deductions       │  │    metadata (JSONB)  │  │        │
│    net_pay          │  │    ip_address        │  │        │
│    pay_stub_url     │  │    created_at        │  │        │
│    components_snap  │  └──────────────────────┘  │        │
│    finalized_at     │                            │        │
│                     │  UQ (employee_id,          │        │
│ UQ (employee_id,    │        month, year)        │        │
│     month, year)    │                            │        │
└─────────────────────┘                            │        │
                                                   │        │
            ┌──────────────────────────────────────┘        │
            │ 1:N                                           │
            ▼                                               │
┌──────────────────────┐                                    │
│    burnout_alerts     │                                    │
│──────────────────────│                                    │
│ PK id               │                                    │
│ FK employee_id ──────│                                    │
│    signal            │                                    │
│    value             │                                    │
│    threshold         │                                    │
│    severity          │                                    │
│    resolved          │                                    │
│    created_at        │                                    │
└──────────────────────┘                                    │
                                                            │
            ┌───────────────────────────────────────────────┘
            │ 1:N
            ▼
┌──────────────────────┐      ┌──────────────────────┐
│      nudges          │      │    burnout_config     │
│──────────────────────│      │──────────────────────│
│ PK id               │      │ PK id                │
│ FK employee_id ──────│      │    department (UQ)   │
│    message           │      │    max_consec_days   │
│    type              │      │    max_weekly_ot     │
│    read              │      │    alert_email       │
│    created_at        │      │    updated_at        │
└──────────────────────┘      └──────────────────────┘


  ┌──────────────────────┐      ┌──────────────────────┐
  │   public_holidays    │      │    office_config      │
  │──────────────────────│      │──────────────────────│
  │ PK id               │      │ PK id                │
  │    name             │      │    office_lat        │
  │    date (UQ)        │      │    office_lng        │
  │    year             │      │    geofence_radius_m │
  └──────────────────────┘      │    office_ip_subnet  │
                                │    wifi_checkin_en   │
                                │    gps_checkin_en    │
                                │    updated_at        │
                                └──────────────────────┘


              CHAT SUBSYSTEM
              ──────────────

┌──────────────────────┐
│    chat_channels      │
│──────────────────────│
│ PK id               │
│    type              │
│    name              │
│    department        │
│ FK created_by ───────│──→ employees.id (SET NULL)
│    created_at        │
└──────────┬───────────┘
           │ 1:N
           ▼
┌──────────────────────┐
│    chat_messages      │
│──────────────────────│
│ PK id               │
│ FK channel_id ───────│──→ chat_channels.id (CASCADE)
│ FK sender_id ────────│──→ employees.id (CASCADE)
│    body              │
│    message_type      │
│    meeting_meta      │
│    created_at        │
└──────┬──────┬────────┘
       │      │
       │ 1:N  │ 1:N
       ▼      ▼
┌──────────────┐  ┌──────────────────┐
│  chat_reads   │  │   meeting_rsvp   │
│──────────────│  │──────────────────│
│ FK employee_id│  │ PK id            │
│   (CPK)      │  │ FK message_id ───│──→ chat_messages.id
│ FK message_id│  │ FK employee_id ──│──→ employees.id
│   (CPK)      │  │    response      │
│    read_at   │  │    created_at    │
└──────────────┘  └──────────────────┘
```

---

## Cardinality Summary

| Relationship | Cardinality | FK Column | On Delete |
|---|---|---|---|
| employees → attendance_records | 1:N | `employee_id` | CASCADE |
| employees → leave_requests | 1:N | `employee_id` | CASCADE |
| employees → leave_requests (reviewer) | 1:N | `reviewed_by` | SET NULL |
| employees → leave_balances | 1:N | `employee_id` | CASCADE |
| employees → salary_components | 1:N | `employee_id` | CASCADE |
| employees → payroll_runs | 1:N | `employee_id` | CASCADE |
| employees → audit_log | 1:N | `actor_id` | SET NULL |
| employees → burnout_alerts | 1:N | `employee_id` | CASCADE |
| employees → nudges | 1:N | `employee_id` | CASCADE |
| employees → chat_channels | 1:N | `created_by` | SET NULL |
| employees → chat_messages | 1:N | `sender_id` | CASCADE |
| employees → chat_reads | 1:N | `employee_id` | CASCADE |
| employees → meeting_rsvp | 1:N | `employee_id` | CASCADE |
| chat_channels → chat_messages | 1:N | `channel_id` | CASCADE |
| chat_messages → chat_reads | 1:N | `message_id` | CASCADE |
| chat_messages → meeting_rsvp | 1:N | `message_id` | CASCADE |

---

## Key Relationship Explanations

### employees ↔ leave_requests (reviewed_by)
- **Self-referential FK:** An admin (employee) reviews leave requests
- **ON DELETE SET NULL:** If the reviewing admin is deleted, the review record is preserved but the reviewer reference is cleared
- **Audit trail preserved:** `reviewed_at` timestamp and `admin_comment` remain intact

### employees ↔ audit_log (actor_id)
- **Soft reference:** Audit logs survive employee deletion
- **ON DELETE SET NULL:** Preserves the audit trail even if the actor is removed
- **Immutable:** No UPDATE or DELETE operations are performed on audit_log

### employees ↔ chat_channels (created_by)
- **Channel ownership:** Tracks who created each channel
- **ON DELETE SET NULL:** Channel persists if creator is deactivated

### leave_requests EXCLUDE constraint
- **GiST-based overlap prevention:** Uses `btree_gist` extension
- **Range type:** `daterange(start_date, end_date, '[]')` — inclusive on both ends
- **Conditional:** Only applies when `status != 'rejected'` — rejected leaves don't block overlapping requests
- **Defense in depth:** Application also performs atomic balance deduction via `UPDATE ... WHERE (total - used) >= :days`

### chat_reads composite PK
- **Composite primary key:** `(employee_id, message_id)` — one read receipt per employee per message
- **Unique constraint:** `uq_chat_read_emp_msg` enforces idempotent read marking

### meeting_rsvp unique constraint
- **One RSVP per employee per meeting:** `uq_meeting_rsvp_emp_msg` on `(message_id, employee_id)`
- **Response values:** `accept`, `decline`, `maybe`

### payroll_runs components_snapshot (JSONB)
- **Immutable snapshot:** Stores the salary components at the time of payroll finalization
- **Historical accuracy:**即使员工薪资后续变更，历史工资单仍反映当时的正确金额
- **No FK to salary_components:** Deliberately decoupled for immutability

### burnout_config ↔ employees
- **No direct FK:** `burnout_config.department` matches `employees.department` by string, not by FK
- **Per-department config:** One row per department with configurable thresholds
- **Alert email:** Optional per-department notification recipient
