# Deployment

Docker Compose setup with 8 services, nginx reverse proxy, SSL/TLS, optional ngrok tunnel, and production considerations.

## Docker Compose Setup

The full stack is defined in `docker-compose.yml` at project root.

```bash
# First-time setup (generates .env + SSL certs)
python scripts/configure_env.py

# Start all services
docker compose up --build -d

# View logs
docker compose logs -f backend

# Stop all services
docker compose down
```

---

## Services Overview

| Service | Image | Port | Purpose |
|---|---|---|---|
| `postgres` | `postgres:16-alpine` | 5432 | Primary database |
| `redis` | `redis:7-alpine` | 6379 | Cache + Pub/Sub + rate limiting |
| `ollama` | `ollama/ollama:latest` | 11434 | LLM inference (GPU required) |
| `whisper` | `onerahmet/openai-whisper-asr-webservice` | 9000 | Speech-to-text |
| `clamav` | `clamav/clamav:stable` | 3310 | Antivirus scanning |
| `backend` | Custom build | 8000 | FastAPI application |
| `nginx` | `nginx:alpine` | 80, 443 | Reverse proxy + SSL termination |
| `ngrok` | `ngrok/ngrok:latest` | — | Public tunnel (optional, profile: `ngrok`) |

### Service Details

#### PostgreSQL

```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: hrms_db
    POSTGRES_USER: hrms
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-hrms_secure_password_2025}
  volumes:
    - pg_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U hrms -d hrms_db"]
    interval: 10s
```

- Persistent data via named volume `pg_data`
- Health check ensures backend waits for database readiness

#### Redis

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

- 256 MB memory limit with LRU eviction
- Used for caching, rate limiting, Pub/Sub, and session data

#### Ollama

```yaml
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

- Requires NVIDIA GPU for local LLM inference
- Models stored in `ollama_data` volume
- Pull models after startup: `docker compose exec ollama ollama pull llama3`

#### Whisper

```yaml
whisper:
  image: onerahmet/openai-whisper-asr-webservice:latest
  environment:
    - ASR_MODEL=base
    - ASR_ENGINE=openai_whisper
```

- OpenAI Whisper for speech-to-text
- Model: `base` (adjustable via env var)

#### ClamAV

```yaml
clamav:
  image: clamav/clamav:stable
  healthcheck:
    test: ["CMD-SHELL", "clamdscan --ping=30 || exit 1"]
    interval: 30s
```

- Antivirus scanning for uploaded documents
- Health check pings the daemon every 30s

#### Backend

```yaml
backend:
  build:
    context: .
    dockerfile: Dockerfile
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  env_file: .env
  volumes:
    - storage_data:/app/storage
  healthcheck:
    test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health')"]
```

- Multi-stage Docker build (builder → production)
- Non-root `hrms` user
- Runs `uvicorn` with 4 workers
- Depends on postgres + redis being healthy

#### Nginx

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
  depends_on:
    backend:
      condition: service_healthy
```

#### ngrok (Optional)

```yaml
ngrok:
  image: ngrok/ngrok:latest
  profiles:
    - ngrok
  environment:
    NGROK_AUTHTOKEN: ${NGROK_AUTHTOKEN}
    NGROK_REGION: ${NGROK_REGION:-us}
  command: http backend:8000
  depends_on:
    backend:
      condition: service_healthy
  healthcheck:
    test: ["CMD-SHELL", "wget -qO- http://localhost:4040/api/tunnels > /dev/null 2>&1 || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 3
  restart: unless-stopped
```

- Uses Docker Compose profile `ngrok` — only starts when profile is active
- Tunnels to `backend:8000`
- Exposes local API on port 4040 (ngrok Inspector)
- Health check verifies tunnel is active

---

## Nginx Configuration

`nginx.conf` provides:

### Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
limit_req_zone $binary_remote_addr zone=ai:10m rate=10r/m;
```

- **API endpoints**: 60 requests/minute per IP, burst=20
- **AI endpoints**: 10 requests/minute per IP, burst=5

### SSL/TLS

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

### Security Headers

```nginx
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Route Handling

| Location | Target | Notes |
|---|---|---|
| `/api/` | `backend:8000` | General API, rate limited |
| `/api/v1/(nlp\|voice\|chatbot)` | `backend:8000` | AI endpoints, stricter rate limit, 120s timeout |
| `/api/v1/chat/stream` | `backend:8000` | SSE — buffering disabled |
| `/health` | `backend:8000` | Health check (no rate limit) |
| `/docs`, `/openapi.json` | `backend:8000` | API docs |
| `/` | `frontend:3000` | Next.js frontend |

### SSE Configuration

