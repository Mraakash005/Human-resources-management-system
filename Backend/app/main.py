"""
HRMS Enterprise Backend — Main Application
Production FastAPI application with all middleware, routers, and lifecycle management.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import db_manager
from app.core.exceptions import HRMSError
from app.core.logging import RequestLogger, setup_logging
from app.core.redis import redis_manager

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    logger.info("Starting HRMS %s (%s)", settings.APP_VERSION, settings.ENVIRONMENT.value)

    # Initialize database
    await db_manager.connect()

    # Initialize Redis
    await redis_manager.connect()

    # Initialize APScheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()

    # Register background jobs
    from app.jobs import register_jobs
    register_jobs(scheduler)
    scheduler.start()
    logger.info("APScheduler started with %d jobs", len(scheduler.get_jobs()))

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    await redis_manager.disconnect()
    await db_manager.disconnect()
    logger.info("HRMS shutdown complete")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise HR Management System API",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # ── Security Headers ────────────────────────────────────────
    from app.middleware.security import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)

    # ── Rate Limiting ───────────────────────────────────────────
    from app.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(
        RateLimitMiddleware,
        general_limit=settings.RATE_LIMIT_PER_MINUTE,
        ai_limit=settings.RATE_LIMIT_AI_PER_MINUTE,
    )

    # ── Request middleware ───────────────────────────────────────
    @app.middleware("http")
    async def request_middleware(request: Request, call_next) -> Response:
        req_id = uuid.uuid4().hex[:16]
        start = time.perf_counter()

        with RequestLogger(method=request.method, path=request.url.path):
            response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        if duration_ms > 1000:
            logger.warning("Slow request: %s %s (%.1fms)", request.method, request.url.path, duration_ms)

        return response

    # ── Exception handler ───────────────────────────────────────
    @app.exception_handler(HRMSError)
    async def hrms_error_handler(request: Request, exc: HRMSError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.message,
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
            headers=exc.headers,
        )

    # ── Health check ────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        db_ok = await db_manager.health_check()
        redis_ok = await redis_manager.health_check()
        return {
            "status": "healthy" if db_ok and redis_ok else "degraded",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT.value,
            "database": db_ok,
            "redis": redis_ok,
        }

    # ── Register routers ────────────────────────────────────────
    from app.routers import (
        analytics,
        attendance,
        chat,
        chatbot,
        dashboard,
        employees,
        leave,
        nudges,
        payroll,
        voice,
        webhooks,
    )

    prefix = settings.API_V1_PREFIX
    app.include_router(employees.router, prefix=prefix)
    app.include_router(attendance.router, prefix=prefix)
    app.include_router(leave.router, prefix=prefix)
    app.include_router(payroll.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(chatbot.router, prefix=prefix)
    app.include_router(voice.router, prefix=prefix)
    app.include_router(chat.router, prefix=prefix)
    app.include_router(nudges.router, prefix=prefix)
    app.include_router(analytics.router, prefix=prefix)
    # Webhooks at root level (Clerk sends to /api/v1/webhooks/clerk)
    app.include_router(webhooks.router, prefix=prefix)

    return app


app = create_app()
