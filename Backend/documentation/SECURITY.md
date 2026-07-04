# Security

## Security Checklist

| # | Item | Status | Implementation |
|---|------|--------|----------------|
| 1 | JWT validation (RS256) | Done | `app/core/auth.py` — `decode_jwt()` |
| 2 | Stale token protection | Done | `app/core/auth.py` — `verify_admin_role_live()` |
| 3 | Rate limiting | Done | `app/middleware/rate_limit.py` — sliding window, Redis |
| 4 | Security headers | Done | `app/middleware/security.py` — 8 headers |
| 5 | CORS configuration | Done | `app/main.py` — configurable origins |
| 6 | File upload validation | Done | `app/services/file_validator.py` — MIME, size, ClamAV |
| 7 | SQL injection prevention | Done | SQLAlchemy ORM (parameterized queries) |
| 8 | Geofence validation | Done | `app/routers/attendance.py` — Haversine formula |
| 9 | Race condition prevention | Done | Redis locks + atomic SQL operations |
| 10 | Audit trail | Done | `app/services/audit.py` — immutable `audit_log` table |
| 11 | Environment secrets | Done | `pydantic-settings` — env-only, never hardcoded |
| 12 | Password/secret rotation | Manual | Clerk handles token rotation; manual key rotation for DB/Redis |
| 13 | HTTPS enforcement | Done | HSTS header + Nginx TLS termination |
| 14 | Request ID tracking | Done | `app/main.py` — `X-Request-ID` header on every response |

## JWT Validation

Every API request is verified against Clerk's RSA public key.

### Process

1. Extract `Authorization: Bearer <token>` header.
2. Decode JWT header → verify `alg=RS256`.
3. Verify signature against `CLERK_JWT_VERIFICATION_KEY` (RSA public key).
4. Check `exp` claim — reject if expired.
5. Extract `sub` (user_id) and `metadata.role`.

### Configuration

```python
# app/core/auth.py:58-66
payload = jwt.decode(
    token,
    CLERK_PEM_KEY,
    algorithms=["RS256"],
    options={"verify_aud": False, "verify_exp": True},
)
```

### Error Responses

| Condition | HTTP | Message |
|-----------|------|---------|
| No credentials | 401 | `Missing authorization header` |
| Expired token | 401 | `Token has expired. Please sign in again.` |
| Invalid signature | 401 | `Invalid authentication token` |
| Missing `sub` | 401 | `Token missing subject claim` |

## Stale Token Protection

Admin tokens verified via real-time Clerk API call, cached for 2 minutes.

```
JWT says role=admin
    │
    ▼
Check Redis: role_verified:{user_id}
    │
    ├── Cache hit → use cached role
    │
    └── Cache miss → GET /v1/users/{user_id} from Clerk API
                        │
                        ▼
                    Read public_metadata.role
                        │
                        ▼
                    Cache in Redis (TTL: 120s)
```

- **Fail-closed**: If Clerk API unreachable → deny admin access.
- **Cache invalidation**: On webhook `user.updated` with role change.

## Rate Limiting

Redis-backed sliding window rate limiter applied to all endpoints.

### Limits

| Category | Limit | Scope |
|----------|-------|-------|
| General API | 60 req/min | Per IP |
| AI endpoints (`/nlp/`, `/voice/`, `/chatbot/`, `/advisor`) | 10 req/min | Per IP |

### Implementation

```python
# Uses Redis sorted sets for sliding window
pipe.zremrangebyscore(key, 0, window_start)  # Remove expired entries
pipe.zadd(key, {f"{now}": now})               # Add current request
pipe.zcard(key)                                # Count in window
pipe.expire(key, self.window_seconds)          # Auto-cleanup
```

### Response Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1719900060
Retry-After: 60  (only on 429)
```

### Fail-Open

If Redis is unreachable, requests pass through without rate limiting (availability over strictness).

## Security Headers Middleware

Applied to all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer leakage |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(self), payment=()` | Feature restrictions |
| `X-Permitted-Cross-Domain-Policies` | `none` | Cross-domain restrictions |
| `Cache-Control` | `no-store, no-cache, must-revalidate, private` | Prevent caching sensitive data |
| `Pragma` | `no-cache` | HTTP/1.0 compatibility |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | HTTPS-only (HTTPS connections only) |

The `Server` header is removed from all responses.

## CORS Configuration

```python
# app/main.py:72-78
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,        # Configurable (default: localhost:3000)
    allow_credentials=True,                       # Allow cookies/auth headers
    allow_methods=["*"],                          # All methods
    allow_headers=["*"],                          # All headers
)
```

### Production Hardening

The `validate_production_settings()` validator in `config.py` enforces:
- `CORS_ORIGINS` must include at least one non-localhost origin.
- `DEBUG` must be `False`.
- `DATABASE_URL` and `REDIS_URL` cannot point to localhost.

## File Upload Validation

All uploads pass through three validation stages:

### 1. Size Check

```python
max_bytes = max_mb * 1024 * 1024
if len(contents) > max_bytes:
    raise FileTooLargeError(max_mb=max_mb)
```

| Type | Max Size |
|------|----------|
| Documents (PDF, JPEG, PNG) | 5 MB |
| Audio (WAV, MP3, WebM) | 10 MB |

### 2. MIME Type Validation

Uses `python-magic` to read file headers (not extension):

```python
detected_mime = magic.from_buffer(contents, mime=True)
if detected_mime not in allowed_types:
    raise InvalidFileTypeError(detected_mime)
```

