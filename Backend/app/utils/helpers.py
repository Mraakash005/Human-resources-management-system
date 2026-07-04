"""
HRMS Utility Functions
Haversine distance, date helpers, input validators, and common helpers.
"""

from __future__ import annotations

import math
import re
import uuid
from datetime import date, datetime, timezone
from typing import Any


# ── Geospatial ──────────────────────────────────────────────────


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula. Returns distance in meters.
    """
    R = 6_371_000  # Earth's radius in meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_within_geofence(
    employee_lat: float,
    employee_lng: float,
    office_lat: float,
    office_lng: float,
    radius_meters: int = 150,
) -> bool:
    """Check if employee coordinates are within the office geofence."""
    distance = haversine_distance(employee_lat, employee_lng, office_lat, office_lng)
    return distance <= radius_meters


def is_ip_in_subnet(ip: str, subnet: str) -> bool:
    """Check if an IP address is within a CIDR subnet (e.g., 192.168.1.0/24)."""
    try:
        import ipaddress
        return ipaddress.ip_address(ip) in ipaddress.ip_network(subnet, strict=False)
    except (ValueError, TypeError):
        return False


# ── Date & Time Helpers ─────────────────────────────────────────


def count_business_days(start: date, end: date) -> int:
    """Count business days (Mon-Fri) between start and end dates, inclusive."""
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current = date.fromordinal(current.toordinal() + 1)
    return days


def get_current_year() -> int:
    return date.today().year


def get_current_month() -> int:
    return date.today().month


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def get_month_date_range(year: int, month: int) -> tuple[date, date]:
    """Get the first and last date of a given month."""
    import calendar
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    return first_day, last_day


def parse_iso_date(date_str: str) -> date:
    """Parse an ISO format date string."""
    return date.fromisoformat(date_str)


def utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


# ── Input Validators ────────────────────────────────────────────


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[\d\s\-()]{7,20}$")
UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone))


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize a string: strip whitespace, truncate, remove control characters."""
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    return value.strip()[:max_length]


def validate_date_range(start: date, end: date) -> bool:
    """Validate that start date is not after end date."""
    return start <= end


def validate_leave_type(leave_type: str) -> bool:
    """Validate leave type against allowed values."""
    return leave_type in ("paid", "sick", "unpaid", "bereavement", "medical")


def validate_leave_status(status: str) -> bool:
    """Validate leave status against allowed values."""
    return status in ("pending", "approved", "rejected", "cancelled")


def validate_employee_role(role: str) -> bool:
    """Validate employee role against allowed values."""
    return role in ("admin", "employee")


# ── Payroll Helpers ─────────────────────────────────────────────


def compute_tax(gross_annual: float, standard_deduction: int = 50000) -> float:
    """
    Compute Indian income tax (old regime) on annual salary.
    Slabs: 0-2.5L: 0%, 2.5-5L: 5%, 5-10L: 20%, 10L+: 30%
    """
    taxable = max(0, gross_annual - standard_deduction)

    tax = 0.0
    slabs = [
        (250000, 0.0),
        (250000, 0.05),
        (500000, 0.20),
        (float("inf"), 0.30),
    ]

    remaining = taxable
    for slab_limit, rate in slabs:
        if remaining <= 0:
            break
        taxable_in_slab = min(remaining, slab_limit)
        tax += taxable_in_slab * rate
        remaining -= taxable_in_slab

    # Add 4% health & education cess
    cess = tax * 0.04
    return round(tax + cess, 2)


# ── UUID Helpers ────────────────────────────────────────────────


def safe_uuid(value: Any) -> uuid.UUID | None:
    """Safely convert a value to UUID, returning None on failure."""
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None
