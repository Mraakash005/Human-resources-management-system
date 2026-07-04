# Ollama Setup

## Overview

Ollama provides local LLM inference for the HRMS backend. It runs as a Docker container with optional GPU acceleration.

---

## Docker Compose Configuration

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: hrms-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
      - OLLAMA_NUM_PARALLEL=2
      - OLLAMA_MAX_LOADED_MODELS=2
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  ollama_data:
    driver: local
```

---

## GPU Support (NVIDIA)

### Prerequisites

- NVIDIA GPU driver installed on host (>= 525.60.13)
- NVIDIA Container Toolkit installed
- `nvidia-smi` returns valid output

### Docker Compose (GPU-enabled)

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: hrms-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
      - OLLAMA_NUM_PARALLEL=2
      - OLLAMA_MAX_LOADED_MODELS=2
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
```

### Verify GPU Access

```bash
# Test from host
nvidia-smi

# Test inside container
docker exec hrms-ollama nvidia-smi
```

---

## Model Pulling

### Required Models

```bash
# Pull llama3 for email drafting
docker exec hrms-ollama ollama pull llama3

# Pull mistral for chatbot
docker exec hrms-ollama ollama pull mistral
```

### Verify Models

```bash
# List pulled models
docker exec hrms-ollama ollama list

# Expected output:
# NAME          ID            SIZE    MODIFIED
# llama3        ...           4.7 GB  ...
# mistral       ...           4.1 GB  ...
```

### Pull Script (startup automation)

```bash
#!/bin/bash
# pull-models.sh — Run after container starts

MAX_RETRIES=5
RETRY_DELAY=10

pull_model() {
    local model=$1
    local attempt=1

    while [ $attempt -le $MAX_RETRIES ]; do
        echo "Pulling $model (attempt $attempt/$MAX_RETRIES)..."
        docker exec hrms-ollama ollama pull "$model"

        if [ $? -eq 0 ]; then
            echo "$model pulled successfully."
            return 0
        fi

        echo "Retry in ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
        attempt=$((attempt + 1))
    done

    echo "ERROR: Failed to pull $model after $MAX_RETRIES attempts"
    return 1
}

pull_model "llama3"
pull_model "mistral"
```

---

## API Endpoint

### Base URL

```
http://localhost:11434
```

### Generate Completion

```
POST /api/generate
```

**Request:**
```json
{
  "model": "llama3",
  "prompt": "Draft a welcome email for new employee John Doe.",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "num_predict": 512
  }
}
```

**Response:**
```json
{
  "model": "llama3",
  "created_at": "2026-07-04T12:00:00Z",
  "response": "Dear John, Welcome to the team!...",
  "done": true,
  "total_duration": 2345678901,
  "eval_count": 128,
  "eval_duration": 1234567890
}
```

### List Models

```
GET /api/tags
```

### Check Health

```
GET /api/tags
```

Returns HTTP 200 if Ollama is running.

---

## Timeout Configuration

| Operation | Timeout |
|-----------|---------|
| API request (single) | 60s |
| Model pull | 300s per model |
| Health check | 10s |
| Startup readiness | 60s |

### Application Config

```python
OLLAMA_CONFIG = {
    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "timeout": int(os.getenv("OLLAMA_TIMEOUT", "60")),
    "retry_attempts": 3,
    "retry_backoff": [1, 2, 4],
    "circuit_breaker_threshold": 5,
    "circuit_breaker_reset": 30,
}
```

---

## Health Monitoring

### Automatic Health Checks

The Docker Compose healthcheck runs every 30 seconds:

```bash
curl -f http://localhost:11434/api/tags
```

### Application-Level Monitoring

```python
def check_ollama_health() -> dict:
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=10
        )
        models = response.json().get("models", [])
        return {
            "status": "healthy",
            "models_available": [m["name"] for m in models],
            "latency_ms": response.elapsed.total_seconds() * 1000
        }
    except requests.RequestException as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### Metrics Tracked

- Response latency per request
- Model load/unload events
- OOM kill events
- GPU memory utilization (if GPU enabled)

---

## Model Recovery

### Automatic Recovery

If Ollama crashes or becomes unresponsive:

1. Docker Compose restarts the container (`restart: unless-stopped`)
2. Application circuit breaker opens, preventing requests
3. After 30s, circuit breaker resets and retries
4. Models are reloaded from disk (cached in `ollama_data` volume)

### Manual Recovery

```bash
# Restart Ollama container
docker restart hrms-ollama

# Force stop and restart
docker stop hrms-ollama && docker start hrms-ollama

# Clear cache and re-pull (nuclear option)
docker rm -v hrms-ollama
docker compose up -d
./pull-models.sh
```

### Model Corruption Recovery

```bash
# Remove corrupted model
docker exec hrms-ollama ollama rm llama3
docker exec hrms-ollama ollama pull llama3
```

---

## Resource Requirements

| Model | RAM | GPU VRAM | Disk |
|-------|-----|----------|------|
| llama3 | 8 GB | 6 GB | 4.7 GB |
| mistral | 8 GB | 6 GB | 4.1 GB |
| Both | 16 GB | 12 GB | 8.8 GB |

**Minimum recommended:** 16 GB RAM, 12 GB GPU VRAM for both models loaded simultaneously.
