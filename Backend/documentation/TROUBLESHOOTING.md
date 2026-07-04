# Troubleshooting Guide

## Overview

Common error messages, root causes, and step-by-step fixes for HRMS backend issues.

---

## Database Connection Issues

### Error: `connection refused`

```
sqlalchemy.exc.OperationalError: (asyncpg.exceptions.ConnectionRejectionError)
Connection refused: localhost:5432
```

**Causes:**
- PostgreSQL container not running
- Port 5432 already in use
- Wrong host/port in DATABASE_URL

**Fix:**
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check port usage
netstat -tlnp | grep 5432

# Restart PostgreSQL
docker compose restart postgres

# Verify connection
docker compose exec postgres pg_isready -U hrms

# Test connection string
docker compose exec backend python -c "
from app.core.database import db_manager
import asyncio
asyncio.run(db_manager.connect())
print('Connected!')
"
```

### Error: `password authentication failed`

```
FATAL: password authentication failed for user "hrms"
```

**Fix:**
```bash
# Check environment variables
docker compose exec backend env | grep DATABASE_URL

# Reset PostgreSQL password
docker compose exec postgres psql -U postgres -c "
  ALTER USER hrms WITH PASSWORD 'new_password';
"

# Update .env and restart
docker compose down
docker compose up -d
```

### Error: `too many connections`

```
FATAL: too many connections for role "hrms"
```

**Fix:**
```bash
# Check current connections
docker compose exec postgres psql -U hrms -c "
  SELECT count(*), state
  FROM pg_stat_activity
  WHERE datname = 'hrms_db'
  GROUP BY state;"

# Kill idle connections
docker compose exec postgres psql -U hrms -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle'
    AND datname = 'hrms_db'
    AND query_start < now() - interval '10 minutes';"

# Increase max connections (in postgresql.conf)
# max_connections = 200
```

### Error: `pool timeout`

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached
```

**Fix:**
```bash
# Check connection pool usage
docker compose exec backend python -c "
from app.core.database import db_manager
import asyncio
asyncio.run(db_manager.connect())
pool = db_manager._engine.pool
print(f'Size: {pool.size()}, Checked out: {pool.checkedout()}, Overflow: {pool.overflow()}')"

# Increase pool size in .env
# DB_POOL_SIZE=30
# DB_MAX_OVERFLOW=15

# Restart backend
docker compose restart backend
```

### Error: `connection pool exhausted`

```
 sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached,
 timeout 30, connection pool exhausted
```

**Fix:**
```bash
# Check for slow queries holding connections
docker compose exec postgres psql -U hrms -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
  FROM pg_stat_activity
  WHERE state != 'idle'
    AND datname = 'hrms_db'
  ORDER BY duration DESC;"

# Kill long-running queries
docker compose exec postgres psql -U hrms -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'active'
    AND datname = 'hrms_db'
    AND query_start < now() - interval '5 minutes';"
```

---

## Redis Connection Issues

### Error: `Connection refused`

```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Fix:**
```bash
# Check Redis status
docker compose ps redis

# Check Redis logs
docker compose logs redis --tail=20

# Restart Redis
docker compose restart redis

# Verify connection
docker compose exec redis redis-cli ping
# Should return: PONG
```

### Error: `OOM command not allowed`

```
redis.exceptions.ResponseError: OOM command not allowed when used memory > maxmemory
```

**Fix:**
```bash
# Check memory usage
docker compose exec redis redis-cli INFO memory | grep used_memory_human

# Check key count
docker compose exec redis redis-cli DBSIZE

# Find keys with no TTL
docker compose exec redis redis-cli --scan --pattern "*" | head -20

# Flush all data (cache is ephemeral)
docker compose exec redis redis-cli FLUSHALL

# Set memory policy in redis.conf
# maxmemory-policy allkeys-lru
```

### Error: `Could not acquire lock`

```
redis.exceptions.LockNotOwnedError: Cannot release a lock
```

**Fix:**
```bash
# Check for stale locks
docker compose exec redis redis-cli --scan --pattern "lock:*"

# Delete stale locks
docker compose exec redis redis-cli DEL lock:attendance:checkin:user123:2026-07-01

# Restart Redis to clear all locks
docker compose restart redis
```

---

## Clerk Authentication Issues

### Error: `Invalid JWT token`

```
app.core.exceptions.AuthenticationError: Invalid JWT token
```

**Causes:**
- CLERK_JWT_VERIFICATION_KEY is wrong
- Token has expired
- Clock skew between server and Clerk

**Fix:**
```bash
# Verify environment variables
docker compose exec backend env | grep CLERK

