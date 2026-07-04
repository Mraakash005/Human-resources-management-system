"""
Unit Tests — HRMS Utility Functions
Tests for helpers: Haversine, validators, date utils, payroll tax.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.utils.helpers import (
    compute_tax,
    count_business_days,
    haversine_distance,
    is_ip_in_subnet,
    is_valid_email,
    is_valid_phone,
    is_valid_uuid,
    is_within_geofence,
    safe_uuid,
    sanitize_string,
    validate_date_range,
    validate_employee_role,
    validate_leave_status,
    validate_leave_type,
)


class TestHaversineDistance:
    def test_same_point_returns_zero(self):
        assert haversine_distance(12.9716, 77.5946, 12.9716, 77.5946) == 0.0

    def test_known_distance_bangalore_to_delhi(self):
        # Bangalore (12.9716, 77.5946) to Delhi (28.6139, 77.2090)
        distance = haversine_distance(12.9716, 77.5946, 28.6139, 77.2090)
        assert 1_700_000 < distance < 2_100_000  # ~1740 km

    def test_symmetric(self):
        d1 = haversine_distance(10.0, 20.0, 30.0, 40.0)
        d2 = haversine_distance(30.0, 40.0, 10.0, 20.0)
        assert abs(d1 - d2) < 0.001


class TestGeofence:
    def test_within_geofence(self):
        assert is_within_geofence(12.9716, 77.5946, 12.9716, 77.5946, 150) is True

    def test_outside_geofence(self):
        # ~1km away
        assert is_within_geofence(12.9800, 77.6000, 12.9716, 77.5946, 150) is False

    def test_borderline_geofence(self):
        # ~100m away
        assert is_within_geofence(12.9725, 77.5946, 12.9716, 77.5946, 150) is True


class TestIPSubnet:
    def test_ip_in_subnet(self):
        assert is_ip_in_subnet("192.168.1.100", "192.168.1.0/24") is True

    def test_ip_not_in_subnet(self):
        assert is_ip_in_subnet("10.0.0.1", "192.168.1.0/24") is False

    def test_invalid_ip(self):
        assert is_ip_in_subnet("not-an-ip", "192.168.1.0/24") is False

    def test_invalid_subnet(self):
        assert is_ip_in_subnet("192.168.1.1", "invalid-subnet") is False


class TestDateHelpers:
    def test_count_business_days_same_day(self):
        d = date(2026, 7, 6)  # Monday
        assert count_business_days(d, d) == 1

    def test_count_business_days_full_week(self):
        start = date(2026, 7, 6)  # Monday
        end = date(2026, 7, 10)  # Friday
        assert count_business_days(start, end) == 5

    def test_count_business_days_with_weekend(self):
        start = date(2026, 7, 4)  # Saturday
        end = date(2026, 7, 12)  # Sunday
        assert count_business_days(start, end) == 5

    def test_validate_date_range_valid(self):
        assert validate_date_range(date(2026, 1, 1), date(2026, 12, 31)) is True

    def test_validate_date_range_invalid(self):
        assert validate_date_range(date(2026, 12, 31), date(2026, 1, 1)) is False


class TestValidators:
    def test_valid_email(self):
        assert is_valid_email("user@company.com") is True

    def test_invalid_email(self):
        assert is_valid_email("not-an-email") is False

    def test_valid_phone(self):
        assert is_valid_phone("+91 98765 43210") is True

    def test_invalid_phone(self):
        assert is_valid_phone("123") is False

    def test_valid_uuid(self):
        assert is_valid_uuid("12345678-1234-5678-1234-567812345678") is True

    def test_invalid_uuid(self):
        assert is_valid_uuid("not-a-uuid") is False

    def test_validate_leave_type_valid(self):
        assert validate_leave_type("paid") is True
        assert validate_leave_type("sick") is True
        assert validate_leave_type("unpaid") is True
        assert validate_leave_type("bereavement") is True
        assert validate_leave_type("medical") is True

    def test_validate_leave_type_invalid(self):
        assert validate_leave_type("vacation") is False

    def test_validate_leave_status_valid(self):
        assert validate_leave_status("pending") is True
        assert validate_leave_status("approved") is True
        assert validate_leave_status("rejected") is True
        assert validate_leave_status("cancelled") is True

    def test_validate_leave_status_invalid(self):
        assert validate_leave_status("unknown") is False

    def test_validate_employee_role_valid(self):
        assert validate_employee_role("admin") is True
        assert validate_employee_role("employee") is True

    def test_validate_employee_role_invalid(self):
        assert validate_employee_role("superadmin") is False


class TestSanitizeString:
    def test_strips_whitespace(self):
        assert sanitize_string("  hello  ") == "hello"

    def test_truncates(self):
        assert len(sanitize_string("a" * 1000, max_length=50)) == 50

    def test_removes_control_chars(self):
        assert sanitize_string("hello\x00world") == "helloworld"


class TestComputeTax:
    def test_zero_tax(self):
        assert compute_tax(200000) == 0.0  # Below 2.5L after deduction

    def test_medium_income(self):
        tax = compute_tax(800000)  # 8L gross
        assert tax > 0
        assert tax < 200000  # Reasonable bound

    def test_high_income(self):
        tax = compute_tax(2000000)  # 20L gross
        assert tax > 200000


class TestSafeUuid:
    def test_valid_uuid_string(self):
        result = safe_uuid("12345678-1234-5678-1234-567812345678")
        assert isinstance(result, uuid.UUID)

    def test_invalid_string(self):
        assert safe_uuid("not-a-uuid") is None

    def test_none(self):
        assert safe_uuid(None) is None

    def test_uuid_object(self):
        u = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert safe_uuid(u) == u