| Type | Allowed MIME Types |
|------|-------------------|
| Documents | `application/pdf`, `image/jpeg`, `image/png` |
| Audio | `audio/wav`, `audio/mpeg`, `audio/webm` |

### 3. ClamAV Virus Scan

```python
async with httpx.AsyncClient(timeout=30.0) as client:
    resp = await client.post(
        f"{settings.CLAMAV_URL}/scan",
        files={"file": (file.filename, contents, detected_mime)},
    )
if result.get("infected"):
    raise VirusDetectedError()
```

- **Fail-open**: If ClamAV is unreachable, the upload proceeds (with warning log).
- **Timeout**: 30 seconds per scan.

## SQL Injection Prevention

All database queries use SQLAlchemy ORM with parameterized queries:

```python
# Parameterized — safe
result = await db.execute(
    select(Employee).where(Employee.clerk_id == user.user_id)
)

# NEVER raw SQL with string interpolation
```

- No `text()` with user input.
- No f-string SQL construction.
- Alembic migrations use typed column definitions.

## Geofence Validation

Check-in locations are validated against the office geofence using the Haversine formula:

```python
def _haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371000  # Earth radius in meters
    # ... calculate great-circle distance
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
```

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `OFFICE_LAT` | 12.9716 | Office latitude |
| `OFFICE_LNG` | 77.5946 | Office longitude |
| `GEOFENCE_RADIUS_METERS` | 150 | Allowed radius in meters |

### Validation

```python
distance = _haversine(payload.lat, payload.lng, office_lat, office_lng)
if distance > geofence_radius:
    raise GeofenceViolationError()  # HTTP 403
```

Also supports WiFi-based check-in via IP subnet matching.

## Race Condition Prevention

### Double Check-In/Out

Prevented using Redis distributed locks:

```python
# Check lock before creating record
if await cache_service.check_attendance_lock(str(employee.id), today):
    raise DoubleCheckInError()

# Set lock after creating record
await cache_service.set_attendance_lock(str(employee.id), today, record.check_in.isoformat())
```

### Atomic SQL

All multi-step operations use single database transactions:

```python
async with session_factory() as db:
    try:
        db.add(record)
        db.add(audit_entry)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
```

### Overlapping Leave Prevention

Leave requests check for date overlaps within the same transaction:

```python
existing = await db.execute(
    select(LeaveRequest).where(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_(["approved", "pending"]),
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date,
    )
)
if existing.scalar_one_or_none():
    raise OverlappingLeaveError()
```

## Audit Trail

Every mutation writes an immutable entry to the `audit_log` table.

### What Gets Logged

| Action | Example |
|--------|---------|
| `check_in` | Employee clocked in |
| `check_out` | Employee clocked out |
| `leave_requested` | Leave application submitted |
| `leave_approved` | Admin approved leave |
| `leave_rejected` | Admin rejected leave |
| `employee_role_changed` | Role updated (old/new values) |
| `payroll_generated` | Payroll created for period |
| `employee_created` | New employee onboarded |
| `employee_deactivated` | Employee account disabled |

### Properties

- **Immutable**: No UPDATE or DELETE operations on `audit_log`.
- **Atomic**: Audit entry written in the same transaction as the mutation.
- **Complete**: Every state-changing operation is logged.
- **Traceable**: Each entry records actor, action, entity, metadata, IP, and timestamp.

## Environment Secrets Management

### Principles

1. **Never hardcode secrets** in source code.
2. **Never commit `.env` files** to version control.
3. **Use environment variables** for all sensitive configuration.
4. **Validate at startup** — pydantic-settings fails fast on missing required vars.

### Secrets Inventory

| Variable | Sensitivity | Description |
|----------|------------|-------------|
| `SECRET_KEY` | Critical | Application secret key (min 32 chars) |
| `CLERK_SECRET_KEY` | Critical | Clerk API key — full API access |
| `CLERK_JWT_VERIFICATION_KEY` | High | RSA public key for JWT verification |
| `CLERK_WEBHOOK_SECRET` | High | Webhook signing secret |
| `DATABASE_URL` | Critical | PostgreSQL connection string with password |
| `REDIS_URL` | High | Redis connection string |
| `RESEND_API_KEY` | High | Email service API key |
| `R2_SECRET_ACCESS_KEY` | High | Cloudflare R2 storage key |

### Production Hardening

- `pydantic-settings` validates required variables at import time.
- `.env` is in `.gitignore`.
- Docker uses `env_file` directive — secrets never in `Dockerfile`.
- Nginx TLS terminates HTTPS — secrets travel encrypted in transit.

### Key Rotation

| Secret | Rotation Method | Frequency |
|--------|----------------|-----------|
| Clerk API keys | Dashboard regeneration | On compromise or quarterly |
| JWT signing key | Clerk dashboard → JWT templates | On compromise |
| Database password | `ALTER ROLE` + connection string update | Quarterly |
| Redis password | `CONFIG SET` + connection string update | Quarterly |
| R2 access key | Cloudflare dashboard | On compromise or quarterly |

## ngrok Security Notes

- **Development only**: ngrok is for local development — never use in production
- **Authtoken**: Never commit `NGROK_AUTHTOKEN` to version control
- **Inspector**: ngrok Inspector (port 4040) is only accessible locally
- **URL rotation**: ngrok free tier generates new URLs on restart — update Clerk webhook URL
- **HTTPS**: ngrok provides HTTPS automatically — no additional SSL config needed
- **Rate limiting**: ngrok has its own rate limits — check ngrok dashboard for quotas
