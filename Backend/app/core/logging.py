"""
HRMS Structured Logging
JSON-formatted logs with correlation IDs, request IDs, performance timings.
All logs are structured and machine-parseable.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings

# Context variables for request-scoped data
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON with structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context
        req_id = request_id_var.get("")
        if req_id:
            log_entry["request_id"] = req_id

        corr_id = correlation_id_var.get("")
        if corr_id:
            log_entry["correlation_id"] = corr_id

        uid = user_id_var.get("")
        if uid:
            log_entry["user_id"] = uid

        # Add exception info if present
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields
        for key in ("status_code", "method", "path", "duration_ms", "db_duration_ms", "cache_hit"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        req_id = request_id_var.get("")
        req_part = f" [{req_id[:8]}]" if req_id else ""
        return (
            f"{color}{record.levelname:<8}{self.RESET}"
            f"{req_part} "
            f"{record.name}: {record.getMessage()}"
        )


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT.value == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Suppress noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class RequestLogger:
    """Context manager for request-scoped logging."""

    def __init__(self, method: str = "", path: str = "") -> None:
        self.method = method
        self.path = path
        self.start_time: float = 0
        self.request_id: str = ""

    def __enter__(self) -> "RequestLogger":
        self.request_id = uuid.uuid4().hex[:16]
        request_id_var.set(self.request_id)
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration_ms = round((time.perf_counter() - self.start_time) * 1000, 2)
        logger = logging.getLogger("hrms.request")
        extra = {
            "method": self.method,
            "path": self.path,
            "duration_ms": duration_ms,
            "request_id": self.request_id,
        }
        if exc_type:
            logger.error("Request failed: %s %s (%.1fms)", self.method, self.path, duration_ms, extra=extra)
        else:
            logger.info("Request completed: %s %s (%.1fms)", self.method, self.path, duration_ms, extra=extra)
        request_id_var.set("")
