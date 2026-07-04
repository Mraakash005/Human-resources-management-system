# HRMS API Reference

**Base URL:** `/api/v1`
**Auth:** Bearer JWT (Clerk RS256) in `Authorization` header
**Content-Type:** `application/json`

---

## Authentication

All endpoints (except webhooks) require a valid Clerk JWT:

```
Authorization: Bearer <token>
```

**Two dependency levels:**
- `get_current_user` — any authenticated user
- `require_admin` — admin role only (real-time Clerk verification via API)

Admin routes perform live role verification against Clerk API (cached 2 min in Redis) to catch stale tokens from demoted users.

---

## Rate Limits

| Category | Limit | Paths |
|---|---|---|
| General API | 60 req/min per IP | All endpoints |
| AI endpoints | 10 req/min per IP | `/nlp/*`, `/voice/*`, `/chatbot/*`, `/advisor` |

Rate limit headers returned on every response:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1719000060
```

On 429: `Retry-After` header included.

---

## Error Response Format

All errors follow a consistent structure:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "detail": null,
  "status_code": 400
}
```

**HTTP Status Codes:**

| Code | Meaning |
|---|---|
| 400 | Bad request / insufficient balance / state conflict |
| 401 | Missing or invalid authentication |
| 403 | Insufficient permissions / geofence violation |
| 404 | Resource not found |
| 409 | Conflict (overlap, duplicate, already exists) |
| 413 | File too large |
| 415 | Unsupported file type |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | Email delivery / external service failure |
| 503 | AI service unavailable |
| 504 | AI service timeout |

---

## Pagination Pattern

Paginated endpoints return:

```json
{
  "success": true,
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "has_next": true,
  "next_cursor": null
}
```

**Query parameters:** `page` (default 1, min 1), `limit` (default 20, range 1–100)

---

## Response Wrapper

Single-resource endpoints use:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "error": null
}
```

---

## Endpoints by Module

### Health Check

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | System health (DB + Redis status) |

---

### Employees (`/employees`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/employees/me` | User | Get own profile |
| `PATCH` | `/employees/me` | User | Update own profile (phone, address, profile_pic) |
| `POST` | `/employees/me/avatar/presign` | User | Get presigned avatar upload URL |
| `GET` | `/employees` | Admin | List employees (paginated, filterable) |
| `GET` | `/employees/{employee_id}` | Admin | Get employee by ID |
| `POST` | `/employees` | Admin | Create new employee (also creates Clerk user) |
| `PATCH` | `/employees/{employee_id}` | Admin | Admin-update any employee |
| `PATCH` | `/employees/{employee_id}/deactivate` | Admin | Soft-deactivate employee |
| `PATCH` | `/employees/{employee_id}/reactivate` | Admin | Reactivate employee |

**List query params:** `page`, `limit`, `department`, `search`, `is_active`

**Create request:**
```json
{
  "employee_id": "EMP-0001",
  "name": "John Doe",
  "email": "john@example.com",
  "department": "Engineering",
  "designation": "Senior Engineer",
  "phone": "+1234567890",
  "role": "employee"
}
```

---

### Attendance (`/attendance`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/attendance/checkin` | User | Check in (with optional GPS) |
| `POST` | `/attendance/checkout` | User | Check out |
| `POST` | `/attendance/auto-checkin` | User | Auto check-in (GPS/WiFi) |
| `GET` | `/attendance/today` | User | Get today's attendance status |
| `GET` | `/attendance/calendar` | User | Monthly calendar view |
| `GET` | `/attendance/heatmap` | User | Yearly attendance heatmap |
| `GET` | `/attendance/weekly` | User | Weekly view |
| `GET` | `/attendance/all` | Admin | Admin list all attendance records |

**Check-in request:**
```json
{
  "lat": 12.9716,
  "lng": 77.5946,
  "method": "gps"
}
```

**Calendar query params:** `year`, `month`
**Heatmap query params:** `year`, `employee_id` (admin only)
**Admin list query params:** `employee_id`, `start_date`, `end_date`, `limit`

---

### Leave (`/leave`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/leave` | User | Create leave request |
| `GET` | `/leave` | User | List my leave requests (admin sees all) |
| `GET` | `/leave/balance` | User | Get my leave balances |
| `PATCH` | `/leave/{leave_id}/approve` | Admin | Approve or reject leave |
| `PATCH` | `/leave/{leave_id}/cancel` | User | Cancel own pending leave |
| `GET` | `/leave/advisor` | User | AI-powered leave recommendations |
| `POST` | `/leave/nlp/chat` | User | Conversational leave application |
| `POST` | `/leave/nlp/generate-leave-email` | User | AI-generated leave email |

