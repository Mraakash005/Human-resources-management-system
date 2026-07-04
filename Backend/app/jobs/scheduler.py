"""
HRMS Background Jobs Module
Centralized job definitions for APScheduler.
All scheduled tasks are registered here for discoverability.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


def register_jobs(scheduler: "AsyncIOScheduler") -> None:
    """Register all background jobs with the scheduler."""

    # Burnout detection — nightly at 2 AM
    from app.services.attendance_analytics import check_burnout
    scheduler.add_job(
        check_burnout,
        "cron",
        hour=2,
        minute=0,
        id="burnout_check",
        name="Burnout Detection Scan",
        replace_existing=True,
    )
    logger.info("Registered job: burnout_check (daily at 02:00)")

    # Monthly payroll — last day of month at 23:59
    from app.services.payroll_calc import run_monthly_payroll
    scheduler.add_job(
        run_monthly_payroll,
        "cron",
        day="last",
        hour=23,
        minute=59,
        id="monthly_payroll",
        name="Monthly Payroll Generation",
        replace_existing=True,
    )
    logger.info("Registered job: monthly_payroll (last day at 23:59)")

    # Nudge checks — daily at 8 AM
    from app.services.nudge_service import run_nudge_checks
    scheduler.add_job(
        run_nudge_checks,
        "cron",
        hour=8,
        minute=0,
        id="nudge_checks",
        name="Daily Nudge Generation",
        replace_existing=True,
    )
    logger.info("Registered job: nudge_checks (daily at 08:00)")

    # Cache cleanup — every 30 minutes
    scheduler.add_job(
        _cleanup_stale_cache,
        "interval",
        minutes=30,
        id="cache_cleanup",
        name="Stale Cache Cleanup",
        replace_existing=True,
    )
    logger.info("Registered job: cache_cleanup (every 30 minutes)")

    # Health monitoring — every 5 minutes
    scheduler.add_job(
        _health_monitor,
        "interval",
        minutes=5,
        id="health_monitor",
        name="Service Health Monitor",
        replace_existing=True,
    )
    logger.info("Registered job: health_monitor (every 5 minutes)")

    logger.info("All background jobs registered successfully")


async def _cleanup_stale_cache() -> None:
    """Clean up expired cache keys and temp data."""
    from app.core.redis import redis_manager
    try:
        # Clean up webhook event cache (replay protection)
        await redis_manager.delete_pattern("webhook_event:*")
        logger.debug("Stale cache cleanup completed")
    except Exception:
        logger.exception("Cache cleanup failed")


async def _health_monitor() -> None:
    """Monitor service health and log warnings."""
    from app.core.database import db_manager
    from app.core.redis import redis_manager

    issues = []

    if not await db_manager.health_check():
        issues.append("database")

    if not await redis_manager.health_check():
        issues.append("redis")

    if issues:
        logger.warning("Health monitor detected issues: %s", ", ".join(issues))
    else:
        logger.debug("All services healthy")
