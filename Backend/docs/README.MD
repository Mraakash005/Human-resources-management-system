# HRMS — Human Resource Management System
## Complete System Documentation & Architecture Blueprint
### Version 3.0 — Production-Ready Specification (All 27 Features)

> **Tagline:** *Every workday, perfectly aligned.*

> **Scope:** This document covers the full HRMS architecture. For detailed implementation specs of all 27 features, see `differentiators_fetaures.md` — the complete feature specification covering:
> - **Part A: Core SRS Features (8)** — Authentication, Dashboards, Profiles, Leave, Attendance, Payroll, Employee Management
> - **Part B: Performance & Security Features (6)** — Redis Caching, Pydantic Validation, DB Optimization, Aggregated APIs, Audit Logging, Async FastAPI
> - **Part C: AI-Powered Differentiators (13)** — NLP Chat, Voice Commands, Heatmap, Burnout Detection, Salary Simulator, AI Advisor, Auto Check-In, Health Scores, Nudges, PDF Pay Stubs, Team Chat

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [System Architecture](#3-system-architecture)
4. [Folder Structure](#4-folder-structure)
5. [Database Design & Schema](#5-database-design--schema)
6. [Authentication & Security](#6-authentication--security)
7. [Functional Requirements — All Modules](#7-functional-requirements--all-modules)
   - 7.1 Auth Module (Clerk Authentication)
   - 7.2 Dashboard Module (Role-Based Dashboards + Aggregated API)
   - 7.3 Employee Profile Module (Profile Management)
   - 7.4 Attendance Module (Check-In/Out + Auto Check-In + Heatmap)
   - 7.5 Leave & Time-Off Module (Leave Application + AI Documenter + Conversational Leave)
   - 7.6 Payroll Module (Payroll Visibility + PDF Pay Stubs + Salary Simulator)
   - 7.7 AI Leave Documenter Feature
   - 7.8 Voice & NLP Input (Voice Commands + Voice-to-Leave)
   - 7.9 Burnout Detection (Early Warning System)
   - 7.10 HR Chatbot (RAG-Lite Q&A)
   - 7.11 Admin Employee Management
   - 7.12 Internal Team Chat & Meeting Announcements
   - 7.13 Proactive Nudge System
   - 7.14 Team Attendance Health Score
8. [Backend Logic — FastAPI](#8-backend-logic--fastapi)
9. [Frontend Logic — Next.js 15](#9-frontend-logic--nextjs-15)
10. [Free API & AI Integration Strategy](#10-free-api--ai-integration-strategy)
11. [Full Data Flow Diagrams](#11-full-data-flow-diagrams)
12. [Security Implementation](#12-security-implementation)
13. [Non-Functional Requirements](#13-non-functional-requirements)
14. [Performance & Security Features](#14-performance--security-features)
    - 14.1 Redis Dashboard Caching
    - 14.2 Input Validation — Pydantic v2
    - 14.3 DB Query Optimization
    - 14.4 Aggregated Dashboard API
    - 14.5 Audit Logging
    - 14.6 Async FastAPI Throughout
15. [DevOps & Deployment](#15-devops--deployment)
16. [Development Timeline & Build Order](#16-development-timeline--build-order)
17. [Feature Reference Matrix](#17-feature-reference-matrix)
18. [Cross-Document Reference](#18-cross-document-reference)

---

## 1. Project Overview

### 1.1 Purpose

The HRMS is a full-stack, AI-augmented Human Resource Management System built to digitize and automate core HR operations for organizations. It removes manual email chains, spreadsheet abuse, and verbal approval loops — replacing them with a single unified portal where employees manage their work-life and admins govern the organization in real time.

### 1.2 Core Objectives

- **Digitize** all HR touchpoints: onboarding, attendance, leave, payroll.
- **Automate** repetitive admin actions: leave email drafting, payroll runs, burnout detection.
- **Secure** every interaction via role-based access control (RBAC) with zero trust at every API layer.
- **Leverage free/open-source AI** (Llama 3, Mistral via Ollama, Whisper, Web Speech API) to deliver intelligent features at zero marginal cost.

### 1.3 User Classes

| User Type | Description |
|-----------|-------------|
| **Employee** | Views personal profile, attendance, applies for leave, views salary details, uses AI leave documenter, uses voice check-in |
| **Admin / HR Officer** | Manages employees, approves leave & attendance, controls payroll, views analytics, manages burnout alerts, accesses audit logs |

---

## 2. Technology Stack

### 2.1 Full Stack Overview

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Frontend** | Next.js 15 (App Router, RSC) | File-based routing, React Server Components for payroll (zero JS to client), streaming |
| **Styling** | Tailwind CSS + shadcn/ui | Utility-first, accessible component primitives |
| **State (Client)** | Zustand (UI state only) | Lightweight, no boilerplate |
| **Server State** | TanStack Query v5 | Caching, background refetch, optimistic updates |
| **Auth** | Clerk | Managed JWT, email verification, role metadata, device session management — free tier covers all needs |
| **Backend** | FastAPI (Python 3.12) | Async, typed, auto-generates OpenAPI docs, fast JWT validation |
| **ORM** | SQLAlchemy (async) + Alembic | Type-safe queries, migration management |
| **Database** | PostgreSQL 16 | ACID, exclusion constraints, row-level locking |
| **Cache** | Redis 7 | Leave balance caching, session state, dirty flags |
| **AI — NLP** | Ollama (Llama 3 / Mistral 7B) | Free, self-hosted, leave text parsing & email drafting |
| **AI — Voice** | OpenAI Whisper (Docker) | Free, self-hosted audio transcription |
| **AI — Browser Voice** | Web Speech API | Zero cost, no server needed for simple commands |
| **Email** | Resend (free tier: 100 emails/day) | Transactional email for leave notifications to HR |
| **Scheduler** | APScheduler (inside FastAPI) | Burnout cron jobs, payroll monthly runs — no separate service |
| **PDF Generation** | WeasyPrint | Pay stub PDF generation, self-hosted |
| **Virus Scan** | ClamAV (Docker sidecar) | File upload safety for medical docs & audio |
| **Containerization** | Docker + Docker Compose | One-command full stack startup |
| **Reverse Proxy** | Nginx | Routes /api → FastAPI, / → Next.js in production |

### 2.2 Why These Free Tools

| Need | Free Solution | Alternative Avoided |
|------|--------------|-------------------|
| AI email drafting | Ollama + Llama 3 (self-hosted) | Claude API (paid) |
| Voice transcription | Whisper Docker | OpenAI Whisper API (paid) |
| Simple voice commands | Browser Web Speech API | Any paid STT service |
| Transactional email | Resend (100/day free) | SendGrid (limited free) |
| Authentication | Clerk (free tier: 10k MAU) | Auth0 (paid at scale) |
| Virus scanning | ClamAV (open-source) | Paid SaaS scanners |
| PDF generation | WeasyPrint (open-source) | Paid PDF APIs |

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│   Browser / Mobile Browser                                          │
│   Next.js 15 App (localhost:3000)                                   │
│   ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│   │ Auth Pages  │  │  Employee    │  │    Admin Dashboard       │   │
│   │ (Clerk UI)  │  │  Dashboard   │  │    (middleware guarded)  │   │
│   └─────────────┘  └──────────────┘  └─────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS (JWT in Authorization header)
┌────────────────────────────▼────────────────────────────────────────┐
│                       GATEWAY LAYER                                 │
│                    Nginx Reverse Proxy                              │
│         /api/* → FastAPI :8000   |   /* → Next.js :3000            │
└───────────────┬────────────────────────────────┬────────────────────┘
                │                                │
┌───────────────▼──────────────┐   ┌─────────────▼────────────────────┐
│    BACKEND LAYER             │   │      AUTH LAYER                   │
│    FastAPI :8000             │   │      Clerk (managed SaaS)         │
│                              │   │      - JWT issuance               │
│  ┌────────┐ ┌─────────────┐  │   │      - Email verification         │
│  │Routers │ │  Services   │  │   │      - Role metadata              │
│  │        │ │             │  │   │      - Device session mgmt        │
│  │/attend │ │payroll_calc │  │◄──│      - getUser() real-time check  │
│  │/leave  │ │notification │  │   └──────────────────────────────────┘
│  │/payroll│ │cache        │  │
│  │/nlp    │ │analytics    │  │
│  │/voice  │ │             │  │
│  └────────┘ └─────────────┘  │
│        │           │          │
│  ┌─────▼───────────▼──────┐   │
│  │   APScheduler          │   │
│  │  (Burnout + Payroll    │   │
│  │   monthly cron jobs)   │   │
│  └────────────────────────┘   │
└───┬──────────┬───────────┬─────┘
    │          │           │
┌───▼──┐  ┌───▼───┐  ┌────▼──────────────────────────────────────┐
│ PG   │  │ Redis │  │    AI SIDECAR SERVICES (Docker)            │
│ :5432│  │ :6379 │  │                                            │
│      │  │       │  │  ┌──────────────┐  ┌─────────────────┐    │
│ ACID │  │ Cache │  │  │ Ollama :11434│  │ Whisper :9000   │    │
│ DB   │  │ Layer │  │  │ Llama3/Mistral│  │ Audio Transcribe│    │
└──────┘  └───────┘  │  └──────────────┘  └─────────────────┘    │
                     │  ┌──────────────┐  ┌─────────────────┐    │
                     │  │ ClamAV :3310 │  │ WeasyPrint      │    │
                     │  │ Virus Scan   │  │ PDF Generator   │    │
                     │  └──────────────┘  └─────────────────┘    │
                     └────────────────────────────────────────────┘
```

### 3.2 Request Lifecycle (Standard API Call)

```
Employee Action (browser)
    → Next.js component calls lib/api.ts typed fetch wrapper
    → Clerk SDK appends Bearer JWT to Authorization header
    → Nginx routes /api/* to FastAPI :8000
    → FastAPI auth.py decodes & validates JWT (RS256, Clerk PEM public key)
    → Role extracted from token metadata
    → Router handler called with validated user context
    → Service layer executes business logic
    → SQLAlchemy async query to PostgreSQL
    → Redis cache checked/updated as needed
    → ApiResponse<T> JSON returned to Next.js
    → TanStack Query updates client cache
    → UI re-renders reactively
```

---

## 4. Folder Structure

### 4.1 Frontend — Next.js 15

```
src/
├── app/
│   ├── (auth)/                          ← Route group: no dashboard layout
│   │   ├── sign-in/[[...sign-in]]/
│   │   │   └── page.tsx                 ← Clerk catch-all sign-in
│   │   └── sign-up/[[...sign-up]]/
│   │       └── page.tsx                 ← Clerk catch-all sign-up
│   ├── (dashboard)/                     ← Route group: shared sidebar/nav
│   │   ├── layout.tsx                   ← Sidebar, navbar, role context
│   │   ├── dashboard/page.tsx           ← Role-split: admin vs employee
│   │   ├── attendance/page.tsx          ← Check-in/out, calendar, heatmap
│   │   ├── leave/page.tsx               ← Apply leave, AI doc, conversational, advisor
│   │   ├── payroll/page.tsx             ← RSC: zero JS, read-only + salary simulator
│   │   ├── chat/page.tsx                ← Internal team chat panel
│   │   └── admin/                       ← middleware blocks employees
│   │       ├── employees/page.tsx       ← Employee list, edit, onboard
│   │       ├── approvals/page.tsx       ← Leave & attendance approvals
│   │       ├── payroll/page.tsx         ← Full payroll control
│   │       ├── analytics/page.tsx       ← Burnout dashboard, health scores, reports
│   │       └── audit/page.tsx           ← Audit log viewer
│   └── api/                             ← Next.js Route Handlers (thin proxy)
│       ├── attendance/route.ts
│       ├── leave/route.ts
│       ├── payroll/route.ts
│       ├── chat/route.ts
│       └── set-role/route.ts            ← Clerk webhook role sync
├── middleware.ts                         ← clerkMiddleware(), role guard
├── components/
│   ├── ui/                              ← shadcn/ui primitives
│   └── features/
│       ├── attendance/
│       │   ├── CheckInButton.tsx
│       │   ├── AttendanceCalendar.tsx
│       │   ├── WeeklyView.tsx
│       │   ├── AttendanceHeatmap.tsx    ← SVG heatmap (Feature 19)
│       │   ├── VoiceMicButton.tsx       ← Voice command trigger (Feature 17)
│       │   └── AutoCheckinBanner.tsx    ← GPS/Wi-Fi auto check-in toast (Feature 23)
│       ├── leave/
│       │   ├── LeaveForm.tsx            ← Includes AI documenter tab
│       │   ├── LeaveCalendar.tsx
│       │   ├── LeaveStatusBadge.tsx
│       │   ├── EmailPreviewModal.tsx    ← AI draft preview before send
│       │   ├── ConversationalLeave.tsx  ← Multi-turn NLP chat (Feature 15)
│       │   ├── LeaveAdvisorCard.tsx     ← AI recommendations (Feature 22)
│       │   └── VoiceToLeave.tsx         ← Audio recording + parsing (Feature 18)
│       ├── payroll/
│       │   ├── SalaryCard.tsx
│       │   ├── PayStubDownload.tsx
│       │   └── SalarySimulator.tsx      ← Interactive salary slider (Feature 21)
│       ├── chat/
│       │   ├── ChatPanel.tsx            ← Main chat UI (Feature 27)
│       │   ├── ChatBubble.tsx           ← Message bubble
│       │   ├── MeetingInviteCard.tsx    ← Structured meeting card
│       │   └── ChannelList.tsx          ← Channel sidebar
│       ├── nudge/
│       │   ├── NudgeBell.tsx            ← Notification bell (Feature 25)
│       │   └── NudgeList.tsx            ← Nudge drawer
│       └── admin/
│           ├── EmployeeTable.tsx
│           ├── ApprovalQueue.tsx
│           ├── BurnoutWidget.tsx
│           ├── BurnoutDashboard.tsx    ← Burnout early warning UI (Feature 20)
│           └── TeamHealthScore.tsx      ← Health score widget (Feature 24)
├── hooks/
│   ├── useAttendance.ts                 ← TanStack Query wrappers
│   ├── useLeave.ts
│   ├── usePayroll.ts
│   ├── useVoice.ts                      ← Web Speech API hook (Feature 17)
│   ├── useVoiceCommand.ts              ← Voice command patterns (Feature 17)
│   ├── useVoiceRecorder.ts             ← MediaRecorder wrapper (Feature 18)
│   ├── useSSE.ts                        ← EventSource wrapper (Feature 27)
│   ├── useNudges.ts                     ← Nudge polling (Feature 25)
│   ├── useLeaveAdvisor.ts              ← AI advisor data (Feature 22)
│   └── useDashboard.ts                 ← Aggregated dashboard (Feature 12)
├── lib/
│   ├── api.ts                           ← Typed fetch wrapper, ApiResponse<T>
│   └── auth.ts                          ← getCurrentRole() helper
├── stores/
│   ├── leaveStore.ts                    ← Zustand: UI state (modal open, etc.)
│   ├── attendanceStore.ts
│   └── chatStore.ts                     ← Zustand: chat UI state (Feature 27)
└── types/
    ├── index.ts                          ← Shared domain types
    └── globals.d.ts                      ← Clerk role type declaration
```

### 4.2 Backend — FastAPI

```
backend/
├── main.py                              ← FastAPI init, CORS, lifespan
├── Dockerfile
├── requirements.txt
├── core/
│   ├── config.py                        ← env vars via pydantic-settings
│   ├── auth.py                          ← Clerk JWT RS256 verification
│   ├── database.py                      ← SQLAlchemy async engine
│   └── redis.py                         ← Redis connection pool
├── models/                              ← SQLAlchemy ORM models
│   ├── employee.py
│   ├── attendance.py
│   ├── leave.py
│   ├── payroll.py
│   ├── audit_log.py
│   ├── burnout_config.py
│   ├── burnout_alerts.py                ← Burnout alerts log (Feature 20)
│   ├── nudges.py                        ← Nudge queue (Feature 25)
│   ├── chat.py                          ← Channels + messages + reads + RSVP (Feature 27)
│   ├── public_holidays.py               ← Public holidays (Feature 22)
│   └── office_config.py                 ← GPS/WiFi auto check-in config (Feature 23)
├── schemas/                             ← Pydantic request/response schemas
│   ├── employee.py
│   ├── attendance.py
│   ├── leave.py
│   ├── payroll.py
│   ├── chat.py                          ← Chat message schemas (Feature 27)
│   └── nudge.py                         ← Nudge schemas (Feature 25)
├── routers/                             ← APIRouter per feature
│   ├── attendance.py
│   ├── leave.py
│   ├── payroll.py
│   ├── employees.py
│   ├── dashboard.py                     ← Aggregated summary endpoint (Feature 12)
│   ├── nlp.py                           ← Leave text parsing + conversational (Feature 15)
│   ├── voice.py                         ← Whisper transcription (Feature 18)
│   ├── chatbot.py                       ← HR FAQ chatbot (Feature 16)
│   ├── chat.py                          ← Team chat + SSE stream (Feature 27)
│   ├── nudges.py                        ← Nudge CRUD (Feature 25)
│   └── analytics.py                     ← Team health score (Feature 24)
├── services/                            ← Business logic layer
│   ├── cache.py                         ← Redis read/write helpers + dashboard cache (Feature 9)
│   ├── payroll_calc.py                  ← Payroll snapshot logic + PDF generation (Feature 26)
│   ├── attendance_analytics.py          ← Burnout detection (Feature 20)
│   ├── notification.py                  ← EmailGenerator + Resend
│   ├── file_validator.py               ← MIME, size, ClamAV
│   ├── nudge_service.py                 ← Nudge generation logic (Feature 25)
│   ├── chat_service.py                  ← Channel management (Feature 27)
│   └── ollama_client.py                 ← Ollama API wrapper (Features 15,16,18,22)
├── templates/
│   └── pay_stub.html                    ← WeasyPrint HTML template (Feature 26)
└── migrations/                          ← Alembic migrations
    └── versions/
```

---

## 5. Database Design & Schema

### 5.1 Core Tables

#### `employees`
```sql
CREATE TABLE employees (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_id      VARCHAR(255) UNIQUE NOT NULL,   -- Clerk user ID
    employee_id   VARCHAR(50) UNIQUE NOT NULL,    -- e.g. EMP-001
    name          VARCHAR(255) NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    department    VARCHAR(100),
    designation   VARCHAR(100),
    phone         VARCHAR(20),
    address       TEXT,
    profile_pic   VARCHAR(500),                   -- S3/storage URL
    role          VARCHAR(20) NOT NULL DEFAULT 'employee',  -- 'admin' | 'employee'
    date_joined   DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);
```

#### `attendance_records`
```sql
CREATE TABLE attendance_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id),
    date            DATE NOT NULL,
    status          VARCHAR(20) NOT NULL,         -- present|absent|half-day|leave
    check_in        TIMESTAMPTZ,
    check_out       TIMESTAMPTZ,
    location_lat    DECIMAL(10, 8),               -- for geofence validation
    location_lng    DECIMAL(11, 8),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(employee_id, date)                     -- one record per employee per day
);
```

#### `leave_requests`
```sql
CREATE TABLE leave_requests (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id           UUID NOT NULL REFERENCES employees(id),
    leave_type            VARCHAR(20) NOT NULL,   -- paid|sick|unpaid|bereavement|medical
    start_date            DATE NOT NULL,
    end_date              DATE NOT NULL,
    status                VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending|approved|rejected
    remarks               TEXT,
    admin_comment         TEXT,
    formal_reason         VARCHAR(100),           -- checklist selection
    generated_email_body  TEXT,                   -- AI-generated email stored for audit
    email_sent            BOOLEAN DEFAULT FALSE,
    reviewed_by           UUID REFERENCES employees(id),
    reviewed_at           TIMESTAMPTZ,
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW(),

    -- EXCLUSION CONSTRAINT: prevents overlapping leave dates for same employee
    EXCLUDE USING gist (
        employee_id WITH =,
        daterange(start_date, end_date, '[]') WITH &&
    )
    WHERE (status != 'rejected')
);
```

#### `leave_balances`
```sql
CREATE TABLE leave_balances (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id  UUID NOT NULL REFERENCES employees(id),
    year         INTEGER NOT NULL,
    leave_type   VARCHAR(20) NOT NULL,
    total        INTEGER NOT NULL DEFAULT 0,
    used         INTEGER NOT NULL DEFAULT 0,
    UNIQUE(employee_id, year, leave_type)
);
```

#### `salary_components`
```sql
CREATE TABLE salary_components (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id  UUID NOT NULL REFERENCES employees(id),
    component    VARCHAR(100) NOT NULL,  -- basic_salary, hra, transport, etc.
    amount       DECIMAL(12, 2) NOT NULL,
    effective_from DATE NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

#### `payroll_runs`
```sql
CREATE TABLE payroll_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id),
    month           INTEGER NOT NULL,               -- 1-12
    year            INTEGER NOT NULL,
    gross_pay       DECIMAL(12, 2) NOT NULL,
    deductions      DECIMAL(12, 2) NOT NULL DEFAULT 0,
    net_pay         DECIMAL(12, 2) NOT NULL,
    pay_stub_url    VARCHAR(500),                   -- PDF stored path
    finalized_at    TIMESTAMPTZ DEFAULT NOW(),
    components_snapshot JSONB NOT NULL,             -- immutable snapshot of salary_components
    UNIQUE(employee_id, month, year)
);
```

#### `burnout_config`
```sql
CREATE TABLE burnout_config (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department              VARCHAR(100) NOT NULL UNIQUE,
    max_consecutive_days    INTEGER NOT NULL DEFAULT 14,
    max_weekly_overtime_hrs INTEGER NOT NULL DEFAULT 10,
    alert_email             VARCHAR(255),           -- HR email to notify
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);
```

#### `audit_log`
```sql
CREATE TABLE audit_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id     UUID REFERENCES employees(id),
    action       VARCHAR(100) NOT NULL,  -- leave_approved, payroll_generated, etc.
    entity_type  VARCHAR(50),            -- leave_request, employee, payroll_run
    entity_id    UUID,
    metadata     JSONB,                  -- { "old_status": "pending", "new_status": "approved" }
    ip_address   VARCHAR(50),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 Extended Tables (Features 15–27)

#### `burnout_alerts`
```sql
CREATE TABLE burnout_alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    signal      VARCHAR(50) NOT NULL,     -- consecutive_days|weekly_overtime|extreme_hours|leave_not_taken
    value       DECIMAL,
    threshold   DECIMAL,
    severity    VARCHAR(20) NOT NULL,     -- high|medium|watch
    resolved    BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

#### `nudges`
```sql
CREATE TABLE nudges (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    message     TEXT NOT NULL,
    type        VARCHAR(50) NOT NULL,     -- burnout|leave_lapse|missed_checkout|approval|birthday
    read        BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

#### `public_holidays`
```sql
CREATE TABLE public_holidays (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name    VARCHAR(100) NOT NULL,
    date    DATE NOT NULL UNIQUE,
    year    INTEGER NOT NULL
);
```

#### `office_config`
```sql
CREATE TABLE office_config (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    office_lat          DECIMAL(10,8),
    office_lng          DECIMAL(11,8),
    geofence_radius_m   INTEGER DEFAULT 150,
    office_ip_subnet    VARCHAR(20),       -- e.g. 192.168.1.0/24
    wifi_checkin_enabled BOOLEAN DEFAULT FALSE,
    gps_checkin_enabled  BOOLEAN DEFAULT TRUE,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `chat_channels`
```sql
CREATE TABLE chat_channels (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type        VARCHAR(30) NOT NULL,  -- 'announcement'|'department'|'direct'|'meeting'
    name        VARCHAR(100),
    department  VARCHAR(100),
    created_by  UUID REFERENCES employees(id),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

#### `chat_messages`
```sql
CREATE TABLE chat_messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id   UUID NOT NULL REFERENCES chat_channels(id),
    sender_id    UUID NOT NULL REFERENCES employees(id),
    body         TEXT NOT NULL,         -- max 1000 chars
    message_type VARCHAR(20) DEFAULT 'text',  -- 'text'|'meeting_invite'|'announcement'
    meeting_meta JSONB,               -- { "time": "...", "room": "...", "agenda": "..." }
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

#### `chat_reads`
```sql
CREATE TABLE chat_reads (
    employee_id UUID REFERENCES employees(id),
    message_id  UUID REFERENCES chat_messages(id),
    read_at     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (employee_id, message_id)
);
```

#### `meeting_rsvp`
```sql
CREATE TABLE meeting_rsvp (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES chat_messages(id),
    employee_id UUID REFERENCES employees(id),
    response   VARCHAR(10) NOT NULL,  -- accept|decline|maybe
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(message_id, employee_id)
);
```

### 5.3 Key Database Safety Mechanisms

**Overlapping Leave Prevention (Exclusion Constraint)**
```sql
-- Uses btree_gist extension
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- The EXCLUDE constraint on leave_requests already handles this at DB level.
-- Even if application logic fails, the DB will reject overlapping approved leaves.
```

**Atomic Leave Balance Deduction (Race Condition Fix)**
```sql
-- Instead of: read balance → deduct → write (WRONG — race condition)
-- Use atomic SQL update:
UPDATE leave_balances
SET used = used + :days_requested
WHERE employee_id = :emp_id
  AND year = :year
  AND leave_type = :leave_type
  AND (total - used) >= :days_requested
RETURNING *;
-- If 0 rows returned → insufficient balance → reject request
```

---

## 6. Authentication & Security

### 6.1 Clerk JWT Flow

```
User logs in via Clerk (email + password)
    → Clerk issues signed JWT (RS256)
    → JWT contains: { sub: clerk_user_id, metadata: { role: "employee" | "admin" } }
    → Frontend stores JWT in Clerk's secure storage (httpOnly-like)
    → Every API request: Clerk SDK auto-appends "Authorization: Bearer <jwt>"
    → FastAPI auth.py decodes with Clerk's RSA public key
    → Role extracted, passed to route handler as dependency
```

### 6.2 FastAPI JWT Verification

```python
# core/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt  # python-jose

security = HTTPBearer()

CLERK_PEM_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
<paste from Clerk dashboard>
-----END PUBLIC KEY-----"""

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            CLERK_PEM_PUBLIC_KEY,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        role = payload.get("metadata", {}).get("role", "employee")
        return {"user_id": payload["sub"], "role": role}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    # For sensitive admin actions: double-check via Clerk getUser() API
    return user
```

### 6.3 Next.js Middleware (Route Guard)

```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isAdminRoute = createRouteMatcher(["/admin(.*)"]);
const isProtectedRoute = createRouteMatcher(["/dashboard(.*)", "/attendance(.*)", "/leave(.*)", "/payroll(.*)"]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) await auth.protect();
  if (isAdminRoute(req)) {
    const { sessionClaims } = await auth();
    if (sessionClaims?.metadata?.role !== "admin") {
      return Response.redirect(new URL("/dashboard", req.url));
    }
  }
});

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)"],
};
```

### 6.4 Stale JWT Role Protection

- Token TTL reduced to **15 minutes** in Clerk dashboard settings.
- For all `require_admin` routes, FastAPI additionally calls Clerk's `getUser()` API to verify current role in real-time — catches demoted admins whose token hasn't expired yet.
- Redis caches the result for 2 minutes to avoid hammering Clerk's API.

```python
# services/cache.py — real-time role verification with Redis cache
import httpx, redis.asyncio as aioredis

async def verify_admin_role_live(clerk_user_id: str, redis_client) -> bool:
    cache_key = f"role_verified:{clerk_user_id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return cached == b"admin"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.clerk.com/v1/users/{clerk_user_id}",
            headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"}
        )
    user_data = resp.json()
    role = user_data.get("public_metadata", {}).get("role", "employee")
    await redis_client.setex(cache_key, 120, role)  # cache 2 minutes
    return role == "admin"
```

### 6.5 Device Session Management

- Clerk's built-in session management surfaced in employee profile settings.
- Employees can view all active sessions (device, IP, last seen).
- One-click remote session invalidation — instantly logs out a lost/stolen device.

---

## 7. Functional Requirements — All Modules

### 7.1 Authentication Module (FR-AUTH)

| ID | Requirement | Implementation |
|----|------------|----------------|
| FR-AUTH-01 | Register with Employee ID, Email, Password, Role | Clerk sign-up form, role stored in `publicMetadata` |
| FR-AUTH-02 | Email verification required before dashboard access | Clerk built-in email verification |
| FR-AUTH-03 | Login with email + password | Clerk sign-in form |
| FR-AUTH-04 | Wrong credentials show error message | Clerk handles, displayed in UI |
| FR-AUTH-05 | Successful login redirects to dashboard | `afterSignInUrl="/dashboard"` in Clerk config |
| FR-AUTH-06 | Password must follow security rules | Clerk password policy: min 8 chars, complexity |
| FR-AUTH-07 | JWT expires in 15 minutes | Clerk token TTL setting |
| FR-AUTH-08 | Employees can view and revoke active sessions | Clerk `<UserProfile>` component in profile settings |

### 7.2 Dashboard Module (FR-DASH)

#### Employee Dashboard
- Quick-access cards: Profile, Attendance, Leave Requests, Logout
- Today's check-in/check-out status
- Leave balance summary (paid/sick/unpaid remaining)
- Recent activity feed (last 5 actions)
- Burnout nudge widget (if applicable)

#### Admin / HR Dashboard
- Total employee count
- Today's attendance summary (present / absent / on-leave counts)
- Pending leave approvals queue (with one-click approve/reject)
- Payroll status for current month
- Burnout alerts by department
- Ability to switch employee context and view their data

### 7.3 Employee Profile Module (FR-PROFILE)

| ID | Requirement | Who Can Edit |
|----|------------|-------------|
| FR-PROF-01 | View personal details (name, employee ID, department, designation) | Read-only for employee |
| FR-PROF-02 | View job details | Read-only for employee |
| FR-PROF-03 | View salary structure | Read-only for employee |
| FR-PROF-04 | View uploaded documents | Employee can view |
| FR-PROF-05 | View & update profile picture | Employee can update |
| FR-PROF-06 | Edit address and phone | Employee can edit |
| FR-PROF-07 | Edit all fields | Admin only |
| FR-PROF-08 | Upload documents (medical, ID) | Admin/Employee with MIME validation |

### 7.4 Attendance Module (FR-ATTEND)

| ID | Requirement | Detail |
|----|------------|--------|
| FR-ATTEND-01 | Employee can check in (once per day) | Timestamp recorded, optional geolocation captured |
| FR-ATTEND-02 | Employee can check out | Duration computed, stored |
| FR-ATTEND-03 | Status types: Present, Absent, Half-day, Leave | Computed from check-in time or admin override |
| FR-ATTEND-04 | Daily and weekly attendance views for employee | Calendar UI with color-coded status |
| FR-ATTEND-05 | Admin views attendance of all employees | Filterable table + calendar |
| FR-ATTEND-06 | Geofence validation (optional, admin-configurable) | Backend validates coordinates against office lat/lng |
| FR-ATTEND-07 | Voice check-in ("Check me in") | Browser Web Speech API → POST /attendance/checkin |
| FR-ATTEND-08 | Monthly calendar with Present/Absent markers | Shown in leave application form as context |

#### Geofence Validation Flow
```
Employee clicks "Check In"
    → Browser requests geolocation permission
    → coords captured (lat, lng)
    → POST /attendance/checkin { lat, lng }
    → FastAPI reads office_lat, office_lng, geofence_radius from admin config
    → Haversine distance computed
    → If distance > radius: return 403 "Outside office zone"
    → Else: record attendance
```

### 7.5 Leave & Time-Off Module (FR-LEAVE)

| ID | Requirement | Detail |
|----|------------|--------|
| FR-LEAVE-01 | Employee selects leave type: Paid, Sick, Unpaid, Bereavement, Medical | Dropdown |
| FR-LEAVE-02 | Choose date range via interactive calendar | Date range picker component |
| FR-LEAVE-03 | Add remarks / reason | Text area |
| FR-LEAVE-04 | View attendance calendar with Present/Absent markers in leave form | Contextual — helps pick appropriate dates |
| FR-LEAVE-05 | Leave statuses: Pending, Approved, Rejected | Badge display |
| FR-LEAVE-06 | Admin views all leave requests | Sortable, filterable table |
| FR-LEAVE-07 | Admin approves or rejects with comment | One-click + optional comment |
| FR-LEAVE-08 | Changes reflect immediately in employee records | Webhook triggers Redis cache invalidation |
| FR-LEAVE-09 | Overlapping leaves prevented at DB level | PostgreSQL exclusion constraint |
| FR-LEAVE-10 | Employee can cancel own pending/approved leave | PATCH /leave/{id}/cancel, balance recredited |
| FR-LEAVE-11 | Leave balance deduction is atomic | PostgreSQL UPDATE ... WHERE (total - used) >= N |
| FR-LEAVE-12 | AI Leave Documenter tab | See Section 7.7 |

### 7.6 Payroll Module (FR-PAYROLL)

| ID | Requirement | Detail |
|----|------------|--------|
| FR-PAY-01 | Payroll data is read-only for employees | RSC page, no JS mutation code sent to client |
| FR-PAY-02 | Employee views salary breakdown | Component-by-component view (basic, HRA, transport...) |
| FR-PAY-03 | Employee downloads pay stub PDF | WeasyPrint-generated, served as download |
| FR-PAY-04 | Admin views payroll of all employees | Full table with search/filter |
| FR-PAY-05 | Admin updates salary structure | Form updates salary_components |
| FR-PAY-06 | Monthly cron job runs payroll snapshot | APScheduler triggers at month-end |
| FR-PAY-07 | Payroll snapshot is immutable (stored as JSONB) | payroll_runs.components_snapshot cannot be updated |
| FR-PAY-08 | Pay stub PDF generated and stored | WeasyPrint renders HTML → PDF → saved to storage path |

#### Automated Payroll Flow
```
APScheduler fires (last day of month, 11:59 PM)
    → For each active employee:
        → Read current salary_components
        → Apply any deductions (unpaid leave days × daily rate)
        → Calculate gross and net pay
        → INSERT into payroll_runs (immutable snapshot)
        → WeasyPrint generates PDF pay stub
        → PDF stored, URL saved to payroll_runs.pay_stub_url
        → Audit log entry created
```

### 7.7 AI Leave Documenter Feature (FR-LEAVE-AI)

This is a smart sub-feature inside the Leave module that eliminates the dual-step of filling the portal AND emailing HR separately.

#### Feature Flow

```
Employee opens Leave tab
    → Clicks "AI Leave Documenter" tab in LeaveForm
    → Sees smart form:
         - Date range picker (same calendar)
         - Reason checklist: Personal Work | Paid Leave | Medical | Bereavement | Custom
         - Optional: custom reason text area
    → Clicks "Generate Preview"
    → Frontend POST /nlp/generate-leave-email
         { name, department, start_date, end_date, reason, leave_type }
    → FastAPI sends structured data to Ollama (Llama 3)
    → Ollama returns formal email text
    → EmailPreviewModal opens showing AI-drafted email
    → Employee can edit the draft
    → Employee clicks "Submit & Send"
    → FastAPI:
         1. INSERT leave_request (status: pending, generated_email_body saved)
         2. Redis flags employee's leave balance cache as "dirty"
         3. Resend API sends email to HR inbox
         4. audit_log entry: { action: "leave_email_sent", metadata: { email_sent: true } }
    → Employee sees confirmation: "Leave request submitted & HR notified"
```

#### Ollama Prompt (Llama 3)

```python
LEAVE_EMAIL_PROMPT = """
You are an HR communications assistant. Generate a formal leave request email.

Employee Name: {name}
Department: {department}
Leave Type: {leave_type}
Start Date: {start_date}
End Date: {end_date}
Reason: {reason}

Requirements:
- Professional and respectful tone
- Subject line included
- Mention that the request is also submitted in the HRMS portal for approval
- Keep it concise (under 150 words body)
- No placeholder text — use the real values provided

Respond in JSON format only:
{
  "subject": "...",
  "body": "..."
}
"""
```

#### NLP Graceful Degradation

```python
# routers/nlp.py
async def generate_leave_email(payload: LeaveEmailRequest):
    try:
        response = await call_ollama(LEAVE_EMAIL_PROMPT.format(**payload.dict()))
        return JSONResponse({"fallback": False, "email": response})
    except Exception:
        # Ollama unavailable or malformed response
        return JSONResponse({"fallback": True})
        # Frontend receives fallback: true → shows standard manual form
        # with toast: "AI drafting unavailable. Please write your reason manually."
```

### 7.8 Voice & NLP Input (FR-VOICE)

#### Tier 1 — Simple Voice Commands (Web Speech API, Free, No Server)

Handles: "Check me in", "Check me out", "Show my attendance", "Apply for leave"

```typescript
// hooks/useVoice.ts
export function useVoiceCommand() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = "en-US";
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.toLowerCase();
    if (transcript.includes("check in")) triggerCheckIn();
    if (transcript.includes("check out")) triggerCheckOut();
    if (transcript.includes("apply for leave")) openLeaveForm();
  };
  return { startListening: () => recognition.start() };
}
```

#### Tier 2 — Audio Leave Application (Whisper, Self-Hosted, Free)

Employee records voice memo describing leave → uploaded as audio → Whisper transcribes → Llama 3 parses dates and reason → pre-fills leave form.

```python
# routers/voice.py
@router.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile, user=Depends(get_current_user)):
    # 1. Validate file (MIME, size, ClamAV scan)
    await validate_file(file, allowed_types=["audio/wav", "audio/mpeg", "audio/webm"], max_mb=10)
    
    # 2. Send to Whisper container
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://whisper:9000/asr", files={"audio_file": file.file})
    transcript = resp.json()["text"]
    
    # 3. Send transcript to Ollama for structured parsing
    parsed = await call_ollama(VOICE_PARSE_PROMPT.format(transcript=transcript))
    # Returns: { "start_date": "2025-08-10", "end_date": "2025-08-12", "reason": "medical" }
    
    return {"transcript": transcript, "parsed": parsed}
```

### 7.9 Burnout Detection (FR-BURNOUT)

```python
# services/attendance_analytics.py — APScheduler runs this nightly
async def check_burnout():
    configs = await db.execute(select(BurnoutConfig))
    for config in configs.scalars():
        employees = await get_employees_by_department(config.department)
        for emp in employees:
            consecutive_days = await count_consecutive_workdays(emp.id)
            weekly_overtime = await compute_weekly_overtime(emp.id)
            
            if consecutive_days >= config.max_consecutive_days:
                await send_burnout_alert(emp, config.alert_email, reason="consecutive_days")
            
            if weekly_overtime >= config.max_weekly_overtime_hrs:
                await send_burnout_alert(emp, config.alert_email, reason="overtime")
```

Admin can configure thresholds per department via the analytics dashboard. No hardcoded values.

### 7.10 HR Chatbot (FR-CHATBOT)

A simple RAG-lite chatbot powered by Ollama that answers HR FAQs grounded in the employee's real data.

**Example queries it handles:**
- "How many sick leaves do I have left?"
- "What is my current salary?"
- "When was my last attendance marked absent?"
- "What is the leave policy for bereavement?"

```python
# routers/chatbot.py
HR_CHATBOT_PROMPT = """
You are an HR assistant for {company_name}. Answer questions using only the data below.
Do not make up information. If you don't know, say so.

Employee Profile: {employee_data}
Leave Balances: {leave_balances}
Recent Attendance: {attendance_summary}
Company Leave Policy: {policy_text}

Employee Question: {question}

Answer concisely and helpfully.
"""
```

---

## 8. Backend Logic — FastAPI

### 8.1 Core Entry Point

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.database import init_db
from services.attendance_analytics import check_burnout
from services.payroll_calc import run_monthly_payroll

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler.add_job(check_burnout, "cron", hour=2)              # nightly 2 AM
    scheduler.add_job(run_monthly_payroll, "cron", day="last", hour=23, minute=59)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="HRMS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourproductiondomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8.2 Leave Router (Full Logic)

```python
# routers/leave.py
@router.post("/leave")
async def create_leave_request(
    payload: LeaveCreateSchema,
    send_email: bool = False,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user=Depends(get_current_user)
):
    # 1. Check burnout config & leave balance
    balance = await get_leave_balance(db, user["user_id"], payload.leave_type)
    days = (payload.end_date - payload.start_date).days + 1
    if balance.total - balance.used < days:
        raise HTTPException(400, "Insufficient leave balance")
    
    # 2. Atomic balance deduction (race-condition safe)
    result = await db.execute(
        text("""
            UPDATE leave_balances
            SET used = used + :days
            WHERE employee_id = (SELECT id FROM employees WHERE clerk_id = :clerk_id)
              AND year = :year AND leave_type = :leave_type
              AND (total - used) >= :days
            RETURNING id
        """),
        {"days": days, "clerk_id": user["user_id"], "year": payload.start_date.year, "leave_type": payload.leave_type}
    )
    if not result.fetchone():
        raise HTTPException(409, "Balance updated concurrently, please retry")
    
    # 3. Insert leave request (DB exclusion constraint catches overlap)
    leave = LeaveRequest(**payload.dict(), employee_id=employee.id)
    db.add(leave)
    
    # 4. Generate and send email if requested
    if send_email and payload.generated_email_body:
        await send_leave_email(payload.generated_email_body, hr_email=settings.HR_EMAIL)
        leave.email_sent = True
    
    await db.commit()
    
    # 5. Invalidate Redis cache
    await redis.delete(f"leave_balance:{user['user_id']}")
    
    # 6. Audit log
    await log_action(db, actor_id=employee.id, action="leave_requested", entity_id=leave.id)
    
    return {"success": True, "leave_id": str(leave.id)}


@router.patch("/leave/{leave_id}/cancel")
async def cancel_leave(leave_id: UUID, db=Depends(get_db), user=Depends(get_current_user)):
    leave = await get_leave_or_404(db, leave_id, user["user_id"])
    if leave.status == "rejected":
        raise HTTPException(400, "Cannot cancel a rejected request")
    
    # Recalculate and recredit balance
    days = (leave.end_date - leave.start_date).days + 1
    await db.execute(
        text("UPDATE leave_balances SET used = used - :days WHERE employee_id = :eid AND year = :y AND leave_type = :lt"),
        {"days": days, "eid": leave.employee_id, "y": leave.start_date.year, "lt": leave.leave_type}
    )
    leave.status = "cancelled"
    await db.commit()
    return {"success": True}
```

### 8.3 File Upload Validation

```python
# services/file_validator.py
import magic
import httpx

ALLOWED_DOCUMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/webm"}

async def validate_file(file: UploadFile, allowed_types: set, max_mb: int):
    contents = await file.read()
    await file.seek(0)  # reset for downstream use
    
    # Size check
    if len(contents) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"File too large. Maximum {max_mb}MB allowed.")
    
    # MIME type check (via python-magic, reads file header not extension)
    detected_mime = magic.from_buffer(contents, mime=True)
    if detected_mime not in allowed_types:
        raise HTTPException(415, f"Invalid file type: {detected_mime}")
    
    # ClamAV virus scan
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://clamav:3310/scan",
            files={"file": contents}
        )
    if resp.json().get("infected"):
        raise HTTPException(400, "File failed virus scan")
```

### 8.4 Email Notification Service

```python
# services/notification.py
import httpx

class EmailGenerator:
    def __init__(self):
        self.resend_api_key = settings.RESEND_API_KEY  # Free tier: 100 emails/day
    
    async def send_leave_notification(self, to: str, subject: str, body: str):
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {self.resend_api_key}"},
                json={
                    "from": "hrms@yourdomain.com",
                    "to": to,
                    "subject": subject,
                    "html": f"<pre style='font-family:sans-serif'>{body}</pre>"
                }
            )
```

---

## 9. Frontend Logic — Next.js 15

### 9.1 Shared TypeScript Types

```typescript
// types/index.ts — used on frontend AND passed to API layer

export interface Employee {
  id: string;
  clerkId: string;
  employeeId: string;
  name: string;
  department: string;
  designation: string;
  role: "admin" | "employee";
}

export interface LeaveRequest {
  id: string;
  employeeId: string;
  leaveType: "paid" | "sick" | "unpaid" | "bereavement" | "medical";
  startDate: string;
  endDate: string;
  status: "pending" | "approved" | "rejected" | "cancelled";
  remarks?: string;
  adminComment?: string;
  generatedEmailBody?: string;
  emailSent: boolean;
}

export interface AttendanceRecord {
  id: string;
  employeeId: string;
  date: string;
  status: "present" | "absent" | "half-day" | "leave";
  checkIn?: string;
  checkOut?: string;
}

export type ApiResponse<T> =
  | { data: T; success: true }
  | { error: string; success: false };
```

### 9.2 Typed API Wrapper

```typescript
// lib/api.ts
import { auth } from "@clerk/nextjs/server";

export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const { getToken } = auth();
  const token = await getToken();
  
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options?.headers,
    },
  });
  
  const json = await res.json();
  if (!res.ok) return { success: false, error: json.detail || "Request failed" };
  return { success: true, data: json };
}
```

### 9.3 TanStack Query Hooks

```typescript
// hooks/useLeave.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useLeaveRequests() {
  return useQuery({
    queryKey: ["leave-requests"],
    queryFn: () => apiFetch<LeaveRequest[]>("/leave"),
    staleTime: 60_000,
  });
}

export function useSubmitLeave() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: LeaveCreatePayload) =>
      apiFetch("/leave", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leave-requests"] });
      qc.invalidateQueries({ queryKey: ["leave-balance"] });
    },
  });
}
```

### 9.4 AI Leave Documenter Component

```typescript
// components/features/leave/LeaveForm.tsx (AI tab)
"use client";
import { useState } from "react";
import { EmailPreviewModal } from "./EmailPreviewModal";

const REASON_CHECKLIST = [
  "Personal Work", "Paid Leave", "Medical Appointment",
  "Bereavement", "Family Emergency", "Custom..."
];

export function AILeaveDocumenter() {
  const [selectedReason, setSelectedReason] = useState("");
  const [customReason, setCustomReason] = useState("");
  const [emailDraft, setEmailDraft] = useState<{subject:string, body:string} | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [fallback, setFallback] = useState(false);

  const generateDraft = async () => {
    const res = await apiFetch<{fallback:boolean, email:{subject:string,body:string}}>("/nlp/generate-leave-email", {
      method: "POST",
      body: JSON.stringify({ reason: selectedReason === "Custom..." ? customReason : selectedReason, ...dateRange })
    });
    if (res.success && !res.data.fallback) {
      setEmailDraft(res.data.email);
      setIsPreviewOpen(true);
    } else {
      setFallback(true); // Show manual form fallback
    }
  };

  return (
    <div>
      <p className="text-sm text-muted-foreground mb-3">
        Select a reason and let AI draft a professional email to HR.
      </p>
      {REASON_CHECKLIST.map(reason => (
        <label key={reason} className="flex items-center gap-2 mb-2 cursor-pointer">
          <input type="radio" name="reason" value={reason}
            checked={selectedReason === reason}
            onChange={() => setSelectedReason(reason)} />
          {reason}
        </label>
      ))}
      {selectedReason === "Custom..." && (
        <textarea className="w-full border rounded p-2 mt-2"
          placeholder="Describe your reason..."
          value={customReason} onChange={e => setCustomReason(e.target.value)} />
      )}
      <button onClick={generateDraft} className="mt-4 btn-primary">
        ✨ Generate Email Preview
      </button>
      {fallback && (
        <p className="text-amber-600 text-sm mt-2">
          AI drafting temporarily unavailable. Please write your reason manually.
        </p>
      )}
      {emailDraft && (
        <EmailPreviewModal
          isOpen={isPreviewOpen}
          draft={emailDraft}
          onEdit={setEmailDraft}
          onConfirmSend={handleSubmitAndSend}
        />
      )}
    </div>
  );
}
```

---

## 10. Free API & AI Integration Strategy

### 10.1 Complete Free AI Stack

| Feature | Tool | Cost | Setup |
|---------|------|------|-------|
| Leave email drafting | Ollama + Llama 3 8B | Free (self-hosted) | Docker container |
| Leave form NLP parsing | Ollama + Mistral 7B | Free (self-hosted) | Same Ollama instance |
| Voice → text (audio) | Whisper (onerahmet/openai-whisper-asr-webservice) | Free (self-hosted) | Docker container |
| Voice commands | Browser Web Speech API | Free (no server) | 3 lines of JS |
| HR chatbot | Ollama + Llama 3 | Free (self-hosted) | Same Ollama instance |
| Email delivery | Resend (free tier) | Free up to 100/day | API key signup |
| Authentication | Clerk (free tier) | Free up to 10k MAU | Clerk dashboard |
| PDF generation | WeasyPrint | Free (open-source) | pip install |
| Virus scanning | ClamAV | Free (open-source) | Docker sidecar |

### 10.2 Ollama Setup in Docker Compose

```yaml
# docker-compose.yml (relevant section)
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia     # remove if no GPU
            count: all
            capabilities: [gpu]
```

On first startup, pull models:
```bash
docker exec -it hrms-ollama-1 ollama pull llama3
docker exec -it hrms-ollama-1 ollama pull mistral
```

### 10.3 Whisper Setup

```yaml
# docker-compose.yml (Whisper section)
whisper:
  image: onerahmet/openai-whisper-asr-webservice:latest
  ports:
    - "9000:9000"
  environment:
    - ASR_MODEL=base          # 'base' is fast and free; 'medium' is more accurate
    - ASR_ENGINE=openai_whisper
```

### 10.4 Calling Ollama from FastAPI

```python
# services/ollama_client.py
import httpx, json

OLLAMA_BASE_URL = "http://ollama:11434"

async def call_ollama(prompt: str, model: str = "llama3") -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
    result = resp.json()
    text = result["response"].strip()
    
    # Strip possible markdown code fences
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    return json.loads(text)
```

---

## 11. Full Data Flow Diagrams

### 11.1 Check-In Flow (with Geofence)

```
Employee clicks "Check In" (browser)
    │
    ▼
Browser requests geolocation permission
    │
    ├─ Denied → show manual check-in (no location) or block (admin-configured)
    │
    ▼
navigator.geolocation.getCurrentPosition() → { lat, lng }
    │
    ▼
POST /attendance/checkin { lat, lng }  [Bearer JWT]
    │
    ▼
FastAPI: get_current_user() — decode JWT
    │
    ▼
Read admin_config.geofence { office_lat, office_lng, radius_meters }
    │
    ▼
Haversine distance calculation
    │
    ├─ distance > radius → 403 "Outside office zone"
    │
    ▼
Check: already checked in today?
    │
    ├─ Yes → 409 "Already checked in"
    │
    ▼
INSERT attendance_records { status: 'present', check_in: NOW() }
    │
    ▼
Redis: invalidate today's attendance cache for employee
    │
    ▼
audit_log: { action: "check_in", metadata: { lat, lng } }
    │
    ▼
200 OK → UI updates check-in button to "Check Out" + shows check-in time
```

### 11.2 Leave Submission Flow (with AI Documenter + Email)

```
Employee fills AI Leave Documenter form
    │
    ▼
POST /nlp/generate-leave-email { name, dates, reason }
    │
    ▼
FastAPI → Ollama (Llama 3) → returns { subject, body }
    │
    ├─ Ollama down → { fallback: true } → frontend shows manual form
    │
    ▼
EmailPreviewModal opens — employee reviews / edits AI draft
    │
    ▼
Employee clicks "Submit & Send"
    │
    ▼
POST /leave { ...leaveData, send_email: true, generated_email_body: "..." }
    │
    ▼
FastAPI: verify JWT + role
    │
    ▼
Check burnout_config limits for department
    │
    ▼
Atomic leave balance check (UPDATE ... WHERE total - used >= days)
    │
    ├─ Insufficient → 400
    │
    ▼
INSERT leave_requests (PostgreSQL EXCLUDE constraint enforces no overlap)
    │
    ├─ Overlap detected → PostgreSQL raises exception → 409 "Dates overlap with existing leave"
    │
    ▼
Resend API: send HTML email to HR inbox
    │
    ▼
Redis: flag employee leave balance cache as dirty (delete key)
    │
    ▼
audit_log: { action: "leave_requested", metadata: { email_sent: true } }
    │
    ▼
200 OK → UI: success toast "Leave submitted & HR notified via email"
```

### 11.3 Admin Approval Flow

```
Admin visits /admin/approvals
    │
    ▼
GET /leave?status=pending (role guard: require_admin)
    │
    ▼
FastAPI: secondary Clerk getUser() verify (stale JWT protection)
    │
    ▼
Returns pending queue from PostgreSQL (no Redis — admin needs fresh data)
    │
    ▼
Admin clicks Approve / Reject + optional comment
    │
    ▼
PATCH /leave/{id}/approve { status: "approved", comment: "..." }
    │
    ▼
UPDATE leave_requests SET status, admin_comment, reviewed_by, reviewed_at
    │
    ▼
If rejected: recalculate & recredit leave balance (atomic UPDATE)
    │
    ▼
Resend: notify employee of decision
    │
    ▼
Redis: invalidate employee's leave balance cache
    │
    ▼
audit_log: { action: "leave_approved", actor: admin_id, entity: leave_id }
    │
    ▼
WebSocket push (or TanStack Query refetch) updates employee dashboard
```

### 11.4 Security Flow (Stale JWT Catch)

```
Admin's role is changed to "employee" by superadmin (Clerk dashboard)
    │
    ▼
Former admin still has valid JWT (up to 15 min remaining TTL)
    │
    ▼
Former admin attempts POST /employees/fire/{id} (admin-only endpoint)
    │
    ▼
FastAPI: require_admin() reads JWT → role still "admin" in token ← STALE
    │
    ▼
Secondary check: verify_admin_role_live(clerk_user_id) → calls Clerk getUser()
    │
    ▼
Clerk returns current role: "employee"
    │
    ▼
403 Forbidden — access denied even though JWT said admin
    │
    ▼
Redis caches "employee" role for 2 minutes (prevents repeated Clerk calls)
```

### 11.5 Monthly Payroll Flow

```
APScheduler fires at end of month (23:59, last day)
    │
    ▼
Query all active employees
    │
    ▼
For each employee:
    Read salary_components (current, effective_from <= today)
    │
    ▼
    Read unpaid leave days for the month
    │
    ▼
    Compute: gross = sum(components), deductions = unpaid_days × daily_rate
    net = gross - deductions
    │
    ▼
    INSERT payroll_runs { gross, deductions, net, components_snapshot: JSONB }
    │
    ▼
    WeasyPrint: render HTML pay stub template → PDF bytes
    │
    ▼
    Save PDF to /storage/paystubs/{employee_id}/{year}-{month}.pdf
    │
    ▼
    UPDATE payroll_runs SET pay_stub_url
    │
    ▼
    Resend: email "Your pay stub for [Month] is ready" to employee
    │
    ▼
audit_log: { action: "payroll_generated", metadata: { month, year, net_pay } }
```

---

## 12. Security Implementation

### 12.1 Security Checklist

| Area | Measure | Implementation |
|------|---------|----------------|
| **JWT Validation** | RS256 signature, Clerk PEM key | python-jose in auth.py |
| **JWT TTL** | 15 minutes | Clerk dashboard setting |
| **Stale Role** | Real-time Clerk getUser() for admin actions | services/cache.py |
| **Route Guard** | Middleware blocks employee from /admin/* | middleware.ts clerkMiddleware |
| **File Upload** | MIME type check (python-magic, not extension) | services/file_validator.py |
| **File Upload** | Size cap: 5MB docs, 10MB audio | services/file_validator.py |
| **Virus Scan** | ClamAV on every upload | Docker sidecar |
| **SQL Injection** | SQLAlchemy parameterized queries, no raw string interpolation | All DB calls |
| **CORS** | Whitelist only frontend origin | FastAPI CORSMiddleware |
| **Geofence Fraud** | Server-side coordinate validation | routers/attendance.py |
| **Race Condition** | Atomic SQL balance updates | PostgreSQL UPDATE WHERE |
| **Data Overlap** | PostgreSQL EXCLUDE constraint | Database schema |
| **Audit Trail** | Every mutation logged | audit_log table |
| **Session Hijack** | Employee can revoke devices | Clerk session management UI |
| **Env Secrets** | All keys in .env, pydantic-settings | Never hardcoded |
| **HTTPS** | Nginx TLS termination | Production Nginx config |

### 12.2 Environment Variables

```bash
# .env (never commit this file)

# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"

# Database
DATABASE_URL=postgresql+asyncpg://hrms:password@postgres:5432/hrms_db

# Redis
REDIS_URL=redis://redis:6379/0

# Email
RESEND_API_KEY=re_...
HR_EMAIL=hr@yourcompany.com

# AI
OLLAMA_URL=http://ollama:11434
WHISPER_URL=http://whisper:9000

# Office Geofence (optional)
OFFICE_LAT=12.9716
OFFICE_LNG=77.5946
GEOFENCE_RADIUS_METERS=200

# Company
COMPANY_NAME="Your Company Ltd"
```

---

## 13. Non-Functional Requirements

### 13.1 Performance

| Metric | Target |
|--------|--------|
| API response time (cached) | < 100ms |
| API response time (uncached) | < 500ms |
| AI email generation (Ollama) | < 5 seconds |
| Whisper transcription (30s audio) | < 10 seconds |
| Dashboard load (RSC) | < 1 second |
| Payroll PDF generation | < 3 seconds per employee |

### 13.2 Scalability

- Redis caches leave balances, dashboard summaries — reduces PG read load.
- SQLAlchemy async engine — non-blocking DB queries.
- TanStack Query staleTime prevents redundant API calls from the client.
- Payroll runs are async background jobs — do not block API.

### 13.3 Reliability

- NLP graceful degradation: Ollama failure falls back to manual form.
- Database exclusion constraint is a hard safety net independent of application logic.
- Atomic SQL updates eliminate race conditions even under concurrent load.
- APScheduler runs inside FastAPI — no external dependency for cron jobs.

### 13.4 Accessibility & UX

- shadcn/ui components are ARIA-compliant by default.
- Voice commands provide hands-free access.
- Email preview allows employee to verify AI draft before sending.
- All status changes are immediately reflected (cache invalidation on write).

---

## 14. Performance & Security Features

> These cross-cutting concerns are implemented across all modules. For full implementation specs, see `differentiators_fetaures.md` Part B.

### 14.1 Redis Dashboard Caching

Dashboard summary data (attendance count, pending leaves, profile) served from Redis with 60-second TTL. No database hit on page load. Cache invalidated on any mutation.

| Aspect | Detail |
|--------|--------|
| **Cache key** | `dashboard:{user_id}:{role}` |
| **TTL** | 60 seconds |
| **Invalidation** | On any mutation (check-in, leave request, approval, profile edit) |
| **Impact** | 80%+ reduction in DB read load, sub-100ms dashboard response |

### 14.2 Input Validation — Pydantic v2

Every API request body validated with Pydantic v2 schemas. SQL injection impossible via SQLAlchemy parameterized queries. XSS prevented at Zod layer on frontend.

| Layer | Tool | Protection |
|-------|------|------------|
| Frontend | Zod schemas | Invalid data never leaves browser |
| Server | Pydantic v2 | Type safety, extra field rejection |
| Database | SQLAlchemy + PostgreSQL | Parameterized queries, constraints |

### 14.3 DB Query Optimization

Composite indexes on all high-frequency queries. EXPLAIN ANALYZE tested before submission. Cursor-based pagination on all list endpoints.

Key indexes: `attendance_records(employee_id, date)`, `leave_requests(status, start_date)`, `payroll_runs(employee_id, year, month)`, `audit_log(actor_id, created_at)`

### 14.4 Aggregated Dashboard API

Single `GET /api/dashboard` endpoint returns everything in one JSON. No waterfall API calls from frontend. TanStack Query caches it client-side too.

- Backend uses `asyncio.gather()` to fan out queries concurrently
- Single roundtrip instead of 4-5 sequential calls
- Reduces dashboard load time from ~400ms to ~150ms

### 14.5 Audit Logging

Every admin action writes to `audit_log` table. Old and new values stored as JSONB. Immutable. Used for compliance reporting.

| Action | Data Stored |
|--------|-------------|
| `leave_approved` | old_status, new_status, admin_comment |
| `salary_updated` | old_components, new_components |
| `admin_profile_edit` | old_values, new_values |
| `employee_created` | employee_id, department, role |
| `payroll_generated` | month, year, net_pay |

### 14.6 Async FastAPI Throughout

All DB calls use asyncpg via SQLAlchemy async. All Redis calls async. No blocking I/O. Handles concurrent requests without thread starvation.

| Scenario | Sync (Thread-per-req) | Async (FastAPI) |
|----------|----------------------|-----------------|
| 100 concurrent requests | Needs 100 threads | Needs ~4 threads |
| Memory per connection | ~8MB | ~8KB |
| Max practical concurrency | ~200 | ~10,000 |

---

## 15. DevOps & Deployment

### 15.1 Docker Compose (Full Stack)

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: hrms_db
      POSTGRES_USER: hrms
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  whisper:
    image: onerahmet/openai-whisper-asr-webservice:latest
    environment:
      - ASR_MODEL=base
      - ASR_ENGINE=openai_whisper
    ports:
      - "9000:9000"

  clamav:
    image: clamav/clamav:stable
    ports:
      - "3310:3310"

  backend:
    build: ./backend
    depends_on: [postgres, redis, ollama, whisper, clamav]
    env_file: .env
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on: [backend]
    env_file: .env
    ports:
      - "3000:3000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on: [frontend, backend]

volumes:
  pg_data:
  ollama_data:
```

### 15.2 Nginx Config

```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Authorization $http_authorization;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend:3000;
    }
}
```

### 15.3 Database Migrations (Alembic)

```bash
# Initialize migrations
alembic init migrations

# Create a migration
alembic revision --autogenerate -m "initial_schema"

# Apply migrations
alembic upgrade head
```

### 15.4 First-Time Setup Script

```bash
#!/bin/bash
# setup.sh — run once

# Start all services
docker compose up -d

# Wait for postgres
sleep 5

# Run migrations
docker compose exec backend alembic upgrade head

# Pull AI models
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull mistral

# Update ClamAV signatures
docker compose exec clamav freshclam

echo "✅ HRMS is ready at http://localhost:3000"
```

---

## 16. Development Timeline & Build Order

### Phase 1 — Foundation (Day 1-2)

1. Create Next.js 15 app (`--typescript --tailwind --app`)
2. Install `@clerk/nextjs`, configure `middleware.ts`
3. Set up `types/globals.d.ts` (Clerk role type), `types/index.ts`
4. Scaffold FastAPI with `core/auth.py`, `core/database.py`, `core/redis.py`
5. Write `docker-compose.yml`, get all services running
6. Run Alembic migrations (create all tables)
7. **Verify:** role switching in Clerk dashboard reflects immediately

### Phase 2 — Auth + Dashboard (Day 3)

1. Build `lib/api.ts` typed fetch wrapper
2. Build employee dashboard (quick-access cards, role split)
3. Build admin dashboard (employee list, pending count widgets)
4. **Verify:** admin sees admin dashboard, employee is blocked from `/admin/*`

### Phase 3 — Core Features (Day 4-6)

1. Attendance: check-in/out UI + API + calendar views + geofence
2. Leave: apply form + calendar + status badges + admin approval queue
3. Employee profile: view + limited edit + admin full edit

### Phase 4 — AI Features (Day 7-8)

1. Integrate Ollama: test Llama 3 and Mistral locally
2. Build AI Leave Documenter: form + NLP endpoint + EmailPreviewModal
3. Build Voice check-in (Web Speech API hook)
4. Build Whisper transcription for audio leave applications
5. Build HR chatbot endpoint + frontend chat widget

### Phase 5 — Payroll + Burnout + Cron (Day 9-10)

1. Salary components model + admin payroll control
2. APScheduler: monthly payroll cron + WeasyPrint PDF generation
3. Burnout detection service + per-department config
4. Pay stub download in employee portal

### Phase 6 — Security Hardening + Polish (Day 11-12)

1. ClamAV file validation integration
2. Stale JWT real-time Clerk verification
3. Device session management in profile
4. Audit log viewer for admin
5. Error boundaries, loading states, empty states throughout UI

---

## Appendix A — Key Decisions Summary

| Decision | Chosen Approach | Reason |
|---------|----------------|--------|
| Auth | Clerk | Zero backend session code; role metadata in JWT; free tier covers hackathon + small prod |
| AI | Ollama self-hosted | Free, no API key, no per-token cost, runs offline |
| Voice | Web Speech API + Whisper | Browser API for commands (instant, free); Whisper for transcription (accurate, free) |
| Email | Resend | 100 free emails/day; clean API; better DX than SendGrid free tier |
| Leave safety | PostgreSQL EXCLUDE constraint | Database-level guarantee that no app bug can cause overlapping leaves |
| Balance update | Atomic SQL UPDATE | Eliminates TOCTOU race condition under concurrent admin approvals |
| Payroll | Immutable JSONB snapshot | Pay stubs must never change retroactively; JSONB snapshot guarantees this |
| Cron | APScheduler in FastAPI | No separate service (Celery, Redis Beat) needed; simpler ops |
| PDF | WeasyPrint | HTML → PDF, free, runs server-side, no external service |
| Caching | Redis with TTL | Sub-100ms dashboard loads, automatic invalidation on mutation |
| Validation | Pydantic v2 + Zod | Type-safe input validation at both server and client layers |
| Real-time | SSE + Redis pub/sub | No WebSocket library needed, works through Nginx |

---

## 17. Feature Reference Matrix

> Complete mapping of all 27 features to their implementation locations.

### Part A — Core SRS Features (Mandatory)

| # | Feature | Backend Router | Frontend Component | DB Tables | Key Dependencies |
|---|---------|---------------|-------------------|-----------|-----------------|
| 1 | Clerk Authentication | `core/auth.py` | `middleware.ts`, Clerk UI | `employees` | Clerk SDK |
| 2 | Role-Based Dashboards | `routers/dashboard.py` | `app/(dashboard)/dashboard/page.tsx` | — | Redis cache |
| 3 | Employee Profile Management | `routers/employees.py` | `components/features/admin/EmployeeTable.tsx` | `employees` | R2 presigned URLs |
| 4 | Admin Leave Approval | `routers/leave.py` | `components/features/admin/ApprovalQueue.tsx` | `leave_requests` | Resend email |
| 5 | Attendance Check-In/Out | `routers/attendance.py` | `components/features/attendance/CheckInButton.tsx` | `attendance_records` | Redis (double check-in) |
| 6 | Payroll Visibility | `routers/payroll.py` | `components/features/payroll/SalaryCard.tsx` | `payroll_runs`, `salary_components` | RSC (zero JS) |
| 7 | Leave Application | `routers/leave.py` | `components/features/leave/LeaveForm.tsx` | `leave_requests`, `leave_balances` | PostgreSQL EXCLUDE |
| 8 | Admin Employee Management | `routers/employees.py` | `components/features/admin/EmployeeTable.tsx` | `employees` | Clerk API |

### Part B — Performance & Security Features

| # | Feature | Implementation Location | Scope |
|---|---------|------------------------|-------|
| 9 | Redis Dashboard Caching | `services/cache.py`, `routers/dashboard.py` | All dashboard endpoints |
| 10 | Input Validation (Pydantic v2) | `schemas/*.py`, Zod on frontend | All API request/response |
| 11 | DB Query Optimization | SQL migrations, `EXPLAIN ANALYZE` | All high-frequency queries |
| 12 | Aggregated Dashboard API | `routers/dashboard.py` | `GET /api/dashboard` |
| 13 | Audit Logging | `services/audit.py`, `audit_log` table | All admin mutations |
| 14 | Async FastAPI Throughout | `core/database.py`, `core/redis.py` | All routers and services |

### Part C — AI-Powered Differentiators

| # | Feature | Backend Router | Frontend Component | AI Model | Cost |
|---|---------|---------------|-------------------|----------|------|
| 15 | Conversational Leave | `routers/nlp.py` | `ConversationalLeave.tsx` | Llama 3 | Free |
| 16 | HR Chatbot | `routers/chatbot.py` | Chat widget | Mistral 7B | Free |
| 17 | Voice Commands | — (browser only) | `VoiceMicButton.tsx` | Web Speech API | Free |
| 18 | Voice-to-Leave | `routers/voice.py` | `VoiceToLeave.tsx` | Whisper + Llama 3 | Free |
| 19 | Attendance Heatmap | `routers/attendance.py` | `AttendanceHeatmap.tsx` | — | Free |
| 20 | Burnout Early Warning | `services/attendance_analytics.py` | `BurnoutDashboard.tsx` | — | Free |
| 21 | Live Salary Simulator | — (client-side) | `SalarySimulator.tsx` | — | Free |
| 22 | AI Leave Advisor | `routers/leave.py` | `LeaveAdvisorCard.tsx` | Llama 3 | Free |
| 23 | Smart Auto Check-In | `routers/attendance.py` | `AutoCheckinBanner.tsx` | — | Free |
| 24 | Team Health Score | `routers/analytics.py` | `TeamHealthScore.tsx` | — | Free |
| 25 | Proactive Nudges | `routers/nudges.py` | `NudgeBell.tsx` | — | Free |
| 26 | PDF Pay Stubs | `services/payroll_calc.py` | `PayStubDownload.tsx` | WeasyPrint | Free |
| 27 | Team Chat | `routers/chat.py` | `ChatPanel.tsx` | Redis pub/sub | Free |

---

## 18. Cross-Document Reference

> This HRMS project uses two complementary documentation files:

| Document | Purpose | Contents |
|----------|---------|----------|
| **`README.MD`** (this file) | System architecture & blueprint | Tech stack, folder structure, DB schema, auth flow, data flows, DevOps, build timeline |
| **`differentiators_fetaures.md`** | Complete feature specifications | All 27 features with: What/Why/How, data flows, code outlines, component specs |

### How to Use Both Documents

1. **Start with this README** for the overall architecture, technology decisions, and system design
2. **Reference `differentiators_fetaures.md`** when implementing specific features — each has detailed code outlines, data flows, and UI mockups
3. **Both documents are kept in sync** — when a feature is added or changed, both files are updated

### Feature Coverage

| Area | README.MD | differentiators_fetaures.md |
|------|-----------|---------------------------|
| Architecture overview | ✅ Full | ❌ Not covered |
| Technology stack | ✅ Full | ✅ Updated stack additions |
| Database schema | ✅ All 15 tables | ✅ Extended tables |
| Auth implementation | ✅ Full flow | ✅ Feature #1 detail |
| API endpoints | ✅ Key endpoints | ✅ All endpoints with code |
| Frontend components | ✅ Folder structure | ✅ All components with code |
| Data flow diagrams | ✅ 5 flows | ✅ Per-feature flows |
| DevOps/Docker | ✅ Full | ❌ Not covered |
| AI integration | ✅ Setup guide | ✅ Per-feature prompts |
| Performance optimization | ✅ NFR targets | ✅ Features #9-14 |
| Security hardening | ✅ Checklist | ✅ Per-feature security |

---

*End of HRMS Full System Documentation v3.0*
*All 27 features documented across two complementary files.*
*Last updated: 2026*
