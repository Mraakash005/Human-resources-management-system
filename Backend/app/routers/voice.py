"""
HRMS Voice Router
Whisper transcription and voice-to-leave parsing.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel

from app.core.auth import get_current_user, TokenPayload
from app.core.exceptions import AIServiceError
from app.schemas.common import ApiResponse
from app.services.file_validator import validate_file, get_audio_types

router = APIRouter(prefix="/voice", tags=["Voice"])


class TranscriptResponse(BaseModel):
    transcript: str
    parsed: dict | None = None


VOICE_PARSE_PROMPT = """Extract leave details from this voice message. Return ONLY valid JSON.
Voice message: "{transcript}"

JSON format:
{{
  "start_date": "YYYY-MM-DD or null",
  "end_date": "YYYY-MM-DD or null",
  "leave_type": "paid|sick|medical|bereavement|unpaid or null",
  "reason": "one sentence summary",
  "days": number or null
}}
Use today's date as reference: {today}"""


@router.post("/transcribe", response_model=ApiResponse[TranscriptResponse])
async def transcribe_voice(
    file: UploadFile,
    user: TokenPayload = Depends(get_current_user),
) -> ApiResponse[TranscriptResponse]:
    # Validate file
    contents = await validate_file(file, get_audio_types(), max_mb=10)

    # Send to Whisper
    import httpx
    from app.core.config import get_settings
    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.WHISPER_URL}/asr?language=en&output=json",
                files={"audio_file": (file.filename, contents, file.content_type)},
            )
        if resp.status_code != 200:
            raise AIServiceError("Whisper transcription failed")

        transcript = resp.json().get("text", "")
    except httpx.RequestError:
        raise AIServiceError("Whisper service unavailable")

    # Parse with Ollama
    prompt = VOICE_PARSE_PROMPT.format(transcript=transcript, today=date.today().isoformat())
    try:
        from app.services.ollama_client import call_ollama_json
        parsed = await call_ollama_json(prompt)
    except Exception:
        parsed = None

    return ApiResponse(data=TranscriptResponse(transcript=transcript, parsed=parsed))
