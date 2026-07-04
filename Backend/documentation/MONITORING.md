# Monitoring

## Overview

The HRMS backend includes comprehensive monitoring with health checks, structured logging, request tracking, and performance metrics.

---

## Health Endpoint

### `GET /health`

Returns the status of all services and application health.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-07-04T12:00:00Z",
  "uptime_seconds": 86400,
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.3
    },
    "ollama": {
      "status": "healthy",
      "models_loaded": ["llama3", "mistral"],
      "latency_ms": 45.2
    },
    "whisper": {
      "status": "healthy",
      "model": "base",
      "latency_ms": 12.1
    },
    "clamav": {
      "status": "healthy",
      "definitions_updated": "2026-07-04T06:00:00Z"
    },
    "resend": {
      "status": "healthy",
      "daily_sent": 23,
      "daily_remaining": 77
    }
  }
}
```

**Status Codes:**
| Status | Meaning |
|--------|---------|
| 200 | All services healthy |
| 207 | Some services degraded |
| 503 | Critical service unavailable |

### Implementation

```python
from fastapi import APIRouter, Response
from datetime import datetime
import time

router = APIRouter()

@router.get("/health")
async def health_check(response: Response):
    start = time.time()
    services = {}
    overall_status = "healthy"

    # Check database
    services["database"] = await check_database_health()

    # Check Ollama
    services["ollama"] = await check_ollama_health()

    # Check Whisper
    services["whisper"] = await check_whisper_health()

    # Check ClamAV
    services["clamav"] = await check_clamav_health()

    # Check Resend
    services["resend"] = await check_resend_health()

    # Determine overall status
    for svc in services.values():
        if svc["status"] == "unhealthy":
            overall_status = "degraded"
            response.status_code = 207

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": int(time.time() - APP_START_TIME),
        "version": APP_VERSION,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": services,
        "response_time_ms": round((time.time() - start) * 1000, 1)
    }
```

---

## Structured Logging

### Configuration

| Environment | Format | Level |
|-------------|--------|-------|
| Production | JSON | INFO |
| Staging | JSON | DEBUG |
| Development | Text (colored) | DEBUG |

### Setup

```python
import logging
import sys
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

class TextFormatter(logging.Formatter):
    """Colored text formatter for development."""
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        return f"{color}[{record.levelname}] {record.name}: {record.getMessage()}{self.RESET}"

def setup_logging():
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "DEBUG")

    handler = logging.StreamHandler(sys.stdout)

    if environment == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=[handler]
    )

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

### Example Output

**Production (JSON):**
```json
{"timestamp": "2026-07-04T12:00:00Z", "level": "INFO", "logger": "app.api.leave", "message": "Leave request created", "module": "leave", "function": "create_leave", "line": 42, "request_id": "req_abc123", "employee_id": 123, "leave_type": "sick"}
```

**Development (Text):**
```
[INFO] app.api.leave: Leave request created (request_id=req_abc123 employee_id=123 leave_type=sick)
```

---

## Request ID Tracking

Every incoming request is assigned a unique ID for tracing.

### Middleware

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Attach to request state
        request.state.request_id = request_id

        # Add to logger context
        logger = logging.getLogger("app")
        logger.adapter("", {"request_id": request_id})

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response
```

### Usage in Handlers

```python
from fastapi import Request

@router.post("/api/v1/leave")
async def create_leave(request: Request, ...):
    request_id = request.state.request_id
    logger.info(f"Creating leave request", extra={"request_id": request_id})
    ...
```

### Propagation

Request ID is propagated through:
- HTTP response headers
- Log entries
- Error responses
- External API calls (as `X-Request-ID` header)

---

## Correlation IDs

Correlation IDs group related operations across services.

### Use Cases

| Scenario | Correlation ID |
|----------|----------------|
| Employee onboarding | `onboard_{employee_id}_{timestamp}` |
| Leave request flow | `leave_{request_id}` |
| Payroll run | `payroll_{period}_{timestamp}` |
| AI pipeline | `ai_{request_id}` |

### Implementation

```python
class CorrelationContext:
    _current = contextvars.ContextVar("correlation_id", default=None)

    @classmethod
    def get(cls) -> str:
        return cls._current.get()

    @classmethod
    def set(cls, correlation_id: str):
        cls._current.set(correlation_id)

    @classmethod
    def generate(cls, prefix: str) -> str:
        cid = f"{prefix}_{uuid.uuid4().hex[:12]}"
        cls.set(cid)
        return cid

