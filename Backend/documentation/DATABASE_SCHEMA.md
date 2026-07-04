# HRMS Database Schema DDL

Complete PostgreSQL `CREATE TABLE` statements for all 16 tables.

**Extension required:**
```sql
CREATE EXTENSION IF NOT EXISTS "btree_gist";
```

---

## 1. employees

```sql
CREATE TABLE employees (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_id    VARCHAR(255) NOT NULL UNIQUE,
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) NOT NULL UNIQUE,
    department  VARCHAR(100),
    designation VARCHAR(100),
    phone       VARCHAR(20),
    address     TEXT,
    profile_pic VARCHAR(500),
    role        VARCHAR(20) NOT NULL DEFAULT 'employee',
    date_joined DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_employees_clerk_id ON employees (clerk_id);
CREATE INDEX ix_employees_employee_id ON employees (employee_id);
CREATE INDEX ix_employees_email ON employees (email);
CREATE INDEX ix_employees_department ON employees (department);
CREATE INDEX ix_employees_role ON employees (role);
CREATE INDEX ix_employees_is_active ON employees (is_active);
```

---

## 2. attendance_records

```sql
CREATE TABLE attendance_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    date            DATE NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'present',
    check_in        TIMESTAMPTZ,
    check_out       TIMESTAMPTZ,
    duration_hours   NUMERIC(6,2),
    location_lat    NUMERIC(10,8),
    location_lng    NUMERIC(11,8),
    check_in_method VARCHAR(20),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_attendance_emp_date UNIQUE (employee_id, date)
);

CREATE INDEX ix_attendance_records_employee_id ON attendance_records (employee_id);
CREATE INDEX ix_attendance_records_date ON attendance_records (date);
CREATE INDEX ix_attendance_emp_date_status ON attendance_records (employee_id, date, status);
```

---

## 3. leave_requests

```sql
CREATE TABLE leave_requests (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id           UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type            VARCHAR(20) NOT NULL,
    start_date            DATE NOT NULL,
    end_date              DATE NOT NULL,
    status                VARCHAR(20) NOT NULL DEFAULT 'pending',
    remarks               TEXT,
    admin_comment         TEXT,
    formal_reason         VARCHAR(100),
    generated_email_body  TEXT,
    email_sent            BOOLEAN DEFAULT false,
    reviewed_by           UUID REFERENCES employees(id) ON DELETE SET NULL,
    reviewed_at           TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_leave_requests_employee_id ON leave_requests (employee_id);
CREATE INDEX ix_leave_requests_status ON leave_requests (status);
CREATE INDEX ix_leave_emp_status ON leave_requests (employee_id, status);
CREATE INDEX ix_leave_status_created ON leave_requests (status, created_at);

-- EXCLUDE constraint: prevents overlapping leaves for same employee
ALTER TABLE leave_requests ADD CONSTRAINT EXCL_leave_overlap
EXCLUDE USING gist (
    employee_id WITH =,
    daterange(start_date, end_date, '[]') WITH &&
) WHERE (status != 'rejected');
```

---

## 4. leave_balances

```sql
CREATE TABLE leave_balances (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    year        INTEGER NOT NULL,
    leave_type  VARCHAR(20) NOT NULL,
    total       INTEGER NOT NULL DEFAULT 0,
    used        INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT uq_leave_balance_emp_year_type UNIQUE (employee_id, year, leave_type)
);

CREATE INDEX ix_leave_balances_employee_id ON leave_balances (employee_id);
```

---

## 5. salary_components

```sql
CREATE TABLE salary_components (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id   UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    component     VARCHAR(100) NOT NULL,
    amount        NUMERIC(12,2) NOT NULL,
    effective_from DATE NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_salary_components_employee_id ON salary_components (employee_id);
CREATE INDEX ix_salary_components_emp_effective ON salary_components (employee_id, effective_from);
```

---

## 6. payroll_runs

```sql
CREATE TABLE payroll_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id         UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    month               INTEGER NOT NULL,
    year                INTEGER NOT NULL,
    gross_pay           NUMERIC(12,2) NOT NULL,
    deductions          NUMERIC(12,2) NOT NULL DEFAULT 0,
    net_pay             NUMERIC(12,2) NOT NULL,
    pay_stub_url        VARCHAR(500),
    components_snapshot JSONB NOT NULL,
    finalized_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_payroll_emp_period UNIQUE (employee_id, month, year)
);

CREATE INDEX ix_payroll_runs_employee_id ON payroll_runs (employee_id);
CREATE INDEX ix_payroll_emp_period ON payroll_runs (employee_id, year, month);
```

---

## 7. audit_log

