"""
HRMS Shared Schemas
Base schemas, API response wrapper, and pagination.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class HRMSBaseModel(BaseModel):
    """Base model with common config."""
    model_config = {"from_attributes": True, "str_strip_whitespace": True}


class ApiResponse(HRMSBaseModel, Generic[T]):
    """Consistent API response wrapper."""
    success: bool = True
    data: T | None = None
    message: str | None = None
    error: str | None = None


class PaginatedResponse(HRMSBaseModel, Generic[T]):
    """Paginated list response."""
    success: bool = True
    items: list[T] = []
    total: int = 0
    page: int = 1
    limit: int = 20
    has_next: bool = False
    next_cursor: str | None = None


class ErrorResponse(HRMSBaseModel):
    """Error response schema."""
    success: bool = False
    error: str
    detail: Any = None
    status_code: int = 500


class HealthResponse(HRMSBaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = ""
    database: bool = False
    redis: bool = False
    timestamp: str = ""
