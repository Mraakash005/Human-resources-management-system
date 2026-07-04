# Performance Guide

## Overview

Performance targets, optimization strategies, and benchmarking procedures for the HRMS backend.

---

## Performance Targets

### Response Time SLAs

| Endpoint                      | p50      | p95      | p99      | Max      |
|-------------------------------|----------|----------|----------|----------|
| GET /health                   | 5ms      | 20ms     | 50ms     | 100ms    |
| GET /api/v1/employees         | 50ms     | 150ms    | 300ms    | 500ms    |
| GET /api/v1/attendance        | 50ms     | 150ms    | 300ms    | 500ms    |
| POST /api/v1/attendance/check-in | 80ms  | 200ms    | 400ms    | 500ms    |
| GET /api/v1/leave             | 50ms     | 150ms    | 300ms    | 500ms    |
| GET /api/v1/dashboard         | 100ms    | 300ms    | 600ms    | 1000ms   |
| POST /api/v1/chatbot          | 500ms    | 1500ms   | 3000ms   | 5000ms   |
| POST /api/v1/voice/transcribe | 1000ms   | 2500ms   | 5000ms   | 10000ms  |

### Throughput Targets

| Metric                       | Target         |
|------------------------------|----------------|
| Requests per second          | 1000+          |
| Concurrent users             | 500+           |
| Database queries per second  | 2000+          |
| Cache operations per second  | 10000+         |

### Resource Limits

| Resource                    | Limit         |
|-----------------------------|---------------|
| API response body           | < 1MB         |
| File upload size            | < 50MB        |
| Database connection pool    | 20 + 10       |
| Redis max connections       | 20            |
| Ollama request timeout      | 60s           |

---

## Redis Caching Strategy

### Cache Architecture

```
Client Request
    │
    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │────▶│  PostgreSQL │
│   Router    │     │   Cache     │     │  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
    │                    │
    │              Cache Hit? ──Yes──▶ Return cached
    │                    │
    │                   No
    │                    │
    ▼                    ▼
  Query DB ◀────────────┘
    │
    ▼
  Cache result
    │
    ▼
  Return response
```

### Cache Key Patterns

```python
# Dashboard cache
"dashboard:{user_id}:{role}"     # TTL: 60s

# Role verification cache
"role_verified:{clerk_user_id}"  # TTL: 120s

# Leave balance cache
"leave_balance:{employee_id}"    # TTL: 300s

# Chatbot context cache
"chatbot_context:{user_id}"      # TTL: 300s

# Leave advisor cache
"leave_advisor:{user_id}:{date}" # TTL: 3600s

# Attendance heatmap cache
"heatmap:{employee_id}:{year}"   # TTL: 3600s

# Team health cache
"team_health:{manager_id}"       # TTL: 21600s

# Attendance lock (prevent double check-in)
"attendance:checkin:{emp_id}:{date}"  # TTL: 86400s
```

### Cache Invalidation

```python
# Invalidation by pattern
await redis_manager.delete_pattern("dashboard:*:admin")  # All admin dashboards
await redis_manager.delete_pattern("dashboard:user123:*")  # All dashboards for user

# Targeted invalidation
await redis_manager.client.delete(f"leave_balance:{employee_id}")

# After leave request
async def invalidate_leave_cache(employee_id: str) -> None:
    await cache_service.invalidate_leave_balance(employee_id)
    await cache_service.invalidate_dashboard(employee_id)

# After attendance update
async def invalidate_attendance_cache(employee_id: str) -> None:
    await redis_manager.delete_pattern(f"heatmap:{employee_id}:*")
```

### Cache Hit Rate Monitoring

```python
# Add to health check
async def cache_hit_rate() -> dict:
    info = await redis_manager.client.info("stats")
    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total = hits + misses
    rate = (hits / total * 100) if total > 0 else 0
    return {
        "hits": hits,
        "misses": misses,
        "hit_rate_percent": round(rate, 2),
    }
```

---

## Database Query Optimization

### Index Strategy

