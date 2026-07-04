# Operations Runbook

## Overview

Quick-reference guide for operating the HRMS backend. Covers startup/shutdown, common issues, health checks, and log analysis.

---

## Service Startup

### Full Stack Startup (Docker Compose)

```bash
# Start all services
docker compose up -d

# Start with logs
docker compose up -d && docker compose logs -f backend

# Start specific services only
docker compose up -d postgres redis backend
```

### Individual Service Startup

```bash
# PostgreSQL
docker compose up -d postgres

# Redis
docker compose up -d redis

# Ollama
docker compose up -d ollama

# Whisper
docker compose up -d whisper

# ClamAV
docker compose up -d clamav

# Backend API
docker compose up -d backend
```

### Startup Order

Services must start in this order:

```
1. PostgreSQL    (must be ready first)
2. Redis         (must be ready first)
3. ClamAV        (optional, can start later)
4. Ollama        (optional, can start later)
5. Whisper       (optional, can start later)
6. Backend API   (depends on 1 and 2)
7. Nginx         (depends on 6)
8. ngrok         (optional, depends on 6)
```

### Manual Development Startup

```bash
# 1. Start infrastructure
docker compose up -d postgres redis

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Run database migrations
alembic upgrade head

# 4. Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Service Shutdown

### Graceful Shutdown

```bash
# Stop backend first, then dependencies
docker compose stop backend
docker compose stop redis postgres

# Or stop everything
docker compose down
```

### Forceful Shutdown

```bash
# Kill specific container
docker compose kill backend

# Remove all containers and volumes (DANGER: deletes data)
docker compose down -v
```

---

## Health Check Interpretation

### Application Health Endpoint

```bash
curl http://localhost:8000/health
```

**Response — Healthy:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "environment": "production",
  "database": true,
  "redis": true
}
```

**Response — Degraded:**
```json
{
  "status": "degraded",
  "version": "3.0.0",
  "environment": "production",
  "database": true,
  "redis": false
}
```

| Field      | Value       | Meaning                              |
|------------|-------------|--------------------------------------|
| `status`   | `healthy`   | All systems operational              |
| `status`   | `degraded`  | Some services unavailable            |
| `database` | `true`      | PostgreSQL connection OK             |
| `database` | `false`     | PostgreSQL unreachable               |
| `redis`    | `true`      | Redis connection OK                  |
| `redis`    | `false`     | Redis unreachable                    |

### Service Health Checks

```bash
# PostgreSQL
docker compose exec postgres pg_isready -U hrms

# Redis
docker compose exec redis redis-cli ping

# Ollama
curl http://localhost:11434/api/tags

# Whisper
curl http://localhost:9000/

# ClamAV
docker compose exec clamav freshclam --version

# ngrok (if running)
curl http://localhost:4040/api/tunnels
```

---

## Common Issues and Fixes

### Issue: Application Won't Start

```
Symptom: docker compose logs backend shows connection errors

Diagnosis:
  docker compose logs backend | head -30

Common Causes:
  1. PostgreSQL not ready yet
  2. Missing environment variables
  3. Port already in use

Fix:
  # Wait for PostgreSQL
  docker compose exec postgres pg_isready -U hrms

  # Check environment
  docker compose exec backend env | grep DATABASE

  # Check port usage
  netstat -tlnp | grep 8000
```

### Issue: ngrok Tunnel Not Working

```
Symptom: Clerk webhooks not delivered, ngrok container exits

Diagnosis:
  docker compose --profile ngrok logs ngrok
  curl http://localhost:4040/api/tunnels

Common Causes:
  1. Missing NGROK_AUTHTOKEN
  2. Invalid authtoken
  3. ngrok container not started

Fix:
  # Check ngrok status
  docker compose --profile ngrok ps ngrok

  # Verify authtoken in .env
  grep NGROK .env

  # Restart ngrok
  docker compose --profile ngrok restart ngrok

  # Print tunnel URL
  bash scripts/print-ngrok-url.sh
```

### Issue: Database Connection Refused

```
Symptom: "connection refused" or "FATAL: password authentication failed"

Diagnosis:
  docker compose logs postgres | tail -20

Fix:
  # Verify PostgreSQL is running
  docker compose ps postgres

  # Check credentials
  docker compose exec postgres psql -U hrms -d hrms_db -c "SELECT 1;"

  # Reset if needed
  docker compose restart postgres
  sleep 5
  docker compose exec postgres pg_isready -U hrms
```

### Issue: Redis Connection Timeout

```
Symptom: "Error while reading from socket" or timeout errors

Diagnosis:
  docker compose logs redis | tail -20

Fix:
  # Check Redis status
  docker compose exec redis redis-cli ping

  # Check memory usage
  docker compose exec redis redis-cli INFO memory

  # Restart Redis
  docker compose restart redis
```

### Issue: Ollama Not Responding

```
Symptom: "Ollama circuit breaker is open" or timeout errors

Diagnosis:
  curl http://localhost:11434/api/tags
  docker compose logs ollama | tail -20

Fix:
  # Restart Ollama
  docker compose restart ollama

  # Wait for model to load
  watch -n 2 'curl -s http://localhost:11434/api/tags | python -m json.tool'

  # Pull model if missing
  docker compose exec ollama ollama pull llama3
```

### Issue: High Memory Usage

