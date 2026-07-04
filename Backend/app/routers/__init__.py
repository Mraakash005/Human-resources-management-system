"""
HRMS Routers — Public API
Import all routers for registration in main.py.
"""

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

__all__ = [
    "analytics",
    "attendance",
    "chat",
    "chatbot",
    "dashboard",
    "employees",
    "leave",
    "nudges",
    "payroll",
    "voice",
    "webhooks",
]