```sql
-- Primary indexes (already exist via constraints)
CREATE UNIQUE INDEX idx_employees_clerk_user_id ON employees(clerk_user_id);
CREATE UNIQUE INDEX idx_employees_email ON employees(email);

-- Composite indexes for common queries
CREATE INDEX idx_attendance_employee_date ON attendance(employee_id, date);
CREATE INDEX idx_leave_employee_status ON leave_requests(employee_id, status);
CREATE INDEX idx_leave_date_range ON leave_requests(start_date, end_date);
CREATE INDEX idx_payroll_employee_month ON payroll(employee_id, pay_month);

-- Partial indexes
CREATE INDEX idx_active_employees ON employees(id)
  WHERE is_active = true;

CREATE INDEX idx_pending_leaves ON leave_requests(id)
  WHERE status = 'pending';

-- Covering indexes (include frequently accessed columns)
CREATE INDEX idx_attendance_covering ON attendance(employee_id, date)
  INCLUDE (check_in_time, check_out_time, status);
```

### Query Optimization Examples

```python
# BAD: N+1 query pattern
employees = await session.execute(select(Employee))
for emp in employees:
    # Each iteration hits the database
    attendance = await session.execute(
        select(Attendance).where(Attendance.employee_id == emp.id)
    )

# GOOD: Eager loading with joinedload
from sqlalchemy.orm import selectinload

employees = await session.execute(
    select(Employee)
    .options(selectinload(Employee.attendance_records))
)

# GOOD: Subquery for aggregations
from sqlalchemy import func

avg_hours = await session.execute(
    select(
        Attendance.employee_id,
        func.avg(Attendance.working_hours).label("avg_hours")
    )
    .where(Attendance.date >= start_date)
    .group_by(Attendance.employee_id)
)
```

### Connection Pool Tuning

```python
# Production configuration
DB_POOL_SIZE = 20      # Base connections
DB_MAX_OVERFLOW = 10   # Extra connections under load
DB_POOL_TIMEOUT = 30   # Seconds to wait for connection
DB_POOL_RECYCLE = 1800 # Recycle connections every 30 minutes
DB_POOL_PRE_PING = True  # Verify connections before use

# Monitoring pool usage
async def pool_stats() -> dict:
    pool = db_manager._engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
```

---

## Async I/O Benefits

### Why Async?

```
Synchronous (Bad):
  Request 1: [----Query DB----][----Wait----][----Response----]
  Request 2:                    [----Query DB----][----Wait----][----Response----]
  Request 3:                                                 [----Query DB----]...
  
  Total time: ~9 seconds for 3 requests

Asynchronous (Good):
  Request 1: [----Query DB----]              [----Response----]
  Request 2: [----Query DB----]              [----Response----]
  Request 3: [----Query DB----]              [----Response----]
  
  Total time: ~3 seconds for 3 requests
```

### Async Patterns in HRMS

```python
# Parallel database queries
async def get_dashboard_data(user_id: str) -> dict:
    employee, attendance, leave = await asyncio.gather(
        get_employee(user_id),
        get_attendance_summary(user_id),
        get_leave_balance(user_id),
    )
    return {"employee": employee, "attendance": attendance, "leave": leave}

# Parallel external API calls
async def process_leave_request(request: LeaveRequest) -> dict:
    employee, manager, calendar = await asyncio.gather(
        get_employee(request.employee_id),
        get_manager(request.manager_id),
        check_calendar_conflicts(request),
    )
    # Process with all data available
    return await create_leave_response(employee, manager, calendar)

# Async file operations
async def upload_profile_picture(employee_id: str, file: bytes) -> str:
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, validate_file, file)
    url = await upload_to_r2(file, employee_id)
    await update_employee_record(employee_id, url)
    return url
```

### Connection Pool Sizing

```
Formula for async applications:
  pool_size = (2 * cpu_cores) + effective_disk_spindles

For a 4-core server:
  pool_size = (2 * 4) + 1 = 9
  max_overflow = pool_size // 2 = 4-5

Recommended for HRMS:
  pool_size = 20 (allows for burst traffic)
  max_overflow = 10
  Total max connections = 30
```

---

## N+1 Query Prevention

### Detection

```python
# Enable query logging in development
DB_ECHO = True

# Or log slow queries
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# Count queries per request
from sqlalchemy import event

query_count = 0

@event.listens_for(Session, "after_execute")
def count_queries(session, query, query_context, result):
    global query_count
    query_count += 1
```

### Prevention Patterns