# Check JWT key format (should start with -----BEGIN PUBLIC KEY-----)
echo "$CLERK_JWT_VERIFICATION_KEY" | head -1

# Test token verification manually
curl -s https://api.clerk.com/v1/sessions/<session_id> \
  -H "Authorization: Bearer $CLERK_SECRET_KEY"
```

### Error: `Webhook signature verification failed`

```
app.core.exceptions.WebhookError: Invalid webhook signature
```

**Fix:**
```bash
# Verify webhook secret
docker compose exec backend env | grep CLERK_WEBHOOK_SECRET

# Check Clerk dashboard for correct webhook URL
# Should be: https://yourdomain.com/api/v1/webhooks/clerk

# Test webhook with Clerk CLI
npx @clerk/cli webhook test https://yourdomain.com/api/v1/webhooks/clerk
```

### Error: `User not found after Clerk sync`

```
app.core.exceptions.NotFoundError: Employee not found for Clerk user
```

**Fix:**
```bash
# Check if user exists in database
docker compose exec postgres psql -U hrms -d hrms_db -c "
  SELECT clerk_user_id, email, full_name
  FROM employees
  WHERE clerk_user_id = '<clerk_user_id>';"

# Check Clerk webhook logs
docker compose logs backend | grep "webhook"

# Manually sync user (if needed)
curl -X POST http://localhost:8000/api/v1/webhooks/clerk \
  -H "Content-Type: application/json" \
  -d '{"type":"user.created","data":{"id":"<clerk_user_id>","email_addresses":[{"email_address":"user@example.com"}],"first_name":"John","last_name":"Doe"}}'
```

### Error: `Clerk rate limit exceeded`

```
clerk_backend_api.errors.rate_limit_exceeded.RateLimitExceeded
```

**Fix:**
```bash
# Wait for rate limit to reset (usually 1 minute)
# Reduce Clerk API calls by caching role verification
# Cache TTL is set in config:
# CACHE_ROLE_VERIFICATION_TTL=120 (2 minutes)
```

---

## Ollama / AI Issues

### Error: `Ollama timeout`

```
app.core.exceptions.OllamaTimeoutError: Ollama request timed out
```

**Fix:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check if model is loaded
docker compose logs ollama | grep "loading model"

# Increase timeout in .env
# OLLAMA_TIMEOUT=120

# Restart Ollama
docker compose restart ollama

# Check GPU availability (if using GPU)
nvidia-smi
```

### Error: `Ollama circuit breaker is open`

```
app.core.exceptions.AIServiceError: Ollama circuit breaker is open
```

**Cause:** Too many consecutive Ollama failures (5+)

**Fix:**
```bash
# Wait 60 seconds for automatic reset
# Or restart backend to reset circuit breaker
docker compose restart backend

# Check Ollama health
curl http://localhost:11434/api/tags

# Pull model if missing
docker compose exec ollama ollama pull llama3
```

### Error: `Model not found`

```
app.core.exceptions.AIServiceError: Ollama returned 404
```

**Fix:**
```bash
# List available models
curl http://localhost:11434/api/tags | python -m json.tool

# Pull the required model
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull mistral

# Verify model is available
curl http://localhost:11434/api/tags | jq .models[].name
```

### Error: `JSON parsing failed`

```
app.core.exceptions.AIServiceError: Failed to parse Ollama response as JSON
```

**Fix:**
```bash
# This is usually an LLM response format issue
# Check logs for the raw response
docker compose logs backend | grep "Failed to parse"

# The system has fallback logic to extract JSON from code fences
# If persistent, try a different model
# OLLAMA_CHATBOT_MODEL=llama3
```

---

## Whisper / Voice Issues

### Error: `Whisper connection refused`

```
httpx.ConnectError: Connection refused to localhost:9000
```

**Fix:**
```bash
# Check Whisper status
docker compose ps whisper

# Check Whisper logs
docker compose logs whisper

# Restart Whisper
docker compose restart whisper

# Verify endpoint
curl http://localhost:9000/
```

### Error: `Whisper timeout`

```
httpx.TimeoutException: Request timed out
```

**Fix:**
```bash
# Increase timeout in .env
# WHISPER_TIMEOUT=120

# Check audio file size (max 10MB)
ls -la /tmp/audio_file.wav

# Check Whisper resource usage
docker stats whisper
```