```nginx
location ~ ^/api/v1/chat/stream {
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
}
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all values:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Application secret (min 32 chars) |
| `DATABASE_URL` | PostgreSQL connection string |
| `CLERK_PUBLISHABLE_KEY` | Clerk auth publishable key |
| `CLERK_SECRET_KEY` | Clerk auth secret key |
| `CLERK_JWT_VERIFICATION_KEY` | Clerk JWT public key (PEM) |
| `RESEND_API_KEY` | Resend email API key |
| `HR_EMAIL` | HR department email |

### Optional / Defaulted

| Variable | Default |
|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `WHISPER_URL` | `http://localhost:9000` |
| `CLAMAV_URL` | `http://localhost:3310` |
| `OFFICE_LAT` / `OFFICE_LNG` | `12.9716` / `77.5946` |
| `NGROK_ENABLED` | `false` |
| `NGROK_AUTHTOKEN` | — (required if NGROK_ENABLED=true) |
| `NGROK_REGION` | `us` |

Full reference: [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)

---

## SSL/TLS Setup

### Development (Self-Signed)

The setup script generates self-signed certificates:

```bash
python scripts/configure_env.py
```

Creates `ssl/cert.pem` and `ssl/key.pem` with a 365-day validity.

### Production

Replace the self-signed certs with real certificates:

```bash
# Using Let's Encrypt / Certbot
certbot certonly --standalone -d hrms.yourdomain.com

# Copy to ssl/ directory
cp /etc/letsencrypt/live/hrms.yourdomain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/hrms.yourdomain.com/privkey.pem ssl/key.pem

# Restart nginx
docker compose restart nginx
```

---

## First-Time Setup Script

`scripts/configure_env.py` automates initial setup:

```bash
python scripts/configure_env.py
```

**What it does**:
1. Generates a random `SECRET_KEY` (48 chars, URL-safe)
2. Generates a random PostgreSQL password
3. Creates `.env` from template with generated secrets
4. Creates `ssl/` directory with self-signed certificates
5. Prints next steps (fill in Clerk + Resend keys)

### Health Check Script

```bash
python scripts/healthcheck.py
```

Checks connectivity to all services: Backend, PostgreSQL, Redis, Ollama, Whisper, ClamAV, and ngrok (if running).

---

## ngrok Integration

ngrok provides a public tunnel for Clerk webhook development during local development.

### Quick Setup

```bash
# 1. Set in .env
NGROK_ENABLED=true
NGROK_AUTHTOKEN=your_token_here

# 2. Start with ngrok profile
docker compose --profile ngrok up -d

# 3. Get tunnel URL
bash scripts/print-ngrok-url.sh
```

### Configure Clerk Webhook

1. Copy the webhook URL from `print-ngrok-url.sh` output
2. Go to Clerk Dashboard → Webhooks → Add Endpoint
3. Paste the URL: `https://<ngrok-url>/api/v1/webhooks/clerk`
4. Subscribe to: `user.created`, `user.updated`, `user.deleted`
5. Copy Signing Secret → set as `CLERK_WEBHOOK_SECRET` in `.env`
6. Restart backend: `docker compose restart backend`

### ngrok Commands

```bash
# Start with ngrok
docker compose --profile ngrok up -d

# View ngrok logs
docker compose --profile ngrok logs ngrok

# Restart ngrok
docker compose --profile ngrok restart ngrok

# Print tunnel URL
bash scripts/print-ngrok-url.sh

# Stop ngrok
docker compose --profile ngrok down
```

### ngrok Inspector

When ngrok is running, access the Inspector at http://localhost:4040 to:
- View all HTTP requests through the tunnel
- Replay requests
- Inspect request/response details

For full documentation, see `docs/NGROK.md`.

---

## Production Considerations

### Docker Build

Multi-stage Dockerfile:

1. **Builder stage**: Python 3.12-slim, installs build dependencies (libpq, libffi, libmagic, WeasyPrint deps)
2. **Production stage**: Python 3.12-slim, runtime dependencies only, non-root `hrms` user

### Scaling

```yaml
# docker-compose.prod.yml override
services:
  backend:
    deploy:
      replicas: 3
```

- Backend runs with `uvicorn --workers 4` (4 async workers per container)
- PostgreSQL and Redis are single-instance (use managed services for HA)

### Monitoring

- **Application health**: `GET /health` returns DB + Redis status
- **Service health**: Docker Compose healthchecks on all services
- **Script**: `scripts/healthcheck.py` for quick diagnostics

### Backup

```bash
# PostgreSQL backup
docker compose exec postgres pg_dump -U hrms hrms_db > backup.sql

# Redis (ephemeral, no backup needed)

# Storage volume
docker compose exec backend tar czf - /app/storage > storage_backup.tar.gz
```

### Security

- Backend runs as non-root user (`hrms`)
- Nginx terminates SSL, forwards to internal network
- Rate limiting at nginx (IP-based) + application (Redis sliding window)
- ClamAV scans uploaded files
- All secrets in `.env` (never committed to git)
- `.gitignore` excludes `.env`, `ssl/`, `storage/`