```python
# Pattern 1: selectinload for one-to-many
from sqlalchemy.orm import selectinload

employees = await session.execute(
    select(Employee)
    .options(
        selectinload(Employee.attendance_records),
        selectinload(Employee.leave_requests),
    )
)

# Pattern 2: joinedload for many-to-one
employees = await session.execute(
    select(Employee)
    .options(joinedload(Employee.department))
)

# Pattern 3: Subquery for counts
from sqlalchemy import func

employees_with_counts = await session.execute(
    select(
        Employee.id,
        Employee.full_name,
        func.count(Attendance.id).label("attendance_count"),
    )
    .outerjoin(Attendance, Attendance.employee_id == Employee.id)
    .group_by(Employee.id, Employee.full_name)
)

# Pattern 4: Batch loading
async def get_employees_batch(employee_ids: list[str]) -> list[Employee]:
    result = await session.execute(
        select(Employee).where(Employee.id.in_(employee_ids))
    )
    return result.scalars().all()
```

### Query Budget

```
Target: Maximum 5 queries per API request

GET /api/v1/dashboard:
  1. SELECT employee WHERE id = ?
  2. SELECT attendance WHERE employee_id = ? AND date >= ?
  3. SELECT leave_requests WHERE employee_id = ? AND status = 'pending'
  4. SELECT payroll WHERE employee_id = ? AND pay_month = ?
  Total: 4 queries ✓

GET /api/v1/employees (list):
  1. SELECT employees (paginated)
  2. SELECT departments WHERE id IN (?)
  Total: 2 queries ✓
```

---

## Benchmarking

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class HRMSUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_dashboard(self):
        self.client.get("/api/v1/dashboard", headers=self.headers)
    
    @task(2)
    def get_employees(self):
        self.client.get("/api/v1/employees", headers=self.headers)
    
    @task(1)
    def check_attendance(self):
        self.client.post("/api/v1/attendance/check-in", headers=self.headers)
```

### Running Benchmarks

```bash
# Start Locust
locust -f locustfile.py --host=http://localhost:8000

# Or headless mode
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  -u 100 \
  -r 10 \
  --run-time 5m \
  --html=benchmark_report.html
```

### Database Query Benchmarks

```python
# scripts/benchmark_queries.py
import asyncio
import time

async def benchmark_query(name: str, query_func, iterations: int = 100):
    start = time.perf_counter()
    for _ in range(iterations):
        await query_func()
    elapsed = time.perf_counter() - start
    avg_ms = (elapsed / iterations) * 1000
    print(f"{name}: {avg_ms:.2f}ms avg ({iterations} iterations)")

async def main():
    from app.core.database import db_manager
    from sqlalchemy import text
    
    await db_manager.connect()
    
    async with db_manager.get_session_factory()() as session:
        await benchmark_query(
            "Simple SELECT",
            lambda: session.execute(text("SELECT 1"))
        )
        
        await benchmark_query(
            "Employee lookup",
            lambda: session.execute(
                text("SELECT * FROM employees WHERE id = :id"),
                {"id": "emp_001"}
            )
        )
        
        await benchmark_query(
            "Dashboard aggregation",
            lambda: session.execute(text("""
                SELECT e.id, e.full_name, COUNT(a.id) as attendance_count
                FROM employees e
                LEFT JOIN attendance a ON a.employee_id = e.id
                WHERE a.date >= :start_date
                GROUP BY e.id, e.full_name
            """), {"start_date": "2026-01-01"})
        )
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### Performance Monitoring

```python
# Add to middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start = time.perf_counter()
    
    # Track database query time
    db_start = time.perf_counter()
    response = await call_next(request)
    db_time = (time.perf_counter() - db_start) * 1000
    
    total_time = (time.perf_counter() - start) * 1000
    
    # Log slow requests
    if total_time > 1000:
        logger.warning(
            "Slow request: %s %s (%.1fms)",
            request.method,
            request.url.path,
            total_time,
        )
    
    # Add performance headers
    response.headers["X-Response-Time"] = f"{total_time:.1f}ms"
    response.headers["X-DB-Time"] = f"{db_time:.1f}ms"
    
    return response
```

---

## Performance Checklist

### Before Deployment

- [ ] Database indexes created for new queries
- [ ] N+1 query patterns eliminated
- [ ] Connection pool sizes appropriate
- [ ] Cache TTLs configured correctly
- [ ] Slow query logging enabled
- [ ] Response time benchmarks pass
- [ ] Load test results acceptable

### During Monitoring

- [ ] Response times within SLA
- [ ] Error rate < 0.1%
- [ ] Database connection pool not exhausted
- [ ] Redis memory usage < 80%
- [ ] CPU usage < 70%
- [ ] Memory usage < 80%
- [ ] No N+1 queries in logs

### After Issues

- [ ] Root cause identified
- [ ] Fix deployed and tested
- [ ] Monitoring updated
- [ ] Runbook updated if needed
- [ ] Performance regression prevented
