# Northwind HRMS

> AI-powered Human Resource Management System built with Next.js 16, FastAPI, PostgreSQL, and Clerk authentication.

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.12-green)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start (Docker)](#quick-start-docker)
  - [Manual Setup](#manual-setup)
- [Environment Variables](#environment-variables)
- [Authentication Flow](#authentication-flow)
- [API Reference](#api-reference)
- [Features](#features)
- [Database Schema](#database-schema)
- [Development](#development)
  - [Frontend Development](#frontend-development)
  - [Backend Development](#backend-development)
  - [Running Tests](#running-tests)
- [Docker Services](#docker-services)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

Northwind is a full-stack HRMS that combines core HR operations (attendance, leave, payroll, chat) with AI-powered differentiators (conversational leave, HR chatbot, voice commands, burnout detection). The frontend communicates with a FastAPI backend via REST APIs, authenticated through Clerk JWTs.

### Key Capabilities

- **Clerk Authentication** — Managed sign-up/sign-in with JWT RS256, role-based access (admin/employee)
- **Real-time Attendance** — GPS/Wi-Fi aware check-in/out, heatmap calendar, team health scores
- **Leave Management** — CRUD requests, AI advisor, conversational NLP-based leave, PDF export
- **Payroll** — Salary structures, automated calculations, PDF pay stub generation
- **Team Chat** — Channels, direct messaging, meeting RSVPs
- **AI Features** — HR chatbot (Ollama LLM), voice-to-text (Whisper), proactive nudge system
- **Admin Dashboard** — Employee management, approval workflows, analytics, audit logs

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                │
│  Clerk SDK → Axios (token injection) → React Query   │
│  Tailwind CSS 4 + Framer Motion + Radix UI           │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS (Clerk JWT Bearer)
                       ▼
┌─────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                  │
│  /api/v1/* → Pydantic v2 validation → SQLAlchemy     │
│  Async throughout (asyncpg, httpx, redis)            │
└───────┬─────────────┬──────────────┬────────────────┘
        │             │              │
        ▼             ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  PostgreSQL  │ │  Redis   │ │   Ollama     │
│  (Neon DB)   │ │ (cache)  │ │  (LLM API)  │
└──────────────┘ └──────────┘ └──────────────┘
```

---

## Tech Stack

### Frontend

| Technology | Purpose |
|---|---|
| Next.js 16 (App Router) | React framework, SSR, routing |
| React 19 | UI library |
| TypeScript 5 | Type safety |
| Clerk (`@clerk/nextjs`) | Authentication, user management |
| React Query (`@tanstack/react-query`) | Server state, caching, mutations |
| Zustand | Client state management |
| Tailwind CSS 4 | Styling, dark glassmorphism design |
| Framer Motion | Animations |
| Radix UI | Accessible primitives (Dialog, Select, Tooltip, Tabs) |
| Recharts | Data visualization |
| Axios | HTTP client with token injection |
| Lucide React | Icons |
| Sonner | Toast notifications |
| date-fns | Date formatting/manipulation |

### Backend

| Technology | Purpose |
|---|---|
| FastAPI 0.115 | Async API framework |
| Python 3.12 | Runtime |
| SQLAlchemy 2.0 (async) | ORM, database queries |
| asyncpg | PostgreSQL async driver |
| Alembic | Database migrations |
| Pydantic v2 | Request/response validation |
| PyJWT + python-jose | Clerk JWT verification (RS256) |
| Redis (hiredis) | Caching, rate limiting, sessions |
| APScheduler | Background job scheduling |
| WeasyPrint + Jinja2 | PDF pay stub generation |
| httpx | Async HTTP client (Ollama, Whisper, Resend) |

### Infrastructure

| Technology | Purpose |
|---|---|
| PostgreSQL 16 | Primary database (Neon serverless) |
| Redis 7 | Caching, rate limiting |
| Ollama | Local LLM inference (Llama 3, Mistral) |
| Whisper | Speech-to-text |
| ClamAV | File virus scanning |
| Docker Compose | Service orchestration |
| Nginx | Reverse proxy, TLS termination |
| ngrok | Optional tunneling for development |

---

## Project Structure

```
TASK18_ODDO/
├── frontend/
│   └── hrms-frontend/               # Next.js 16 application
│       ├── src/
│       │   ├── app/
│       │   │   ├── (auth)/           # Clerk sign-in/sign-up pages
│       │   │   └── (dashboard)/      # Authenticated app pages
│       │   │       ├── layout.tsx    # Dashboard shell (sidebar + navbar)
│       │   │       ├── dashboard/    # Role-based dashboard
│       │   │       ├── attendance/   # Check-in/out, calendar, heatmap
│       │   │       ├── leave/        # Leave requests, AI advisor
│       │   │       ├── payroll/      # Salary structure, PDF stubs
│       │   │       ├── chat/         # Team channels, messaging
│       │   │       ├── profile/      # Employee profile
│       │   │       └── admin/        # Admin-only pages
│       │   │           ├── employees/
│       │   │           ├── approvals/
│       │   │           ├── analytics/
│       │   │           └── audit/
│       │   ├── components/
│       │   │   ├── features/         # Domain components (attendance, leave, payroll, etc.)
│       │   │   ├── layout/           # Sidebar, Navbar, PageHeader
│       │   │   └── ui/               # Reusable UI primitives
│       │   ├── hooks/
│       │   │   ├── useApi.ts         # 35+ React Query hooks
│       │   │   └── useAuthSync.ts    # Clerk ↔ backend token sync
│       │   ├── lib/
│       │   │   └── api.ts            # Axios instance + setAccessToken()
│       │   ├── stores/               # Zustand stores
│       │   └── types/
│       │       └── index.ts          # TypeScript types (aligned with backend schemas)
│       ├── .env.local                # Clerk keys, API URL (not committed)
│       ├── .env.example              # Sanitized template
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       └── package.json
│
├── Backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                   # App factory, lifespan, middleware
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic Settings (env vars)
│   │   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   │   ├── auth.py               # Clerk JWT verification
│   │   │   ├── redis.py              # Redis connection manager
│   │   │   └── exceptions.py         # Custom HRMSError classes
│   │   ├── models/                   # 15 SQLAlchemy models
│   │   │   ├── employee.py
│   │   │   ├── attendance.py
│   │   │   ├── leave.py
│   │   │   ├── payroll.py
│   │   │   ├── chat.py
│   │   │   └── ...
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── routers/                  # API route handlers
│   │   │   ├── attendance.py         # 8 endpoints
│   │   │   ├── leave.py              # 12 endpoints
│   │   │   ├── payroll.py            # 5 endpoints
│   │   │   ├── chat.py               # 7 endpoints
│   │   │   ├── employees.py          # 3 endpoints
│   │   │   ├── analytics.py          # 2 endpoints
│   │   │   ├── dashboard.py          # 2 endpoints
│   │   │   ├── nudges.py             # 3 endpoints
│   │   │   ├── chatbot.py            # 1 endpoint
│   │   │   ├── voice.py              # 1 endpoint
│   │   │   └── webhooks.py           # 2 endpoints (Clerk webhooks)
│   │   ├── middleware/               # Security headers, rate limiting
│   │   ├── jobs/                     # APScheduler background jobs
│   │   └── storage/                  # Pay stubs, avatars
│   ├── alembic/                      # Database migrations
│   ├── scripts/                      # setup.sh, healthcheck.py, configure_env.py
│   ├── docs/                         # Backend documentation
│   ├── docker-compose.yml            # 8-service orchestration
│   ├── Dockerfile                    # Multi-stage Python 3.12 build
│   ├── nginx.conf                    # TLS reverse proxy
│   ├── requirements.txt              # 56 Python dependencies
│   └── .env.example                  # Backend env template
│
└── README.md                         # This file
```

---

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm/yarn/pnpm
- **Python** 3.12+
- **Docker** and **Docker Compose** (recommended for full stack)
- **Clerk account** (free tier: 10,000 MAU) — [clerk.com](https://clerk.com)
- **Neon PostgreSQL** account (free tier) — [neon.tech](https://neon.tech)

### Quick Start (Docker)

This starts all services: PostgreSQL, Redis, backend, Ollama, Whisper, ClamAV, and Nginx.

```bash
cd Backend
bash scripts/setup.sh
```

The script will:
1. Create `.env` from template (interactive)
2. Generate self-signed SSL certificates
3. Build and start all Docker containers
4. Run database migrations
5. Pull AI models (Llama 3, Mistral)
6. Update ClamAV virus definitions
7. Run health checks

Then start the frontend:

```bash
cd frontend/hrms-frontend
cp .env.local.example .env.local   # Add your Clerk keys
npm install
npm run dev
```

**Access points:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Manual Setup

#### Backend

```bash
cd Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your Clerk keys, database URL, etc.

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend/hrms-frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Add CLERK_PUBLISHABLE_KEY and NEXT_PUBLIC_API_URL

# Start development server
npm run dev
```

---

## Environment Variables

### Backend (`Backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Application secret (min 32 chars) |
| `DATABASE_URL` | Yes | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | No | Redis URL (default: `redis://localhost:6379/0`) |
| `CLERK_PUBLISHABLE_KEY` | Yes | Clerk publishable key (`pk_...`) |
| `CLERK_SECRET_KEY` | Yes | Clerk secret key (`sk_...`) |
| `CLERK_JWT_VERIFICATION_KEY` | Yes | Clerk JWT public key (PEM, RS256) |
| `CLERK_WEBHOOK_SECRET` | No | Clerk webhook signing secret (`whsec_...`) |
| `ENVIRONMENT` | No | `development` / `staging` / `production` (default: `development`) |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `OLLAMA_BASE_URL` | No | Ollama API URL (default: `http://localhost:11434`) |
| `WHISPER_BASE_URL` | No | Whisper API URL (default: `http://localhost:9000`) |
| `RESEND_API_KEY` | No | Resend email API key |
| `NGROK_ENABLED` | No | Enable ngrok tunnel (`true`/`false`) |

### Frontend (`frontend/hrms-frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Yes | Clerk publishable key |
| `NEXT_PUBLIC_API_URL` | Yes | Backend API base URL (default: `http://localhost:8000`) |

---

## Authentication Flow

```
1. User visits /sign-in or /sign-up
   → Clerk UI renders (hosted, no custom forms)
   → User authenticates via email/password (or social OAuth)

2. Clerk issues JWT (RS256 signed)
   → Contains: { sub: "clerk_user_id", metadata: { role: "admin"|"employee" } }
   → Stored as httpOnly cookie (XSS-safe)

3. Frontend syncs token to backend
   → useAuthSync hook calls Clerk getToken()
   → Token injected into Axios instance via setAccessToken()
   → Every API request includes: Authorization: Bearer <jwt>

4. Backend verifies JWT
   → app.core.auth extracts and verifies RS256 signature
   → Decoded payload used for employee lookup and role checks

5. Route protection
   → src/middleware.ts checks sessionClaims.metadata.role for /admin/* routes
   → Backend routers use dependency injection for role-based access
```

---

## API Reference

All endpoints are prefixed with `/api/v1`. Authentication required for all endpoints except `/health`.

### Attendance

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/attendance/check-in` | Check in (with optional GPS/Wi-Fi) |
| POST | `/api/v1/attendance/check-out` | Check out |
| GET | `/api/v1/attendance/today` | Get today's attendance record |
| GET | `/api/v1/attendance/history` | Attendance history (paginated) |
| GET | `/api/v1/attendance/calendar/{year}/{month}` | Monthly calendar data |
| GET | `/api/v1/attendance/heatmap` | Attendance heatmap data |
| GET | `/api/v1/attendance/team-health` | Team attendance health score (admin) |
| PUT | `/api/v1/attendance/{id}` | Update attendance record (admin) |

### Leave

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/leave/request` | Submit leave request |
| GET | `/api/v1/leave/requests` | List leave requests |
| GET | `/api/v1/leave/requests/{id}` | Get leave request details |
| PUT | `/api/v1/leave/requests/{id}/approve` | Approve leave (admin) |
| PUT | `/api/v1/leave/requests/{id}/reject` | Reject leave (admin) |
| GET | `/api/v1/leave/balance` | Get leave balance |
| POST | `/api/v1/leave/balance/adjust` | Adjust leave balance (admin) |
| GET | `/api/v1/leave/history` | Leave history |
| POST | `/api/v1/leave/conversational` | Conversational NLP leave |
| GET | `/api/v1/leave/advisor` | AI leave advisor |
| GET | `/api/v1/leave/export/{id}` | Export leave as PDF |
| GET | `/api/v1/leave/policy` | Get leave policy |

### Payroll

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/payroll/salary-structure` | Get salary structure |
| POST | `/api/v1/payroll/salary-structure` | Create/update salary structure (admin) |
| GET | `/api/v1/payroll/history` | Payroll history |
| POST | `/api/v1/payroll/run` | Run payroll (admin) |
| GET | `/api/v1/payroll/stub/{id}` | Download PDF pay stub |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/chat/channels` | List channels |
| POST | `/api/v1/chat/channels` | Create channel |
| GET | `/api/v1/chat/channels/{id}/messages` | Get channel messages |
| POST | `/api/v1/chat/channels/{id}/messages` | Send message |
| POST | `/api/v1/chat/messages/{id}/read` | Mark message as read |
| POST | `/api/v1/chat/meetings/{id}/rsvp` | RSVP to meeting |
| GET | `/api/v1/chat/unread` | Get unread count |

### Employees (Admin)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/employees` | List all employees |
| GET | `/api/v1/employees/{id}` | Get employee details |
| PUT | `/api/v1/employees/{id}` | Update employee |

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/dashboard/admin` | Admin dashboard data |
| GET | `/api/v1/dashboard/employee` | Employee dashboard data |

### Analytics (Admin)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/analytics/overview` | Overview metrics |
| GET | `/api/v1/analytics/trends` | Trend data |

### Nudges

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/nudges` | List nudges |
| POST | `/api/v1/nudges/{id}/dismiss` | Dismiss nudge |
| GET | `/api/v1/nudges/unread` | Get unread nudge count |

### Chatbot

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/chatbot/message` | Send message to HR chatbot |

### Voice

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/voice/transcribe` | Transcribe audio via Whisper |

### Webhooks

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/webhooks/clerk` | Clerk webhook (user sync) |

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |

---

## Features

### Core HR (SRS)

- **Authentication** — Clerk-managed sign-up/sign-in, JWT RS256, role-based access
- **Role-Based Dashboards** — Admin sees org-wide metrics; employees see personal data
- **Employee Profiles** — View and edit profile information
- **Attendance** — GPS/Wi-Fi aware check-in/out with location verification
- **Leave Management** — Submit, approve/reject, balance tracking, history
- **Payroll** — Salary structures, automated calculations, PDF pay stubs

### AI-Powered Differentiators

- **Conversational Leave** — NLP multi-turn leave application via chat
- **HR Chatbot** — Ollama LLM-powered assistant for HR queries
- **Voice Check-In** — Whisper speech-to-text for hands-free attendance
- **Voice-to-Leave** — Audio leave application
- **Attendance Heatmap** — Visual calendar of attendance patterns
- **Burnout Early Warning** — AI-driven analysis of overtime and absence patterns
- **Live Salary Simulator** — Interactive salary breakdown calculator
- **AI Leave Advisor** — Smart suggestions for optimal leave planning
- **Smart GPS & Wi-Fi Auto Check-In** — Location-based automatic attendance
- **Team Attendance Health Score** — Aggregated team wellness metric
- **Proactive Nudge System** — Context-aware reminders and alerts
- **PDF Pay Stub Generation** — Automated WeasyPrint-based pay documents

### Collaboration

- **Team Chat** — Channel-based messaging with read receipts
- **Meeting Announcements** — Schedule meetings with RSVP tracking

---

## Database Schema

### Models (15 total)

| Model | Table | Description |
|---|---|---|
| `Employee` | `employees` | User profiles, roles, departments |
| `AttendanceRecord` | `attendance_records` | Daily check-in/out logs |
| `LeaveRequest` | `leave_requests` | Leave applications |
| `LeaveBalance` | `leave_balances` | Leave entitlements per type |
| `SalaryComp` | `salary_comps` | Salary component structures |
| `ChatChannel` | `chat_channels` | Chat channels/rooms |
| `ChatMessage` | `chat_messages` | Channel messages |
| `ChatRead` | `chat_reads` | Message read status |
| `MeetingRSVP` | `meeting_rsvps` | Meeting attendance responses |
| `Nudge` | `nudges` | Proactive notification nudges |
| `AuditLog` | `audit_logs` | System audit trail |
| `PublicHoliday` | `public_holidays` | Holiday calendar |
| `OfficeConfig` | `office_configs` | Office location settings |
| `BurnoutConfig` | `burnout_configs` | Burnout threshold config |
| `BurnoutAlert` | `burnout_alerts` | Burnout warning alerts |
| `PayrollRun` | `payroll_runs` | Payroll execution records |

---

## Development

### Frontend Development

```bash
cd frontend/hrms-frontend
npm run dev        # Start dev server (port 3000)
npm run build      # Production build
npm run lint       # ESLint check
```

### Backend Development

```bash
cd Backend
uvicorn app.main:app --reload --port 8000
```

### Running Tests

```bash
cd Backend
pytest                    # Run all tests
pytest --cov=app          # With coverage
pytest -x                 # Stop on first failure
pytest tests/test_auth.py # Specific file
```

---

## Docker Services

| Service | Port | Description |
|---|---|---|
| `postgres` | 5432 | PostgreSQL 16 database |
| `redis` | 6379 | Redis 7 cache |
| `backend` | 8000 | FastAPI application |
| `ollama` | 11434 | LLM inference server |
| `whisper` | 9000 | Speech-to-text service |
| `clamav` | 3310 | Virus scanner |
| `nginx` | 80, 443 | Reverse proxy + TLS |

---

## Troubleshooting

### Common Issues

**Backend won't start**
- Verify `.env` exists with all required variables
- Ensure PostgreSQL is reachable (`DATABASE_URL`)
- Check Redis is running on `localhost:6379`

**Frontend can't reach API**
- Confirm `NEXT_PUBLIC_API_URL` matches backend URL
- Check CORS settings in `Backend/.env`
- Verify Clerk keys are correct

**Clerk authentication fails**
- Ensure `CLERK_JWT_VERIFICATION_KEY` matches your Clerk instance
- Check that user has `role` set in Clerk metadata
- Verify frontend has `CLERK_PUBLISHABLE_KEY` (not secret key)

**Database connection errors**
- For Neon: ensure IP is whitelisted
- Check connection pool settings in `.env`
- Run `alembic upgrade head` for migrations

**AI features not working**
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Pull models: `ollama pull llama3`
- Check Whisper: `curl http://localhost:9000/health`

### Health Check

```bash
# Backend
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "3.0.0",
  "environment": "development",
  "database": true,
  "redis": true
}
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- **TypeScript**: 0 compile errors, 0 ESLint errors
- **Python**: Ruff linting, mypy type checking
- **No mock data**: All interactions go through real API endpoints
- **No placeholders**: Every feature is fully implemented

---

## License

MIT License — see [LICENSE](LICENSE) for details.
