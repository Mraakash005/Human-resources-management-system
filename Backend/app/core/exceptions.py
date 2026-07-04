"""
HRMS Custom Exceptions
Centralized exception system with typed HTTP errors.
Every error produces a meaningful response, meaningful log, and correct HTTP status.
"""

from __future__ import annotations

from typing import Any


class HRMSError(Exception):
    """Base exception for all HRMS errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        detail: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(self.message)


class AuthenticationError(HRMSError):
    """401 — Invalid or missing credentials."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message=message, status_code=401)


class TokenExpiredError(HRMSError):
    """401 — JWT token has expired."""

    def __init__(self) -> None:
        super().__init__(
            message="Token has expired. Please sign in again.",
            status_code=401,
        )


class InvalidTokenError(HRMSError):
    """401 — JWT token is invalid."""

    def __init__(self, message: str = "Invalid authentication token") -> None:
        super().__init__(message=message, status_code=401)


class ForbiddenError(HRMSError):
    """403 — Insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, status_code=403)


class AdminRequiredError(ForbiddenError):
    """403 — Admin role required."""

    def __init__(self) -> None:
        super().__init__(message="Admin access required")


class NotFoundError(HRMSError):
    """404 — Resource not found."""

    def __init__(self, resource: str = "Resource", resource_id: Any = None) -> None:
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=msg, status_code=404)


class ConflictError(HRMSError):
    """409 — Resource conflict (duplicate, overlap, state conflict)."""

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message=message, status_code=409)


class OverlappingLeaveError(ConflictError):
    """409 — Leave dates overlap with existing leave."""

    def __init__(self) -> None:
        super().__init__(
            message="Leave dates overlap with an existing approved leave request"
        )


class DoubleCheckInError(ConflictError):
    """409 — Employee already checked in today."""

    def __init__(self) -> None:
        super().__init__(message="Already checked in today")


class DoubleCheckOutError(ConflictError):
    """409 — Employee already checked out today."""

    def __init__(self) -> None:
        super().__init__(message="Already checked out today")


class InsufficientBalanceError(HRMSError):
    """400 — Insufficient leave balance."""

    def __init__(self, leave_type: str = "leave", available: int = 0, requested: int = 0) -> None:
        super().__init__(
            message=f"Insufficient {leave_type} balance. Available: {available}, Requested: {requested}",
            status_code=400,
        )


class ValidationError(HRMSError):
    """422 — Input validation error."""

    def __init__(self, message: str = "Validation failed", detail: Any = None) -> None:
        super().__init__(message=message, status_code=422, detail=detail)


class BadRequestError(HRMSError):
    """400 — Bad request."""

    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(message=message, status_code=400)


class FileUploadError(HRMSError):
    """400/413/415 — File upload validation error."""

    def __init__(self, message: str = "File upload failed", status_code: int = 400) -> None:
        super().__init__(message=message, status_code=status_code)


class FileTooLargeError(FileUploadError):
    """413 — File exceeds size limit."""

    def __init__(self, max_mb: int = 5) -> None:
        super().__init__(message=f"File too large. Maximum {max_mb}MB allowed.", status_code=413)


class InvalidFileTypeError(FileUploadError):
    """415 — Unsupported file type."""

    def __init__(self, detected_mime: str = "unknown") -> None:
        super().__init__(message=f"Invalid file type: {detected_mime}", status_code=415)


class VirusDetectedError(HRMSError):
    """400 — File failed virus scan."""

    def __init__(self) -> None:
        super().__init__(message="File failed virus scan. Upload rejected.", status_code=400)


class AIServiceError(HRMSError):
    """503 — AI service (Ollama/Whisper) unavailable."""

    def __init__(self, service: str = "AI service") -> None:
        super().__init__(
            message=f"{service} temporarily unavailable. Please try again later.",
            status_code=503,
        )


class OllamaTimeoutError(AIServiceError):
    """504 — Ollama request timed out."""

    def __init__(self) -> None:
        super().__init__(service="Ollama AI")


class WhisperTimeoutError(AIServiceError):
    """504 — Whisper transcription timed out."""

    def __init__(self) -> None:
        super().__init__(service="Whisper transcription")


class EmailDeliveryError(HRMSError):
    """502 — Email delivery failed."""

    def __init__(self, detail: str = "Email delivery failed") -> None:
        super().__init__(message=detail, status_code=502)


class GeofenceViolationError(HRMSError):
    """403 — Check-in outside office geofence."""

    def __init__(self) -> None:
        super().__init__(
            message="Check-in location is outside the office geofence",
            status_code=403,
        )


class RateLimitExceededError(HRMSError):
    """429 — Rate limit exceeded."""

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )


class PayrollAlreadyGeneratedError(ConflictError):
    """409 — Payroll already generated for this period."""

    def __init__(self, month: int, year: int) -> None:
        super().__init__(message=f"Payroll already generated for {month}/{year}")


class EmployeeDeactivatedError(HRMSError):
    """400 — Operation on deactivated employee."""

    def __init__(self) -> None:
        super().__init__(message="Employee account is deactivated", status_code=400)