### Error: `Invalid audio format`

```
app.core.exceptions.ValidationError: Unsupported audio format
```

**Fix:**
```bash
# Supported formats are defined in config.py:
# ALLOWED_AUDIO_MIMES: {"audio/wav", "audio/mpeg", "audio/webm"}

# Convert audio to supported format
ffmpeg -i input.mp3 -acodec pcm_s16le -ar 16000 output.wav

# Check file MIME type
file --mime-type audio_file.wav
```

---

## Email Delivery Issues

### Error: `Resend API error`

```
resend.exceptions.ResendError: Invalid API key
```

**Fix:**
```bash
# Verify API key
docker compose exec backend env | grep RESEND

# Test API key directly
curl https://api.resend.com/domains \
  -H "Authorization: Bearer $RESEND_API_KEY"

# Check email domain verification in Resend dashboard
```

### Error: `Email not delivered`

```
app.core.exceptions.EmailError: Email delivery failed
```

**Fix:**
```bash
# Check Resend logs in dashboard
# https://resend.com/emails

# Verify sender email is verified
# EMAIL_FROM must be from a verified domain in Resend

# Check HR_EMAIL is configured
docker compose exec backend env | grep HR_EMAIL

# Test email sending
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from":"hrms@yourdomain.com","to":"test@example.com","subject":"Test","html":"<p>Test email</p>"}'
```

### Error: `Rate limit exceeded`

```
resend.exceptions.RateLimitExceeded: Rate limit exceeded
```

**Fix:**
```bash
# Wait for rate limit to reset
# Implement email queueing for bulk sends
# Check for email loops in code
docker compose logs backend | grep "send_email" | wc -l
```

---

## File Upload Issues

### Error: `ClamAV connection refused`

```
app.core.exceptions.FileScanError: ClamAV connection refused
```

**Fix:**
```bash
# Check ClamAV status
docker compose ps clamav

# Check ClamAV logs
docker compose logs clamav

# Restart ClamAV
docker compose restart clamav

# Update virus definitions
docker compose exec clamav freshclam
```

### Error: `File too large`

```
app.core.exceptions.ValidationError: File size exceeds maximum (5MB)
```

**Fix:**
```bash
# Maximum sizes are configured in config.py:
# MAX_DOCUMENT_SIZE_MB: 5
# MAX_AUDIO_SIZE_MB: 10

# Increase limit in .env if needed
# MAX_DOCUMENT_SIZE_MB=10

# Check uploaded file size
ls -la uploaded_file.pdf
```

### Error: `Invalid file type`

```
app.core.exceptions.ValidationError: Unsupported file type: application/msword
```

**Fix:**
```bash
# Allowed types are in config.py:
# ALLOWED_DOCUMENT_MIMES: {"application/pdf", "image/jpeg", "image/png"}
# ALLOWED_AUDIO_MIMES: {"audio/wav", "audio/mpeg", "audio/webm"}

# Add new types in .env (comma-separated)
# ALLOWED_DOCUMENT_MIMES=application/pdf,image/jpeg,image/png,application/msword

# Check file MIME type
file --mime-type document.doc
```

### Error: `R2 upload failed`

```
boto3.exceptions.Boto3Error: An error occurred accessing R2
```

**Fix:**
```bash
# Verify R2 credentials
docker compose exec backend env | grep R2_

# Test R2 connection
curl -X PUT "https://${R2_BUCKET_NAME}.r2.cloudflarestorage.com/test.txt" \
  -H "Authorization: AWS ${R2_ACCESS_KEY_ID}:${R2_SECRET_ACCESS_KEY}" \
  -d "test"

# Check bucket permissions in Cloudflare dashboard
```

---

## Performance Issues

### Symptom: Slow API responses

```bash
# Check response times in logs
docker compose logs backend | grep "duration_ms" | \
  python -c "
import sys, json
for line in sys.stdin:
    try:
        data = json.loads(line)
        ms = data.get('duration_ms', 0)
        if ms > 1000:
            print(f\"SLOW: {data.get('path')} {ms}ms\")
    except: pass
"

# Check database query times
docker compose exec postgres psql -U hrms -c "
  SELECT calls, mean_exec_time, rows, query
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;"
```

