# EXECUTION.md — HRMS Enterprise Backend

> **Version 3.1.0** | **Execution Runbook** | **Zero-Assumption Validation**

> This is NOT documentation. This is the definitive operational execution manual.
> Every section validates that a specific subsystem ACTUALLY WORKS.

---

## Table of Contents

- [PHASE 0: Repository Validation](#phase-0-repository-validation)
- [PHASE 1: Environment Validation](#phase-1-environment-validation)
- [PHASE 2: Environment Variables](#phase-2-environment-variables)
- [PHASE 3: Docker Validation](#phase-3-docker-validation)
- [PHASE 4: Database Validation](#phase-4-database-validation)
- [PHASE 5: Database Integrity](#phase-5-database-integrity)
- [PHASE 6: Redis Validation](#phase-6-redis-validation)
- [PHASE 7: Authentication](#phase-7-authentication)
- [PHASE 8: RBAC](#phase-8-rbac)
- [PHASE 9: Clerk Webhooks](#phase-9-clerk-webhooks)
- [PHASE 9A: ngrok Tunnel Integration](#phase-9a-ngrok-tunnel-integration)
- [PHASE 10: API Validation](#phase-10-api-validation)
- [PHASE 11: Business Logic](#phase-11-business-logic)
- [PHASE 12: Background Jobs](#phase-12-background-jobs)
- [PHASE 13: AI Services](#phase-13-ai-services)
- [PHASE 14: File Uploads](#phase-14-file-uploads)
- [PHASE 15: Email](#phase-15-email)
- [PHASE 16: Caching](#phase-16-caching)
- [PHASE 17: Performance](#phase-17-performance)
- [PHASE 18: Security](#phase-18-security)
- [PHASE 19: Observability](#phase-19-observability)
- [PHASE 20: CI/CD](#phase-20-cicd)
- [PHASE 21: End-to-End Integration](#phase-21-end-to-end-integration)
- [PHASE 22: Failure Simulation](#phase-22-failure-simulation)
- [PHASE 23: Production Readiness](#phase-23-production-readiness)
- [FINAL REPORT](#final-report)

---

## PHASE 0: Repository Validation

### Objective
Verify the backend repository structure is complete and all required files exist.

### Required Services
None (filesystem only).

### Commands

**Windows PowerShell:**
```powershell
Set-Location "C:\INTERNSHIP_TASK\TASK18_ODDO\Backend"

$requiredRoot = @(
    ".env.example", ".gitignore", "alembic.ini", "docker-compose.yml",
    "Dockerfile", "nginx.conf", "requirements.txt"
)
foreach ($f in $requiredRoot) {
    if (Test-Path $f) { Write-Host "OK: $f" -ForegroundColor Green }
    else { Write-Host "MISSING: $f" -ForegroundColor Red }
}

$requiredDirs = @(
    "app\core", "app\models", "app\schemas", "app\routers",
    "app\services", "app\middleware", "app\jobs", "app\utils",
    "app\templates", "migrations\versions", "tests\unit", "tests\integration"
)
foreach ($d in $requiredDirs) {
    if (Test-Path $d) { Write-Host "OK: $d" -ForegroundColor Green }
    else { Write-Host "MISSING: $d" -ForegroundColor Red }
}

Write-Host "`nFile counts:"
Write-Host "  Python files: $((Get-ChildItem -Path app -Recurse -Filter *.py).Count)"
Write-Host "  Test files:   $((Get-ChildItem -Path tests -Recurse -Filter *.py).Count)"
Write-Host "  Migration:    $((Get-ChildItem -Path migrations\versions -Filter *.py).Count)"
Write-Host "  Doc files:    $((Get-ChildItem -Path documentation -Recurse -Filter *.md).Count)"
```

**Linux/macOS:**
```bash
cd C:/INTERNSHIP_TASK/TASK18_ODDO/Backend

for f in .env.example .gitignore alembic.ini docker-compose.yml Dockerfile nginx.conf requirements.txt; do
    [ -f "$f" ] && echo "OK: $f" || echo "MISSING: $f"
done

for d in app/core app/models app/schemas app/routers app/services app/middleware app/jobs app/utils app/templates migrations/versions tests/unit tests/integration; do
    [ -d "$d" ] && echo "OK: $d" || echo "MISSING: $d"
done

echo "Python files: $(find app -name '*.py' | wc -l)"
echo "Test files:   $(find tests -name '*.py' | wc -l)"
echo "Migrations:   $(find migrations/versions -name '*.py' | wc -l)"
echo "Doc files:    $(find documentation -name '*.md' | wc -l)"
```

### Files Involved
| File | Purpose |
|------|---------|
| `.env.example` | Environment variable template |
| `alembic.ini` | Alembic configuration |
| `docker-compose.yml` | Service orchestration (8 services + ngrok profile) |
| `Dockerfile` | Backend container build |
| `nginx.conf` | Reverse proxy config |
| `requirements.txt` | Python dependencies |
| `app/main.py` | FastAPI application entry |

### Pass Criteria
- [ ] All 7 root config files present
- [ ] All 11 app subdirectories present
- [ ] 40+ Python files in app/
- [ ] 8+ test files in tests/
- [ ] 1+ migration in migrations/versions/
- [ ] 30+ documentation files in documentation/

---

## PHASE 1: Environment Validation

### Objective
Verify all required runtime tools are installed with compatible versions.

### Commands

**Windows PowerShell:**
```powershell
Write-Host "=== Python ===" -ForegroundColor Cyan
python --version

Write-Host "`n=== Docker ===" -ForegroundColor Cyan
docker --version
docker compose version

Write-Host "`n=== Git ===" -ForegroundColor Cyan
git --version

Write-Host "`n=== pip packages ===" -ForegroundColor Cyan
pip list 2>$null | Select-String "fastapi|sqlalchemy|alembic|redis|pydantic|uvicorn|apscheduler|httpx|weasyprint|PyJWT"
```

**Linux/macOS:**
```bash
echo "=== Python ==="
python3 --version

echo "=== Docker ==="
docker --version
docker compose version

echo "=== Git ==="
git --version

echo "=== pip packages ==="
pip3 list 2>/dev/null | grep -E "fastapi|sqlalchemy|alembic|redis|pydantic|uvicorn|apscheduler|httpx|weasyprint|PyJWT"
```

### Expected Versions
| Tool | Minimum | Recommended |
|------|---------|-------------|
| Python | 3.11+ | 3.12 |
| Docker | 24.0+ | 25.0+ |
| Docker Compose | 2.20+ | 2.24+ |
| Git | 2.40+ | 2.44+ |
| fastapi | 0.110+ | 0.115.6 |
| sqlalchemy | 2.0+ | 2.0.36 |
| alembic | 1.13+ | 1.14.1 |
| redis | 5.0+ | 5.2.1 |
| pydantic | 2.5+ | 2.10.4 |
| uvicorn | 0.27+ | 0.34.0 |

### Possible Failures
| Failure | Fix |
|---------|-----|
| `python` not found | Install Python 3.12 from python.org |
| `docker` not found | Install Docker Desktop |
| Package version mismatch | `pip install -r requirements.txt` |
| `weasyprint` fails on Windows | Use Docker for WeasyPrint |

---

## PHASE 2: Environment Variables

### Objective
Validate every required environment variable is set and correctly formatted.

### Commands

**Windows PowerShell:**
```powershell
Set-Location "C:\INTERNSHIP_TASK\TASK18_ODDO\Backend"

if (Test-Path .env) {
    Write-Host "OK: .env file exists" -ForegroundColor Green
} else {
    Write-Host "CREATING: .env from .env.example" -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "ACTION REQUIRED: Edit .env with real values" -ForegroundColor Red
}

$required = @(
    "SECRET_KEY", "DATABASE_URL", "REDIS_URL",
    "CLERK_PUBLISHABLE_KEY", "CLERK_SECRET_KEY", "CLERK_JWT_VERIFICATION_KEY",
    "RESEND_API_KEY", "HR_EMAIL"
)

$envContent = Get-Content .env -Raw
foreach ($var in $required) {
    if ($envContent -match "$var=(.+)") {
        $val = $Matches[1].Trim('"').Trim("'")
        if ($val -and $val -notlike "*placeholder*" -and $val -notlike "*your_*" -and $val -ne "") {
            Write-Host "OK: $var" -ForegroundColor Green
        } else {
            Write-Host "INVALID: $var (placeholder or empty)" -ForegroundColor Red
        }
    } else {
        Write-Host "MISSING: $var" -ForegroundColor Red
    }
}
```

### Complete Variable Reference

| Variable | Required | Default | Validation |
|----------|----------|---------|------------|
| `SECRET_KEY` | **YES** | — | Min 32 chars |
| `DATABASE_URL` | **YES** | — | Must start with `postgresql+asyncpg://` |
| `REDIS_URL` | **YES** | `redis://localhost:6379/0` | Must start with `redis://` |
| `CLERK_PUBLISHABLE_KEY` | **YES** | — | Must start with `pk_` |
| `CLERK_SECRET_KEY` | **YES** | — | Must start with `sk_`, min 20 chars |
| `CLERK_JWT_VERIFICATION_KEY` | **YES** | — | Must be PEM format |
| `RESEND_API_KEY` | **YES** | — | Must start with `re_` |
| `HR_EMAIL` | **YES** | — | Valid email |
| `EMAIL_FROM` | no | `hrms@localhost.com` | Valid email |
| `CLERK_WEBHOOK_SECRET` | no | `""` | Starts with `whsec_` |
| `OLLAMA_BASE_URL` | no | `http://localhost:11434` | Valid URL |
| `OLLAMA_DEFAULT_MODEL` | no | `llama3` | — |
| `OLLAMA_CHATBOT_MODEL` | no | `mistral` | — |
| `WHISPER_URL` | no | `http://localhost:9000` | Valid URL |
| `CLAMAV_URL` | no | `http://localhost:3310` | Valid URL |
| `OFFICE_LAT` | no | `12.9716` | Float |
| `OFFICE_LNG` | no | `77.5946` | Float |
| `GEOFENCE_RADIUS_METERS` | no | `150` | Integer, 10-5000 |
| `COMPANY_NAME` | no | `HRMS Corp` | String |
| `ENVIRONMENT` | no | `development` | development/staging/production/testing |
| `DEBUG` | no | `False` | Boolean |
| `LOG_LEVEL` | no | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `NGROK_ENABLED` | no | `false` | true/false |
| `NGROK_AUTHTOKEN` | no | — | Required if NGROK_ENABLED=true |
| `NGROK_REGION` | no | `us` | us/eu/au/ap |

### Database URL Format
```
postgresql+asyncpg://hrms:password@localhost:5432/hrms_db
         ^^^^^^^^^^^^  ^^^^  ^^^^^^^^  ^^^^^^^^^^^^^^
         async driver   user  host      database
```

### Redis URL Format
```
redis://localhost:6379/0
     ^^^^^^^^^^  ^  ^
     host        port db
```

### Possible Failures
| Failure | Cause | Fix |
|---------|-------|-----|
| `DATABASE_URL must use postgresql+asyncpg://` | Wrong scheme | Change `postgresql://` to `postgresql+asyncpg://` |
| `CLERK_SECRET_KEY` too short | Placeholder value | Get real key from Clerk dashboard |
| `SECRET_KEY` missing | Not generated | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| Production validation fails | Using localhost URLs | Use production DB/Redis URLs |
| ngrok tunnel fails | Missing NGROK_AUTHTOKEN | Set token in `.env` from ngrok dashboard |

---

## PHASE 3: Docker Validation

### Objective
Build and verify all Docker containers, networks, volumes, and health checks.

### Commands

**Windows PowerShell:**
```powershell
Set-Location "C:\INTERNSHIP_TASK\TASK18_ODDO\Backend"

# Build all images
docker compose build --no-cache

# Start all services
docker compose up -d

# Wait for startup
Start-Sleep -Seconds 10

# Check container status
docker compose ps

# Check container health
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Check logs for errors
docker compose logs backend --tail=50
docker compose logs postgres --tail=20
docker compose logs redis --tail=20

# Start with ngrok profile (optional)
docker compose --profile ngrok up -d
```

**Linux/macOS:**
```bash
cd C:/INTERNSHIP_TASK/TASK18_ODDO/Backend

docker compose build --no-cache
docker compose up -d
sleep 10
docker compose ps
docker compose logs --tail=50 backend
docker compose logs --tail=20 postgres
docker compose logs --tail=20 redis

# Start with ngrok profile (optional)
docker compose --profile ngrok up -d
```

### Expected Container State (without ngrok)
| Container | Image | Port | Health |
|-----------|-------|------|--------|
| hrms-postgres | postgres:16-alpine | 5432 | healthy |
| hrms-redis | redis:7-alpine | 6379 | healthy |
| hrms-ollama | ollama/ollama:latest | 11434 | running |
| hrms-whisper | onerahmet/openai-whisper-asr-webservice | 9000 | running |
| hrms-clamav | clamav/clamav:stable | 3310 | running |
| hrms-backend | custom (Dockerfile) | 8000 | running |
| hrms-nginx | nginx:alpine | 80,443 | running |

### Expected Container State (with ngrok profile)
| Container | Image | Port | Health |
|-----------|-------|------|--------|
| hrms-ngrok | ngrok/ngrok:latest | — | running |
| (all above) | | | |

### Docker Compose Profiles

The project uses Docker Compose profiles to optionally include ngrok:

| Profile | Services | Use Case |
|---------|----------|----------|
| (none) | postgres, redis, ollama, whisper, clamav, backend, nginx | Normal development |
| `ngrok` | all above + ngrok | Clerk webhook development |

```bash
# Without ngrok (default)
docker compose up -d

# With ngrok profile
docker compose --profile ngrok up -d

# Smart launcher (auto-detects NGROK_ENABLED from .env)
bash scripts/docker-start.sh
```

### Health Check Commands
```powershell
# PostgreSQL
docker compose exec postgres pg_isready -U hrms -d hrms_db

# Redis
docker compose exec redis redis-cli ping

# Backend
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Ollama
Invoke-RestMethod -Uri "http://localhost:11434/api/tags"

# ngrok (if running)
Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
```

### Possible Failures
| Failure | Cause | Fix |
|---------|-------|-----|
| `postgres` exits immediately | Wrong POSTGRES_PASSWORD | Check `.env` matches `DATABASE_URL` |
| `clamav` takes long to start | Signature download | Wait 60s, check `docker compose logs clamav` |
| `ollama` OOM killed | Insufficient GPU/RAM | Remove GPU reservation or add memory limit |
| `backend` exits with import error | Missing dependency | Check `docker compose logs backend` |
| Port conflict | Another service on port | `netstat -ano | findstr :5432` |
| `ngrok` fails to start | Missing authtoken | Set `NGROK_AUTHTOKEN` in `.env` |
| `ngrok` exits immediately | Invalid authtoken | Verify token at ngrok dashboard |

### Recovery Procedure
```powershell
# Nuclear restart
docker compose down -v --remove-orphans
docker compose up -d --build

# Restart single service
docker compose restart backend

# View real-time logs
docker compose logs -f backend

# Restart ngrok
docker compose --profile ngrok restart ngrok
```

---

## PHASE 4: Database Validation

### Objective
Verify database exists, all 16 tables are created, migrations applied, connection pool healthy.

### Required Services
- PostgreSQL running (Docker or local)
- Backend running (for pool validation)

### Commands

```powershell
docker compose exec postgres psql -U hrms -d hrms_db
```

```sql
-- Verify all 16 tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Expected tables:
-- attendance_records, audit_log, burnout_alerts, burnout_config,
-- chat_channels, chat_messages, chat_reads, employees,
-- leave_balances, leave_requests, meeting_rsvp, nudges,
-- office_config, payroll_runs, public_holidays, salary_components

-- Verify Alembic migration version
SELECT * FROM alembic_version;

-- Verify btree_gist extension (for EXCLUDE constraint)
SELECT * FROM pg_extension WHERE extname = 'btree_gist';

-- Verify EXCLUDE constraint exists
SELECT conname, contype FROM pg_constraint
WHERE conrelid = 'leave_requests'::regclass AND contype = 'x';
```

**Health check endpoint:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json
```

### Expected Result
```json
{
    "status": "healthy",
    "version": "3.0.0",
    "environment": "development",
    "database": true,
    "redis": true
}
```

### Connection Pool Configuration
| Parameter | Value | Source |
|-----------|-------|--------|
| `pool_size` | 20 | `config.py:DB_POOL_SIZE` |
| `max_overflow` | 10 | `config.py:DB_MAX_OVERFLOW` |
| `pool_timeout` | 30s | `config.py:DB_POOL_TIMEOUT` |
| `pool_recycle` | 1800s | `config.py:DB_POOL_RECYCLE` |
| `pool_pre_ping` | True | `database.py` |

### Pass Criteria
- [ ] 16 tables exist
- [ ] `alembic_version` table has exactly one row
- [ ] `btree_gist` extension installed
- [ ] EXCLUDE constraint on `leave_requests`
- [ ] All foreign keys present with correct cascade rules
- [ ] All composite indexes created

---

## PHASE 5: Database Integrity

### Objective
Verify all constraints, foreign keys, indexes, and safety mechanisms.

### Commands

```sql
-- Foreign Keys
SELECT
    tc.table_name, kcu.column_name,
    ccu.table_name AS references_table,
    ccu.column_name AS references_column,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
JOIN information_schema.referential_constraints rc ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;

-- Unique Constraints
SELECT conname, conrelid::regclass, pg_get_constraintdef(oid)
FROM pg_constraint WHERE contype = 'u' ORDER BY conrelid::regclass::text;

-- EXCLUDE Constraints
SELECT conname, conrelid::regclass, pg_get_constraintdef(oid)
FROM pg_constraint WHERE contype = 'x';
```

### Cascade Rules
| Parent Table | Child Table | On Delete |
|-------------|-------------|-----------|
| `employees` | `attendance_records` | CASCADE |
| `employees` | `leave_requests` | CASCADE |
| `employees` | `leave_balances` | CASCADE |
| `employees` | `salary_components` | CASCADE |
| `employees` | `payroll_runs` | CASCADE |
| `employees` | `burnout_alerts` | CASCADE |
| `employees` | `nudges` | CASCADE |
| `employees` | `audit_log` | SET NULL |
| `employees` | `chat_messages` | CASCADE |
| `employees` | `chat_channels` | SET NULL |
| `employees` | `meeting_rsvp` | CASCADE |
| `employees` | `chat_reads` | CASCADE |
| `leave_requests` | `leave_requests.reviewed_by` | SET NULL |
| `chat_channels` | `chat_messages` | CASCADE |
| `chat_messages` | `chat_reads` | CASCADE |
| `chat_messages` | `meeting_rsvp` | CASCADE |

### Pass Criteria
- [ ] 16 tables exist
- [ ] All foreign keys present with correct cascade rules
- [ ] EXCLUDE constraint on `leave_requests`
- [ ] All unique constraints present
- [ ] All composite indexes created

---

## PHASE 6: Redis Validation

### Objective
Verify Redis connectivity, caching, TTL, pub/sub, and all cache key patterns.

### Commands

```powershell
# Redis connectivity
docker compose exec redis redis-cli ping
# Expected: PONG

# Redis info
docker compose exec redis redis-cli info server
docker compose exec redis redis-cli info memory

# Monitor keys (in separate terminal)
docker compose exec redis redis-cli MONITOR
```

**Redis CLI commands:**
```bash
# List all keys
docker compose exec redis redis-cli KEYS "*"

# Check specific cache patterns
docker compose exec redis redis-cli KEYS "dashboard:*"
docker compose exec redis redis-cli KEYS "role_verified:*"
docker compose exec redis redis-cli KEYS "ratelimit:*"
docker compose exec redis redis-cli KEYS "webhook_event:*"
docker compose exec redis redis-cli KEYS "chat:*"
docker compose exec redis redis-cli KEYS "chatbot_context:*"
docker compose exec redis redis-cli KEYS "leave_advisor:*"
docker compose exec redis redis-cli KEYS "heatmap:*"
docker compose exec redis redis-cli KEYS "team_health:*"
```

### Redis Key Patterns
| Pattern | TTL | Source | Purpose |
|---------|-----|--------|---------|
| `dashboard:{user_id}:{role}` | 60s | `cache.py` | Dashboard cache |
| `role_verified:{user_id}` | 120s | `auth.py` | Stale JWT protection |
| `ratelimit:general:{ip}` | 60s | `rate_limit.py` | API rate limit |
| `ratelimit:ai:{ip}` | 60s | `rate_limit.py` | AI rate limit |
| `webhook_event:{svix_id}` | 300s | `webhooks.py` | Replay protection |
| `chatbot_context:{user_id}` | 300s | `cache.py` | Chatbot context |
| `leave_advisor:{emp_id}:{date}` | 3600s | `cache.py` | Leave advisor |
| `heatmap:{emp_id}:{year}` | 3600s | `cache.py` | Attendance heatmap |
| `attendance:checkin:{emp_id}:{date}` | 86400s | `cache.py` | Double check-in prevention |
| `chat:{channel_id}` | — | `chat.py` | Pub/Sub channel |

### Pass Criteria
- [ ] `PING` returns `PONG`
- [ ] Keys appear after API calls
- [ ] Keys expire after TTL
- [ ] Pub/Sub channel works for chat SSE
- [ ] Rate limit keys increment correctly

---

## PHASE 7: Authentication

### Objective
Verify Clerk JWT validation, RS256 verification, role extraction, and stale token protection.

### Commands

```powershell
# Test unauthenticated access (should return 401/403)
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard"
} catch {
    Write-Host "Expected 401: $($_.Exception.Message)" -ForegroundColor Green
}

# Test with invalid token
$headers = @{ "Authorization" = "Bearer invalid_token_here" }
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard" -Headers $headers
} catch {
    Write-Host "Expected 401: $($_.Exception.Message)" -ForegroundColor Green
}
```

### JWT Verification Chain
| Step | Code Location | What Happens |
|------|--------------|--------------|
| 1 | `auth.py` `decode_jwt()` | Decode JWT with RS256 |
| 2 | `auth.py` | Verify signature with PEM key |
| 3 | `auth.py` | Check expiration |
| 4 | `auth.py` | Extract `sub` (user_id) |
| 5 | `auth.py` | Extract `metadata.role` |
| 6 | `auth.py` `require_admin()` | For admin routes: call Clerk API |
| 7 | `auth.py` | Cache role in Redis for 2 min |

### Stale Token Protection
```
Admin's role changed in Clerk dashboard
  → Admin still has valid JWT (up to 15 min TTL)
  → Admin hits admin-only endpoint
  → require_admin() reads JWT → role says "admin" ← STALE
  → verify_admin_role_live() calls Clerk API
  → Clerk returns current role: "employee"
  → 403 Forbidden
  → Redis caches "employee" for 2 minutes
```

### Pass Criteria
- [ ] Unauthenticated requests return 401
- [ ] Invalid tokens return 401
- [ ] Valid employee tokens access employee endpoints
- [ ] Valid admin tokens access admin endpoints
- [ ] Employee tokens blocked from admin endpoints (403)
- [ ] Stale admin tokens caught by Clerk API verification
- [ ] Role verification cached in Redis for 120s

---

## PHASE 8: RBAC

### Objective
Verify every role, every permission, and every route protection.

### Role Matrix
| Role | Can Access | Cannot Access |
|------|-----------|---------------|
| `employee` | Own profile, own attendance, own leave, own payroll, chat, dashboard | Admin endpoints, other employees' data |
| `admin` | Everything including: employee management, leave approvals, all payroll, analytics, audit logs, burnout dashboard | — |

### Admin-Only Endpoints
| Endpoint | Method | Protection |
|----------|--------|------------|
| `/api/v1/employees/` | GET | `require_admin` |
| `/api/v1/employees/` | POST | `require_admin` |
| `/api/v1/employees/{id}` | GET | `require_admin` |
| `/api/v1/employees/{id}` | PATCH | `require_admin` |
| `/api/v1/employees/{id}/deactivate` | PATCH | `require_admin` |
| `/api/v1/employees/{id}/reactivate` | PATCH | `require_admin` |
| `/api/v1/leave/{id}/approve` | PATCH | `require_admin` |
| `/api/v1/attendance/all` | GET | `require_admin` |
| `/api/v1/payroll/all` | GET | `require_admin` |
| `/api/v1/payroll/employees/{id}/salary` | PATCH | `require_admin` |
| `/api/v1/analytics/team-health` | GET | `require_admin` |
| `/api/v1/analytics/burnout-dashboard` | GET | `require_admin` |

### Pass Criteria
- [ ] All admin-only endpoints return 403 for employee tokens
- [ ] All admin-only endpoints return 200 for admin tokens
- [ ] Employee endpoints work for both roles
- [ ] Unauthenticated requests return 401
- [ ] Role changes in Clerk reflected within 2 minutes

---

## PHASE 9: Clerk Webhooks

### Objective
Verify webhook signature verification, replay protection, and database sync.

### Commands

```powershell
# Simulate user.created webhook (requires valid svix headers)
$body = '{"type":"user.created","data":{"id":"user_test123","email_addresses":[{"email_address":"test@example.com","id":"email_1"}],"primary_email_address_id":"email_1","first_name":"Test","last_name":"User","public_metadata":{"role":"employee"}}}'

$timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$svixId = "msg_test_$(Get-Random)"

$headers = @{
    "Content-Type" = "application/json"
    "svix-id" = $svixId
    "svix-timestamp" = $timestamp.ToString()
    "svix-signature" = "v1,placeholder"
}

try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/webhooks/clerk" -Method POST -Body $body -Headers $headers
} catch {
    Write-Host "Webhook response: $($_.Exception.Message)" -ForegroundColor Yellow
}
```

### Webhook Events
| Event | Handler | Action |
|-------|---------|--------|
| `user.created` | `_handle_user_created` | Create employee, init leave balances |
| `user.updated` | `_handle_user_updated` | Sync role, name, email changes |
| `user.deleted` | `_handle_user_deleted` | Soft-delete (set is_active=False) |
| `session.created` | Log only | — |
| `session.ended` | Log only | — |

### Security Mechanisms
| Mechanism | Implementation | Location |
|-----------|---------------|----------|
| Signature verification | HMAC-SHA256 (Svix) | `webhooks.py` |
| Replay protection | Redis key with 5-min TTL | `webhooks.py` |
| Idempotency | Check if event already processed | `webhooks.py` |
| Error isolation | Webhook returns 200 even on error | `webhooks.py` |

### Pass Criteria
- [ ] Invalid signatures rejected (401)
- [ ] Replay attacks blocked
- [ ] user.created creates employee + leave balances
- [ ] user.updated syncs role changes
- [ ] user.deleted sets is_active=False
- [ ] Redis caches replay protection keys

---

## PHASE 9A: ngrok Tunnel Integration

### Objective
Verify the ngrok Docker integration is correctly configured and provides a public tunnel for Clerk webhook development.

### Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Clerk Cloud │────▶│  ngrok       │────▶│  Backend     │
│  (webhooks)  │     │  (tunnel)    │     │  (FastAPI)   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                     ┌──────┴──────┐
                     │  Public     │
                     │  URL        │
                     └─────────────┘
```

### Prerequisites
- ngrok account (free tier): https://ngrok.com
- ngrok authtoken: https://dashboard.ngrok.com/get-started/your-authtoken

### Setup

1. **Set environment variables in `.env`:**
```bash
NGROK_ENABLED=true
NGROK_AUTHTOKEN=your_actual_authtoken_here
NGROK_REGION=us
```

2. **Start with ngrok profile:**
```bash
# Option A: Use the wrapper script (recommended)
bash scripts/docker-start.sh

# Option B: Direct Docker Compose command
docker compose --profile ngrok up -d
```

3. **Get your public tunnel URL:**
```bash
bash scripts/print-ngrok-url.sh
```

Output:
```
============================================
  ngrok Tunnel Status
============================================
  Tunnel Name:    default
  Public URL:     https://abc123.ngrok-free.app
  Webhook URL:    https://abc123.ngrok-free.app/api/v1/webhooks/clerk
============================================
```

4. **Configure Clerk webhook:**
   - Open Clerk Dashboard → Webhooks → Add Endpoint
   - Paste the Webhook URL from step 3
   - Select events: `user.created`, `user.updated`, `user.deleted`
   - Copy Signing Secret → set in `.env` as `CLERK_WEBHOOK_SECRET`
   - Restart backend: `docker compose restart backend`

### Commands

**Windows PowerShell:**
```powershell
Set-Location "C:\INTERNSHIP_TASK\TASK18_ODDO\Backend"

# Start with ngrok profile
docker compose --profile ngrok up -d

# Print tunnel URL
powershell -ExecutionPolicy Bypass -File scripts/print-ngrok-url.sh

# View ngrok logs
docker compose --profile ngrok logs ngrok

# Stop
docker compose --profile ngrok down
```

**Linux/macOS:**
```bash
cd C:/INTERNSHIP_TASK/TASK18_ODDO/Backend

# Start with ngrok profile
docker compose --profile ngrok up -d

# Print tunnel URL
bash scripts/print-ngrok-url.sh

# View ngrok logs
docker compose --profile ngrok logs ngrok

# Stop
docker compose --profile ngrok down
```

### Validation

| Check | Expected | Command |
|-------|----------|---------|
| ngrok container running | Status: Up | `docker compose --profile ngrok ps ngrok` |
| ngrok API accessible | HTTP 200 | `curl http://localhost:4040/api/tunnels` |
| Tunnel active | public_url present | `bash scripts/print-ngrok-url.sh` |
| Backend reachable via tunnel | HTTP 200 | `curl https://<tunnel-url>/health` |
| Webhook endpoint reachable | HTTP 200 | `curl https://<tunnel-url>/api/v1/webhooks/clerk` |

### Pass Criteria
- [ ] ngrok container starts and stays running
- [ ] Public tunnel URL is displayed
- [ ] Backend health check passes via tunnel URL
- [ ] Webhook endpoint responds via tunnel URL
- [ ] ngrok Inspector accessible at http://localhost:4040
- [ ] `NGROK_ENABLED=false` starts stack without ngrok

---

## PHASE 10: API Validation

### Objective
Test every API endpoint for correct behavior, validation, error handling, and response format.

### Complete Endpoint Reference

| # | Method | Endpoint | Auth | Admin | Rate Limited |
|---|--------|----------|------|-------|-------------|
| 1 | GET | `/health` | No | No | No |
| 2 | GET | `/api/v1/dashboard` | Yes | No | Yes |
| 3 | POST | `/api/v1/attendance/checkin` | Yes | No | Yes |
| 4 | POST | `/api/v1/attendance/checkout` | Yes | No | Yes |
| 5 | POST | `/api/v1/attendance/auto-checkin` | Yes | No | Yes |
| 6 | GET | `/api/v1/attendance/today` | Yes | No | Yes |
| 7 | GET | `/api/v1/attendance/calendar` | Yes | No | Yes |
| 8 | GET | `/api/v1/attendance/heatmap` | Yes | No | Yes |
| 9 | GET | `/api/v1/attendance/weekly` | Yes | No | Yes |
| 10 | GET | `/api/v1/attendance/all` | Yes | Yes | Yes |
| 11 | POST | `/api/v1/leave` | Yes | No | Yes |
| 12 | GET | `/api/v1/leave` | Yes | No | Yes |
| 13 | GET | `/api/v1/leave/balance` | Yes | No | Yes |
| 14 | PATCH | `/api/v1/leave/{id}/approve` | Yes | Yes | Yes |
| 15 | PATCH | `/api/v1/leave/{id}/cancel` | Yes | No | Yes |
| 16 | GET | `/api/v1/leave/advisor` | Yes | No | Yes |
| 17 | POST | `/api/v1/leave/nlp/chat` | Yes | No | Yes |
| 18 | POST | `/api/v1/leave/nlp/generate-leave-email` | Yes | No | Yes |
| 19 | GET | `/api/v1/payroll/me` | Yes | No | Yes |
| 20 | GET | `/api/v1/payroll/me/salary` | Yes | No | Yes |
| 21 | GET | `/api/v1/payroll/me/stub` | Yes | No | Yes |
| 22 | GET | `/api/v1/payroll/all` | Yes | Yes | Yes |
| 23 | PATCH | `/api/v1/payroll/employees/{id}/salary` | Yes | Yes | Yes |
| 24 | GET | `/api/v1/employees/me` | Yes | No | Yes |
| 25 | PATCH | `/api/v1/employees/me` | Yes | No | Yes |
| 26 | POST | `/api/v1/employees/me/avatar/presign` | Yes | No | Yes |
| 27 | GET | `/api/v1/employees` | Yes | Yes | Yes |
| 28 | GET | `/api/v1/employees/{id}` | Yes | Yes | Yes |
| 29 | POST | `/api/v1/employees` | Yes | Yes | Yes |
| 30 | PATCH | `/api/v1/employees/{id}` | Yes | Yes | Yes |
| 31 | PATCH | `/api/v1/employees/{id}/deactivate` | Yes | Yes | Yes |
| 32 | PATCH | `/api/v1/employees/{id}/reactivate` | Yes | Yes | Yes |
| 33 | POST | `/api/v1/chatbot/ask` | Yes | No | Yes (AI) |
| 34 | POST | `/api/v1/voice/transcribe` | Yes | No | Yes (AI) |
| 35 | GET | `/api/v1/chat/channels` | Yes | No | Yes |
| 36 | GET | `/api/v1/chat/messages` | Yes | No | Yes |
| 37 | POST | `/api/v1/chat/messages` | Yes | No | Yes |
| 38 | GET | `/api/v1/chat/unread` | Yes | No | Yes |
| 39 | POST | `/api/v1/chat/read/{channel_id}` | Yes | No | Yes |
| 40 | POST | `/api/v1/chat/rsvp/{message_id}` | Yes | No | Yes |
| 41 | GET | `/api/v1/chat/stream/{channel_id}` | Yes | No | No (SSE) |
| 42 | GET | `/api/v1/nudges` | Yes | No | Yes |
| 43 | PATCH | `/api/v1/nudges/{id}/read` | Yes | No | Yes |
| 44 | GET | `/api/v1/analytics/team-health` | Yes | Yes | Yes |
| 45 | GET | `/api/v1/analytics/burnout-dashboard` | Yes | Yes | Yes |
| 46 | POST | `/api/v1/webhooks/clerk` | Webhook Sig | No | No |

### Rate Limiting
| Category | Limit | Window | Key Pattern |
|----------|-------|--------|-------------|
| General API | 60 req/min | Sliding | `ratelimit:general:{ip}` |
| AI endpoints | 10 req/min | Sliding | `ratelimit:ai:{ip}` |
| Health check | Unlimited | — | — |

### Security Headers
| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(self)` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` (HTTPS only) |
| `X-RateLimit-Limit` | Per request |
| `X-RateLimit-Remaining` | Per request |
| `X-Request-ID` | Per request |
| `X-Response-Time` | Per request |

### Pass Criteria
- [ ] All 46 endpoints respond correctly
- [ ] Auth required endpoints return 401 without token
- [ ] Admin endpoints return 403 for employees
- [ ] Rate limiting returns 429 when exceeded
- [ ] Security headers present on all responses
- [ ] Request IDs present on all responses
- [ ] Response times under 500ms for non-AI endpoints
- [ ] OpenAPI docs available at `/docs` (non-production)

---

## PHASE 11: Business Logic

### Objective
Execute every business workflow end-to-end and verify correct behavior.

### 11.1 Attendance Workflow

```powershell
# Check in
$body = '{"lat": 12.9716, "lng": 77.5946, "method": "gps"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/attendance/checkin" -Method POST -Body $body -ContentType "application/json" -Headers $headers

# Verify today's attendance
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/attendance/today" -Headers $headers

# Check out
$body = '{}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/attendance/checkout" -Method POST -Body $body -ContentType "application/json" -Headers $headers

# View calendar
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/attendance/calendar?year=2026&month=7" -Headers $headers
```

**Business Rules:**
- One check-in per day (Redis lock prevents double)
- Geofence validation: distance must be ≤ configured radius
- Duration calculated on checkout
- Status auto-set: present if check-in before 10am, half-day otherwise

### 11.2 Leave Workflow

```powershell
# Create leave request
$body = '{"leave_type":"paid","start_date":"2026-08-01","end_date":"2026-08-05","remarks":"Vacation"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leave" -Method POST -Body $body -ContentType "application/json" -Headers $headers

# Check balance
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leave/balance" -Headers $headers

# Admin approves
$leaveId = "uuid-of-leave"
$body = '{"status":"approved","comment":"Approved"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leave/$leaveId/approve" -Method PATCH -Body $body -ContentType "application/json" -Headers $adminHeaders
```

**Business Rules:**
- Atomic balance deduction (UPDATE WHERE total-used >= N)
- PostgreSQL EXCLUDE constraint prevents overlapping approved leaves
- Rejection recredits balance
- Cancellation recredits balance
- Email sent to HR on submission
- Email sent to employee on approval/rejection

### 11.3 Payroll Workflow

```powershell
# Employee views payroll
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/payroll/me" -Headers $headers

# Employee views salary structure
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/payroll/me/salary" -Headers $headers

# Employee downloads pay stub
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/payroll/me/stub" -Headers $headers

# Admin views all payroll
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/payroll/all" -Headers $adminHeaders

# Admin updates salary
$body = '{"components":[{"component":"basic_salary","amount":50000}]}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/payroll/employees/{id}/salary" -Method PATCH -Body $body -ContentType "application/json" -Headers $adminHeaders
```

### 11.4 Chat Workflow

```powershell
# List channels
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat/channels" -Headers $headers

# Send message
$body = '{"channel_id":"uuid","body":"Hello team!"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat/messages" -Method POST -Body $body -ContentType "application/json" -Headers $headers

# Get messages
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat/messages?channel_id=uuid" -Headers $headers
```

### Pass Criteria
- [ ] Attendance: check-in creates record, checkout calculates duration
- [ ] Attendance: double check-in prevented
- [ ] Leave: balance deducted atomically on creation
- [ ] Leave: balance recredited on rejection/cancellation
- [ ] Leave: EXCLUDE constraint prevents overlapping dates
- [ ] Payroll: salary structure readable by employee
- [ ] Chat: messages sent and received via Redis pub/sub
- [ ] All mutations logged in audit_log

---

## PHASE 12: Background Jobs

### Objective
Verify all APScheduler jobs are registered and can execute.

### Registered Jobs
| Job ID | Schedule | Function | Source |
|--------|----------|----------|--------|
| `burnout_check` | Daily 02:00 | `check_burnout()` | `attendance_analytics.py` |
| `monthly_payroll` | Last day 23:59 | `run_monthly_payroll()` | `payroll_calc.py` |
| `nudge_checks` | Daily 08:00 | `run_nudge_checks()` | `nudge_service.py` |
| `cache_cleanup` | Every 30 min | `_cleanup_stale_cache()` | `scheduler.py` |
| `health_monitor` | Every 5 min | `_health_monitor()` | `scheduler.py` |

### Verification Commands
```powershell
# Check scheduler is running (from backend logs)
docker compose logs backend | Select-String "APScheduler started"

# Trigger burnout check manually
docker compose exec backend python -c "
import asyncio
from app.services.attendance_analytics import check_burnout
asyncio.run(check_burnout())
print('Burnout check completed')
"

# Trigger nudge checks manually
docker compose exec backend python -c "
import asyncio
from app.services.nudge_service import run_nudge_checks
asyncio.run(run_nudge_checks())
print('Nudge checks completed')
"
```

### Pass Criteria
- [ ] All 5 jobs registered in APScheduler
- [ ] `burnout_check` runs without error
- [ ] `monthly_payroll` runs without error
- [ ] `nudge_checks` runs without error
- [ ] `cache_cleanup` deletes stale Redis keys
- [ ] `health_monitor` reports service status

---

## PHASE 13: AI Services

### Objective
Verify Ollama, Whisper, prompt templates, circuit breaker, and graceful degradation.

### Commands

```powershell
# Ollama health
Invoke-RestMethod -Uri "http://localhost:11434/api/tags" | ConvertTo-Json

# Pull models (first time)
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull mistral

# Test Ollama directly
$body = '{"model":"llama3","prompt":"Say hello","stream":false}'
Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method POST -Body $body -ContentType "application/json"

# Test chatbot endpoint
$body = '{"question":"How many sick leaves do I have?"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chatbot/ask" -Method POST -Body $body -ContentType "application/json" -Headers $headers

# Test AI email generation
$body = '{"name":"John","department":"Engineering","leave_type":"paid","start_date":"2026-08-01","end_date":"2026-08-05","reason":"Vacation"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leave/nlp/generate-leave-email" -Method POST -Body $body -ContentType "application/json" -Headers $headers
```

### Circuit Breaker
| Parameter | Value | Location |
|-----------|-------|----------|
| Failure threshold | 5 | `ollama_client.py` |
| Reset timeout | 60s | `ollama_client.py` |
| States | closed → open → half-open | `ollama_client.py` |

### Graceful Degradation
| Service | Failure Behavior |
|---------|------------------|
| Ollama down | Returns `{"fallback": true}` → frontend shows manual form |
| Whisper down | Returns 503 error → frontend shows retry option |
| ClamAV down | Allows upload with warning (fail-open) |

### Pass Criteria
- [ ] Ollama responds to `/api/tags`
- [ ] Ollama generates text via `/api/generate`
- [ ] Whisper endpoint accessible at `/docs`
- [ ] Chatbot returns grounded answers
- [ ] AI email generation returns structured JSON
- [ ] Circuit breaker opens after 5 failures
- [ ] Graceful degradation when AI unavailable

---

## PHASE 14: File Uploads

### Objective
Verify MIME validation, size limits, virus scanning, and storage.

### Validation Chain
```
1. MIME type check (python-magic, reads file headers)
2. Size check (5MB docs, 10MB audio)
3. ClamAV virus scan
4. Store to disk / R2
```

### Allowed Types
| Category | MIME Types | Max Size |
|----------|-----------|----------|
| Documents | `application/pdf`, `image/jpeg`, `image/png` | 5MB |
| Audio | `audio/wav`, `audio/mpeg`, `audio/webm` | 10MB |

### Pass Criteria
- [ ] Oversized files rejected (413)
- [ ] Invalid MIME types rejected (415)
- [ ] Virus-infected files rejected (400)
- [ ] Valid files stored successfully
- [ ] ClamAV graceful degradation when unavailable

---

## PHASE 15: Email

### Objective
Verify email templates, Resend integration, retry logic, and delivery.

### Email Templates
| Template | Trigger | Recipient |
|----------|---------|-----------|
| Leave notification | Leave submitted/approved/rejected | HR / Employee |
| Welcome email | Employee created | Employee |
| Pay stub email | Payroll generated | Employee |
| Burnout alert | Burnout detected | HR |

### Retry Logic
| Attempt | Delay | Condition |
|---------|-------|-----------|
| 1 | Immediate | First attempt |
| 2 | 2s | First attempt failed |
| 3 | 4s | Second attempt failed |

### Pass Criteria
- [ ] Email service module loads
- [ ] API key configured
- [ ] Templates render correctly
- [ ] Retry logic works (3 attempts)
- [ ] Failure logged, not raised to caller

---

## PHASE 16: Caching

### Objective
Verify cache hits, misses, invalidation, and TTL expiration.

### Cache Operations Test
```powershell
# 1. Cold cache — should miss
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard" -Headers $headers

# 2. Check Redis for cache key
docker compose exec redis redis-cli KEYS "dashboard:*"

# 3. Second request — should hit cache
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard" -Headers $headers

# 4. Mutate data (e.g., check-in)
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/attendance/checkin" -Method POST -Body '{"lat":12.9716,"lng":77.5946,"method":"gps"}' -ContentType "application/json" -Headers $headers

# 5. Verify cache invalidated
docker compose exec redis redis-cli KEYS "dashboard:*"
```

### Cache Invalidation Triggers
| Event | Cache Invalidated | Key Pattern |
|-------|------------------|-------------|
| Check-in | Dashboard, attendance lock | `dashboard:*`, `attendance:checkin:*` |
| Leave request | Dashboard, leave balance | `dashboard:*`, `leave_balance:*` |
| Leave approval | Dashboard, leave balance | `dashboard:*`, `leave_balance:*` |
| Profile edit | Dashboard | `dashboard:*` |
| Salary update | Payroll | `payroll:*` |

### Pass Criteria
- [ ] First request: cache miss (key created)
- [ ] Second request: cache hit (faster response)
- [ ] After mutation: cache invalidated
- [ ] Keys expire after configured TTL
- [ ] Cache rebuilds on next request

---

## PHASE 17: Performance

### Objective
Benchmark startup, latency, memory, and concurrency.

### Benchmarks
| Metric | Target | How to Measure |
|--------|--------|----------------|
| Startup time | < 5s | Time from `uvicorn` start to "Application startup complete" |
| Health endpoint | < 50ms | `curl -w "%{time_total}" http://localhost:8000/health` |
| Dashboard (cached) | < 100ms | Response time with warm cache |
| Dashboard (uncached) | < 500ms | Response time with cold cache |
| AI email generation | < 5s | Ollama response time |
| Whisper transcription | < 10s | 30s audio file |
| Payroll PDF | < 3s/employee | WeasyPrint render time |

### Pass Criteria
- [ ] Startup under 5 seconds
- [ ] Health endpoint under 50ms
- [ ] Cached responses under 100ms
- [ ] Uncached responses under 500ms
- [ ] Connection pool handles 20 concurrent connections
- [ ] No connection leaks after sustained load

---

## PHASE 18: Security

### Objective
Verify protection against OWASP Top 10 and application-specific threats.

### Security Checklist

| # | Threat | Protection | Verification |
|---|--------|-----------|-------------|
| 1 | SQL Injection | SQLAlchemy parameterized queries | No raw SQL with string interpolation |
| 2 | XSS | Pydantic validation, output encoding | HTML tags stripped in LeaveCreate |
| 3 | SSRF | No user-controlled URLs in server requests | AI calls use configured URLs only |
| 4 | Path Traversal | Fixed storage paths, no user path input | `storage/paystubs/{emp_id}/` |
| 5 | Rate Limiting | Redis sliding window | 60/min general, 10/min AI |
| 6 | Brute Force | Clerk handles lockout | — |
| 7 | Security Headers | SecurityHeadersMiddleware | All responses have headers |
| 8 | Secrets | Environment variables, never hardcoded | `config.py` uses pydantic-settings |
| 9 | JWT Attacks | RS256 verification, short TTL (15min) | `auth.py` verifies signature |
| 10 | Replay | Redis-based event ID tracking | Webhook replay protection |
| 11 | Privilege Escalation | `require_admin` + Clerk live verify | Admin endpoints double-check |
| 12 | File Upload | MIME + size + ClamAV | `file_validator.py` |
| 13 | Race Conditions | Atomic SQL UPDATE WHERE | Leave balance deduction |
| 14 | Data Overlap | PostgreSQL EXCLUDE constraint | Leave date overlap prevention |
| 15 | CORS | Whitelist only frontend origin | `CORS_ORIGINS` config |

### Pass Criteria
- [ ] All 15 security measures verified
- [ ] No hardcoded secrets in codebase
- [ ] Security headers on all responses
- [ ] Rate limiting active
- [ ] Input validation on all endpoints
- [ ] Audit log records all mutations

---

## PHASE 19: Observability

### Objective
Verify logging, health checks, request tracking, and error reporting.

### Health Endpoint
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json
```

### Log Formats
| Environment | Format | Fields |
|-------------|--------|--------|
| Production | JSON | timestamp, level, logger, message, request_id, user_id, exception |
| Development | Text | colored level, request_id, logger, message |

### Request Tracking
Every response includes:
- `X-Request-ID`: Unique request identifier
- `X-Response-Time`: Response duration in ms

### Pass Criteria
- [ ] Health endpoint returns status of all services
- [ ] Structured JSON logs in production
- [ ] Request IDs present on all responses
- [ ] Slow request warnings (>1s) logged
- [ ] Exception tracebacks logged with context

---

## PHASE 20: CI/CD

### Objective
Run linting, type checking, tests, and Docker build validation.

### Commands

```powershell
Set-Location "C:\INTERNSHIP_TASK\TASK18_ODDO\Backend"

# Lint
ruff check app/ tests/

# Format check
ruff format --check app/ tests/

# Type check
mypy app/ --ignore-missing-imports

# Run tests
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Docker build validation
docker compose build --no-cache backend
```

### Quality Gates
| Gate | Tool | Threshold |
|------|------|-----------|
| Linting | ruff | 0 errors |
| Formatting | ruff format | All files formatted |
| Type checking | mypy | 0 errors (with ignores) |
| Unit tests | pytest | All pass |
| Coverage | pytest-cov | > 80% |
| Docker build | docker compose | Builds successfully |

### Pass Criteria
- [ ] `ruff check` returns 0 errors
- [ ] `ruff format --check` returns 0 changes needed
- [ ] `mypy` returns 0 errors
- [ ] All pytest tests pass
- [ ] Coverage > 80%
- [ ] Docker image builds successfully

---

## PHASE 21: End-to-End Integration

### Objective
Execute the complete user journey through all backend systems.

### Complete Workflow

```
1. Clerk creates user → webhook → employee created in DB
2. Employee logs in → JWT issued
3. Employee checks in → attendance record + Redis lock
4. Employee checks out → duration calculated
5. Employee applies for leave → balance deducted atomically
6. AI generates leave email → Ollama processes
7. Admin approves leave → balance recredited if needed
8. Email sent to employee → Resend API
9. Monthly payroll runs → PDF generated → email sent
10. Burnout detection runs → alerts created
11. Nudges generated → notification bell updated
12. Team chat messages → Redis pub/sub → SSE streaming
13. Dashboard loaded → Redis cache served
14. Admin views analytics → health scores computed
15. Audit log records all mutations
```

### Verification Script
```powershell
Write-Host "=== E2E Integration Test ===" -ForegroundColor Cyan

# 1. Health check
$health = Invoke-RestMethod -Uri "http://localhost:8000/health"
Write-Host "Health: $($health.status)" -ForegroundColor $(if($health.status -eq "healthy"){"Green"}else{"Red"})

# 2. Auth test (expect 401)
try { Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard" }
catch { Write-Host "Auth: 401 returned (OK)" -ForegroundColor Green }

# 3. Database check
$dbCheck = docker compose exec postgres psql -U hrms -d hrms_db -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
Write-Host "Database tables: $($dbCheck.Trim())" -ForegroundColor Green

# 4. Redis check
$redisCheck = docker compose exec redis redis-cli ping
Write-Host "Redis: $redisCheck" -ForegroundColor $(if($redisCheck -eq "PONG"){"Green"}else{"Red"})

# 5. Scheduler check
$logs = docker compose logs backend --tail=10 2>&1
if ($logs -match "APScheduler started") {
    Write-Host "Scheduler: Running" -ForegroundColor Green
} else {
    Write-Host "Scheduler: Not found in logs" -ForegroundColor Yellow
}

Write-Host "`n=== Integration Complete ===" -ForegroundColor Cyan
```

### Pass Criteria
- [ ] All 15 workflow steps complete without error
- [ ] All services communicate correctly
- [ ] Data flows through all layers
- [ ] No unhandled exceptions
- [ ] All external services reachable

---

## PHASE 22: Failure Simulation

### Objective
Simulate failures and verify graceful degradation.

### Failure Scenarios

| # | Scenario | Expected Behavior | Recovery |
|---|----------|------------------|----------|
| 1 | Redis down | Requests pass through (fail-open), cache misses | Restart Redis |
| 2 | Database down | 500 error, connection pool retry | Restart PostgreSQL |
| 3 | Ollama down | AI endpoints return fallback/503 | Restart Ollama |
| 4 | Whisper down | Voice endpoint returns 503 | Restart Whisper |
| 5 | ClamAV down | File uploads allowed with warning | Restart ClamAV |
| 6 | Expired JWT | 401 error | Re-login |
| 7 | Invalid Clerk token | 401 error | Use valid token |
| 8 | Stale admin role | 403 error | Re-login |
| 9 | Rate limit exceeded | 429 with Retry-After header | Wait 60s |
| 10 | Disk full | PDF generation fails, error logged | Free disk space |
| 11 | ngrok tunnel down | Webhook delivery fails | `docker compose --profile ngrok restart ngrok` |

### Simulation Commands
```powershell
# Stop Redis
docker compose stop redis
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json
# Expected: status "degraded", redis false

# Restart Redis
docker compose start redis

# Stop PostgreSQL
docker compose stop postgres
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard" -Headers $headers
# Expected: 500 error

# Restart PostgreSQL
docker compose start postgres
```

### Pass Criteria
- [ ] Redis failure: requests still served (cache misses)
- [ ] Database failure: appropriate error returned
- [ ] AI failure: graceful fallback, no crashes
- [ ] Recovery: all services restore automatically
- [ ] No data corruption during failures
- [ ] ngrok failure: webhook delivery fails, backend unaffected

---

## PHASE 23: Production Readiness

### Objective
Final validation of all production requirements.

### Production Checklist

| # | Category | Requirement | Status |
|---|----------|------------|--------|
| 1 | Security | No hardcoded secrets | |
| 2 | Security | JWT TTL ≤ 15 minutes | |
| 3 | Security | Admin routes double-check via Clerk API | |
| 4 | Security | Rate limiting active | |
| 5 | Security | Security headers on all responses | |
| 6 | Security | Input validation on all endpoints | |
| 7 | Security | File upload validation (MIME + size + virus) | |
| 8 | Performance | Redis caching with TTL | |
| 9 | Performance | Async I/O throughout | |
| 10 | Performance | Connection pooling configured | |
| 11 | Performance | Response times < 500ms (non-AI) | |
| 12 | Reliability | Atomic operations (leave balance) | |
| 13 | Reliability | EXCLUDE constraint (leave overlap) | |
| 14 | Reliability | Graceful degradation (AI down) | |
| 15 | Reliability | Fail-open for non-critical services | |
| 16 | Observability | Structured logging | |
| 17 | Observability | Request ID tracking | |
| 18 | Observability | Health endpoint | |
| 19 | Operations | Docker Compose orchestration | |
| 20 | Operations | Alembic migrations | |
| 21 | Operations | Background job scheduling | |
| 22 | Operations | Audit trail | |
| 23 | Documentation | 30+ documentation files | |
| 24 | Testing | Unit + integration tests | |
| 25 | Deployment | Nginx reverse proxy | |
| 26 | Deployment | ngrok integration (optional) | |

### Pass Criteria
- [ ] All 26 production requirements verified
- [ ] No critical issues found
- [ ] All warnings documented
- [ ] Ready for deployment

---

## FINAL REPORT

### Backend Validation Summary

```
╔══════════════════════════════════════════════════════════════╗
║              HRMS BACKEND VALIDATION REPORT                  ║
║              Version 3.1.0                                   ║
║              Date: 2026-07-04                                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  PHASE 0: Repository Validation      [  ] PASS / [  ] FAIL  ║
║  PHASE 1: Environment Validation     [  ] PASS / [  ] FAIL  ║
║  PHASE 2: Environment Variables      [  ] PASS / [  ] FAIL  ║
║  PHASE 3: Docker Validation          [  ] PASS / [  ] FAIL  ║
║  PHASE 4: Database Validation        [  ] PASS / [  ] FAIL  ║
║  PHASE 5: Database Integrity         [  ] PASS / [  ] FAIL  ║
║  PHASE 6: Redis Validation           [  ] PASS / [  ] FAIL  ║
║  PHASE 7: Authentication             [  ] PASS / [  ] FAIL  ║
║  PHASE 8: RBAC                       [  ] PASS / [  ] FAIL  ║
║  PHASE 9: Clerk Webhooks             [  ] PASS / [  ] FAIL  ║
║  PHASE 9A: ngrok Tunnel Integration  [  ] PASS / [  ] FAIL  ║
║  PHASE 10: API Validation            [  ] PASS / [  ] FAIL  ║
║  PHASE 11: Business Logic            [  ] PASS / [  ] FAIL  ║
║  PHASE 12: Background Jobs           [  ] PASS / [  ] FAIL  ║
║  PHASE 13: AI Services               [  ] PASS / [  ] FAIL  ║
║  PHASE 14: File Uploads              [  ] PASS / [  ] FAIL  ║
║  PHASE 15: Email                     [  ] PASS / [  ] FAIL  ║
║  PHASE 16: Caching                   [  ] PASS / [  ] FAIL  ║
║  PHASE 17: Performance               [  ] PASS / [  ] FAIL  ║
║  PHASE 18: Security                  [  ] PASS / [  ] FAIL  ║
║  PHASE 19: Observability             [  ] PASS / [  ] FAIL  ║
║  PHASE 20: CI/CD                     [  ] PASS / [  ] FAIL  ║
║  PHASE 21: E2E Integration           [  ] PASS / [  ] FAIL  ║
║  PHASE 22: Failure Simulation        [  ] PASS / [  ] FAIL  ║
║  PHASE 23: Production Readiness      [  ] PASS / [  ] FAIL  ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  MODULE SCORES:                                              ║
║  ─────────────                                               ║
║  Database:          ___ /100                                  ║
║  Redis:             ___ /100                                  ║
║  Authentication:    ___ /100                                  ║
║  RBAC:              ___ /100                                  ║
║  API Endpoints:     ___ /100                                  ║
║  Business Logic:    ___ /100                                  ║
║  Schedulers:        ___ /100                                  ║
║  AI Services:       ___ /100                                  ║
║  Security:          ___ /100                                  ║
║  Performance:       ___ /100                                  ║
║  Observability:     ___ /100                                  ║
║  Deployment:        ___ /100                                  ║
║  ngrok Integration: ___ /100                                  ║
║  Testing:           ___ /100                                  ║
║  Documentation:     ___ /100                                  ║
║                                                              ║
║  ─────────────────────────────────────────────────────────   ║
║  OVERALL PRODUCTION READINESS:  ___ /100 %                   ║
║                                                              ║
║  CRITICAL ISSUES:   ___                                       ║
║  WARNINGS:          ___                                       ║
║  RECOMMENDATIONS:   ___                                       ║
║                                                              ║
║  VERDICT:  [  ] READY FOR PRODUCTION                         ║
║            [  ] NEEDS REMEDIATION                             ║
║            [  ] NOT READY                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Scoring Rubric

| Score | Rating | Description |
|-------|--------|-------------|
| 95-100 | Production Ready | All systems verified, no critical issues |
| 85-94 | Near Production Ready | Minor issues, all fixable |
| 70-84 | Development Ready | Functional, needs hardening |
| 50-69 | Partially Functional | Core works, gaps exist |
| < 50 | Not Ready | Significant issues |

### Critical Blockers (must be resolved before production)
1. All required environment variables must be set with real values
2. All Docker containers must be healthy
3. All database migrations must be applied
4. Authentication must work end-to-end
5. No SQL injection vulnerabilities
6. If ngrok enabled: `NGROK_AUTHTOKEN` must be set in `.env`

### Warnings (should be resolved)
1. ClamAV graceful degradation may allow malicious files
2. AI services may be slow on first request (model loading)
3. WeasyPrint may fail on some platforms (use Docker)
4. ngrok free tier generates new URL on each restart

### Recovery Procedures

| Failure | Recovery |
|---------|----------|
| Database corruption | Restore from pg_dump backup |
| Redis data loss | Cache rebuilds automatically |
| Container crash | `docker compose restart` |
| Migration failure | `alembic downgrade -1` then retry |
| Disk full | Clear `storage/paystubs/` old files |
| Ollama model corrupted | `docker compose exec ollama ollama pull llama3` |
| ngrok tunnel down | `docker compose --profile ngrok restart ngrok` |
| ngrok URL changed | Run `bash scripts/print-ngrok-url.sh` and update Clerk webhook URL |

---

> **This document is the single source of truth for backend validation.**
> **Every phase must pass before marking the backend as production-ready.**
> **Generated: 2026-07-04 | HRMS Enterprise Backend v3.1.0**
