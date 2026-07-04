"""
HRMS Jobs Package
Background task definitions for APScheduler.
"""

from app.jobs.scheduler import register_jobs

__all__ = ["register_jobs"]
