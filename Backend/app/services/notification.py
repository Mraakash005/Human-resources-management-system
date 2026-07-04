"""
HRMS Email Notification Service
Complete Resend integration with retry, templates, and audit.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import EmailDeliveryError

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


class EmailService:
    """Handles all email delivery via Resend."""

    def __init__(self) -> None:
        self._settings = None

    def _get_settings(self):
        """Lazy-load settings to avoid import-time crashes."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def api_key(self) -> str:
        return self._get_settings().RESEND_API_KEY

    @property
    def from_email(self) -> str:
        return self._get_settings().EMAIL_FROM

    @property
    def hr_email(self) -> str:
        return self._get_settings().HR_EMAIL

    async def send(
        self,
        to: str | list[str],
        subject: str,
        html: str,
        text: str | None = None,
        reply_to: str | None = None,
        retries: int = MAX_RETRIES,
    ) -> dict[str, Any]:
        """Send an email via Resend with retry logic."""
        recipients = [to] if isinstance(to, str) else to

        payload: dict[str, Any] = {
            "from": self.from_email,
            "to": recipients,
            "subject": subject,
            "html": html,
        }
        if text:
            payload["text"] = text
        if reply_to:
            payload["reply_to"] = reply_to

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        RESEND_API_URL, json=payload, headers=headers
                    )
                if resp.status_code in (200, 201):
                    result = resp.json()
                    logger.info(
                        "Email sent: to=%s subject='%s' id=%s",
                        recipients,
                        subject,
                        result.get("id"),
                    )
                    return result

                last_error = EmailDeliveryError(
                    f"Resend returned {resp.status_code}: {resp.text}"
                )
                logger.warning(
                    "Email attempt %d/%d failed: %d %s",
                    attempt,
                    retries,
                    resp.status_code,
                    resp.text[:200],
                )
            except httpx.TimeoutException:
                last_error = EmailDeliveryError("Email request timed out")
                logger.warning("Email attempt %d/%d timed out", attempt, retries)
            except httpx.RequestError as exc:
                last_error = EmailDeliveryError(f"Email request error: {exc}")
                logger.warning("Email attempt %d/%d network error: %s", attempt, retries, exc)

            if attempt < retries:
                import asyncio
                await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)

        logger.error(
            "Email delivery failed after %d attempts: to=%s subject='%s'",
            retries,
            recipients,
            subject,
        )
        raise last_error or EmailDeliveryError("Unknown email error")

    async def send_leave_notification(
        self, to: str, subject: str, body: str
    ) -> dict[str, Any]:
        """Send a leave-related email."""
        settings = self._get_settings()
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a1a2e;">{subject}</h2>
            <div style="padding: 16px; background: #f8f9fa; border-radius: 8px; white-space: pre-wrap;">
                {body}
            </div>
            <p style="color: #666; font-size: 12px; margin-top: 24px;">
                This is an automated message from {settings.COMPANY_NAME} HRMS.
            </p>
        </div>
        """
        return await self.send(to=to, subject=subject, html=html)

    async def send_welcome_email(self, to: str, name: str) -> dict[str, Any]:
        """Send a welcome email to a new employee."""
        settings = self._get_settings()
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a1a2e;">Welcome to {settings.COMPANY_NAME}!</h2>
            <p>Hi {name},</p>
            <p>Your HRMS account has been created. You can now sign in using your registered email.</p>
            <p>If you have any questions, please contact HR at {self.hr_email}.</p>
            <p style="color: #666; font-size: 12px; margin-top: 24px;">
                — {settings.COMPANY_NAME} HR Team
            </p>
        </div>
        """
        return await self.send(to=to, subject=f"Welcome to {settings.COMPANY_NAME}!", html=html)

    async def send_pay_stub_email(self, to: str, name: str, month: int, year: int) -> dict[str, Any]:
        """Send pay stub ready notification."""
        settings = self._get_settings()
        import calendar
        month_name = calendar.month_name[month]
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a1a2e;">Pay Stub Ready</h2>
            <p>Hi {name},</p>
            <p>Your pay stub for <strong>{month_name} {year}</strong> is now available in the HRMS portal.</p>
            <p>Please log in to download your pay stub.</p>
            <p style="color: #666; font-size: 12px; margin-top: 24px;">
                — {settings.COMPANY_NAME} HR Team
            </p>
        </div>
        """
        return await self.send(to=to, subject=f"Your {month_name} {year} pay stub is ready", html=html)

    async def send_burnout_alert(
        self, to: str, employee_name: str, signal: str, severity: str
    ) -> dict[str, Any]:
        """Send burnout alert to HR."""
        settings = self._get_settings()
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc2626;">Burnout Alert — {severity.upper()}</h2>
            <p><strong>Employee:</strong> {employee_name}</p>
            <p><strong>Signal:</strong> {signal}</p>
            <p><strong>Severity:</strong> {severity}</p>
            <p>Please review this employee's work patterns and consider appropriate action.</p>
            <p style="color: #666; font-size: 12px; margin-top: 24px;">
                — {settings.COMPANY_NAME} HRMS Burnout Detection System
            </p>
        </div>
        """
        return await self.send(to=to, subject=f"Burnout Alert: {employee_name} ({severity})", html=html)


email_service = EmailService()