```sql
CREATE TABLE audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id    UUID REFERENCES employees(id) ON DELETE SET NULL,
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   UUID,
    metadata    JSONB,
    ip_address  VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_audit_log_actor_id ON audit_log (actor_id);
CREATE INDEX ix_audit_log_action ON audit_log (action);
CREATE INDEX ix_audit_log_entity_type ON audit_log (entity_type);
CREATE INDEX ix_audit_log_created_at ON audit_log (created_at);
CREATE INDEX ix_audit_actor_created ON audit_log (actor_id, created_at);
CREATE INDEX ix_audit_entity ON audit_log (entity_type, entity_id);
```

---

## 8. burnout_config

```sql
CREATE TABLE burnout_config (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department             VARCHAR(100) NOT NULL UNIQUE,
    max_consecutive_days   INTEGER NOT NULL DEFAULT 14,
    max_weekly_overtime_hrs INTEGER NOT NULL DEFAULT 10,
    alert_email            VARCHAR(255),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 9. burnout_alerts

```sql
CREATE TABLE burnout_alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    signal      VARCHAR(50) NOT NULL,
    value       NUMERIC,
    threshold   NUMERIC,
    severity    VARCHAR(20) NOT NULL,
    resolved    BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_burnout_alerts_employee_id ON burnout_alerts (employee_id);
CREATE INDEX ix_burnout_alerts_resolved ON burnout_alerts (resolved);
CREATE INDEX ix_burnout_alerts_emp_resolved ON burnout_alerts (employee_id, resolved);
```

---

## 10. nudges

```sql
CREATE TABLE nudges (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    message     TEXT NOT NULL,
    type        VARCHAR(50) NOT NULL,
    read        BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_nudges_employee_id ON nudges (employee_id);
CREATE INDEX ix_nudges_type ON nudges (type);
CREATE INDEX ix_nudges_read ON nudges (read);
CREATE INDEX ix_nudges_emp_read ON nudges (employee_id, read);
```

---

## 11. public_holidays

```sql
CREATE TABLE public_holidays (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL
);

CREATE INDEX ix_public_holidays_year ON public_holidays (year);
```

---

## 12. office_config

```sql
CREATE TABLE office_config (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    office_lat           NUMERIC(10,8),
    office_lng           NUMERIC(11,8),
    geofence_radius_m    INTEGER DEFAULT 150,
    office_ip_subnet     VARCHAR(20),
    wifi_checkin_enabled BOOLEAN DEFAULT false,
    gps_checkin_enabled  BOOLEAN DEFAULT true,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 13. chat_channels

```sql
CREATE TABLE chat_channels (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type       VARCHAR(30) NOT NULL,
    name       VARCHAR(100),
    department VARCHAR(100),
    created_by UUID REFERENCES employees(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 14. chat_messages

```sql
CREATE TABLE chat_messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id   UUID NOT NULL REFERENCES chat_channels(id) ON DELETE CASCADE,
    sender_id    UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    body         TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    meeting_meta JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_chat_messages_channel_id ON chat_messages (channel_id);
CREATE INDEX ix_chat_messages_sender_id ON chat_messages (sender_id);
CREATE INDEX ix_chat_messages_created_at ON chat_messages (created_at);
CREATE INDEX ix_chat_messages_channel_created ON chat_messages (channel_id, created_at);
```

---

## 15. chat_reads

```sql
CREATE TABLE chat_reads (
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    message_id  UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    read_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (employee_id, message_id),
    CONSTRAINT uq_chat_read_emp_msg UNIQUE (employee_id, message_id)
);
```

---

## 16. meeting_rsvp

```sql
CREATE TABLE meeting_rsvp (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id  UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    response    VARCHAR(10) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_meeting_rsvp_emp_msg UNIQUE (message_id, employee_id)
);

CREATE INDEX ix_meeting_rsvp_message_id ON meeting_rsvp (message_id);
CREATE INDEX ix_meeting_rsvp_employee_id ON meeting_rsvp (employee_id);
```

---

## Composite Indexes (Performance)

```sql
CREATE INDEX ix_attendance_emp_date_status ON attendance_records (employee_id, date, status);
CREATE INDEX ix_leave_emp_status ON leave_requests (employee_id, status);
CREATE INDEX ix_leave_status_created ON leave_requests (status, created_at);
CREATE INDEX ix_payroll_emp_period ON payroll_runs (employee_id, year, month);
CREATE INDEX ix_audit_actor_created ON audit_log (actor_id, created_at);
CREATE INDEX ix_audit_entity ON audit_log (entity_type, entity_id);
CREATE INDEX ix_chat_messages_channel_created ON chat_messages (channel_id, created_at);
CREATE INDEX ix_nudges_emp_read ON nudges (employee_id, read);
CREATE INDEX ix_burnout_alerts_emp_resolved ON burnout_alerts (employee_id, resolved);
CREATE INDEX ix_salary_components_emp_effective ON salary_components (employee_id, effective_from);
```