# Usage
CorrelationContext.generate("leave")
logger.info("Processing leave request")  # Includes correlation_id automatically
```

### Cross-Service Propagation

```python
# Outgoing requests include correlation ID
headers = {
    "X-Correlation-ID": CorrelationContext.get(),
    "X-Request-ID": str(uuid.uuid4())
}
response = requests.post("http://other-service/api", headers=headers)
```

---

## Performance Timing Headers

### Response Headers

Every API response includes timing information:

```
X-Response-Time: 45.2ms
X-DB-Time: 12.1ms
X-AI-Time: 30.5ms
```

### Middleware

```python
import time

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        total_time = (time.perf_counter() - start) * 1000

        response.headers["X-Response-Time"] = f"{total_time:.1f}ms"

        # Log slow requests
        if total_time > 1000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path}",
                extra={
                    "duration_ms": total_time,
                    "path": request.url.path,
                    "method": request.method,
                }
            )

        return response
```

### Database Timing

```python
from sqlalchemy import event

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.perf_counter() - conn.info["query_start_time"].pop(-1)
    request = get_current_request()
    if request:
        request.state.db_time = getattr(request.state, "db_time", 0) + total
```

---

## Slow Request Warnings

### Threshold

| Threshold | Action |
|-----------|--------|
| > 500ms | Log at WARNING level |
| > 1000ms | Log at WARNING level + metric increment |
| > 5000ms | Log at ERROR level + alert |

### Implementation

```python
SLOW_REQUEST_THRESHOLD_MS = 1000
VERY_SLOW_REQUEST_THRESHOLD_MS = 5000

class SlowRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        if duration_ms > VERY_SLOW_REQUEST_THRESHOLD_MS:
            logger.error(
                f"Very slow request: {request.method} {request.url.path}",
                extra={
                    "duration_ms": duration_ms,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                }
            )
            metrics.increment("http.slow_request.very_slow")

        elif duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                f"Slow request: {request.method} {request.url.path}",
                extra={
                    "duration_ms": duration_ms,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                }
            )
            metrics.increment("http.slow_request.slow")

        return response
```

---

## Service Health Monitoring

### Periodic Checks

```python
import asyncio

class ServiceHealthMonitor:
    def __init__(self):
        self.health_status = {}
        self.check_interval = 30  # seconds

    async def start(self):
        asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        while True:
            await self._check_all_services()
            await asyncio.sleep(self.check_interval)

    async def _check_all_services(self):
        checks = [
            ("database", self._check_database),
            ("ollama", self._check_ollama),
            ("whisper", self._check_whisper),
            ("clamav", self._check_clamav),
        ]

        for name, check_fn in checks:
            try:
                status = await asyncio.wait_for(check_fn(), timeout=10)
                self.health_status[name] = status
            except asyncio.TimeoutError:
                self.health_status[name] = {
                    "status": "unhealthy",
                    "error": "Health check timed out"
                }
            except Exception as e:
                self.health_status[name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

    def get_status(self) -> dict:
        return self.health_status
```

### Metrics Tracked

| Metric | Source | Description |
|--------|--------|-------------|
| `http.requests.total` | Middleware | Total HTTP requests |
| `http.request.duration` | Middleware | Request duration histogram |
| `http.errors.total` | Middleware | Error responses (4xx, 5xx) |
| `db.query.duration` | SQLAlchemy | Database query duration |
| `ai.request.duration` | Ollama | AI inference duration |
| `ai.request.errors` | Ollama | AI request failures |
| `email.sent.total` | Resend | Emails sent |
| `email.send.duration` | Resend | Email send latency |
| `files.upload.total` | Upload handler | Files uploaded |
| `files.scan.duration` | ClamAV | Virus scan duration |
| `slow.request.count` | Middleware | Requests > 1s |

### Alert Conditions

```python
ALERTS = {
    "service_down": {
        "condition": "service.status == 'unhealthy' for > 2 minutes",
        "severity": "critical",
        "action": "page on-call engineer"
    },
    "high_error_rate": {
        "condition": "error_rate > 5% for > 5 minutes",
        "severity": "high",
        "action": "notify team"
    },
    "slow_requests": {
        "condition": "slow_request_rate > 10% for > 10 minutes",
        "severity": "medium",
        "action": "investigate"
    },
    "high_latency": {
        "condition": "p99_latency > 2000ms for > 5 minutes",
        "severity": "medium",
        "action": "investigate"
    }
}
```
