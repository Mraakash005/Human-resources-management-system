"""
HRMS Ollama AI Client
Async client for Ollama LLM with retry, timeout, circuit breaker, and JSON parsing.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import AIServiceError, OllamaTimeoutError

logger = logging.getLogger(__name__)

# Simple circuit breaker state
_circuit_failures = 0
_circuit_open = False
_CIRCUIT_THRESHOLD = 5
_CIRCUIT_RESET_TIMEOUT = 60


async def call_ollama(
    prompt: str,
    model: str | None = None,
    timeout: int | None = None,
    retries: int | None = None,
) -> str:
    """
    Call Ollama API with retry logic and circuit breaker.
    Returns the raw text response.
    """
    global _circuit_failures, _circuit_open

    if _circuit_open:
        raise AIServiceError("Ollama circuit breaker is open — service temporarily unavailable")

    settings = get_settings()
    model = model or settings.OLLAMA_DEFAULT_MODEL
    timeout = timeout or settings.OLLAMA_TIMEOUT
    retries = retries if retries is not None else settings.OLLAMA_MAX_RETRIES

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    last_error: Exception | None = None
    for attempt in range(1, retries + 2):
        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                )
            if resp.status_code == 200:
                result = resp.json()
                text = result.get("response", "").strip()
                _circuit_failures = 0
                return text

            last_error = AIServiceError(f"Ollama returned {resp.status_code}")
            logger.warning(
                "Ollama attempt %d/%d failed: %d",
                attempt, retries + 1, resp.status_code,
            )
        except httpx.TimeoutException:
            last_error = OllamaTimeoutError()
            logger.warning("Ollama attempt %d/%d timed out", attempt, retries + 1)
        except httpx.RequestError as exc:
            last_error = AIServiceError(f"Ollama connection error: {exc}")
            logger.warning("Ollama attempt %d/%d connection error: %s", attempt, retries + 1, exc)

        if attempt <= retries:
            import asyncio
            await asyncio.sleep(1 * attempt)

    _circuit_failures += 1
    if _circuit_failures >= _CIRCUIT_THRESHOLD:
        _circuit_open = True
        logger.error("Ollama circuit breaker OPEN — too many failures")
        import asyncio

        async def _reset_circuit() -> None:
            global _circuit_open, _circuit_failures
            await asyncio.sleep(_CIRCUIT_RESET_TIMEOUT)
            _circuit_open = False
            _circuit_failures = 0
            logger.info("Ollama circuit breaker reset")

        asyncio.create_task(_reset_circuit())

    raise last_error or AIServiceError("Ollama: unknown error")


async def call_ollama_json(
    prompt: str,
    model: str | None = None,
    retries: int | None = None,
) -> dict[str, Any]:
    """
    Call Ollama and parse the response as JSON.
    Strips markdown code fences and extracts JSON.
    """
    raw = await call_ollama(prompt, model=model, retries=retries)
    return _extract_json(raw)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response, handling code fences."""
    cleaned = text.strip()

    # Remove markdown code fences
    fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(fence_pattern, cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    # Try direct parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            return json.loads(cleaned[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass

    # Try to find JSON array
    bracket_start = cleaned.find("[")
    bracket_end = cleaned.rfind("]")
    if bracket_start != -1 and bracket_end > bracket_start:
        try:
            parsed = json.loads(cleaned[bracket_start : bracket_end + 1])
            if isinstance(parsed, list):
                return {"items": parsed, "raw": cleaned}
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to parse Ollama response as JSON: %s", cleaned[:200])
    return {"reply": cleaned, "intent": "idle", "parse_error": True}
