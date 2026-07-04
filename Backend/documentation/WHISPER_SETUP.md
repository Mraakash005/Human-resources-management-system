# Whisper Setup

## Overview

Whisper provides audio transcription for voice-based leave requests. The HRMS backend uses a Dockerized ASR (Automatic Speech Recognition) web service.

---

## Docker Image

```yaml
services:
  whisper:
    image: onerahmet/openai-whisper-asr-webservice:latest
    container_name: hrms-whisper
    ports:
      - "9000:9000"
    volumes:
      - whisper_models:/root/.cache/whisper
    environment:
      - ASR_MODEL=base
      - ASR_ENGINE=openai_whisper
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  whisper_models:
    driver: local
```

---

## Model Sizes

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | 75 MB | Fastest | Low | Quick drafts |
| `base` | 142 MB | Fast | Good | Default for HRMS |
| `small` | 466 MB | Moderate | Better | Multi-language |
| `medium` | 1.5 GB | Slow | High | Accurate transcription |
| `large` | 2.9 GB | Slowest | Best | Maximum accuracy |

### Recommended Configuration

- **Production:** `base` model (balance of speed and accuracy)
- **Multi-language support:** `medium` model
- **Resource-constrained:** `tiny` model

### Switching Models

```bash
# Stop container, change env, restart
docker stop hrms-whisper
docker rm hrms-whisper

# Update docker-compose.yml ASR_MODEL value
# Then restart
docker compose up -d whisper
```

---

## API Endpoint

### Base URL

```
http://localhost:9000
```

### Transcription

```
POST /asr
```

**Request:**
```bash
curl -X POST http://localhost:9000/asr \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@recording.wav" \
  -F "output=json" \
  -F "language=en"
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `audio_file` | file | Yes | — | Audio file to transcribe |
| `output` | string | No | `json` | Output format: `json`, `text`, `verbose_json` |
| `language` | string | No | auto-detect | ISO 639-1 language code |
| `task` | string | No | `transcribe` | `transcribe` or `translate` |

**Response (JSON):**
```json
{
  "text": "I would like to request sick leave from July 10th to July 12th.",
  "language": "en",
  "duration": 5.2,
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "I would like to request sick leave from July 10th to July 12th."
    }
  ]
}
```

**Response (text):**
```
I would like to request sick leave from July 10th to July 12th.
```

### Health Check

```
GET /health
```

Returns HTTP 200 when the service is ready.

---

## File Validation

### MIME Types

The HRMS backend validates audio files before sending to Whisper:

| MIME Type | Extension | Allowed |
|-----------|-----------|---------|
| `audio/wav` | `.wav` | Yes |
| `audio/x-wav` | `.wav` | Yes |
| `audio/mpeg` | `.mp3` | Yes |
| `audio/mp3` | `.mp3` | Yes |
| `audio/ogg` | `.ogg` | Yes |
| `audio/flac` | `.flac` | Yes |
| `audio/mp4` | `.m4a` | Yes |
| `audio/x-m4a` | `.m4a` | Yes |
| `audio/webm` | `.webm` | Yes |
| `video/mp4` | `.mp4` | Yes (audio track) |

### Size Limits

| Limit | Value |
|-------|-------|
| Maximum file size | 10 MB |
| Minimum duration | 0.5 seconds |
| Maximum duration | 300 seconds (5 minutes) |

### Validation Code

```python
ALLOWED_AUDIO_MIMES = {
    "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3",
    "audio/ogg", "audio/flac", "audio/mp4", "audio/x-m4a",
    "audio/webm", "video/mp4",
}

MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_audio_file(file_path: str) -> tuple[bool, str]:
    mime = magic.from_file(file_path, mime=True)
    if mime not in ALLOWED_AUDIO_MIMES:
        return False, f"Unsupported audio format: {mime}"

    size = os.path.getsize(file_path)
    if size > MAX_AUDIO_SIZE:
        return False, f"File too large: {size} bytes (max {MAX_AUDIO_SIZE})"

    return True, "valid"
```

---

## Integration with Ollama for Leave Parsing

### Flow

```
Audio File → Whisper (transcription) → Ollama (structured parsing) → Leave Request
```

### Process

1. User uploads or records audio message
2. File validated (MIME type, size)
3. Whisper transcribes audio to text
4. Transcription passed to Ollama (mistral) for structured extraction
5. Ollama returns JSON with leave type, dates, reason
6. Leave request created in database

### Code Flow

```python
async def process_voice_leave_request(audio_path: str, employee_id: int) -> dict:
    # 1. Transcribe with Whisper
    transcription = await transcribe_audio(audio_path)

    # 2. Parse with Ollama
    parsed = await call_ollama_json(
        model="mistral",
        prompt=LEAVE_PARSING_PROMPT.format(transcription=transcription),
        schema=LEAVE_REQUEST_SCHEMA
    )

    # 3. Create leave request
    leave_request = await create_leave_request(
        employee_id=employee_id,
        leave_type=parsed.get("leave_type"),
        start_date=parsed.get("start_date"),
        end_date=parsed.get("end_date"),
        reason=parsed.get("reason"),
        source="voice",
        transcription=transcription,
        confidence=parsed.get("confidence", 0.0)
    )

    return leave_request
```

### Error Handling

| Error | Action |
|-------|--------|
| Whisper unavailable | Return error, suggest text input |
| Transcription empty | Prompt user to re-record |
| Ollama parse failure | Return raw transcription for manual entry |
| Low confidence (<0.5) | Flag for manual review |

---

## Health Monitoring

### Docker Healthcheck

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### Application Health Check

```python
def check_whisper_health() -> dict:
    try:
        response = requests.get(
            "http://localhost:9000/health",
            timeout=10
        )
        return {
            "status": "healthy",
            "model": os.getenv("ASR_MODEL", "base"),
            "latency_ms": response.elapsed.total_seconds() * 1000
        }
    except requests.RequestException as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### Metrics Tracked

- Transcription request count
- Average transcription latency
- File size distribution
- Error rate by failure type
- Model load status

### Monitoring Endpoint

The `/health` endpoint of the HRMS backend includes Whisper status:

```json
{
  "services": {
    "whisper": {
      "status": "healthy",
      "model": "base",
      "uptime_seconds": 86400
    }
  }
}
```

---

## Resource Requirements

| Model | RAM | GPU VRAM | CPU Cores |
|-------|-----|----------|-----------|
| tiny | 1 GB | 1 GB | 2 |
| base | 2 GB | 2 GB | 2 |
| small | 4 GB | 4 GB | 4 |
| medium | 8 GB | 8 GB | 4 |
| large | 12 GB | 12 GB | 8 |

**Note:** CPU-only mode works but is 5-10x slower than GPU.
