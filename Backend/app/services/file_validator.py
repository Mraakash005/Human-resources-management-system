"""
HRMS File Validation Service
MIME validation, size checks, ClamAV virus scanning.
"""

from __future__ import annotations

import logging
import magic
import httpx
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    VirusDetectedError,
)

logger = logging.getLogger(__name__)

CLAMAV_TIMEOUT = 30.0


async def validate_file(
    file: UploadFile,
    allowed_types: set[str],
    max_mb: int,
    scan_virus: bool = True,
) -> bytes:
    """
    Validate uploaded file: size, MIME type, and optional virus scan.
    Returns file contents on success.
    """
    settings = get_settings()
    contents = await file.read()
    await file.seek(0)

    # Size check
    max_bytes = max_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise FileTooLargeError(max_mb=max_mb)

    # MIME type check (reads file header, not extension)
    detected_mime = magic.from_buffer(contents, mime=True)
    if detected_mime not in allowed_types:
        raise InvalidFileTypeError(detected_mime)

    # ClamAV virus scan
    if scan_virus:
        try:
            async with httpx.AsyncClient(timeout=CLAMAV_TIMEOUT) as client:
                resp = await client.post(
                    f"{settings.CLAMAV_URL}/scan",
                    files={"file": (file.filename, contents, detected_mime)},
                )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("infected"):
                    logger.warning(
                        "Virus detected in upload: filename=%s mime=%s",
                        file.filename,
                        detected_mime,
                    )
                    raise VirusDetectedError()
            else:
                logger.warning("ClamAV scan returned %d — proceeding without scan", resp.status_code)
        except httpx.RequestError:
            logger.warning("ClamAV unreachable — proceeding without virus scan")

    return contents


def get_document_types() -> set[str]:
    """Return allowed MIME types for document uploads."""
    settings = get_settings()
    return settings.ALLOWED_DOCUMENT_MIMES


def get_audio_types() -> set[str]:
    """Return allowed MIME types for audio uploads."""
    settings = get_settings()
    return settings.ALLOWED_AUDIO_MIMES
