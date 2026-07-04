# HRMS — Complete Feature Specification
## Core SRS Features + Advanced AI-Powered Differentiators
### Version 2.0 — Full Detail, Production-Ready

> This document contains the **complete feature set** for the HRMS system:
> - **Part A: Core SRS Features (Mandatory)** — The foundational features required for any production HRMS
> - **Part B: Performance & Security Features** — Cross-cutting concerns for production readiness
> - **Part C: Creative Differentiator Features (AI-Powered)** — Advanced features that set this HRMS apart
>
> Each feature is documented with:
> **What it is → Why it exists → How it works → Data flow → Tech used → Free/cost → Code outline**

---

## Table of Contents

### Part A — Core SRS Features (Mandatory)

1. [Clerk Authentication](#1-clerk-authentication)
2. [Role-Based Dashboards](#2-role-based-dashboards)
3. [Employee Profile Management](#3-employee-profile-management)
4. [Admin Leave Approval](#4-admin-leave-approval)
5. [Attendance Check-In/Check-Out](#5-attendance-check-incheck-out)
6. [Payroll Visibility](#6-payroll-visibility)
7. [Leave Application](#7-leave-application)
8. [Admin Employee Management](#8-admin-employee-management)

### Part B — Performance & Security Features

9. [Redis Dashboard Caching](#9-redis-dashboard-caching)
10. [Input Validation — Pydantic v2](#10-input-validation--pydantic-v2)
11. [DB Query Optimization](#11-db-query-optimization)
12. [Aggregated Dashboard API](#12-aggregated-dashboard-api)
13. [Audit Logging](#13-audit-logging)
14. [Async FastAPI Throughout](#14-async-fastapi-throughout)

### Part C — Creative Differentiator Features (AI-Powered)

15. [Conversational Leave (NLP Multi-Turn)](#15-conversational-leave-nlp-multi-turn)
16. [HR Chatbot](#16-hr-chatbot)
17. [Voice Check-In & Voice Commands](#17-voice-check-in--voice-commands)
18. [Voice-to-Leave (Audio Leave Application)](#18-voice-to-leave-audio-leave-application)
19. [Attendance Heatmap & Calendar](#19-attendance-heatmap--calendar)
20. [Burnout Early Warning System](#20-burnout-early-warning-system)
21. [Live Salary Simulator](#21-live-salary-simulator)
22. [AI Leave Advisor](#22-ai-leave-advisor)
23. [Smart GPS & Wi-Fi Auto Check-In](#23-smart-gps--wi-fi-auto-check-in)
24. [Team Attendance Health Score](#24-team-attendance-health-score)
25. [Proactive Nudge System](#25-proactive-nudge-system)
26. [Automated PDF Pay Stub Generation](#26-automated-pdf-pay-stub-generation)
27. [Internal Team Chat & Meeting Announcements](#27-internal-team-chat--meeting-announcements)

### Appendices

- [Database Additions for All Features](#database-additions-for-all-features)
- [Updated Folder Structure Additions](#updated-folder-structure-additions)
- [Updated Tech Stack Additions](#updated-tech-stack-additions)
- [Free Tools Master Reference](#free-tools-master-reference)

---

# PART A — CORE SRS FEATURES (MANDATORY)

> These are the foundational, non-negotiable features that every production HRMS must ship with. They form the backbone of the system and are prerequisites for all advanced features.

---

## 1. Clerk Authentication

### What It Is
Managed authentication powered by Clerk — handles sign-up, sign-in, email verification, JWT issuance, and role management. No custom auth code. No password hashing. No session table.

### Why It Exists
Building auth from scratch is error-prone, time-consuming, and a security liability. Clerk provides battle-tested auth with a generous free tier (10,000 MAU) including email verification, password policies, MFA, and session management out of the box.

### How It Works — Data Flow

```
Employee signs up via Clerk UI (sign-up page)
    │
    ▼
Clerk collects: Email + Password + Employee ID + Role (assigned at registration or by admin)
    │
    ▼
Clerk sends verification email → employee clicks link → email verified
    │
    ▼
Clerk issues JWT (RS256 signed) containing:
    {
      "sub": "clerk_user_id",
      "metadata": { "role": "employee" | "admin" }
    }
    │
    ▼
Frontend: Clerk SDK stores JWT in httpOnly cookie (secure, XSS-safe)
    │
    ▼
Every API request: Clerk SDK auto-appends "Authorization: Bearer <jwt>"
    │
    ▼
FastAPI core/auth.py:
    1. Decodes JWT with Clerk RSA public key (RS256)
    2. Extracts role from metadata
    3. Returns user context to route handler
    │
    ▼
For admin routes: secondary Clerk getUser() API call verifies role in real-time
(stale JWT protection — catches demoted admins)
    │
    ▼
Redis caches role verification for 2 minutes (avoids hammering Clerk API)
```

### Implementation Details

| Aspect | Detail |
|--------|--------|
| **Sign-up flow** | Clerk `<SignUp />` component with custom fields (Employee ID, Role) |
| **Sign-in flow** | Clerk `<SignIn />` component — email + password |
| **JWT TTL** | 15 minutes (configured in Clerk dashboard) |
| **Role assignment** | Stored in Clerk `publicMetadata.role` — set at registration or by admin |
| **Stale role protection** | `require_admin` calls `getUser()` API to verify current role |
| **Session management** | Clerk `<UserProfile />` in employee settings — view/revoke sessions |
| **Frontend integration** | `@clerk/nextjs` — `auth()` server-side, `useAuth()` client-side |

### Backend Code Outline

```python
# core/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

security = HTTPBearer()
CLERK_PEM_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"""

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, CLERK_PEM_PUBLIC_KEY,
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
    return user
```

### Frontend Middleware

```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isAdminRoute = createRouteMatcher(["/admin(.*)"]);
const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)", "/attendance(.*)", "/leave(.*)", "/payroll(.*)"
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) await auth.protect();
  if (isAdminRoute(req)) {
    const { sessionClaims } = await auth();
    if (sessionClaims?.metadata?.role !== "admin") {
      return Response.redirect(new URL("/dashboard", req.url));
    }
  }
});
```

**Cost:** Free (Clerk free tier: 10,000 MAU — covers hackathon + small production)

---

## 2. Role-Based Dashboards

### What It Is
A single `/dashboard` route that dynamically renders either an `AdminDashboard` or `EmployeeDashboard` based on the authenticated user's Clerk role. Middleware blocks `/admin/*` routes for employees at the edge.

### Why It Exists
Admins and employees have fundamentally different needs. Admins need organizational oversight (employee counts, pending approvals, burnout alerts). Employees need personal data (attendance, leave balance, salary). One route with role-splitting avoids code duplication while keeping experiences tailored.

### How It Works — Data Flow

```
User navigates to /dashboard
    │
    ▼
middleware.ts checks role from Clerk sessionClaims
    │
    ├─ role == "admin" → renders AdminDashboard
    │   └─ Shows: employee count, today's attendance summary,
    │             pending leave queue, burnout alerts, payroll status
    │
    └─ role == "employee" → renders EmployeeDashboard
        └─ Shows: today's check-in status, leave balance summary,
                   recent activity, quick-action cards

If employee tries /admin/* → middleware redirects to /dashboard
If unauthenticated → middleware redirects to /sign-in
```

### Dashboard Layouts

**Employee Dashboard:**
```
┌─────────────────────────────────────────────────────┐
│  Welcome back, Rohan!                    [Profile]   │
├──────────────┬──────────────┬───────────────────────┤
│  ☑ Checked   │  Leave       │  Active              │
│  In: 9:02 AM │  Balance: 8  │  Requests: 2         │
├──────────────┴──────────────┴───────────────────────┤
│  Quick Actions                                       │
│  [Check In/Out] [Apply Leave] [View Payroll] [Chat] │
├─────────────────────────────────────────────────────┤
│  Recent Activity                                     │
│  • Leave approved (Aug 11-12) — 2 hours ago         │
│  • Check-out recorded — yesterday 6:15 PM           │
│  • Pay stub ready — Aug 2025                        │
└─────────────────────────────────────────────────────┘
```

**Admin Dashboard:**
```
┌─────────────────────────────────────────────────────┐
│  Admin Dashboard — Engineering Dept        [Switch ▼]│
├──────────┬──────────┬──────────┬────────────────────┤
│  Total   │ Present  │ Pending  │ Burnout            │
│  Emp: 42 │ Today:38 │ Leave: 3 │ Alerts: 2          │
├──────────┴──────────┴──────────┴────────────────────┤
│  Pending Approvals                                   │
│  ┌────────────────────────────────────────────────┐ │
│  │ Priya Sharma — Sick Leave Aug 15-16  [Approve] │ │
│  │ Amit Singh — Paid Leave Aug 20-22    [Approve] │ │
│  └────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  Department Health: 🟢 92/100  ↑ 3pts vs last month │
└─────────────────────────────────────────────────────┘
```

### Implementation

| Aspect | Detail |
|--------|--------|
| **Route** | `/dashboard` — single route, role-split via conditional render |
| **Middleware** | `clerkMiddleware()` blocks `/admin/*` for non-admin roles |
| **Data source** | `GET /api/dashboard` — single aggregated endpoint returns all data |
| **Caching** | TanStack Query caches dashboard data client-side (60s stale time) |
| **Role switching** | Admin can switch employee context from admin panel |

**Cost:** Free. Standard frontend routing + Clerk role metadata.

---

## 3. Employee Profile Management

### What It Is
A unified profile page where employees view their personal details, and admins manage all employee records. Employees can edit limited fields (phone, address, avatar). Admins can edit everything. Profile picture uploaded to R2 via presigned URL.

### Why It Exists
Employees need to update their own contact details without bothering HR. Admins need full control over employee records for onboarding, corrections, and offboarding.

### How It Works — Data Flow

```
Employee clicks "Profile" card on dashboard
    │
    ▼
GET /employees/me → returns own profile data
    │
    ▼
Profile page renders:
  - Name, Employee ID, Department, Designation (read-only for employee)
  - Phone, Address (editable by employee)
  - Profile picture (uploadable by employee)
  - Documents section (view uploaded docs)

Employee edits phone/address:
    │
    ▼
PATCH /employees/me { phone, address }
    │
    ▼
FastAPI validates with Pydantic schema
    │
    ▼
UPDATE employees SET phone = ..., address = ... WHERE clerk_id = ...
    │
    ▼
Redis: invalidate profile cache
    │
    ▼
audit_log: { action: "profile_updated", old_values, new_values }
    │
    ▼
200 OK → UI reflects changes

Employee uploads profile picture:
    │
    ▼
POST /employees/me/avatar → presigned R2 URL generated
    │
    ▼
Frontend uploads directly to R2 (no server roundtrip for file)
    │
    ▼
PATCH /employees/me { profile_pic: r2_url }
    │
    ▼
DB updated, old avatar optionally deleted from R2
```

### Admin Profile Management

```
Admin navigates to /admin/employees → employee table
    │
    ▼
Clicks employee row → full profile view
    │
    ▼
Admin can edit ALL fields: name, department, designation, role, etc.
    │
    ▼
PATCH /employees/{id} { ...allFields }
    │
    ▼
audit_log: { action: "admin_profile_edit", old_values, new_values }
```

### Backend Code Outline

```python
# routers/employees.py
@router.get("/employees/me")
async def get_my_profile(db=Depends(get_db), user=Depends(get_current_user)):
    employee = await get_employee_by_clerk_id(db, user["user_id"])
    return employee

@router.patch("/employees/me")
async def update_my_profile(
    payload: EmployeeSelfUpdateSchema,  # limited fields: phone, address
    db=Depends(get_db), user=Depends(get_current_user)
):
    employee = await get_employee_by_clerk_id(db, user["user_id"])
    old_values = {"phone": employee.phone, "address": employee.address}
    employee.phone = payload.phone
    employee.address = payload.address
    await db.commit()
    await log_action(db, employee.id, "profile_updated", old=old_values, new=payload.dict())
    return employee

@router.patch("/employees/{employee_id}")
@admin_only
async def admin_update_employee(
    employee_id: UUID,
    payload: EmployeeAdminUpdateSchema,  # all fields
    db=Depends(get_db), user=Depends(require_admin)
):
    employee = await get_employee(db, employee_id)
    old_values = serialize(employee)
    update_fields(employee, payload)
    await db.commit()
    await log_action(db, user["user_id"], "admin_profile_edit",
                     entity_id=employee_id, old=old_values, new=payload.dict())
    return employee
```

### Profile Picture Upload (R2 Presigned URL)

```python
# routers/employees.py
@router.post("/employees/me/avatar/presign")
async def get_avatar_upload_url(
    user=Depends(get_current_user),
    filename: str = Query(...),
):
    key = f"avatars/{user['user_id']}/{filename}"
    presigned_url = generate_r2_presigned_url(key, method="PUT", expires=300)
    return {"upload_url": presigned_url, "public_url": f"{R2_PUBLIC_BASE}/{key}"}
```

**Cost:** Free. Cloudflare R2 free tier: 10 GB storage, 10M reads/month.

---

## 4. Admin Leave Approval

### What It Is
Admin/HR views all pending leave requests in a sortable queue. One-click approve or reject with optional comment. Instant status update reflected in the employee's record. Every change is written to audit logs.

### Why It Exists
Leave approval is the most frequent admin action in any HRMS. It must be fast, auditable, and provide instant feedback to both admin and employee.

### How It Works — Data Flow

```
Admin navigates to /admin/approvals
    │
    ▼
GET /leave?status=pending (require_admin dependency)
    │
    ▼
FastAPI: secondary Clerk getUser() verify (stale JWT protection)
    │
    ▼
Returns pending queue from PostgreSQL (no Redis — admin needs fresh data)
    │
    ▼
Admin sees table: employee name, leave type, dates, days, reason
    │
    ▼
Admin clicks "Approve" or "Reject" + optional comment
    │
    ▼
PATCH /leave/{leave_id}/approve { status: "approved", comment: "..." }
    │
    ▼
UPDATE leave_requests
    SET status = 'approved',
        admin_comment = '...',
        reviewed_by = :admin_id,
        reviewed_at = NOW()
    WHERE id = :leave_id
    │
    ├─ If rejected: recredit leave balance (atomic UPDATE)
    │
    ▼
Redis: invalidate employee's leave balance cache
    │
    ▼
Resend: email notification to employee
    │
    ▼
audit_log: { action: "leave_approved", actor: admin_id, entity: leave_id,
             old_status: "pending", new_status: "approved" }
    │
    ▼
200 OK → TanStack Query invalidates ["leave-requests"] → UI updates instantly
```

### Admin Approval Queue UI

```
┌──────────────────────────────────────────────────────────────┐
│  PENDING LEAVE REQUESTS (3)                    [Filter ▼]   │
├──────────────────────────────────────────────────────────────┤
│  Employee       │ Type  │ Dates       │ Days │ Action       │
├─────────────────┼───────┼─────────────┼──────┼──────────────┤
│  Priya Sharma   │ Sick  │ Aug 15-16   │ 2    │ [✓][✗][💬]  │
│  Amit Singh     │ Paid  │ Aug 20-22   │ 3    │ [✓][✗][💬]  │
│  Neha Gupta     │ Med.  │ Aug 25-28   │ 4    │ [✓][✗][💬]  │
└──────────────────────────────────────────────────────────────┘

✓ = Approve  |  ✗ = Reject  |  💬 = Add comment before action
```

### Backend Code Outline

```python
# routers/leave.py
@router.patch("/leave/{leave_id}/approve")
async def approve_leave(
    leave_id: UUID,
    payload: LeaveApprovalSchema,  # status: "approved"|"rejected", comment: str
    db=Depends(get_db),
    user=Depends(require_admin)
):
    leave = await db.get(LeaveRequest, leave_id)
    if not leave or leave.status != "pending":
        raise HTTPException(404, "Pending leave not found")

    old_status = leave.status
    leave.status = payload.status
    leave.admin_comment = payload.comment
    leave.reviewed_by = employee.id
    leave.reviewed_at = datetime.now(timezone.utc)

    # If rejected, recredit balance
    if payload.status == "rejected":
        days = (leave.end_date - leave.start_date).days + 1
        await db.execute(
            text("UPDATE leave_balances SET used = used - :days "
                 "WHERE employee_id = :eid AND year = :y AND leave_type = :lt"),
            {"days": days, "eid": leave.employee_id,
             "y": leave.start_date.year, "lt": leave.leave_type}
        )

    await db.commit()

    # Audit log
    await log_action(db, user["user_id"], "leave_approved",
                     entity_id=leave_id,
                     metadata={"old_status": old_status, "new_status": payload.status,
                               "comment": payload.comment})

    # Notify employee
    await send_leave_decision_email(leave, payload.status, payload.comment)

    # Invalidate cache
    await redis.delete(f"leave_balance:{leave.employee_id}")

    return {"success": True, "status": payload.status}
```

**Cost:** Free. Standard PostgreSQL queries + Resend email (free tier).

---

## 5. Attendance Check-In/Check-Out

### What It Is
One-click check-in and check-out. Redis prevents double check-in. Stores timestamp, auto-computes duration. Daily/weekly calendar view. Statuses: Present, Absent, Half-day, Leave.

### Why It Exists
Accurate attendance tracking is the foundation of payroll, leave management, and burnout detection. Manual attendance is unreliable. A simple one-click system with Redis guard rails ensures accuracy without friction.

### How It Works — Data Flow

```
Employee clicks "Check In" button
    │
    ▼
Frontend: navigator.geolocation.getCurrentPosition() (optional, admin-configurable)
    │
    ▼
POST /attendance/checkin { lat?, lng? }
    │
    ▼
FastAPI:
    1. Check Redis: attendance:checkin:{employee_id}:{date} — prevents double check-in
    2. If Redis key exists → 409 "Already checked in today"
    3. If geofence enabled → validate coordinates against office location
    4. If outside geofence → 403 "Outside office zone"
    │
    ▼
INSERT attendance_records { employee_id, date, status: 'present', check_in: NOW() }
    │
    ▼
Redis: SET attendance:checkin:{employee_id}:{date} = check_in_time (TTL: 24h)
    │
    ▼
audit_log: { action: "check_in", metadata: { lat, lng, method } }
    │
    ▼
200 OK → Button changes to "Check Out" + shows check-in time

---

Employee clicks "Check Out" button
    │
    ▼
POST /attendance/checkout
    │
    ▼
FastAPI:
    1. Read today's attendance record
    2. Compute duration = check_out - check_in
    3. UPDATE attendance_records SET check_out = NOW(), duration = ...
    │
    ▼
Redis: update cached attendance status
    │
    ▼
200 OK → Shows duration: "8h 12m"
```

### Calendar View (Daily/Weekly)

```
┌─────────────────────────────────────────────────┐
│  August 2025 — Weekly View                      │
├──────┬──────┬──────┬──────┬──────┬──────┬──────┤
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│  4   │  5   │  6   │  7   │  8   │  ─   │  ─   │
│ 9:01 │ 8:55 │ 9:03 │ 8:47 │ 9:10 │      │      │
│ 18:02│ 17:50│ 18:15│ 18:30│ 17:45│      │      │
│ 🟢   │ 🟢   │ 🟢   │ 🟢   │ 🟢   │  ⬜  │  ⬜  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│ 11   │ 12   │ 13   │ 14   │ 15   │  ─   │  ─   │
│ 9:02 │  ─   │ 9:00 │ 8:58 │  ─   │      │      │
│ 18:10│      │ 18:20│ 17:55│      │      │      │
│ 🟢   │ 🔴   │ 🟢   │ 🟢   │ 🔵   │  ⬜  │  ⬜  │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

🟢 = Present  |  🔴 = Absent  |  🔵 = Leave  |  ⬜ = Weekend
```

### Redis Double Check-In Prevention

```python
# routers/attendance.py
@router.post("/attendance/checkin")
async def check_in(payload: CheckInSchema, db=Depends(get_db),
                   redis=Depends(get_redis), user=Depends(get_current_user)):
    employee = await get_employee(db, user["user_id"])
    today = date.today().isoformat()
    redis_key = f"attendance:checkin:{employee.id}:{today}"

    # Prevent double check-in via Redis
    if await redis.exists(redis_key):
        raise HTTPException(409, "Already checked in today")

    # Geofence validation (if enabled)
    config = await get_office_config(db)
    if config.gps_checkin_enabled and payload.lat and payload.lng:
        distance = haversine(payload.lat, payload.lng,
                           config.office_lat, config.office_lng)
        if distance > config.geofence_radius_meters:
            raise HTTPException(403, "Outside office zone")

    # Create attendance record
    record = AttendanceRecord(
        employee_id=employee.id, date=today,
        status="present", check_in=datetime.now(timezone.utc),
        location_lat=payload.lat, location_lng=payload.lng
    )
    db.add(record)
    await db.commit()

    # Redis guard — TTL 24 hours
    await redis.setex(redis_key, 86400, record.check_in.isoformat())

    return {"status": "checked_in", "time": record.check_in.isoformat()}
```

### Backend Code Outline

```python
@router.post("/attendance/checkout")
async def check_out(db=Depends(get_db), redis=Depends(get_redis),
                    user=Depends(get_current_user)):
    employee = await get_employee(db, user["user_id"])
    today = date.today().isoformat()

    record = await get_today_record(db, employee.id)
    if not record or not record.check_in:
        raise HTTPException(400, "No check-in found for today")
    if record.check_out:
        raise HTTPException(409, "Already checked out today")

    record.check_out = datetime.now(timezone.utc)
    record.duration = (record.check_out - record.check_in).total_seconds() / 3600
    await db.commit()

    return {"status": "checked_out", "duration_hours": round(record.duration, 2)}
```

**Cost:** Free. Redis (already in stack) + PostgreSQL + browser Geolocation API.

---

## 6. Payroll Visibility

### What It Is
Read-only payroll view for employees showing basic, HRA, deductions, net pay per month. Admin can update salary structure. Payroll records are immutable once generated.

### Why It Exists
Employees need transparent visibility into their salary breakdown without contacting HR. Admins need full control to update salary components. Immutability ensures payroll records are audit-proof and legally defensible.

### How It Works — Data Flow

```
Employee navigates to /payroll
    │
    ▼
GET /payroll/me?month=8&year=2025 (RSC — zero JS sent to client)
    │
    ▼
FastAPI returns:
    {
      "month": 8, "year": 2025,
      "earnings": {
        "basic_salary": 50000,
        "hra": 20000,
        "transport": 3000,
        "performance_bonus": 5000
      },
      "deductions": {
        "pf": 6000,
        "income_tax": 4200,
        "unpaid_leave_deduction": 0
      },
      "gross_pay": 78000,
      "net_pay": 67800,
      "pay_stub_url": "/storage/paystubs/emp-0042/2025-08.pdf"
    }
    │
    ▼
Frontend renders:
    - Earnings breakdown (card)
    - Deductions breakdown (card)
    - Net take-home (highlighted)
    - Download pay stub PDF button

---

Admin navigates to /admin/payroll
    │
    ▼
GET /payroll/all → full table of all employees' latest payroll
    │
    ▼
Admin can update salary structure:
    │
    ▼
PATCH /employees/{id}/salary { basic_salary, hra, transport, ... }
    │
    ▼
INSERT INTO salary_components (new effective_from date)
    │
    ▼
audit_log: { action: "salary_updated", old_values, new_values }
```

### Immutability Guarantee

```sql
-- Payroll runs are INSERT-only. No UPDATE, no DELETE.
-- The components_snapshot JSONB column captures the exact salary structure
-- at the time of payroll generation. Even if salary changes later,
-- the payroll record remains unchanged.

-- Example components_snapshot:
{
  "basic_salary": 50000,
  "hra": 20000,
  "transport": 3000,
  "effective_from": "2025-01-01"
}
```

### Backend Code Outline

```python
# routers/payroll.py
@router.get("/payroll/me")
async def get_my_payroll(
    month: int = Query(default=date.today().month),
    year: int = Query(default=date.today().year),
    db=Depends(get_db), user=Depends(get_current_user)
):
    employee = await get_employee(db, user["user_id"])
    payroll = await db.execute(
        select(PayrollRun).where(
            PayrollRun.employee_id == employee.id,
            PayrollRun.month == month,
            PayrollRun.year == year
        )
    )
    result = payroll.scalar_one_or_none()
    if not result:
        raise HTTPException(404, "No payroll record for this month")
    return result  # read-only — no mutation endpoints for employees

@router.patch("/employees/{employee_id}/salary")
@admin_only
async def update_salary_structure(
    employee_id: UUID, payload: SalaryUpdateSchema,
    db=Depends(get_db), user=Depends(require_admin)
):
    old_components = await get_current_salary_components(db, employee_id)
    for component in payload.components:
        new_entry = SalaryComponent(
            employee_id=employee_id,
            component=component.name,
            amount=component.amount,
            effective_from=date.today()
        )
        db.add(new_entry)
    await db.commit()
    await log_action(db, user["user_id"], "salary_updated",
                     entity_id=employee_id,
                     metadata={"old": serialize(old_components), "new": payload.dict()})
    return {"success": True}
```

**Cost:** Free. Standard PostgreSQL queries + RSC for zero-JS client delivery.

---

## 7. Leave Application

### What It Is
Calendar date picker, leave type selection (Paid/Sick/Unpaid), remarks field. Status tracking: Pending → Approved/Rejected. Monthly calendar shows Present/Absent markers for context. Overlapping leaves prevented at DB level.

### Why It Exists
Leave application is the most used employee-facing feature. It must be intuitive (calendar picker, not manual date typing), safe (no overlapping leaves), and provide context (show existing attendance so employees pick appropriate dates).

### How It Works — Data Flow

```
Employee clicks "Apply Leave" on dashboard
    │
    ▼
Leave page loads:
    - LeaveForm component (date picker, type dropdown, remarks)
    - AttendanceCalendar shows current month with Present/Absent markers
    - Leave balance summary (paid: 8/12, sick: 5/10, etc.)
    │
    ▼
Employee selects dates via calendar picker
    │
    ▼
Live validation:
    - Check selected dates against attendance calendar (avoid already-present days)
    - Check against existing approved leaves (DB exclusion constraint)
    - Check leave balance (enough days remaining?)
    │
    ▼
Employee fills: Leave type + Remarks
    │
    ▼
POST /leave { leave_type, start_date, end_date, remarks }
    │
    ▼
FastAPI:
    1. Pydantic v2 validates all fields
    2. Compute days = (end_date - start_date).days + 1
    3. Atomic balance check: UPDATE leave_balances WHERE (total - used) >= days
    4. INSERT leave_requests (PostgreSQL EXCLUDE constraint catches overlap)
    │
    ├─ Insufficient balance → 400
    ├─ Overlapping dates → 409 (PostgreSQL raises exception)
    │
    ▼
Redis: invalidate employee's leave balance cache
    │
    ▼
audit_log: { action: "leave_requested", entity_id: leave.id }
    │
    ▼
200 OK → UI: "Leave request submitted (Pending approval)"
    - Status badge appears on leave card
    - Monthly calendar updates with "Leave" marker on those dates
```

### Leave Application Form UI

```
┌──────────────────────────────────────────────────────┐
│  APPLY FOR LEAVE                                     │
├──────────────────────────────────────────────────────┤
│  Leave Type: [Paid ▼]                                │
│                                                      │
│  Start Date: [📅 Aug 18, 2025]                      │
│  End Date:   [📅 Aug 19, 2025]                      │
│  Days: 2                                              │
│                                                      │
│  Reason:                                             │
│  ┌────────────────────────────────────────────────┐ │
│  │ Personal work — need to handle some errands     │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Balance After: Paid 8→6 | Sick 5→5 | Unpaid ∞     │
│                                                      │
│  ┌─────────────────────┐                             │
│  │  Submit Leave Request │                            │
│  └─────────────────────┘                             │
├──────────────────────────────────────────────────────┤
│  YOUR LEAVE HISTORY                                  │
│  ┌──────────┬──────────┬────────┬──────────────┐    │
│  │ Dates    │ Type     │ Status │ Remarks      │    │
│  ├──────────┼──────────┼────────┼──────────────┤    │
│  │ Aug 11-12│ Medical  │ ✅ App │ Doctor appt  │    │
│  │ Jul 20   │ Paid     │ ❌ Rej │ Personal     │    │
│  └──────────┴──────────┴────────┴──────────────┘    │
└──────────────────────────────────────────────────────┘
```

### Overlapping Leave Prevention (DB-Level Safety)

```sql
-- PostgreSQL EXCLUSION CONSTRAINT — catches overlaps at database level
-- Even if application logic has a bug, the DB rejects overlapping leaves

CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE leave_requests ADD CONSTRAINT no_overlapping_leave
    EXCLUDE USING gist (
        employee_id WITH =,
        daterange(start_date, end_date, '[]') WITH &&
    )
    WHERE (status != 'rejected');
```

### Atomic Balance Deduction

```python
# Race-condition safe: atomic SQL UPDATE with condition
result = await db.execute(
    text("""
        UPDATE leave_balances
        SET used = used + :days
        WHERE employee_id = :emp_id
          AND year = :year
          AND leave_type = :leave_type
          AND (total - used) >= :days
        RETURNING id
    """),
    {"days": days, "emp_id": employee.id,
     "year": start_date.year, "leave_type": leave_type}
)
if not result.fetchone():
    raise HTTPException(409, "Insufficient leave balance or concurrent update")
```

**Cost:** Free. Standard PostgreSQL + browser calendar components.

---

## 8. Admin Employee Management

### What It Is
Admin can add, edit, soft-delete employees. Assign departments. View all attendance records. Switch between employees from one panel.

### Why It Exists
HR admins need a single control panel to manage the entire employee lifecycle: onboard new hires, update records, handle departures (soft-delete), and drill into any employee's attendance/leave/payroll data.

### How It Works — Data Flow

```
Admin navigates to /admin/employees
    │
    ▼
GET /employees?page=1&limit=20&department=engineering&search=rohan
    │
    ▼
FastAPI returns paginated employee list with:
    - Employee ID, Name, Department, Designation, Status (active/inactive)
    - Quick actions: View, Edit, Deactivate
    │
    ▼
Admin table with search, filter by department, sort by any column

---

Admin clicks "Add Employee":
    │
    ▼
Modal form: Name, Email, Employee ID, Department, Designation, Phone, Role
    │
    ▼
POST /employees { ... }
    │
    ▼
FastAPI:
    1. Create Clerk user account (via Clerk API)
    2. INSERT into employees table
    3. Initialize leave_balances for current year
    4. audit_log: { action: "employee_created" }
    │
    ▼
Resend: welcome email to new employee

---

Admin clicks "Edit" on employee row:
    │
    ▼
Full profile edit form (all fields editable)
    │
    ▼
PATCH /employees/{id} { ...allFields }
    │
    ▼
audit_log: { action: "employee_updated", old_values, new_values }

---

Admin clicks "Deactivate" (soft-delete):
    │
    ▼
PATCH /employees/{id}/deactivate
    │
    ▼
UPDATE employees SET is_active = FALSE
    │
    ▼
Clerk: disable user account (not delete — preserves audit trail)
    │
    ▼
audit_log: { action: "employee_deactivated" }

---

Admin switches employee context:
    │
    ▼
Admin dropdown: "Viewing as: Rohan Mehta [Switch ▼]"
    │
    ▼
Admin can see employee's dashboard, attendance, leave, payroll
    (read-only view — admin does not modify employee's data accidentally)
```

### Admin Employee Management UI

```
┌──────────────────────────────────────────────────────────────┐
│  EMPLOYEE MANAGEMENT                        [+ Add Employee] │
│  Search: [____________] Department: [All ▼] Status: [All ▼] │
├──────────────────────────────────────────────────────────────┤
│  Emp ID   │ Name          │ Dept        │ Status │ Actions  │
├───────────┼───────────────┼─────────────┼────────┼──────────┤
│  EMP-001  │ Rohan Mehta   │ Engineering │ 🟢 Act │ [👁][✏️][🔴]│
│  EMP-002  │ Priya Sharma  │ Design      │ 🟢 Act │ [👁][✏️][🔴]│
│  EMP-003  │ Amit Singh    │ Engineering │ 🟢 Act │ [👁][✏️][🔴]│
│  EMP-004  │ Neha Gupta    │ HR          │ 🔴 Ina │ [👁][✏️][🟢]│
└──────────────────────────────────────────────────────────────┘

👁 = View Profile  |  ✏️ = Edit  |  🔴 = Deactivate  |  🟢 = Reactivate
```

### Backend Code Outline

```python
# routers/employees.py
@router.post("/employees")
@admin_only
async def create_employee(
    payload: EmployeeCreateSchema,
    db=Depends(get_db), user=Depends(require_admin)
):
    # 1. Create Clerk user
    clerk_user = await clerk_client.users.create({
        "email_address": [payload.email],
        "password": generate_temp_password(),
        "public_metadata": {"role": payload.role}
    })

    # 2. Create employee record
    employee = Employee(
        clerk_id=clerk_user.id,
        employee_id=payload.employee_id,
        name=payload.name,
        email=payload.email,
        department=payload.department,
        designation=payload.designation,
        role=payload.role
    )
    db.add(employee)

    # 3. Initialize leave balances for current year
    for leave_type in ["paid", "sick", "unpaid"]:
        db.add(LeaveBalance(
            employee_id=employee.id, year=date.today().year,
            leave_type=leave_type,
            total=LEAVE_DEFAULTS[leave_type]
        ))

    await db.commit()
    await log_action(db, user["user_id"], "employee_created", entity_id=employee.id)
    await send_welcome_email(payload.email, payload.name)

    return {"success": True, "employee_id": str(employee.id)}

@router.get("/employees")
@admin_only
async def list_employees(
    page: int = 1, limit: int = 20,
    department: str = None, search: str = None,
    db=Depends(get_db), user=Depends(require_admin)
):
    query = select(Employee).where(Employee.is_active == True)
    if department:
        query = query.where(Employee.department == department)
    if search:
        query = query.where(Employee.name.ilike(f"%{search}%"))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
```

**Cost:** Free. Standard PostgreSQL + Clerk API (free tier).

---

# PART B — PERFORMANCE & SECURITY FEATURES

> These cross-cutting concerns ensure the HRMS performs well under load, validates all inputs, and maintains audit trails for compliance.

---

## 9. Redis Dashboard Caching

### What It Is
Dashboard summary data (attendance count, pending leaves, profile info) served from Redis with 60-second TTL. No database hit on page load. Cache invalidated on any mutation.

### Why It Exists
The dashboard is loaded on every login and refreshed frequently. Without caching, every page load hits PostgreSQL for multiple aggregate queries. Redis caching reduces DB read load by 80%+ and delivers sub-100ms response times.

### How It Works

```
GET /api/dashboard
    │
    ▼
Check Redis: dashboard:{user_id}:{role}
    │
    ├─ HIT → return cached JSON (< 10ms)
    │
    └─ MISS → query PostgreSQL:
        - Today's attendance status
        - Leave balance summary
        - Pending leave requests (if admin: all pending; if employee: own)
        - Recent activity (last 5 actions)
        - Burnout alerts (if admin: department alerts)
        │
        ▼
    Serialize to JSON → SET dashboard:{user_id}:{role} = data (TTL: 60s)
        │
        ▼
    Return data to frontend

---

On ANY mutation (leave request, check-in, profile edit, approval):
    │
    ▼
DELETE dashboard:{user_id}:{role} from Redis
    │
    ▼
Next dashboard load → cache miss → fresh data from PostgreSQL
```

### Cache Invalidation Strategy

| Mutation | Cache Key Invalidated |
|----------|----------------------|
| Check-in/out | `dashboard:{employee_id}:employee` |
| Leave request | `dashboard:{employee_id}:employee` + `dashboard:*:admin` |
| Leave approval | `dashboard:{employee_id}:employee` + `dashboard:*:admin` |
| Profile edit | `dashboard:{employee_id}:employee` |
| Salary update | `dashboard:{employee_id}:employee` + `dashboard:*:admin` |

### Backend Code Outline

```python
# services/cache.py
import json
import redis.asyncio as aioredis

DASHBOARD_TTL = 60  # seconds

async def get_dashboard_cache(redis: aioredis.Redis, user_id: str, role: str):
    key = f"dashboard:{user_id}:{role}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    return None

async def set_dashboard_cache(redis: aioredis.Redis, user_id: str, role: str, data: dict):
    key = f"dashboard:{user_id}:{role}"
    await redis.setex(key, DASHBOARD_TTL, json.dumps(data))

async def invalidate_dashboard_cache(redis: aioredis.Redis, user_id: str):
    # Invalidate employee cache
    await redis.delete(f"dashboard:{user_id}:employee")
    # Invalidate all admin caches (pattern delete)
    keys = await redis.keys("dashboard:*:admin")
    if keys:
        await redis.delete(*keys)
```

### Dashboard Router with Caching

```python
# routers/dashboard.py
@router.get("/api/dashboard")
async def get_dashboard(
    db=Depends(get_db), redis=Depends(get_redis), user=Depends(get_current_user)
):
    # Check cache first
    cached = await get_dashboard_cache(redis, user["user_id"], user["role"])
    if cached:
        return cached

    # Build fresh data
    employee = await get_employee(db, user["user_id"])
    data = {
        "attendance_today": await get_today_attendance(db, employee.id),
        "leave_balance": await get_leave_balances(db, employee.id),
        "recent_activity": await get_recent_activity(db, employee.id, limit=5),
    }

    if user["role"] == "admin":
        data["pending_leaves"] = await count_pending_leaves(db)
        data["total_employees"] = await count_active_employees(db)
        data["burnout_alerts"] = await get_burnout_alerts(db, employee.department)

    # Cache for 60 seconds
    await set_dashboard_cache(redis, user["user_id"], user["role"], data)
    return data
```

**Cost:** Free. Redis already in stack. TTL-based invalidation requires no external pub/sub.

---

## 10. Input Validation — Pydantic v2

### What It Is
Every API request body validated with Pydantic v2 schemas. SQL injection impossible via SQLAlchemy parameterized queries. XSS prevented at Zod layer on frontend.

### Why It Exists
Input validation is the first line of defense against malformed data, injection attacks, and business logic errors. Pydantic v2 (compiled with Rust core) provides 5-50x faster validation than v1 while enforcing strict type safety.

### Validation Layers

```
User Input
    │
    ▼
Layer 1: Frontend — Zod schemas (client-side)
    - Form fields validated before submission
    - Invalid data never leaves the browser
    - XSS prevented by React's automatic escaping
    │
    ▼
Layer 2: FastAPI — Pydantic v2 schemas (server-side)
    - Every request body validated against typed schema
    - Type coercion enforced (no implicit string→int)
    - Extra fields rejected by default
    │
    ▼
Layer 3: Database — SQLAlchemy ORM + PostgreSQL
    - Parameterized queries (no raw SQL interpolation)
    - UNIQUE constraints prevent duplicates
    - CHECK constraints enforce valid values
    - EXCLUSION constraints prevent overlaps
```

### Pydantic Schema Examples

```python
# schemas/leave.py
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from enum import Enum

class LeaveType(str, Enum):
    paid = "paid"
    sick = "sick"
    unpaid = "unpaid"
    bereavement = "bereavement"
    medical = "medical"

class LeaveCreateSchema(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    remarks: Optional[str] = Field(None, max_length=500)

    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v, info):
        if v < info.data.get("start_date"):
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator("remarks")
    @classmethod
    def no_html_tags(cls, v):
        if v and ("<script" in v.lower() or "<" in v):
            raise ValueError("HTML tags not allowed in remarks")
        return v

class LeaveApprovalSchema(BaseModel):
    status: Literal["approved", "rejected"]
    comment: Optional[str] = Field(None, max_length=1000)

class CheckInSchema(BaseModel):
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
```

### SQLAlchemy Parameterized Queries (SQL Injection Prevention)

```python
# SAFE — parameterized query
result = await db.execute(
    text("SELECT * FROM employees WHERE department = :dept AND is_active = :active"),
    {"dept": "engineering", "active": True}
)

# NEVER — raw string interpolation (VULNERABLE)
# result = await db.execute(text(f"SELECT * FROM employees WHERE department = '{dept}'"))
```

**Cost:** Free. Pydantic v2 and SQLAlchemy are open-source libraries.

---

## 11. DB Query Optimization

### What It Is
Composite indexes on all high-frequency queries. EXPLAIN ANALYZE tested before submission. Cursor-based pagination on all list endpoints.

### Why It Exists
As employee count grows, unoptimized queries become the #1 performance bottleneck. A 100ms query on 10 employees becomes a 10-second query on 10,000 employees without proper indexes.

### Composite Indexes

```sql
-- High-frequency queries and their optimal indexes

-- Attendance lookup: employee + date range
CREATE INDEX idx_attendance_emp_date
    ON attendance_records (employee_id, date DESC);

-- Leave requests: status filtering + date range
CREATE INDEX idx_leave_status_date
    ON leave_requests (status, start_date)
    WHERE status = 'pending';

-- Payroll: employee + month/year
CREATE INDEX idx_payroll_emp_period
    ON payroll_runs (employee_id, year, month DESC);

-- Salary components: current effective components
CREATE INDEX idx_salary_emp_effective
    ON salary_components (employee_id, effective_from DESC);

-- Audit log: actor lookup + timestamp
CREATE INDEX idx_audit_actor_time
    ON audit_log (actor_id, created_at DESC);

-- Burnout alerts: unresolved alerts per department
CREATE INDEX idx_burnout_active
    ON burnout_alerts (employee_id, created_at DESC)
    WHERE resolved = FALSE;

-- Leave balances: current year per employee
CREATE INDEX idx_leave_balance_current
    ON leave_balances (employee_id, year, leave_type);
```

### Cursor-Based Pagination

```python
# Instead of OFFSET pagination (slow on large tables):
# BAD: SELECT * FROM employees ORDER BY name LIMIT 20 OFFSET 1000
# GOOD: cursor-based pagination

@router.get("/employees")
async def list_employees(
    cursor: Optional[str] = None,  # base64-encoded last seen ID + name
    limit: int = 20,
    db=Depends(get_db)
):
    query = select(Employee).order_by(Employee.name)

    if cursor:
        decoded = json.loads(base64.b64decode(cursor))
        query = query.where(
            (Employee.name > decoded["name"]) |
            (Employee.name == decoded["name"], Employee.id > decoded["id"])
        )

    results = (await db.execute(query.limit(limit + 1))).scalars().all()

    has_next = len(results) > limit
    items = results[:limit]
    next_cursor = None
    if has_next:
        last = items[-1]
        next_cursor = base64.b64encode(
            json.dumps({"id": str(last.id), "name": last.name}).encode()
        ).decode()

    return {"items": items, "next_cursor": next_cursor, "has_next": has_next}
```

### EXPLAIN ANALYZE Testing

```sql
-- Before submitting any query, always verify with EXPLAIN ANALYZE:

EXPLAIN ANALYZE
SELECT ar.* FROM attendance_records ar
WHERE ar.employee_id = 'some-uuid'
  AND ar.date BETWEEN '2025-08-01' AND '2025-08-31'
ORDER BY ar.date DESC;

-- Look for:
-- ✓ Index Scan (not Seq Scan)
-- ✓ Actual rows ≈ Estimated rows
-- ✓ No nested loops on large tables
-- ✓ Execution time < 10ms for typical queries
```

**Cost:** Free. PostgreSQL indexing is built-in.

---

## 12. Aggregated Dashboard API

### What It Is
Single `GET /api/dashboard` endpoint returns everything in one JSON. No waterfall API calls from frontend. TanStack Query caches it client-side too.

### Why It Exists
Waterfall API calls (fetch attendance, then leave balance, then pending leaves, then profile) multiply latency. If each takes 100ms, four sequential calls take 400ms+. A single aggregated endpoint returns all data in one roundtrip at ~150ms.

### How It Works

```
Frontend loads dashboard
    │
    ▼
Single API call: GET /api/dashboard
    │
    ▼
FastAPI fans out queries in parallel (asyncio.gather):
    ├─ AttendanceService.get_today_status()     ─┐
    ├─ LeaveService.get_balances()               │ parallel
    ├─ LeaveService.get_pending_count()          │ (all run
    ├─ EmployeeService.get_profile()             │ concurrently)
    ├─ ActivityService.get_recent(limit=5)      ─┘
    │
    ▼
All results merged into single JSON response:
    {
      "attendance": { "status": "present", "check_in": "09:02", "check_out": null },
      "leave_balance": { "paid": {"total": 12, "used": 4}, "sick": {"total": 10, "used": 5} },
      "pending_requests": 0,
      "recent_activity": [...],
      "profile": { "name": "Rohan", "dept": "Engineering" }
    }
    │
    ▼
TanStack Query caches with staleTime: 60_000 (1 minute)
    │
    ▼
On mutation (check-in, leave request, etc.):
    qc.invalidateQueries({ queryKey: ["dashboard"] })
    → triggers fresh fetch
```

### Backend Implementation

```python
# routers/dashboard.py
import asyncio

@router.get("/api/dashboard")
async def get_dashboard(db=Depends(get_db), redis=Depends(get_redis),
                        user=Depends(get_current_user)):
    # Check cache
    cached = await get_dashboard_cache(redis, user["user_id"], user["role"])
    if cached:
        return cached

    employee = await get_employee(db, user["user_id"])

    # Fan out — all queries run concurrently
    results = await asyncio.gather(
        get_today_attendance(db, employee.id),
        get_leave_balances(db, employee.id),
        get_pending_leaves_count(db) if user["role"] == "admin" else async_return(0),
        get_recent_activity(db, employee.id, limit=5),
        get_active_employees_count(db) if user["role"] == "admin" else async_return(0),
        return_exceptions=True  # don't fail entire dashboard if one query fails
    )

    data = {
        "attendance": results[0] if not isinstance(results[0], Exception) else None,
        "leave_balance": results[1] if not isinstance(results[1], Exception) else None,
        "pending_leaves": results[2] if not isinstance(results[2], Exception) else 0,
        "recent_activity": results[3] if not isinstance(results[3], Exception) else [],
        "total_employees": results[4] if not isinstance(results[4], Exception) else 0,
    }

    await set_dashboard_cache(redis, user["user_id"], user["role"], data)
    return data
```

### Frontend Integration

```typescript
// hooks/useDashboard.ts
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch<DashboardData>("/api/dashboard"),
    staleTime: 60_000,      // serve from cache for 60s
    refetchOnWindowFocus: true,  // refresh when user returns to tab
  });
}
```

**Cost:** Free. Single query + Redis cache + TanStack Query client cache.

---

## 13. Audit Logging

### What It Is
Every admin action (approve leave, change salary, edit profile) writes to audit logs. Old and new values stored. Immutable. Used for compliance reporting.

### Why It Exists
Audit logs are legally required in many jurisdictions for HR systems. They provide an immutable trail of who changed what, when, and why. Essential for compliance, dispute resolution, and security investigations.

### What Gets Logged

| Action | Who | Data Stored |
|--------|-----|-------------|
| `leave_requested` | Employee | leave details, email_sent |
| `leave_approved` / `leave_rejected` | Admin | old_status, new_status, comment |
| `leave_cancelled` | Employee | old_status, balance_recredited |
| `check_in` | Employee | lat, lng, method |
| `check_out` | Employee | duration |
| `profile_updated` | Employee | old_values, new_values |
| `admin_profile_edit` | Admin | old_values, new_values |
| `salary_updated` | Admin | old_components, new_components |
| `employee_created` | Admin | employee_id, department |
| `employee_deactivated` | Admin | employee_id |
| `payroll_generated` | System | month, year, net_pay |
| `pay_stub_generated` | System | employee_id, file_path |

### Database Schema

```sql
CREATE TABLE audit_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id     UUID REFERENCES employees(id),
    action       VARCHAR(100) NOT NULL,
    entity_type  VARCHAR(50),
    entity_id    UUID,
    metadata     JSONB,       -- { "old_status": "pending", "new_status": "approved" }
    ip_address   VARCHAR(50),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_audit_entity ON audit_log (entity_type, entity_id);
CREATE INDEX idx_audit_actor ON audit_log (actor_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log (action, created_at DESC);
```

### Backend Implementation

```python
# services/audit.py
async def log_action(
    db: AsyncSession,
    actor_id: UUID,
    action: str,
    entity_type: str = None,
    entity_id: UUID = None,
    metadata: dict = None,
    ip_address: str = None
):
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
        ip_address=ip_address
    )
    db.add(entry)
    # No separate commit — included in the calling transaction
    # This ensures audit log is written atomically with the mutation
```

### Admin Audit Log Viewer

```
┌──────────────────────────────────────────────────────────────┐
│  AUDIT LOG                                   [Filter ▼]     │
├──────────────────────────────────────────────────────────────┤
│  Timestamp           │ Actor       │ Action      │ Details  │
├──────────────────────┼─────────────┼─────────────┼──────────┤
│  Aug 15, 2:30 PM     │ Admin User  │ leave_appro │ Priya S. │
│                      │             │             │ approved │
│  Aug 15, 11:15 AM    │ Rohan M.    │ check_in    │ GPS, 9:02│
│  Aug 14, 4:45 PM     │ Admin User  │ salary_upd  │ Basic ↑  │
│  Aug 14, 9:30 AM     │ Priya S.    │ leave_req   │ Sick 2d  │
└──────────────────────┴─────────────┴─────────────┴──────────┘
```

**Cost:** Free. Single PostgreSQL table + indexes.

---

## 14. Async FastAPI Throughout

### What It Is
All DB calls use asyncpg via SQLAlchemy async. All Redis calls async. No blocking I/O. Handles concurrent requests without thread starvation.

### Why It Exists
Blocking I/O in a synchronous framework means each request holds a thread while waiting for DB/Redis responses. Under load, threads are exhausted and requests queue. Async FastAPI handles thousands of concurrent requests with minimal threads because threads are released during I/O waits.

### Async Architecture

```
Request arrives at FastAPI
    │
    ▼
AsyncIO event loop picks a free thread
    │
    ▼
Route handler executes:
    │
    ├─ await db.execute(...)        → thread released during DB I/O
    ├─ await redis.get(...)         → thread released during Redis I/O
    ├─ await httpx.get(ollama)      → thread released during HTTP I/O
    │
    ▼
All I/O completes → event loop resumes handler
    │
    ▼
Response sent → thread freed for next request
```

### Async Stack Components

```python
# core/database.py — async SQLAlchemy engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://hrms:password@postgres:5432/hrms_db",
    pool_size=20,
    max_overflow=10
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# core/redis.py — async Redis
import redis.asyncio as aioredis

redis_pool = aioredis.ConnectionPool.from_url("redis://redis:6379/0", max_connections=20)
redis_client = aioredis.Redis(connection_pool=redis_pool)

# routers/attendance.py — fully async
@router.post("/attendance/checkin")
async def check_in(
    payload: CheckInSchema,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user=Depends(get_current_user)
):
    # All operations are non-blocking
    employee = await get_employee(db, user["user_id"])           # async DB
    cached = await redis.exists(f"checkin:{employee.id}:{today}")  # async Redis
    async with httpx.AsyncClient() as client:                     # async HTTP
        resp = await client.post("http://ollama:11434/api/generate", ...)
```

### Concurrency Benefits

| Scenario | Sync (Thread-per-req) | Async (FastAPI) |
|----------|----------------------|-----------------|
| 100 concurrent check-ins | Needs 100 threads | Needs ~4 threads |
| DB query latency | Blocks thread (100ms) | Releases thread |
| Redis cache hit | Blocks thread (5ms) | Releases thread |
| Memory per connection | ~8MB (thread stack) | ~8KB (coroutine) |
| Max practical concurrency | ~200 requests | ~10,000 requests |

### Background Tasks (Non-Blocking)

```python
# APScheduler runs inside async event loop — no blocking
scheduler = AsyncIOScheduler()

# These jobs run asynchronously:
scheduler.add_job(check_burnout, "cron", hour=2)           # nightly
scheduler.add_job(run_monthly_payroll, "cron", day="last")  # monthly
scheduler.add_job(send_nudge_checks, "cron", hour=8)       # morning
```

**Cost:** Free. FastAPI + asyncpg + redis.asyncio are all open-source.

---

# PART C — CREATIVE DIFFERENTIATOR FEATURES (AI-POWERED)

> These features sit on top of the core HRMS. Each one is documented with:
> **What it is → Why it exists → How it works → Data flow → Tech used → Free/cost → Code outline**

---

## 15. Conversational Leave (NLP Multi-Turn)

### What It Is
Instead of filling a form, the employee types naturally — like texting — and the system understands and builds the leave request in real time through back-and-forth conversation. It is NOT a one-shot form. It is a multi-turn chat flow powered by Llama 3 running locally via Ollama.

### Why It Exists
Employees often don't know exactly which leave type to pick, or forget to add dates. A conversation guides them step by step without making them think about form fields.

### Example Conversation
```
Employee: "I need a few days off next week for a doctor thing"

AI: "Got it! Is this a medical appointment or a longer recovery period?
     Also, do you mean Monday Aug 11 to Friday Aug 15, or specific days?"

Employee: "Just Monday and Tuesday, doctor + rest"

AI: "Perfect — I'll file this as Medical Leave for Aug 11–12 (2 days).
     You have 6 sick leave days remaining. Shall I submit this and
     also send a formal email to HR?"

Employee: "Yes go ahead"

AI: "Done! Leave request submitted (Pending approval) and HR has
     been notified via email. Reference ID: LR-2025-0847"
```

### How It Works — Data Flow

```
Employee types message in ConversationalLeave chat UI
    │
    ▼
POST /nlp/chat  { message, conversation_history[] }
    │
    ▼
FastAPI: routers/nlp.py
    Build context prompt:
      - Employee name, department
      - Current leave balances
      - Existing leave dates (to avoid overlap)
      - Conversation history (last 10 turns)
    │
    ▼
Ollama (Llama 3) generates response + extracts intent
    Returns JSON:
    {
      "reply": "...",           ← text shown to employee
      "intent": "confirm_submit" | "ask_dates" | "ask_type" | "idle",
      "extracted": {
        "start_date": "2025-08-11",
        "end_date": "2025-08-12",
        "leave_type": "medical",
        "ready_to_submit": true
      }
    }
    │
    ▼
If intent == "confirm_submit" and employee said yes:
    → POST /leave (atomic balance deduction)
    → Resend email to HR
    → Return confirmation with leave ID
    │
    ▼
Frontend updates chat bubble with AI reply
Conversation history stored in React state (Zustand)
```

### Backend Code Outline

```python
# routers/nlp.py

CONVERSATION_PROMPT = """
You are an HR assistant helping an employee apply for leave conversationally.

Employee Info:
- Name: {name}
- Department: {department}
- Leave Balances: {balances}
- Already booked leave dates: {existing_leaves}

Conversation so far:
{history}

Latest message from employee: "{message}"

Your job:
1. Reply naturally and helpfully (under 60 words)
2. Extract any leave details mentioned
3. When you have enough info (dates + type), summarize and ask for confirmation
4. When confirmed, set ready_to_submit: true

Respond ONLY in this JSON format:
{
  "reply": "...",
  "intent": "ask_dates|ask_type|ask_confirm|confirm_submit|idle",
  "extracted": {
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "leave_type": "paid|sick|unpaid|medical|bereavement or null",
    "ready_to_submit": true|false
  }
}
"""

@router.post("/nlp/chat")
async def conversational_leave(
    payload: ConversationPayload,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    employee = await get_employee(db, user["user_id"])
    balances = await get_leave_balances(db, employee.id)
    existing = await get_upcoming_leaves(db, employee.id)

    prompt = CONVERSATION_PROMPT.format(
        name=employee.name,
        department=employee.department,
        balances=balances,
        existing_leaves=existing,
        history="\n".join([f"{m['role']}: {m['content']}" for m in payload.history]),
        message=payload.message
    )

    result = await call_ollama(prompt)

    # Auto-submit if AI says ready and employee confirmed
    if result["extracted"]["ready_to_submit"] and result["intent"] == "confirm_submit":
        leave_id = await auto_submit_leave(db, employee, result["extracted"])
        await send_leave_email(employee, result["extracted"])
        result["reply"] += f" Reference ID: LR-{leave_id[:8].upper()}"

    return result
```

### Frontend Component

```typescript
// components/features/leave/ConversationalLeave.tsx
"use client";
import { useState } from "react";

interface Message { role: "user" | "assistant"; content: string; }

export function ConversationalLeave() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hi! Tell me about the leave you need — I'll take care of the rest." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: "user", content: input };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    const res = await apiFetch<{ reply: string }>("/nlp/chat", {
      method: "POST",
      body: JSON.stringify({ message: input, history: messages })
    });

    if (res.success) {
      setMessages([...newHistory, { role: "assistant", content: res.data.reply }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-[500px] border rounded-xl overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm
              ${m.role === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-800"}`}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && <div className="text-xs text-gray-400 italic">HR Assistant is typing...</div>}
      </div>
      <div className="flex gap-2 p-3 border-t">
        <input className="flex-1 border rounded-lg px-3 py-2 text-sm"
          value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Tell me about your leave..." />
        <button onClick={send} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">Send</button>
      </div>
    </div>
  );
}
```

**Cost:** Free (Ollama + Llama 3, self-hosted)

---

## 16. HR Chatbot

### What It Is
A RAG-lite question-answering bot for employees. It answers HR-related questions grounded in the employee's actual data from PostgreSQL — not generic answers. It lives in a chat bubble in the employee dashboard.

### What It Can Answer
- "How many sick leaves do I have left this year?"
- "What is my current net salary?"
- "When was I last marked absent?"
- "What is the company's bereavement leave policy?"
- "When does my annual leave balance reset?"
- "Has my leave request from last Monday been approved?"

### How It Works

```
Employee types question in chat bubble
    │
    ▼
POST /chatbot/ask  { question }
    │
    ▼
FastAPI fetches context from DB for this employee:
  - leave_balances (all types, current year)
  - last 30 attendance_records
  - pending/recent leave_requests
  - salary_components (current)
  - payroll_runs (last 3 months)
    │
    ▼
Builds grounded prompt (employee data injected)
    │
    ▼
Ollama (Mistral 7B — faster for Q&A) answers
    │
    ▼
Response shown in chat bubble
No data is fabricated — only answers from actual DB values
```

### Backend Code Outline

```python
# routers/chatbot.py

HR_CHATBOT_PROMPT = """
You are a helpful HR assistant. Answer the employee's question using ONLY
the data provided below. If the answer is not in the data, say
"I don't have that information — please contact HR directly."

Employee: {name} | Dept: {department}

Leave Balances This Year:
{leave_balances}

Recent Attendance (last 30 days):
{attendance_summary}

Recent Leave Requests:
{leave_requests}

Current Salary Components:
{salary_components}

Company Leave Policy:
- Paid Leave: 12 days/year
- Sick Leave: 10 days/year
- Unpaid Leave: unlimited (unpaid)
- Bereavement: 5 days/year
- Balances reset every January 1

Employee's Question: "{question}"

Answer in 2-3 sentences max. Be direct and friendly.
"""

@router.post("/chatbot/ask")
async def chatbot_ask(payload: ChatbotPayload, db=Depends(get_db), user=Depends(get_current_user)):
    # Check Redis cache first
    cache_key = f"chatbot_context:{user['user_id']}"
    context = await redis.get(cache_key)

    if not context:
        employee = await get_employee(db, user["user_id"])
        context = {
            "name": employee.name,
            "department": employee.department,
            "leave_balances": await get_leave_balances(db, employee.id),
            "attendance_summary": await get_attendance_summary(db, employee.id, days=30),
            "leave_requests": await get_recent_leaves(db, employee.id, limit=5),
            "salary_components": await get_salary_components(db, employee.id),
        }
        await redis.setex(cache_key, 300, json.dumps(context))  # cache 5 min
    else:
        context = json.loads(context)

    prompt = HR_CHATBOT_PROMPT.format(**context, question=payload.question)
    answer = await call_ollama(prompt, model="mistral")
    return {"answer": answer}
```

**Cost:** Free (Ollama + Mistral 7B, self-hosted)

---

## 17. Voice Check-In & Voice Commands

### What It Is
Tier 1 voice feature — uses the browser's built-in Web Speech API. No server involved. Employee speaks a command and the app responds instantly. Works offline (no API call for recognition).

### Supported Commands

| Voice Command | Action Triggered |
|--------------|-----------------|
| "Check me in" | Fires POST /attendance/checkin |
| "Check me out" | Fires POST /attendance/checkout |
| "Show my attendance" | Navigates to /attendance |
| "Apply for leave" | Opens leave form modal |
| "What's my leave balance" | Opens HR chatbot with pre-filled question |
| "Show my salary" | Navigates to /payroll |

### How It Works

```
Employee clicks mic button (or it's always listening — admin-configurable)
    │
    ▼
Browser SpeechRecognition API activates (no server call)
    │
    ▼
Speech captured as text transcript (runs entirely in browser)
    │
    ▼
useVoiceCommand() hook pattern-matches transcript against command list
    │
    ▼
Matching action dispatched (API call or navigation)
    │
    ▼
Visual feedback: animated mic icon + transcript shown briefly
    │
    ▼
Text-to-speech confirmation spoken back:
  "Checked in at 9:14 AM" (using browser SpeechSynthesis API)
```

### Frontend Hook

```typescript
// hooks/useVoiceCommand.ts
"use client";
import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

type CommandMap = { [pattern: string]: () => void };

export function useVoiceCommand(commands: CommandMap) {
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!("SpeechRecognition" in window || "webkitSpeechRecognition" in window)) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SR();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.toLowerCase().trim();
      for (const [pattern, action] of Object.entries(commands)) {
        if (transcript.includes(pattern)) {
          action();
          speak(`Command received: ${pattern}`);
          break;
        }
      }
    };

    recognitionRef.current = recognition;
  }, []);

  const speak = (text: string) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.1;
    window.speechSynthesis.speak(utterance);
  };

  return {
    startListening: () => recognitionRef.current?.start(),
    stopListening: () => recognitionRef.current?.stop(),
    speak,
  };
}

// Usage in AttendancePage:
const { startListening } = useVoiceCommand({
  "check me in": () => checkInMutation.mutate(),
  "check me out": () => checkOutMutation.mutate(),
  "apply for leave": () => setLeaveModalOpen(true),
  "show my attendance": () => router.push("/attendance"),
});
```

**Cost:** Completely free. Browser API. Zero server calls.

---

## 18. Voice-to-Leave (Audio Leave Application)

### What It Is
Tier 2 voice feature — the employee records a voice memo describing their leave situation. The audio is sent to a self-hosted Whisper server, transcribed to text, then Llama 3 parses the dates, reason, and leave type from the transcript, and pre-fills the leave form automatically.

### Example
```
Employee records: "Hi, I need to take leave from the 15th to the 18th of August.
                  My mother is unwell and I need to take her to the hospital
                  and stay with her for a few days."

Whisper transcribes → exact text above

Llama 3 parses → {
  "start_date": "2025-08-15",
  "end_date": "2025-08-18",
  "leave_type": "medical",
  "reason": "Family medical emergency - mother hospitalisation",
  "days": 4
}

Leave form auto-filled → Employee reviews → Submits
```

### Data Flow

```
Employee clicks "Apply by Voice" button
    │
    ▼
Browser MediaRecorder API starts recording (WAV/WebM)
    │
    ▼
Employee speaks → clicks stop
    │
    ▼
Audio blob → FormData
    │
    ▼
POST /voice/transcribe (multipart/form-data)
    │
    ▼
FastAPI: file_validator.py
    - MIME check: audio/wav, audio/mpeg, audio/webm only
    - Size check: max 10MB
    - ClamAV scan
    │
    ▼
POST to Whisper container (http://whisper:9000/asr)
    Returns: { "text": "I need to take leave from..." }
    │
    ▼
POST /nlp/parse-leave-from-transcript { transcript }
    │
    ▼
Ollama (Llama 3) extracts structured leave data from free text
    Returns: { start_date, end_date, leave_type, reason, days }
    │
    ▼
Frontend receives parsed data
    → Pre-fills leave form fields
    → Employee reviews and corrects if needed
    → Clicks submit
```

### Backend Code

```python
# routers/voice.py
@router.post("/voice/transcribe")
async def transcribe_voice(file: UploadFile, user=Depends(get_current_user)):
    await validate_file(file, allowed_types={"audio/wav","audio/mpeg","audio/webm"}, max_mb=10)

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "http://whisper:9000/asr?language=en&output=json",
            files={"audio_file": (file.filename, await file.read(), file.content_type)}
        )
    transcript = resp.json().get("text", "")

    # Parse with Ollama
    parse_prompt = f"""
    Extract leave details from this voice message. Return ONLY valid JSON.
    Voice message: "{transcript}"

    JSON format:
    {{
      "start_date": "YYYY-MM-DD or null",
      "end_date": "YYYY-MM-DD or null",
      "leave_type": "paid|sick|medical|bereavement|unpaid or null",
      "reason": "one sentence summary",
      "days": number or null
    }}
    Use today's date as reference: {date.today().isoformat()}
    """

    parsed = await call_ollama(parse_prompt)
    return {"transcript": transcript, "parsed": parsed}
```

**Cost:** Free. Whisper Docker (onerahmet/openai-whisper-asr-webservice), Ollama (self-hosted).

---

## 19. Attendance Heatmap & Calendar

### What It Is
A GitHub-style contribution heatmap showing an employee's attendance pattern over the year, plus a monthly calendar view with color-coded daily status. Admins see it for all employees. Employees see only their own.

### Heatmap Visual Design

```
Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
 ██   ██   ░░   ██   ██   ██   ██   ░░   ██   ██   ██   ██
 ██   ██   ██   ██   ██   ██   ░░   ██   ██   ██   ██   ██
 ...

Legend:
██ Dark green  = Present
░░ Light green = Half-day
■■ Yellow      = Leave (approved)
░░ Red         = Absent
   White       = Weekend / Holiday
```

### Calendar View (Monthly)

```
        August 2025
Mo  Tu  We  Th  Fr  Sa  Su
                 1   2   3
[P] [P] [P] [P] [P]  ─   ─     P = Present (green)
[P] [P] [A] [P] [P]  ─   ─     A = Absent (red)
[L] [L] [P] [P] [P]  ─   ─     L = Leave (blue)
[P] [H] [P] [P] [P]  ─   ─     H = Half-day (orange)
[P] [P] [P]
```

### Data Flow

```
GET /attendance/heatmap?year=2025  (employee) or
GET /attendance/heatmap?employee_id=...&year=2025  (admin)
    │
    ▼
FastAPI queries attendance_records for the full year
    │
    ▼
Aggregates into { date: status } map (365 entries)
    │
    ▼
Redis caches result: key = heatmap:{employee_id}:{year}
TTL = 1 hour (invalidated on any new attendance record)
    │
    ▼
Frontend AttendanceHeatmap.tsx renders SVG grid
Each cell colored by status
Tooltip on hover: "Aug 13 — Present | Check-in: 9:02 AM | Check-out: 6:15 PM"
```

### Frontend Component

```typescript
// components/features/attendance/AttendanceHeatmap.tsx
const STATUS_COLORS = {
  present: "#22c55e",
  absent: "#ef4444",
  "half-day": "#f97316",
  leave: "#3b82f6",
  holiday: "#e5e7eb",
  weekend: "#f9fafb",
};

export function AttendanceHeatmap({ data }: { data: Record<string, string> }) {
  const weeks = buildWeekGrid(data); // groups dates into 53 weeks × 7 days

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${53 * 14} ${7 * 14}`} className="w-full">
        {weeks.map((week, wi) =>
          week.map((day, di) => (
            <rect
              key={`${wi}-${di}`}
              x={wi * 14} y={di * 14}
              width={12} height={12} rx={2}
              fill={day ? STATUS_COLORS[day.status] : STATUS_COLORS.weekend}
              className="cursor-pointer hover:opacity-80"
            >
              <title>{day ? `${day.date} — ${day.status}` : "Weekend"}</title>
            </rect>
          ))
        )}
      </svg>
      {/* Legend */}
      <div className="flex gap-4 mt-2 text-xs text-gray-500">
        {Object.entries(STATUS_COLORS).map(([label, color]) => (
          <span key={label} className="flex items-center gap-1">
            <span style={{ background: color }} className="w-3 h-3 rounded-sm inline-block" />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
```

**Cost:** Free. Pure frontend SVG rendering. Backend is a simple DB query.

---

## 20. Burnout Early Warning System

### What It Is
An intelligent early warning system that monitors each employee's work patterns and fires proactive alerts to HR before burnout becomes a crisis. Goes beyond simple consecutive-day counting — looks at multiple signals.

### Burnout Signals Monitored

| Signal | Threshold (configurable per dept) | Severity |
|--------|----------------------------------|----------|
| Consecutive working days without break | > 14 days | 🔴 High |
| Weekly overtime hours | > 10 hrs/week for 3 weeks | 🟠 Medium |
| Check-in before 7 AM + check-out after 9 PM pattern | 5+ days in a row | 🔴 High |
| Absence spike after long stretch | Sudden absent/sick after 10+ day streak | 🟡 Watch |
| Leave balance never used (annual) | 0 leave taken by September | 🟡 Watch |
| Repeated half-days | 6+ half-days in a month | 🟠 Medium |

### How It Works

```
APScheduler fires nightly at 2 AM
    │
    ▼
For each department → read burnout_config (thresholds)
    │
    ▼
For each active employee in dept:
    attendance_analytics.py computes all 6 signals
    │
    ▼
If ANY signal breaches threshold:
    → INSERT burnout_alerts table
    → Resend email to HR + department head
    → Redis flag set: burnout_alert:{employee_id} = true
    │
    ▼
Admin burnout dashboard shows:
    - Alert severity badge per employee
    - Which signal triggered it
    - Trend chart (is it getting better or worse?)
    │
    ▼
Optional: Employee gets a gentle in-app nudge
(see Proactive Nudge System — Feature 11)
```

### Backend Service

```python
# services/attendance_analytics.py

async def compute_burnout_signals(db, employee_id: UUID, config: BurnoutConfig) -> list[BurnoutAlert]:
    alerts = []
    records = await get_attendance_records(db, employee_id, days=90)

    # Signal 1: Consecutive working days
    consecutive = count_max_consecutive_present(records)
    if consecutive >= config.max_consecutive_days:
        alerts.append(BurnoutAlert(
            signal="consecutive_days",
            value=consecutive,
            threshold=config.max_consecutive_days,
            severity="high"
        ))

    # Signal 2: Weekly overtime
    for week in get_weekly_groups(records):
        overtime = sum_overtime_hours(week)
        if overtime > config.max_weekly_overtime_hrs:
            alerts.append(BurnoutAlert(
                signal="weekly_overtime",
                value=overtime,
                threshold=config.max_weekly_overtime_hrs,
                severity="medium"
            ))

    # Signal 3: Late night + early morning pattern
    extreme_hours = count_extreme_hour_days(records, before_hour=7, after_hour=21)
    if extreme_hours >= 5:
        alerts.append(BurnoutAlert(signal="extreme_hours", value=extreme_hours, severity="high"))

    # Signal 4: Leave balance never used
    balance = await get_leave_balance(db, employee_id, "paid")
    if date.today().month >= 9 and balance.used == 0:
        alerts.append(BurnoutAlert(signal="leave_not_taken", severity="watch"))

    return alerts


async def check_burnout():
    """Called by APScheduler nightly"""
    async with AsyncSession(engine) as db:
        configs = await db.execute(select(BurnoutConfig))
        for config in configs.scalars():
            employees = await get_employees_by_department(db, config.department)
            for emp in employees:
                alerts = await compute_burnout_signals(db, emp.id, config)
                if alerts:
                    await save_burnout_alerts(db, emp.id, alerts)
                    await notify_hr_burnout(emp, alerts, config.alert_email)
```

### Admin Burnout Dashboard View

```
┌─────────────────────────────────────────────────────────┐
│  BURNOUT EARLY WARNING — Engineering Department         │
├─────────────────────────────────────────────────────────┤
│  🔴 Rohan Mehta       18 consecutive days    HIGH       │
│     ↳ Also: 2 weeks of late-night check-outs            │
│     [Send Nudge] [Schedule 1:1] [Approve Leave Now]     │
├─────────────────────────────────────────────────────────┤
│  🟠 Priya Sharma       12 hrs overtime/week  MEDIUM     │
│     ↳ 3 weeks running                                   │
│     [Send Nudge] [View Attendance]                      │
├─────────────────────────────────────────────────────────┤
│  🟡 Amit Singh         0 leaves taken (Sep)  WATCH      │
│     [Send Nudge]                                        │
└─────────────────────────────────────────────────────────┘
```

**Cost:** Free. APScheduler + PostgreSQL analytics + Resend (100 emails/day free).

---

## 21. Live Salary Simulator

### What It Is
An interactive tool in the employee's payroll section where they can adjust hypothetical salary components (like bonus, HRA, tax slab) using sliders and see how their net take-home pay changes in real time — all computed client-side, no server call needed.

### Why It Exists
Employees always ask "what if I get a 10% raise?" or "how much tax will I pay if my salary is X?" This lets them explore without bothering HR.

### What Can Be Simulated
- Basic salary adjustment (slider)
- HRA percentage change
- Performance bonus addition (one-time or monthly)
- Standard deduction impact
- Tax slab preview (basic slab ranges shown)
- PF contribution toggle (12% of basic)

### How It Works — All Client-Side

```
Payroll page loads current salary_components from DB (read-only RSC)
    │
    ▼
Salary Simulator component mounts with current values as defaults
    │
    ▼
Employee adjusts sliders — all computation happens in browser:
    gross = basic + hra + transport + bonus
    pf_deduction = basic * 0.12  (if PF enabled)
    taxable = gross - standard_deduction(50000) - pf_deduction
    tax = compute_tax_slab(taxable)  // simple slab function
    net = gross - pf_deduction - tax
    │
    ▼
Values update instantly (React state, no API call)
    │
    ▼
"Save as Scenario" button → stores in localStorage for reference
    (note: this is client-only, not written to DB — it's a simulator)
```

### Frontend Component

```typescript
// components/features/payroll/SalarySimulator.tsx
"use client";
import { useState } from "react";

function computeTax(taxable: number): number {
  // Basic Indian income tax slabs (simplified)
  if (taxable <= 300000) return 0;
  if (taxable <= 600000) return (taxable - 300000) * 0.05;
  if (taxable <= 900000) return 15000 + (taxable - 600000) * 0.10;
  if (taxable <= 1200000) return 45000 + (taxable - 900000) * 0.15;
  if (taxable <= 1500000) return 90000 + (taxable - 1200000) * 0.20;
  return 150000 + (taxable - 1500000) * 0.30;
}

export function SalarySimulator({ current }: { current: SalaryComponents }) {
  const [basic, setBasic] = useState(current.basic_salary);
  const [hra, setHra] = useState(current.hra);
  const [bonus, setBonus] = useState(0);
  const [pfEnabled, setPfEnabled] = useState(true);

  const gross = basic + hra + current.transport + bonus;
  const pf = pfEnabled ? basic * 0.12 : 0;
  const taxable = Math.max(0, gross - 50000 - pf); // 50k standard deduction
  const tax = computeTax(taxable);
  const net = gross - pf - tax;

  return (
    <div className="border rounded-xl p-6 bg-gradient-to-br from-blue-50 to-white">
      <h3 className="font-semibold text-lg mb-4">💰 Salary Simulator</h3>

      <div className="space-y-4">
        <SliderField label="Basic Salary" value={basic} min={10000} max={500000}
          onChange={setBasic} prefix="₹" />
        <SliderField label="HRA" value={hra} min={0} max={basic * 0.5}
          onChange={setHra} prefix="₹" />
        <SliderField label="Bonus (one-time)" value={bonus} min={0} max={200000}
          onChange={setBonus} prefix="₹" />
        <ToggleField label="PF Contribution (12% of Basic)"
          value={pfEnabled} onChange={setPfEnabled} />
      </div>

      <div className="mt-6 bg-white rounded-lg p-4 space-y-2 text-sm border">
        <Row label="Gross Pay" value={gross} />
        <Row label="PF Deduction" value={-pf} color="text-red-500" />
        <Row label="Income Tax (est.)" value={-tax} color="text-red-500" />
        <hr />
        <Row label="Net Take-Home" value={net} bold color="text-green-600" />
      </div>

      <p className="text-xs text-gray-400 mt-3">
        * This is a simulation only. Actual payroll computed by HR.
      </p>
    </div>
  );
}
```

**Cost:** Completely free. 100% client-side computation. No API calls.

---

## 22. AI Leave Advisor

### What It Is
A proactive AI feature that analyzes the employee's leave history, remaining balances, upcoming holidays, and team leave patterns — then gives personalized advice about when to take leave for maximum benefit.

### What It Advises On
- "You have 8 paid leaves left. Take them before Dec 31 or they lapse."
- "The week of Oct 13 has a public holiday on Monday + Friday — you could take 3 days off and get 9 days total."
- "3 of your teammates are already on leave Aug 20–25. You may want to pick different dates to avoid team gaps."
- "You've worked 16 consecutive days. HR guidelines recommend a break. Want me to suggest leave dates?"
- "You haven't taken any sick leave this year. Your 10 days will lapse on Dec 31."

### Data Flow

```
Employee opens Leave Advisor tab
    │
    ▼
GET /leave/advisor
    │
    ▼
FastAPI fetches:
    - Employee's leave_balances (all types)
    - Employee's leave history (this year)
    - Upcoming public holidays (from static config or admin-set)
    - Team leave overlaps (teammates on leave in next 60 days)
    - Consecutive workdays (from attendance_records)
    - Current date + year end proximity
    │
    ▼
Ollama (Llama 3) generates 3-5 personalized recommendations
    │
    ▼
Each recommendation has:
    - Title: short label
    - Message: the actual advice
    - Action button: "Apply Leave for These Dates" (pre-fills form)
    - Priority: urgent | suggested | info
    │
    ▼
Advisor card shown in leave page
```

### Backend

```python
# routers/leave.py (advisor endpoint)

LEAVE_ADVISOR_PROMPT = """
You are an HR advisor. Analyze this employee's situation and give 3-5
personalized, specific leave recommendations.

Employee: {name}
Today: {today}
Year End: Dec 31, {year}

Leave Balances:
{balances}

Leave Taken This Year:
{leave_history}

Consecutive Working Days (current streak): {consecutive_days}

Upcoming Public Holidays (next 90 days):
{holidays}

Teammates on Leave (next 60 days):
{team_leaves}

Give actionable recommendations. Be specific with dates where possible.
Format as JSON array:
[
  {{
    "title": "Short title",
    "message": "Detailed advice with specific dates/numbers",
    "priority": "urgent|suggested|info",
    "suggested_dates": {{ "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }} or null
  }}
]
"""

@router.get("/leave/advisor")
async def leave_advisor(db=Depends(get_db), user=Depends(get_current_user)):
    cache_key = f"leave_advisor:{user['user_id']}:{date.today()}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Build context
    employee = await get_employee(db, user["user_id"])
    context = {
        "name": employee.name,
        "today": date.today().isoformat(),
        "year": date.today().year,
        "balances": await get_leave_balances(db, employee.id),
        "leave_history": await get_leave_history_this_year(db, employee.id),
        "consecutive_days": await count_consecutive_workdays(db, employee.id),
        "holidays": await get_upcoming_holidays(db, days=90),
        "team_leaves": await get_team_leaves(db, employee.department, days=60),
    }

    prompt = LEAVE_ADVISOR_PROMPT.format(**context)
    recommendations = await call_ollama(prompt)

    await redis.setex(cache_key, 3600, json.dumps(recommendations))  # cache 1 hr
    return recommendations
```

**Cost:** Free (Ollama + Llama 3). DB queries are standard.

---

## 23. Smart GPS & Wi-Fi Auto Check-In

### What It Is
Two complementary automatic check-in mechanisms so employees don't need to manually click "Check In" every morning.

**GPS Auto Check-In:** When the employee opens the app and their GPS coordinates are within the office geofence, the app automatically checks them in — no button press needed.

**Wi-Fi Auto Check-In:** When the employee's browser/device connects to the office Wi-Fi network (identified by SSID name stored in admin config), a background service detects this and auto-checks them in.

### GPS Auto Check-In Flow

```
Employee opens HRMS app / dashboard
    │
    ▼
Frontend: navigator.geolocation.getCurrentPosition()
    │
    ▼
If permission granted + not yet checked in today:
    Coordinates sent to POST /attendance/auto-checkin { lat, lng, method: "gps" }
    │
    ▼
FastAPI:
    - Haversine distance from office coordinates
    - If within radius: auto check-in
    - If outside: do nothing (don't error — employee opened app from home)
    │
    ▼
If auto-checked-in:
    Toast notification: "📍 Auto checked in at 9:03 AM (GPS)"
    No manual action needed
```

### Wi-Fi Auto Check-In Flow

```
Employee connects to office Wi-Fi
    │
    ▼
(Approach: Network Information API — partially supported)
Frontend polls: navigator.connection.type or checks window.location
    │
    ▼
Alternative (more reliable): Admin gives employees a browser bookmark
that pings POST /attendance/auto-checkin { method: "wifi", ssid_hint: "OfficeNet" }
The backend trusts the request if:
    - JWT is valid
    - Originating IP is in office IP range (admin-configured)
    │
    ▼
If IP matches office subnet: auto check-in recorded
Toast: "📶 Auto checked in at 8:58 AM (Office Wi-Fi detected)"
```

### Backend

```python
# routers/attendance.py

@router.post("/attendance/auto-checkin")
async def auto_checkin(
    payload: AutoCheckinPayload,
    request: Request,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    employee = await get_employee(db, user["user_id"])

    # Already checked in today?
    existing = await get_today_attendance(db, employee.id)
    if existing and existing.check_in:
        return {"status": "already_checked_in", "time": existing.check_in}

    verified = False

    if payload.method == "gps" and payload.lat and payload.lng:
        config = await get_office_config(db)
        distance = haversine(payload.lat, payload.lng, config.office_lat, config.office_lng)
        verified = distance <= config.geofence_radius_meters

    elif payload.method == "wifi":
        client_ip = request.client.host
        office_subnet = await get_office_ip_range(db)
        verified = ip_in_subnet(client_ip, office_subnet)

    if verified:
        await create_attendance_record(db, employee.id, method=payload.method)
        return {"status": "checked_in", "method": payload.method, "time": datetime.now().isoformat()}

    return {"status": "not_in_office", "auto_checkin": False}
```

### Admin Configuration

Admin sets in the office config panel:
- Office latitude + longitude
- Geofence radius (meters, default: 150)
- Office Wi-Fi IP subnet (e.g., 192.168.1.0/24)
- Auto check-in enabled/disabled toggle per method

**Cost:** Free. Browser Geolocation API + IP subnet check. No third-party service.

---

## 24. Team Attendance Health Score

### What It Is
A department-level metric (0–100 score) that summarizes the overall attendance health of a team. Admins see it at a glance on the dashboard. It factors in present rate, leave patterns, absence spikes, and burnout signals.

### Score Formula

```
Health Score = weighted average of:

  Present Rate (40%)         → (present days / working days) × 100
  Leave Utilization (20%)    → balanced leave use is healthy (never = bad, always = bad)
  Absence Pattern (20%)      → sudden spikes penalized
  Burnout Risk (20%)         → active burnout alerts reduce score

Score Ranges:
  90–100  🟢 Excellent
  70–89   🟡 Good
  50–69   🟠 Needs Attention
  0–49    🔴 Critical
```

### Data Flow

```
GET /analytics/team-health?department=Engineering&month=8&year=2025
    │
    ▼
FastAPI computes for all employees in department:
    - Days present this month
    - Leave days taken
    - Absence count
    - Active burnout alerts
    │
    ▼
Weighted score computed per employee
    │
    ▼
Department aggregate = average of all employee scores
    │
    ▼
Redis caches: team_health:{department}:{month}:{year}  TTL: 6 hours
    │
    ▼
Admin dashboard shows:
    - Score badge per department
    - Trend vs last month (↑ improving / ↓ declining)
    - Top 3 risk employees (lowest individual scores)
    - Drill-down to individual heatmaps
```

### Frontend Widget

```typescript
// components/features/admin/TeamHealthScore.tsx
export function TeamHealthScore({ department, score, trend }: TeamHealthProps) {
  const color = score >= 90 ? "green" : score >= 70 ? "yellow" : score >= 50 ? "orange" : "red";
  const emoji = score >= 90 ? "🟢" : score >= 70 ? "🟡" : score >= 50 ? "🟠" : "🔴";

  return (
    <div className="border rounded-xl p-5">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm text-gray-500">{department}</p>
          <p className="text-4xl font-bold mt-1" style={{ color }}>{score}</p>
          <p className="text-xs text-gray-400 mt-1">Attendance Health Score</p>
        </div>
        <span className="text-3xl">{emoji}</span>
      </div>
      <div className={`text-xs mt-3 ${trend > 0 ? "text-green-600" : "text-red-500"}`}>
        {trend > 0 ? "↑" : "↓"} {Math.abs(trend)} pts vs last month
      </div>
    </div>
  );
}
```

**Cost:** Free. PostgreSQL aggregate queries + Redis caching.

---

## 25. Proactive Nudge System

### What It Is
The system sends gentle, contextual, non-intrusive in-app notifications and optional emails to employees (not just admins) when specific conditions are detected. It acts like a thoughtful HR officer who notices things before the employee does.

### Nudge Triggers & Messages

| Trigger | Who Gets It | Channel | Message |
|---------|------------|---------|---------|
| 16+ consecutive working days | Employee | In-app + Email | "You've worked 16 days straight — you've earned a break! You have 8 paid leaves available." |
| Leave balance will lapse in 30 days | Employee | In-app | "You have 5 paid leaves expiring Dec 31. Plan your time off before they lapse." |
| Forgot to check out (after 9 PM) | Employee | In-app | "Looks like you didn't check out today. Did you work late? Tap to log your check-out time." |
| Leave request approved | Employee | In-app + Email | "Great news! Your leave Aug 11–12 has been approved by [Admin Name]." |
| Leave request rejected | Employee | In-app + Email | "Your leave request was reviewed. Comment from HR: [comment]" |
| Team member has birthday | HR Admin | In-app | "🎂 Riya's birthday is tomorrow — don't forget to wish her!" |
| Pending approval >48 hours | Admin | In-app | "3 leave requests have been waiting over 48 hours for your review." |

### Architecture

```
Nudge sources:
  1. APScheduler (nightly) → burnout + lapse checks
  2. Event hooks (immediate) → leave approved/rejected
  3. Attendance check (nightly) → forgot check-out

    │
    ▼
nudge_queue table in PostgreSQL
  { employee_id, message, type, read: false, created_at }
    │
    ▼
GET /nudges (called on dashboard load + every 5 min via TanStack Query)
    │
    ▼
Unread nudges shown as:
  - Bell icon badge count in navbar
  - Toast notification on first load
  - Nudge drawer (slide-out panel)
    │
    ▼
PATCH /nudges/{id}/read → marks as read
```

### Nudge Bell Component

```typescript
// components/features/nudge/NudgeBell.tsx
export function NudgeBell() {
  const { data } = useQuery({
    queryKey: ["nudges"],
    queryFn: () => apiFetch<Nudge[]>("/nudges?unread=true"),
    refetchInterval: 5 * 60 * 1000, // every 5 minutes
  });

  const unreadCount = data?.success ? data.data.length : 0;

  return (
    <Popover>
      <PopoverTrigger className="relative">
        <BellIcon className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white
            text-xs rounded-full w-4 h-4 flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0">
        <NudgeList nudges={data?.success ? data.data : []} />
      </PopoverContent>
    </Popover>
  );
}
```

**Cost:** Free. APScheduler + PostgreSQL + optional Resend emails.

---

## 26. Automated PDF Pay Stub Generation

### What It Is
Every month, when the payroll cron job runs, a professional PDF pay stub is automatically generated for each employee and stored. Employees can download it anytime from their payroll page. Admins can download any employee's stub.

### Pay Stub Contents

```
┌────────────────────────────────────────────────────────┐
│  ACME Corp                              PAY STUB       │
│  123 Business Park, Mumbai                             │
├────────────────────────────────────────────────────────┤
│  Employee: Rohan Mehta          Emp ID: EMP-0042       │
│  Department: Engineering        Month: August 2025     │
│  Designation: Senior Developer                         │
├────────────────────────────────────────────────────────┤
│  EARNINGS                        DEDUCTIONS            │
│  Basic Salary    ₹ 50,000        PF (12%)  ₹  6,000  │
│  HRA             ₹ 20,000        Income Tax ₹  4,200  │
│  Transport       ₹  3,000                              │
│  Performance Bns ₹  5,000                              │
│  ─────────────────────────────────────────────────     │
│  Gross Pay       ₹ 78,000        Total Ded  ₹ 10,200  │
├────────────────────────────────────────────────────────┤
│  NET TAKE-HOME PAY:              ₹ 67,800             │
├────────────────────────────────────────────────────────┤
│  Working Days: 23 | Present: 22 | Leave: 1            │
│  Generated: Aug 31, 2025 | Ref: PAY-2025-08-0042      │
└────────────────────────────────────────────────────────┘
```

### Generation Flow

```
APScheduler (last day of month, 23:59)
    │
    ▼
For each active employee:
    Fetch salary_components, attendance summary, deductions
    │
    ▼
Render Jinja2 HTML template with employee data
    │
    ▼
WeasyPrint converts HTML → PDF bytes
    │
    ▼
PDF saved to: /storage/paystubs/{employee_id}/{year}-{month}.pdf
    │
    ▼
payroll_runs.pay_stub_url updated
    │
    ▼
Resend email: "Your August 2025 pay stub is ready — download from portal"
    │
    ▼
audit_log: { action: "pay_stub_generated", employee_id, month, year }
```

### Backend Code

```python
# services/payroll_calc.py
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

jinja_env = Environment(loader=FileSystemLoader("templates/"))

async def generate_pay_stub(employee, payroll_run: PayrollRun) -> bytes:
    template = jinja_env.get_template("pay_stub.html")

    html_content = template.render(
        employee=employee,
        payroll=payroll_run,
        components=payroll_run.components_snapshot,
        month_name=calendar.month_name[payroll_run.month],
        year=payroll_run.year,
        ref_id=f"PAY-{payroll_run.year}-{payroll_run.month:02d}-{employee.employee_id[-4:]}",
        generated_date=date.today().strftime("%b %d, %Y")
    )

    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes


async def run_monthly_payroll():
    async with AsyncSession(engine) as db:
        employees = await get_all_active_employees(db)
        for emp in employees:
            components = await get_current_salary_components(db, emp.id)
            attendance = await get_month_attendance_summary(db, emp.id)

            gross = sum(c.amount for c in components)
            unpaid_deduction = attendance.unpaid_days * (components.basic / 22)
            pf = components.basic * 0.12
            tax = compute_tax(gross - pf - 50000)
            net = gross - unpaid_deduction - pf - tax

            run = PayrollRun(
                employee_id=emp.id,
                month=date.today().month,
                year=date.today().year,
                gross_pay=gross,
                deductions=pf + tax + unpaid_deduction,
                net_pay=net,
                components_snapshot=jsonable_encoder(components)
            )
            db.add(run)
            await db.flush()

            pdf_bytes = await generate_pay_stub(emp, run)
            path = f"/storage/paystubs/{emp.id}/{run.year}-{run.month:02d}.pdf"
            save_file(path, pdf_bytes)
            run.pay_stub_url = path

        await db.commit()
```

**Cost:** Free. WeasyPrint (open-source) + Jinja2 (built-in Python) + Resend (free tier).

---

## 27. Internal Team Chat & Meeting Announcements

### What It Is
A lightweight internal messaging feature — NOT a full chat application like Slack or WhatsApp. Think of it as a structured communication layer inside the HRMS for:

- **HR announcements** (policy updates, office closures, payroll dates)
- **Meeting call-outs** ("All hands meeting — Friday 3 PM, Conference Room B")
- **Department group messages** (HR to Engineering, HR to Sales, etc.)
- **One-to-one HR ↔ Employee messages** for leave discussions
- **Team-wide broadcasts** from admin

### What It Is NOT
- Not real-time group chat (no competing with WhatsApp)
- No file sharing (HRMS is not a file server)
- No chat history beyond 90 days
- No employee-to-employee direct messaging (admin/HR initiated only, or employee replies to HR)

### Message Types

| Type | Who Can Send | Who Receives |
|------|-------------|-------------|
| Announcement | Admin / HR | All employees |
| Department Broadcast | Admin / HR | Specific department |
| Meeting Invite | Admin / HR | Selected employees or department |
| Direct Message | Admin/HR → Employee or Employee → HR | 1:1 only |
| Leave Discussion | System (auto) | Employee + approving admin |

### Database Schema

```sql
CREATE TABLE chat_channels (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type        VARCHAR(30) NOT NULL,  -- 'announcement'|'department'|'direct'|'meeting'
    name        VARCHAR(100),          -- "Engineering Dept" or null for direct
    department  VARCHAR(100),          -- if type=department
    created_by  UUID REFERENCES employees(id),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id  UUID NOT NULL REFERENCES chat_channels(id),
    sender_id   UUID NOT NULL REFERENCES employees(id),
    body        TEXT NOT NULL,         -- max 1000 chars
    message_type VARCHAR(20) DEFAULT 'text',  -- 'text'|'meeting_invite'|'announcement'
    meeting_meta JSONB,               -- { "time": "...", "room": "...", "agenda": "..." }
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_reads (
    employee_id UUID REFERENCES employees(id),
    message_id  UUID REFERENCES chat_messages(id),
    read_at     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (employee_id, message_id)
);
```

### Meeting Invite Message (Special Type)

When HR sends a meeting invite, it's a structured message with metadata:

```json
{
  "type": "meeting_invite",
  "body": "Quarterly review meeting — please attend",
  "meeting_meta": {
    "title": "Q3 Quarterly Review",
    "date": "2025-08-22",
    "time": "3:00 PM",
    "duration_minutes": 60,
    "location": "Conference Room B, 3rd Floor",
    "agenda": "Q3 performance review, leave policy update, team targets for Q4",
    "rsvp_required": true
  }
}
```

Employees see it as a formatted card — not just plain text:

```
┌──────────────────────────────────────────────┐
│  📅  MEETING INVITE                          │
│  Q3 Quarterly Review                         │
│  Friday, Aug 22, 2025 • 3:00 PM (60 min)    │
│  📍 Conference Room B, 3rd Floor             │
│                                              │
│  Agenda: Q3 performance review, leave policy │
│  update, team targets for Q4                 │
│                                              │
│  [✅ Accept]  [❌ Decline]  [❓ Maybe]       │
└──────────────────────────────────────────────┘
```

### Data Flow

```
HR types message in Chat panel → selects channel (All / Dept / Employee)
    │
    ▼
POST /chat/messages { channel_id, body, message_type, meeting_meta? }
    │
    ▼
FastAPI: validate sender is admin/HR (for broadcasts)
    or employee (for direct reply to HR only)
    │
    ▼
INSERT chat_messages
    │
    ▼
Redis pub/sub: publish to channel "chat:{channel_id}"
    │
    ▼
All connected clients subscribed to channel receive message
(via Server-Sent Events — SSE — no WebSocket library needed)
    │
    ▼
Nudge Bell gets new unread count
    │
    ▼
Optional: Resend email for meeting invites (so employee gets email too)
```

### Real-Time Delivery — Server-Sent Events (SSE)

SSE is chosen over WebSockets because:
- Simpler backend (native FastAPI support)
- One-directional push from server (sufficient — users post via normal HTTP)
- Works through Nginx without special config
- No external library needed

```python
# routers/chat.py
from fastapi.responses import StreamingResponse
import asyncio

@router.get("/chat/stream/{channel_id}")
async def chat_stream(channel_id: UUID, user=Depends(get_current_user)):
    async def event_generator():
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"chat:{channel_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data'].decode()}\n\n"
        finally:
            await pubsub.unsubscribe(f"chat:{channel_id}")

    return StreamingResponse(event_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/chat/messages")
async def send_message(payload: ChatMessagePayload, db=Depends(get_db), user=Depends(get_current_user)):
    employee = await get_employee(db, user["user_id"])

    # Permission check: only admin can broadcast; employees can only reply in direct channels
    channel = await get_channel(db, payload.channel_id)
    if channel.type in ["announcement", "department", "meeting"] and employee.role != "admin":
        raise HTTPException(403, "Only HR/Admin can send to this channel")

    msg = ChatMessage(
        channel_id=payload.channel_id,
        sender_id=employee.id,
        body=payload.body[:1000],  # hard cap
        message_type=payload.message_type,
        meeting_meta=payload.meeting_meta
    )
    db.add(msg)
    await db.commit()

    # Push to Redis pub/sub for SSE delivery
    await redis.publish(f"chat:{payload.channel_id}", json.dumps({
        "id": str(msg.id),
        "sender": employee.name,
        "body": msg.body,
        "type": msg.message_type,
        "meeting_meta": msg.meeting_meta,
        "time": msg.created_at.isoformat()
    }))

    return {"success": True, "message_id": str(msg.id)}
```

### Frontend Chat Panel

```typescript
// components/features/chat/ChatPanel.tsx
"use client";
import { useEffect, useRef, useState } from "react";

export function ChatPanel({ channelId }: { channelId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load existing messages
  useEffect(() => {
    apiFetch<ChatMessage[]>(`/chat/messages?channel_id=${channelId}`)
      .then(res => res.success && setMessages(res.data));
  }, [channelId]);

  // SSE for real-time new messages
  useEffect(() => {
    const token = getClerkToken();
    const es = new EventSource(`/api/chat/stream/${channelId}?token=${token}`);
    es.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      setMessages(prev => [...prev, msg]);
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    };
    return () => es.close();
  }, [channelId]);

  const send = async () => {
    if (!input.trim()) return;
    await apiFetch("/chat/messages", {
      method: "POST",
      body: JSON.stringify({ channel_id: channelId, body: input, message_type: "text" })
    });
    setInput("");
  };

  return (
    <div className="flex flex-col h-full border-l">
      {/* Header */}
      <div className="px-4 py-3 border-b bg-gray-50 font-medium text-sm">
        💬 Team Chat
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(msg => (
          msg.message_type === "meeting_invite"
            ? <MeetingInviteCard key={msg.id} message={msg} />
            : <ChatBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 p-3 border-t">
        <input className="flex-1 border rounded-lg px-3 py-2 text-sm"
          value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Message HR or your team..." />
        <button onClick={send} className="bg-blue-600 text-white px-4 rounded-lg text-sm">
          Send
        </button>
      </div>
    </div>
  );
}

// Meeting invite card component
function MeetingInviteCard({ message }: { message: ChatMessage }) {
  const m = message.meeting_meta;
  return (
    <div className="border-2 border-blue-200 bg-blue-50 rounded-xl p-4">
      <div className="flex items-center gap-2 font-semibold text-blue-800 mb-2">
        📅 Meeting Invite
      </div>
      <p className="font-medium">{m.title}</p>
      <p className="text-sm text-gray-600">{m.date} • {m.time} ({m.duration_minutes} min)</p>
      <p className="text-sm text-gray-600">📍 {m.location}</p>
      {m.agenda && <p className="text-xs text-gray-500 mt-2 italic">{m.agenda}</p>}
      {m.rsvp_required && (
        <div className="flex gap-2 mt-3">
          <button className="bg-green-600 text-white px-3 py-1 rounded text-xs">✅ Accept</button>
          <button className="bg-red-100 text-red-700 px-3 py-1 rounded text-xs">❌ Decline</button>
          <button className="bg-gray-100 text-gray-700 px-3 py-1 rounded text-xs">❓ Maybe</button>
        </div>
      )}
    </div>
  );
}
```

**Cost:** Free. Redis pub/sub (already in stack) + SSE (FastAPI native) + Resend for email fallback.

---

# APPENDICES

---

## Database Additions for All Features

New tables required beyond the core schema:

```sql
-- Burnout alerts log
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

-- Nudge queue
CREATE TABLE nudges (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    message     TEXT NOT NULL,
    type        VARCHAR(50) NOT NULL,     -- burnout|leave_lapse|missed_checkout|approval|birthday
    read        BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Public holidays (admin-configurable)
CREATE TABLE public_holidays (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name    VARCHAR(100) NOT NULL,
    date    DATE NOT NULL UNIQUE,
    year    INTEGER NOT NULL
);

-- Office configuration
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

-- Chat channels
CREATE TABLE chat_channels (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type        VARCHAR(30) NOT NULL,
    name        VARCHAR(100),
    department  VARCHAR(100),
    created_by  UUID REFERENCES employees(id),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Chat messages
CREATE TABLE chat_messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id   UUID NOT NULL REFERENCES chat_channels(id),
    sender_id    UUID NOT NULL REFERENCES employees(id),
    body         TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    meeting_meta JSONB,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Chat read receipts
CREATE TABLE chat_reads (
    employee_id UUID REFERENCES employees(id),
    message_id  UUID REFERENCES chat_messages(id),
    read_at     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (employee_id, message_id)
);

-- RSVP responses for meeting invites
CREATE TABLE meeting_rsvp (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES chat_messages(id),
    employee_id UUID REFERENCES employees(id),
    response   VARCHAR(10) NOT NULL,  -- accept|decline|maybe
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(message_id, employee_id)
);
```

---

## Updated Folder Structure Additions

New files/folders to add to both frontend and backend:

### Frontend Additions

```
components/features/
├── attendance/
│   ├── AttendanceHeatmap.tsx          ← NEW: SVG heatmap
│   ├── VoiceMicButton.tsx             ← NEW: voice command trigger
│   └── AutoCheckinBanner.tsx          ← NEW: GPS/Wi-Fi auto check-in toast
├── leave/
│   ├── ConversationalLeave.tsx        ← NEW: multi-turn NLP chat
│   ├── LeaveAdvisorCard.tsx           ← NEW: AI recommendations
│   └── VoiceToLeave.tsx               ← NEW: audio recording + parsing
├── payroll/
│   └── SalarySimulator.tsx            ← NEW: interactive salary slider
├── chat/
│   ├── ChatPanel.tsx                  ← NEW: main chat UI
│   ├── ChatBubble.tsx                 ← NEW: message bubble
│   ├── MeetingInviteCard.tsx          ← NEW: structured meeting card
│   └── ChannelList.tsx                ← NEW: channel sidebar
├── nudge/
│   ├── NudgeBell.tsx                  ← NEW: notification bell
│   └── NudgeList.tsx                  ← NEW: nudge drawer
└── admin/
    ├── BurnoutDashboard.tsx           ← NEW: burnout early warning UI
    └── TeamHealthScore.tsx            ← NEW: health score widget

hooks/
├── useVoiceCommand.ts                 ← NEW
├── useVoiceRecorder.ts                ← NEW: MediaRecorder wrapper
├── useSSE.ts                          ← NEW: EventSource wrapper
├── useNudges.ts                       ← NEW
└── useLeaveAdvisor.ts                 ← NEW
```

### Backend Additions

```
routers/
├── chat.py                            ← NEW: chat + SSE stream
├── nudges.py                          ← NEW: nudge CRUD
└── analytics.py                       ← NEW: team health score

services/
├── attendance_analytics.py            ← EXPANDED: burnout signals
├── nudge_service.py                   ← NEW: nudge generation logic
└── chat_service.py                    ← NEW: channel management

models/
├── burnout_alerts.py                  ← NEW
├── nudges.py                          ← NEW
├── chat.py                            ← NEW: channels + messages + reads + rsvp
├── public_holidays.py                 ← NEW
└── office_config.py                   ← NEW

templates/
└── pay_stub.html                      ← NEW: WeasyPrint HTML template
```

---

## Updated Tech Stack Additions

| Feature | Tool Added | Cost |
|---------|-----------|------|
| Real-time chat delivery | Redis pub/sub + FastAPI SSE | Free (Redis already in stack) |
| Pay stub PDF | WeasyPrint + Jinja2 | Free (open-source) |
| SVG heatmap | React + SVG (no library) | Free |
| Voice recording | Browser MediaRecorder API | Free |
| Salary simulator | React state math (no API) | Free |
| GPS auto check-in | Browser Geolocation API | Free |
| Wi-Fi auto check-in | IP subnet check (Python ipaddress) | Free |
| RSVP for meetings | PostgreSQL + FastAPI | Free |

---

## Free Tools Master Reference

| Feature | Tool | How to Get It |
|---------|------|--------------|
| AI conversations, NLP, parsing, advisor | Ollama + Llama 3 | `docker pull ollama/ollama` then `ollama pull llama3` |
| AI Q&A chatbot | Ollama + Mistral 7B | `ollama pull mistral` |
| Voice transcription | Whisper Docker | `docker pull onerahmet/openai-whisper-asr-webservice` |
| Voice commands | Browser Web Speech API | Built into Chrome, Edge, Safari |
| Voice recording | Browser MediaRecorder API | Built into all modern browsers |
| Email delivery | Resend | resend.com — free 100 emails/day, no CC needed |
| PDF generation | WeasyPrint | `pip install weasyprint` |
| HTML templates | Jinja2 | `pip install jinja2` (included with FastAPI) |
| Real-time push | SSE (Server-Sent Events) | Built into FastAPI (`StreamingResponse`) |
| Virus scanning | ClamAV | `docker pull clamav/clamav:stable` |
| Auth + sessions | Clerk | clerk.com — free up to 10,000 MAU |
| SVG heatmap | Custom React component | No library needed |
| GPS check-in | Browser Geolocation API | Built into all browsers |
| IP subnet check | Python `ipaddress` module | Built into Python 3 stdlib |
| Salary simulation | React `useState` math | No library needed |
| Cron jobs | APScheduler | `pip install apscheduler` |

**Total external paid services required: ZERO.**
Everything runs self-hosted or on free tiers sufficient for any team under 10,000 employees.

---

*End of HRMS Complete Feature Specification v2.0*

*Part A: Core SRS Features (Mandatory) — 8 foundational features*
*Part B: Performance & Security Features — 6 cross-cutting concerns*
*Part C: Creative Differentiators (AI-Powered) — 13 advanced features*
*Total: 27 features documented with implementation detail.*

*All features are designed to work together as a unified system.*
*Each feature is independently implementable — pick any order after core is stable.*