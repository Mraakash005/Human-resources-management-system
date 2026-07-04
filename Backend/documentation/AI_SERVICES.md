# AI Services Integration

## Overview

The HRMS backend integrates two AI services for enhanced functionality:

- **Ollama** — LLM inference for email drafting and chatbot responses
- **Whisper** — Audio transcription for voice-based leave requests

---

## Ollama Integration

### Models Used

| Model | Purpose | Context |
|-------|---------|---------|
| `llama3` | Email drafting, formal communications | Employee onboarding, leave notifications |
| `mistral` | Chatbot responses, casual interactions | Employee Q&A, HR assistant |

### Core Functions

#### `call_ollama(model: str, prompt: str, temperature: float = 0.7) -> str`

Makes a request to the Ollama API with retry logic and circuit breaker protection.

**Retry behavior:**
- Max retries: 3
- Exponential backoff: 1s → 2s → 4s
- Circuit breaker: Opens after 5 consecutive failures
- Circuit breaker reset: 30 seconds

**Parameters:**
- `model` — Target model name (`"llama3"` or `"mistral"`)
- `prompt` — The full prompt string
- `temperature` — Controls randomness (0.0 = deterministic, 1.0 = creative)

**Returns:** Generated text string

**Raises:** `OllamaServiceError` when circuit breaker is open or all retries exhausted.

#### `call_ollama_json(model: str, prompt: str, schema: dict) -> dict`

Wrapper around `call_ollama` that enforces structured JSON output.

**Behavior:**
- Appends JSON schema instructions to the prompt
- Parses response with `json.loads()`
- Validates against provided schema
- Falls back to default values on parse failure

**Parameters:**
- `model` — Target model
- `prompt` — Prompt string
- `schema` — JSON schema dict for validation

**Returns:** Parsed and validated dict

---

## Prompt Templates

### Email Drafting (llama3)

```
You are an HR assistant drafting professional emails.

Context: {context}
Recipient: {recipient_name}
Purpose: {purpose}
Tone: {tone}

Generate a clear, professional email. Keep it under {max_words} words.
Do not include a subject line. Start directly with the greeting.
```

### Chatbot (mistral)

```
You are an HR chatbot for {company_name}.

You can help with:
- Company policies and benefits
- Leave request procedures
- Payroll inquiries
- General HR questions

Employee context:
- Name: {employee_name}
- Department: {department}
- Role: {role}

Question: {user_message}

Respond helpfully and concisely. If unsure, suggest contacting HR directly.
```

### Leave Request Parsing (mistral + Whisper)

```
You are parsing a transcribed voice message for a leave request.

Transcription: "{transcription}"

Extract the following fields and return valid JSON:
{
  "leave_type": "sick|vacation|personal|unpaid",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "reason": "brief explanation",
  "confidence": 0.0 to 1.0
}

If any field cannot be determined, set it to null.
```

### Burnout Detection (llama3)

```
You are an HR wellness assistant analyzing employee workload data.

Employee: {employee_name}
Department: {department}
Metrics:
- Overtime hours this month: {overtime_hours}
- Tasks completed: {tasks_completed}
- Tasks overdue: {tasks_overdue}
- Days since last PTO: {days_since_pto}
- Sentiment score: {sentiment_score}

Assess burnout risk (low/medium/high) and suggest one actionable recommendation.
Respond in JSON:
{
  "risk_level": "low|medium|high",
  "score": 0-100,
  "recommendation": "specific suggestion"
}
```

---

## Graceful Degradation

When Ollama is unavailable, the system degrades gracefully:

| Feature | Fallback Behavior |
|---------|-------------------|
| Email drafting | Returns generic template email |
| Chatbot | Returns pre-defined FAQ responses |
| Leave parsing from audio | Returns raw transcription for manual entry |
| Burnout detection | Uses rule-based scoring (no LLM) |

**Implementation:**
```python
try:
    response = call_ollama(model, prompt)
except OllamaServiceError:
    logger.warning("Ollama unavailable, using fallback")
    response = get_fallback_response(feature_type)
```

All fallback responses include a `"source": "fallback"` flag in the response dict.

---

## Input Sanitization

All user inputs are sanitized before being passed to AI models:

1. **Length limits** — Prompt capped at 4000 characters to prevent token overflow
2. **Injection prevention** — Special characters and prompt injection patterns are stripped
3. **PII redaction** — Social Security Numbers, bank accounts, and credit card numbers are redacted before logging
4. **HTML stripping** — All HTML tags removed from input text
5. **Encoding normalization** — Unicode normalization (NFKC) applied

```python
def sanitize_input(text: str) -> str:
    text = strip_html_tags(text)
    text = normalize_unicode(text, form='NFKF')
    text = redact_pii(text)
    text = text[:4000]
    text = sanitize_prompt_injection(text)
    return text
```
