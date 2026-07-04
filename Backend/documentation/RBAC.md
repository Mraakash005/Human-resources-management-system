# Role-Based Access Control (RBAC)

## Overview

The HRMS enforces a two-role access control model: **admin** and **employee**. Roles are stored in Clerk's `public_metadata`, embedded in JWTs, verified locally, and checked against protected routes via FastAPI dependencies.

## Two Roles

### Admin

Full system access. Can:
- View and manage all employees (CRUD)
- Approve or reject leave requests
- Generate payroll for all employees
- View attendance records for all employees
- Access analytics dashboards (burnout, heatmap, team health)
- Override attendance records
- Configure office settings (geofence, IP subnet)

### Employee

Self-service access. Can:
- View own profile and edit non-sensitive fields
- Check in/out for attendance
- Submit leave requests (and cancel pending ones)
- View own payroll and download pay stubs
- Participate in team chat
- Ask the HR chatbot questions
- View own attendance history and heatmap

## Role Hierarchy

```
admin ─────────────────────────────────────────────────────
  ├── All employee permissions
  ├── Employee CRUD (create, read, update, deactivate)
  ├── Leave approval (approve, reject)
  ├── Payroll generation (all employees)
  ├── Attendance override (all employees)
  ├── Analytics access (burnout, heatmap, team health)
  └── System configuration (geofence, IP settings)

employee ────────────────────────────────────────────────
  ├── Profile (read, limited update)
  ├── Attendance (check-in/out, own history, own heatmap)
  ├── Leave (request, cancel, view balance)
  ├── Payroll (view own, download own stub)
  ├── Chat (send messages, join channels)
  └── Chatbot (ask HR questions)
```

## Permission Model

### Route-Level Protection

Every protected route declares its required dependency:

```python
# Employee routes (any authenticated user)
@router.get("/dashboard")
async def dashboard(user: TokenPayload = Depends(get_current_user)):
    ...

# Admin-only routes
@router.get("/employees/all")
async def list_all(user: TokenPayload = Depends(require_admin)):
    ...

# Optional authentication (public with personalization)
@router.get("/announcements")
async def announcements(user: TokenPayload | None = Depends(get_optional_user)):
    ...
```

### Dependency Chain

```
get_current_user
    │
    ▼
Extract Bearer token from Authorization header
    │
    ▼
Decode JWT (RS256 verification)
    │
    ▼
Return TokenPayload(user_id, role)
    │
    ├──→ require_admin
    │       │
    │       ▼
    │    Check role == "admin"
    │       │
    │       ├── Yes → verify_admin_role_live() → Redis cache / Clerk API
    │       │         │
    │       │         ├── Cache hit → return cached role
    │       │         └── Cache miss → Clerk API call → cache for 2min
    │       │
    │       └── No → return 403
    │
    └──→ get_optional_user
            │
            ▼
         Decode JWT (catch exceptions silently)
            │
            ├── Valid → return TokenPayload
            └── Invalid/expired → return None
```

### Data Isolation

Employees can only access their own data:

```python
# Attendance — always filtered by current user
@router.get("/today")
async def get_today(user: TokenPayload = Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(
        select(Employee).where(Employee.clerk_id == user.user_id)
    )
    employee = result.scalar_one_or_none()
    # Query filtered by employee.id
```

Admins can access all data:

```python
@router.get("/all")
async def admin_list(user: TokenPayload = Depends(require_admin), db=Depends(get_db)):
    # No employee filter — returns all records
    ...
```

## Real-Time Role Verification

### Problem

JWTs have a 15-minute TTL. If an admin is demoted, their token still says `role=admin` until expiry.

### Solution

`require_admin` performs live verification via Clerk API:

```python
async def require_admin(user: TokenPayload = Depends(get_current_user)):
    # JWT says admin — verify via Clerk
    live_admin = await verify_admin_role_live(user.user_id)
    if not live_admin:
        raise HTTPException(status_code=403, detail="Admin access revoked")
    return user
```

### Verification Flow

1. JWT claims `role=admin`.
2. Check Redis cache (`role_verified:{user_id}`).
3. **Cache hit (2-min TTL)**: Return cached role — no API call.
4. **Cache miss**: Call `GET https://api.clerk.com/v1/users/{user_id}`.
5. Read `public_metadata.role` from response.
6. Cache result for 2 minutes.
7. If Clerk API fails → **fail closed** (deny access).

### Cache Invalidation

Role cache is invalidated when:
- Webhook receives `user.updated` with role change.
- Webhook receives `user.deleted`.
- Redis TTL expires (2 minutes).

## Audit Logging of Role Changes

Every role change is logged to the `audit_log` table with old and new values:

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

### Audit Log Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `actor_id` | UUID (FK → employees) | Who performed the action |
| `action` | string | Action type (`employee_role_changed`, `check_in`, etc.) |
| `entity_type` | string | Entity type (`employee`, `attendance`, etc.) |
| `entity_id` | UUID | Entity being modified |
| `metadata` | JSONB | Old/new values, context |
| `ip_address` | string | Client IP |
| `created_at` | timestamptz | When the action occurred |

### Immutable

Audit logs are append-only. They are never updated or deleted. The `audit_log` table has no `UPDATE` or `DELETE` triggers.

## Route Protection Reference

| Endpoint | Dependency | Access |
|----------|-----------|--------|
| `GET /health` | None | Public |
| `GET /dashboard` | `get_current_user` | Employee (own data) |
| `POST /attendance/checkin` | `get_current_user` | Employee |
| `GET /attendance/all` | `require_admin` | Admin only |
| `POST /leave/request` | `get_current_user` | Employee |
| `PATCH /leave/{id}/approve` | `require_admin` | Admin only |
| `GET /payroll/{id}` | `get_current_user` | Employee (own) |
| `POST /payroll/generate` | `require_admin` | Admin only |
| `GET /employees/all` | `require_admin` | Admin only |
| `POST /employees/create` | `require_admin` | Admin only |
| `POST /webhooks/clerk` | Signature verification | Clerk only |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CLERK_JWT_TTL_MINUTES` | 15 | JWT lifetime before refresh required |
| `CACHE_ROLE_VERIFICATION_TTL` | 120 | Seconds before re-verifying role with Clerk |