```
Symptom: Application becomes slow, OOM kills

Diagnosis:
  docker stats
  docker compose exec postgres psql -U hrms -c "
    SELECT pg_size_pretty(pg_database_size('hrms_db'));"

Fix:
  # Check connection pool
  docker compose exec backend python -c "
    from app.core.config import get_settings
    s = get_settings()
    print(f'Pool size: {s.DB_POOL_SIZE}, Overflow: {s.DB_MAX_OVERFLOW}')"

  # Restart to clear connections
  docker compose restart backend
```

---

## Log Analysis

### Application Logs

```bash
# Real-time application logs
docker compose logs -f backend

# Filter by log level
docker compose logs backend | grep '"level": "ERROR"'

# Filter by request ID
docker compose logs backend | grep "request_id.*abc123"

# Slow requests (>1s)
docker compose logs backend | grep "Slow request"

# JSON log parsing (production)
docker compose logs backend | python -m json.tool | grep -A5 '"level": "ERROR"'
```

### Database Logs

```bash
# Slow queries
docker compose logs postgres | grep "duration:" | grep -v "duration: 0"

# Connection errors
docker compose logs postgres | grep -i "FATAL\|error"

# Check active connections
docker compose exec postgres psql -U hrms -c "
  SELECT count(*), state
  FROM pg_stat_activity
  WHERE datname = 'hrms_db'
  GROUP BY state;"
```

### Log File Locations

| Service    | Location                        | Format  |
|------------|---------------------------------|---------|
| Backend    | stdout (Docker logs)            | JSON    |
| PostgreSQL | /var/log/postgresql/            | Text    |
| Redis      | stdout (Docker logs)            | Text    |
| Ollama     | stdout (Docker logs)            | Text    |

### Structured Log Fields

Production logs are JSON with these fields:

```json
{
  "timestamp": "2026-07-01T14:30:00Z",
  "level": "INFO",
  "logger": "app.routers.attendance",
  "message": "Check-in recorded",
  "module": "attendance",
  "function": "check_in",
  "line": 42,
  "request_id": "abc123def456",
  "user_id": "user_123",
  "method": "POST",
  "path": "/api/v1/attendance/check-in",
  "duration_ms": 45.2
}
```

---

## Escalation Procedures

### Level 1: Self-Service (On-Call Engineer)

| Symptom                     | Action                                   |
|-----------------------------|------------------------------------------|
| Single service down         | Restart the service                      |
| Slow response               | Check logs, restart if needed            |
| Disk space warning          | Run cleanup script                       |
| Cache miss storm            | Verify Redis, restart if needed          |

### Level 2: Team Escalation (Engineering Lead)

| Symptom                     | Action                                   |
|-----------------------------|------------------------------------------|
| Multiple services down      | Page engineering lead                     |
| Database corruption         | Initiate DR playbook                      |
| Data loss reported          | Pause writes, investigate                |
| Security incident           | Isolate, notify security team            |

### Level 3: Management Escalation (CTO/VP Engineering)

| Symptom                     | Action                                   |
|-----------------------------|------------------------------------------|
| Full outage >15 minutes     | Notify management                        |
| Data breach confirmed       | Legal and compliance notification        |
| Customer data affected      | Customer communication                   |
| Regulatory compliance issue | Compliance team engagement               |

### Contact Matrix

| Role                | Contact                    | Availability     |
|---------------------|----------------------------|------------------|
| On-Call Engineer    | Slack #hrms-oncall         | 24/7             |
| Engineering Lead    | Slack + Phone              | Business hours   |
| DevOps              | Slack #hrms-infra          | Business hours   |
| Security            | security@company.com       | 24/7             |
| Management          | vp-eng@company.com         | Escalation only  |

---

## Performance Quick Reference

### Response Time Targets

| Endpoint                 | Target    | Max       |
|--------------------------|-----------|-----------|
| /health                  | < 10ms    | 100ms     |
| /api/v1/employees        | < 100ms   | 500ms     |
| /api/v1/attendance       | < 100ms   | 500ms     |
| /api/v1/dashboard        | < 200ms   | 1000ms    |
| /api/v1/chatbot          | < 2000ms  | 5000ms    |
| /api/v1/voice/transcribe | < 3000ms  | 10000ms   |

### Key Metrics to Monitor

```bash
# Requests per second
docker compose logs backend | grep "Request completed" | wc -l

# Error rate
docker compose logs backend | grep '"level": "ERROR"' | wc -l

# Average response time
docker compose logs backend | grep "duration_ms" | \
  python -c "import sys, json; data=[float(l.split('duration_ms\":')[1].split('}')[0]) for l in sys.stdin]; print(f'Avg: {sum(data)/len(data):.1f}ms')"

# Database connections
docker compose exec postgres psql -U hrms -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory
docker compose exec redis redis-cli INFO memory | grep used_memory_human
```

---

## Maintenance Windows

| Day       | Time          | Activity                    |
|-----------|---------------|-----------------------------|
| Monday    | 9:00 AM       | Weekly standup review        |
| Tuesday   | 2:00 AM       | Automated backups verify     |
| Wednesday | 10:00 PM      | Log rotation                 |
| Thursday  | 2:00 AM       | Cache cleanup                |
| Friday    | 6:00 PM       | Dependency updates (if any)  |
| Saturday  | 2:00 AM       | Full database maintenance    |
| Sunday    | 3:00 AM       | Ollama model updates         |