**Fix:**
```bash
# Add missing indexes
docker compose exec postgres psql -U hrms -d hrms_db -c "
  -- Check for sequential scans on large tables
  SELECT relname, seq_scan, idx_scan,
    CASE WHEN seq_scan > 0 AND idx_scan = 0 THEN 'MISSING INDEX'
         WHEN seq_scan > idx_scan THEN 'NEEDS INDEX'
         ELSE 'OK' END AS status
  FROM pg_stat_user_tables
  WHERE n_live_tup > 1000
  ORDER BY seq_scan DESC;"

# Enable query logging
# DB_ECHO=true (in .env, for debugging only)
```

### Symptom: High memory usage

```bash
# Check container memory
docker stats --no-stream

# Check Python memory
docker compose exec backend python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Check for memory leaks
docker compose exec backend python -c "
import gc
gc.collect()
print(f'Garbage objects: {len(gc.garbage)}')
"
```

**Fix:**
```bash
# Reduce connection pool size
# DB_POOL_SIZE=15
# DB_MAX_OVERFLOW=5

# Restart backend periodically
docker compose restart backend

# Check for large objects in memory
docker compose exec backend python -c "
import objgraph
objgraph.show_most_common_types(limit=10)
"
```

### Symptom: High CPU usage

```bash
# Check container CPU
docker stats --no-stream

# Check for CPU-intensive queries
docker compose exec postgres psql -U hrms -c "
  SELECT pid, query, state, wait_event_type
  FROM pg_stat_activity
  WHERE state = 'active'
    AND datname = 'hrms_db';"

# Check Ollama CPU usage
docker stats ollama --no-stream
```

**Fix:**
```bash
# Check for N+1 queries in application
docker compose logs backend | grep "SELECT" | wc -l

# Enable query batching
# Use SQLAlchemy eager loading where appropriate

# Scale backend instances
docker compose up -d --scale backend=3
```

---

## Quick Diagnostic Commands

```bash
# Full system status
docker compose ps
docker compose logs --tail=10 backend postgres redis

# Database status
docker compose exec postgres pg_isready -U hrms
docker compose exec postgres psql -U hrms -c "SELECT count(*) FROM pg_stat_activity;"

# Redis status
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli INFO memory | grep used_memory_human

# Application status
curl -s http://localhost:8000/health | python -m json.tool

# ngrok status (if running)
curl -s http://localhost:4040/api/tunnels | python -m json.tool

# Disk usage
df -h /var/lib/postgresql/data /var/lib/redis /app/storage

# Network connectivity
docker compose exec backend python -c "
import httpx, asyncio
async def test():
    async with httpx.AsyncClient() as c:
        r = await c.get('http://postgres:5432')
        print(f'PostgreSQL: {r.status_code}')
asyncio.run(test())
" 2>/dev/null || echo "PostgreSQL: unreachable"
```

---

## ngrok Issues

### Issue: ngrok Won't Start

```
Symptom: ngrok container exits immediately or shows auth error

Diagnosis:
  docker compose --profile ngrok logs ngrok
  curl http://localhost:4040/api/tunnels

Fix:
  # Check if NGROK_AUTHTOKEN is set
  grep NGROK_AUTHTOKEN .env

  # Verify token at ngrok dashboard
  # https://dashboard.ngrok.com/get-started/your-authtoken

  # Restart ngrok
  docker compose --profile ngrok restart ngrok
```

### Issue: ngrok URL Changed After Restart

```
Symptom: Clerk webhooks not delivered after docker compose restart

Diagnosis:
  bash scripts/print-ngrok-url.sh

Fix:
  # Get new tunnel URL
  bash scripts/print-ngrok-url.sh

  # Update webhook URL in Clerk Dashboard
  # https://dashboard.clerk.com > Webhooks > Edit Endpoint

  # Update CLERK_WEBHOOK_SECRET if needed
```

### Issue: Webhook Not Receiving Events

```
Symptom: Clerk dashboard shows webhook delivery failures

Diagnosis:
  # Check ngrok tunnel is active
  curl http://localhost:4040/api/tunnels

  # Check backend is healthy
  curl http://localhost:8000/health

  # Check webhook endpoint
  curl -X POST http://localhost:8000/api/v1/webhooks/clerk \
    -H "Content-Type: application/json" \
    -d '{"type":"test"}'

Fix:
  # Restart ngrok
  docker compose --profile ngrok restart ngrok

  # Restart backend
  docker compose restart backend

  # Verify CLERK_WEBHOOK_SECRET matches Clerk dashboard
  grep CLERK_WEBHOOK_SECRET .env
```
