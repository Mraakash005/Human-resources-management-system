# HRMS Backend — Enterprise Human Resource Management System

> **Version 3.1.0** | **Production-Ready** | **All 27 Features**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                          │
│   Next.js 15 (App Router, RSC) → localhost:3000         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS (JWT)
┌──────────────────────▼──────────────────────────────────┐
│                    GATEWAY LAYER                         │
│   Nginx Reverse Proxy (TLS termination)                 │
│   /api/* → FastAPI :8000  |  /* → Next.js :3000         │
└──────────┬───────────────────────────┬──────────────────┘
           │                           │
┌──────────▼──────────┐  ┌─────────────▼──────────────────┐
│   BACKEND LAYER     │  │   AUTH LAYER                    │
│   FastAPI :8000     │  │   Clerk (managed SaaS)          │
│   Python 3.12       │  │   JWT RS256 verification        │
│                     │  │   Role metadata (admin/employee) │
│  ┌────────────────┐ │  └────────────────────────────────┘
│  │ 10 API Routers │ │
│  │ 10 Services    │ │
│  │ APScheduler    │ │
│  └────────────────┘ │
└──┬────────┬────────┬┘
   │        │        │
┌──▼──┐ ┌───▼──┐ ┌───▼──────────────────────────┐
│ PG  │ │Redis │ │  AI SIDECAR SERVICES (Docker)  │
│:5432│ │:6379 │ │  Ollama :11434 (Llama3/Mistral)│
│16tbl│ │Cache │ │  Whisper :9000 (ASR)            │
└─────┘ └──────┘ │  ClamAV :3310 (Virus Scan)      │
                 │  ngrok  (optional, webhooks)     │
                 └─────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115 + Python 3.12 |
| Database | PostgreSQL 16 (asyncpg) |
| Cache | Redis 7 |
| Auth | Clerk (JWT RS256) |
| AI | Ollama (Llama 3, Mistral) + Whisper |
| Email | Resend (100/day free) |
| PDF | WeasyPrint + Jinja2 |
| Scheduler | APScheduler (in-process) |
| Virus Scan | ClamAV |
| Tunnel | ngrok (Docker profile, optional) |
| ORM | SQLAlchemy 2.0 (async) + Alembic |

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your keys

# 2. Start all services
docker compose up -d --build

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Pull AI models
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull mistral

# 5. Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Health:   http://localhost:8000/health

# 6. (Optional) Start with ngrok for Clerk webhooks
# Set NGROK_ENABLED=true and NGROK_AUTHTOKEN in .env
docker compose --profile ngrok up -d
bash scripts/print-ngrok-url.sh
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/dashboard` | Aggregated dashboard |
| GET/POST | `/api/v1/attendance/*` | Check-in/out, calendar, heatmap |
| GET/POST | `/api/v1/leave/*` | Leave CRUD, balance, AI advisor |
| GET/PATCH | `/api/v1/payroll/*` | Payroll, salary, pay stubs |
| GET/POST | `/api/v1/employees/*` | Employee CRUD |
| GET/POST | `/api/v1/chat/*` | Team chat, channels, SSE |
| POST | `/api/v1/chatbot/ask` | HR chatbot |
| POST | `/api/v1/voice/transcribe` | Voice-to-leave |
| GET | `/api/v1/nudges` | Proactive notifications |
| GET | `/api/v1/analytics/*` | Health scores, burnout dashboard |
| POST | `/api/v1/webhooks/clerk` | Clerk webhook handler |

## Features (27/27)

### Core (8)
1. Clerk Authentication (JWT RS256)
2. Role-Based Dashboards (Employee + Admin)
3. Employee Profile Management
4. Admin Leave Approval
5. Attendance Check-In/Out + Geofence
6. Payroll Visibility + PDF Pay Stubs
7. Leave Application + Balance
8. Admin Employee Management

### Performance & Security (6)
9. Redis Dashboard Caching (60s TTL)
10. Pydantic v2 Input Validation
11. DB Query Optimization (10 composite indexes)
12. Aggregated Dashboard API
13. Audit Logging (immutable)
14. Async FastAPI Throughout

### AI-Powered (13)
15. Conversational Leave (NLP)
16. HR Chatbot (RAG-lite)
17. Voice Commands (Web Speech API)
18. Voice-to-Leave (Whisper)
19. Attendance Heatmap
20. Burnout Early Warning (6 signals)
21. Live Salary Simulator
22. AI Leave Advisor
23. Smart Auto Check-In (GPS/WiFi)
24. Team Health Score
25. Proactive Nudges
26. PDF Pay Stubs (WeasyPrint)
27. Internal Team Chat (SSE + Redis pub/sub)

## Docker Compose Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| (default) | postgres, redis, ollama, whisper, clamav, backend, nginx | Normal development |
| `ngrok` | all above + ngrok | Clerk webhook development |

```bash
# Without ngrok (default)
docker compose up -d

# With ngrok profile
docker compose --profile ngrok up -d

# Smart launcher (auto-detects NGROK_ENABLED from .env)
bash scripts/docker-start.sh
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v
```

## Documentation

See `documentation/` directory for complete guides:
- `DATABASE.md` — Schema and ER diagram
- `API_REFERENCE.md` — All endpoints
- `AUTHENTICATION.md` — Clerk JWT flow
- `SECURITY.md` — Security hardening
- `DEPLOYMENT.md` — Production deployment
- `TROUBLESHOOTING.md` — Common issues
- `NGROK.md` — ngrok integration (in `docs/`)
