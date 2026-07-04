"""
Unit Tests — HRMS Custom Exceptions
Tests for all exception classes and their HTTP status codes.
"""

from __future__ import annotations

import pytest

from app.core.exceptions import (
    AdminRequiredError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    DoubleCheckInError,
    DoubleCheckOutError,
    EmailDeliveryError,
    EmployeeDeactivatedError,
    FileTooLargeError,
    FileUploadError,
    ForbiddenError,
    GeofenceViolationError,
    HRMSError,
    InsufficientBalanceError,
    InvalidFileTypeError,
    InvalidTokenError,
    NotFoundError,
    OllamaTimeoutError,
    OverlappingLeaveError,
    PayrollAlreadyGeneratedError,
    RateLimitExceededError,
    TokenExpiredError,
    ValidationError,
    VirusDetectedError,
    WhisperTimeoutError,
)


class TestHRMSErrorBase:
    def test_default_message(self):
        err = HRMSError()
        assert err.message == "An unexpected error occurred"
        assert err.status_code == 500

    def test_custom_message(self):
        err = HRMSError(message="custom", status_code=418)
        assert err.message == "custom"
        assert err.status_code == 418

    def test_inheritance(self):
        assert issubclass(AuthenticationError, HRMSError)
        assert issubclass(ForbiddenError, HRMSError)
        assert issubclass(NotFoundError, HRMSError)
        assert issubclass(ConflictError, HRMSError)


class TestAuthenticationErrors:
    def test_authentication_error(self):
        err = AuthenticationError()
        assert err.status_code == 401
        assert "required" in err.message.lower()

    def test_token_expired(self):
        err = TokenExpiredError()
        assert err.status_code == 401
        assert "expired" in err.message.lower()

    def test_invalid_token(self):
        err = InvalidTokenError()
        assert err.status_code == 401

    def test_invalid_token_custom_message(self):
        err = InvalidTokenError("bad token")
        assert err.message == "bad token"


class TestForbiddenErrors:
    def test_forbidden(self):
        err = ForbiddenError()
        assert err.status_code == 403

    def test_admin_required(self):
        err = AdminRequiredError()
        assert err.status_code == 403
        assert "admin" in err.message.lower()


class TestNotFoundErrors:
    def test_not_found(self):
        err = NotFoundError("Employee")
        assert err.status_code == 404
        assert "Employee" in err.message

    def test_not_found_with_id(self):
        err = NotFoundError("Employee", "123")
        assert "123" in err.message


class TestConflictErrors:
    def test_conflict(self):
        err = ConflictError()
        assert err.status_code == 409

    def test_overlapping_leave(self):
        err = OverlappingLeaveError()
        assert err.status_code == 409
        assert "overlap" in err.message.lower()

    def test_double_checkin(self):
        err = DoubleCheckInError()
        assert err.status_code == 409

    def test_double_checkout(self):
        err = DoubleCheckOutError()
        assert err.status_code == 409

    def test_payroll_already_generated(self):
        err = PayrollAlreadyGeneratedError(1, 2026)
        assert err.status_code == 409


class TestValidationError:
    def test_insufficient_balance(self):
        err = InsufficientBalanceError("paid", 5, 10)
        assert err.status_code == 400
        assert "paid" in err.message
        assert "5" in err.message
        assert "10" in err.message

    def test_validation_error(self):
        err = ValidationError()
        assert err.status_code == 422

    def test_bad_request(self):
        err = BadRequestError()
        assert err.status_code == 400


class TestFileUploadErrors:
    def test_file_upload(self):
        err = FileUploadError()
        assert err.status_code == 400

    def test_file_too_large(self):
        err = FileTooLargeError(5)
        assert err.status_code == 413
        assert "5MB" in err.message

    def test_invalid_file_type(self):
        err = InvalidFileTypeError("text/html")
        assert err.status_code == 415

    def test_virus_detected(self):
        err = VirusDetectedError()
        assert err.status_code == 400


class TestAIErrors:
    def test_ollama_timeout(self):
        err = OllamaTimeoutError()
        assert err.status_code == 503

    def test_whisper_timeout(self):
        err = WhisperTimeoutError()
        assert err.status_code == 503


class TestMiscErrors:
    def test_email_delivery(self):
        err = EmailDeliveryError()
        assert err.status_code == 502

    def test_geofence_violation(self):
        err = GeofenceViolationError()
        assert err.status_code == 403

    def test_rate_limit(self):
        err = RateLimitExceededError(60)
        assert err.status_code == 429
        assert err.headers["Retry-After"] == "60"

    def test_employee_deactivated(self):
        err = EmployeeDeactivatedError()
        assert err.status_code == 400
