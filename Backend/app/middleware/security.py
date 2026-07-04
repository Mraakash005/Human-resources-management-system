"""
HRMS Security Headers Middleware
Adds security headers to all responses.
"""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all HTTP responses."""

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(self), payment=()",
        "X-Permitted-Cross-Domain-Policies": "none",
        "Cache-Control": "no-store, no-cache, must-revalidate, private",
        "Pragma": "no-cache",
    }

    HSTS_HEADER = "max-age=31536000; includeSubDomains; preload"

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        for key, value in self.SECURITY_HEADERS.items():
            response.headers[key] = value

        # HSTS only over HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = self.HSTS_HEADER

        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]

        return response