**Create leave request:**
```json
{
  "leave_type": "paid",
  "start_date": "2025-07-10",
  "end_date": "2025-07-12",
  "remarks": "Family vacation",
  "formal_reason": "Annual leave",
  "generated_email_body": "...",
  "send_email": true
}
```

**Approve/reject request:**
```json
{
  "status": "approved",
  "comment": "Approved. Enjoy your time off."
}
```

**Conversational leave message:**
```json
{
  "message": "I want to take 3 days off next week",
  "history": [
    {"role": "user", "content": "Hi, I need time off"},
    {"role": "assistant", "content": "Sure! What dates?"}
  ]
}
```

**Leave query params:** `page`, `limit`, `status`
**Balance query params:** `year`

---

### Payroll (`/payroll`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/payroll/me` | User | Get my payroll for a period |
| `GET` | `/payroll/me/salary` | User | Get my salary structure |
| `GET` | `/payroll/me/stub` | User | Download pay stub URL |
| `GET` | `/payroll/all` | Admin | List all payroll runs (paginated) |
| `PATCH` | `/payroll/employees/{employee_id}/salary` | Admin | Update salary structure |

**Payroll query params:** `month`, `year`
**Admin list query params:** `page`, `limit`, `month`, `year`

**Salary update request:**
```json
{
  "components": [
    {"name": "basic_salary", "amount": 80000},
    {"name": "hra", "amount": 32000},
    {"name": "transport", "amount": 5000}
  ]
}
```

---

### Dashboard (`/dashboard`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard/dashboard` | User | Aggregated dashboard (role-aware) |

Returns `EmployeeDashboard` for employees or `AdminDashboard` for admins. Response cached in Redis (60s TTL).

**Employee dashboard includes:**
- Today's attendance
- Leave balances (all types)
- Recent activity (last 5 audit logs)
- Pending leave request count

**Admin dashboard includes:**
- Total/active employee counts
- Today's attendance summary
- Pending leave requests (top 10)
- Active burnout alerts (top 10)

---

### Chat (`/chat`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/chat/channels` | User | List employee's channels |
| `GET` | `/chat/messages` | User | Get messages for a channel |
| `POST` | `/chat/messages` | User | Send a message |
| `GET` | `/chat/unread` | User | Get unread counts per channel |
| `POST` | `/chat/read/{channel_id}` | User | Mark channel as read |
| `POST` | `/chat/rsvp/{message_id}` | User | RSVP to meeting invite |
| `GET` | `/chat/stream/{channel_id}` | User | SSE stream for real-time messages |

**Send message request:**
```json
{
  "channel_id": "uuid",
  "body": "Hello team!",
  "message_type": "text",
  "meeting_meta": null
}
```

**RSVP request:**
```json
{
  "response": "accept"
}
```

**SSE stream:** Returns `text/event-stream` with `Cache-Control: no-cache`.

---

### Nudges (`/nudges`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/nudges` | User | List nudges (last 50) |
| `PATCH` | `/nudges/{nudge_id}/read` | User | Mark nudge as read |

**Query params:** `unread_only` (boolean)

---

### Chatbot (`/chatbot`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/chatbot/ask` | User | Ask HR chatbot a question |

**Request:**
```json
{
  "question": "How many paid leaves do I have left?"
}
```

Uses RAG-lite pattern: fetches employee's leave data from DB, injects into prompt, calls Ollama.

---

### Voice (`/voice`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/voice/transcribe` | User | Transcribe voice message (Whisper + Ollama parse) |

**Request:** `multipart/form-data` with `file` field (audio: wav/mpeg/webm, max 10MB)

Returns transcript and parsed leave details (if detected).

---

### Analytics (`/analytics`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/analytics/team-health` | Admin | Department health score |
| `GET` | `/analytics/burnout-dashboard` | Admin | Burnout alerts dashboard |

**Team health query params:** `department` (required), `month`, `year`
**Burnout dashboard query params:** `department` (optional filter)

---

### Webhooks (`/webhooks`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/webhooks/clerk` | Svix signature | Clerk webhook handler |

**Required headers:** `svix-id`, `svix-timestamp`, `svix-signature`

**Handled events:** `user.created`, `user.updated`, `user.deleted`, `session.created`, `session.ended`

**Security:**
- HMAC-SHA256 signature verification
- Replay protection (event IDs cached 5 min in Redis)
- Idempotent processing

---

## Security Headers

All responses include:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(self), payment=()
Cache-Control: no-store, no-cache, must-revalidate, private
X-Request-ID: <16-char hex>
X-Response-Time: <ms>
```

Over HTTPS, `Strict-Transport-Security` is added.

---

## CORS Configuration

```
allow_origins: configurable (default: http://localhost:3000)
allow_credentials: true
allow_methods: *
allow_headers: *
```
