"""
Unit Tests — HRMS Schemas
Tests for Pydantic schema validation.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.leave import LeaveCreate
from app.schemas.employee import EmployeeSelfUpdate


class TestApiResponse:
    def test_success_response(self):
        resp = ApiResponse(data={"key": "value"}, success=True, message="ok")
        assert resp.success is True
        assert resp.data == {"key": "value"}

    def test_error_response(self):
        resp = ApiResponse(success=False, error="something failed")
        assert resp.success is False
        assert resp.error == "something failed"


class TestPaginatedResponse:
    def test_pagination(self):
        resp = PaginatedResponse(
            items=[1, 2, 3],
            total=10,
            page=1,
            limit=3,
            has_next=True,
        )
        assert len(resp.items) == 3
        assert resp.has_next is True

    def test_last_page(self):
        resp = PaginatedResponse(
            items=[8, 9, 10],
            total=10,
            page=4,
            limit=3,
            has_next=False,
        )
        assert resp.has_next is False


class TestLeaveCreate:
    def test_valid_leave(self):
        leave = LeaveCreate(
            leave_type="paid",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 5),
        )
        assert leave.leave_type == "paid"

    def test_all_leave_types(self):
        for lt in ["paid", "sick", "unpaid", "bereavement", "medical"]:
            leave = LeaveCreate(
                leave_type=lt,
                start_date=date(2026, 8, 1),
                end_date=date(2026, 8, 1),
            )
            assert leave.leave_type == lt


class TestEmployeeSelfUpdate:
    def test_valid_update(self):
        update = EmployeeSelfUpdate(phone="+91 98765 43210")
        assert update.phone == "+91 98765 43210"

    def test_empty_update(self):
        update = EmployeeSelfUpdate()
        assert update.phone is None
