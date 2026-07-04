# Clerk Webhooks

## Overview

The HRMS backend receives real-time events from Clerk via webhooks. The endpoint `POST /api/v1/webhooks/clerk` handles user lifecycle events, syncing Clerk user data to the local employee database.

## Supported Events

| Event | Handler | Action |
|-------|---------|--------|
| `user.created` | `_handle_user_created()` | Create employee record + initialize leave balances |
| `user.updated` | `_handle_user_updated()` | Sync role, name, email changes |
| `user.deleted` | `_handle_user_deleted()` | Soft-delete employee (set `is_active=False`) |
| `session.created` | Logging only | Log session creation |
| `session.ended` | Logging only | Log session end |

## Svix Signature Verification

Clerk uses [Svix](https://svix.com) to sign webhook payloads. The backend verifies signatures using HMAC-SHA256.

### Verification Process

```python
# app/routers/webhooks.py:35-61
def verify_clerk_webhook_signature(
    payload: bytes,
    svix_id: str,
    svix_timestamp: str,
    svix_signature: str,
) -> bool:
    to_sign = f"{svix_id}.{svix_timestamp}.{payload.decode('utf-8')}"
    secret_bytes = settings.CLERK_WEBHOOK_SECRET.replace("whsec_", "")
    key = base64.b64decode(secret_bytes)
    expected = hmac.new(key, to_sign.encode("utf-8"), hashlib.sha256).digest()
    expected_b64 = f"v1,{base64.b64encode(expected).decode('utf-8')}"
    return hmac.compare_digest(expected_b64, svix_signature)
```

### Headers

| Header | Description |
|--------|-------------|
| `svix-id` | Unique event identifier |
| `svix-timestamp` | Event timestamp (seconds since epoch) |
| `svix-signature` | HMAC-SHA256 signature (`v1,<base64>`) |

### Fallback

If `CLERK_WEBHOOK_SECRET` is not configured, signature verification is skipped with a warning log. **This is insecure and should only be used in development.**

## Replay Protection

Duplicate webhook deliveries are prevented using Redis-backed event ID tracking.

### Implementation

```python
# app/routers/webhooks.py:64-74
async def check_replay_protection(event_id: str) -> bool:
    cache_key = f"webhook_event:{event_id}"
    exists = await redis_manager.exists(cache_key)
    if exists:
        return False  # Already processed
    await redis_manager.setex(cache_key, REPLAY_WINDOW_SECONDS, "1")
    return True
```

### Properties

| Property | Value |
|----------|-------|
| Storage | Redis |
| Key pattern | `webhook_event:{svix_id}` |
| TTL | 300 seconds (5 minutes) |
| Scope | Per-event (by `svix-id`) |

### Flow

1. Webhook arrives with `svix-id`.
2. Check if `webhook_event:{svix_id}` exists in Redis.
3. If exists → return `{"status": "already_processed"}` (HTTP 200).
4. If new → store with 5-min TTL, process event.

## Event Routing and Handling

```
POST /api/v1/webhooks/clerk
  │
  ├─ 1. Verify Svix signature (HMAC-SHA256)
  │
  ├─ 2. Check replay protection (Redis, 5-min window)
  │
  ├─ 3. Parse JSON body
  │
  └─ 4. Route by event type
       ├─ user.created  → _handle_user_created()
       ├─ user.updated  → _handle_user_updated()
       ├─ user.deleted  → _handle_user_deleted()
       ├─ session.created → log only
       └─ session.ended   → log only
```

### Error Handling

- **Signature invalid**: HTTP 401 `{"detail": "Invalid signature"}`
- **Invalid JSON**: HTTP 400 `{"detail": "Invalid JSON"}`
- **Handler exception**: Logged but HTTP 200 returned (prevents Clerk retries for unhandled events)

## Employee Sync on User Creation

When Clerk fires `user.created`:

1. Extract `clerk_user_id`, primary email, name, and `public_metadata.role`.
2. Check if employee already exists (idempotent).
3. Generate employee ID (`EMP-0001`, `EMP-0002`, etc.).
4. Create `Employee` record with role from metadata.
5. Initialize leave balances (paid, sick, unpaid, bereavement) from config defaults.
6. Commit transaction.

```python
employee = Employee(
    clerk_id=clerk_user_id,
    employee_id=emp_id,
    name=name,
    email=primary_email,
    role=role,
)
```

## Role Sync on Metadata Changes

When Clerk fires `user.updated`:

1. Look up employee by `clerk_id`.
2. Compare `public_metadata.role` with current `employee.role`.
3. If role changed:
   - Update `employee.role`.
   - Invalidate Redis role cache (`role_verified:{clerk_id}`).
   - Write audit log entry: `employee_role_changed` with old/new values.
4. Sync name and email if changed.
5. If user is deleted or banned, set `is_active=False`.

### Audit Log Entry

```python
await log_action(
    db=db,
    actor_id=employee.id,
    action="employee_role_changed",
    entity_type="employee",
    entity_id=employee.id,
    metadata={"old_role": "employee", "new_role": "admin"},
)
```

## Soft-Delete on User Deletion

When Clerk fires `user.deleted`:

1. Look up employee by `clerk_id`.
2. Set `is_active = False` (soft delete — data is preserved).
3. Invalidate Redis caches:
   - `role_verified:{clerk_id}`
   - `dashboard:{clerk_id}:*`

> **Note**: Employee records are never hard-deleted. This preserves referential integrity for attendance, leave, payroll, and audit history.

## Webhook Endpoint Reference

### `POST /api/v1/webhooks/clerk`

**Request Headers**:
```
Content-Type: application/json
svix-id: evt_xxxxx
svix-timestamp: 1234567890
svix-signature: v1,xxxxx...
```

**Request Body** (Clerk event format):
```json
{
  "type": "user.created",
  "data": {
    "id": "user_xxxxx",
    "email_addresses": [
      {"id": "email_xxx", "email_address": "user@example.com"}
    ],
    "primary_email_address_id": "email_xxx",
    "first_name": "John",
    "last_name": "Doe",
    "public_metadata": {
      "role": "employee"
    }
  }
}
```

**Response** (always HTTP 200):
```json
{"status": "processed"}
```

Or for replays:
```json
{"status": "already_processed"}
```

## Configuration

| Variable | Description |
|----------|-------------|
| `CLERK_WEBHOOK_SECRET` | Signing secret (`whsec_...`) — required for signature verification |
| `REPLAY_WINDOW_SECONDS` | Replay protection window (default: 300s) |
| `NGROK_ENABLED` | Set to `true` to enable ngrok tunnel for webhook development |
| `NGROK_AUTHTOKEN` | Your ngrok auth token (required if NGROK_ENABLED=true) |

## ngrok Integration for Webhook Development

For local development, Clerk needs a public URL to deliver webhooks. ngrok provides a secure tunnel from the internet to your local Docker backend.

### Quick Setup

1. Set in `.env`:
```bash
NGROK_ENABLED=true
NGROK_AUTHTOKEN=your_token_here
```

2. Start with ngrok profile:
```bash
docker compose --profile ngrok up -d
```

3. Get your webhook URL:
```bash
bash scripts/print-ngrok-url.sh
```

4. Configure in Clerk Dashboard:
- Go to Webhooks → Add Endpoint
- Paste: `https://<ngrok-url>/api/v1/webhooks/clerk`
- Subscribe to: `user.created`, `user.updated`, `user.deleted`
- Copy Signing Secret → set as `CLERK_WEBHOOK_SECRET` in `.env`

### Architecture

```
Clerk Cloud → ngrok (public URL) → Docker backend:8000
```

### Commands

```bash
# Start with ngrok
docker compose --profile ngrok up -d

# Print tunnel URL
bash scripts/print-ngrok-url.sh

# View ngrok logs
docker compose --profile ngrok logs ngrok

# Stop ngrok
docker compose --profile ngrok down
```

For full ngrok documentation, see `docs/NGROK.md`.

## Security Notes

- **Always enable signature verification in production.** Remove the fallback bypass.
- **Use HTTPS** for webhook endpoints in production.
- **Return HTTP 200** quickly — process asynchronously if handler logic is slow.
- **Idempotent handlers**: `user.created` checks for existing employee before creating.
- **No PII in logs**: Email addresses are logged at `INFO` level; audit logs reference entity IDs only.
