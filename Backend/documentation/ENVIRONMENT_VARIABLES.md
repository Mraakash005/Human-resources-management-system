# Environment Variables

All environment variables used by the HRMS backend, defined in `app/core/config.py` via pydantic-settings.

## Loading

Settings are loaded from `.env` file (UTF-8, case-insensitive). The `get_settings()` function is cached with `@lru_cache`.

```python
from app.core.config import get_settings
settings = get_settings()
```

---

## Application

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_NAME` | No | `HRMS Enterprise` | Application name |
| `APP_VERSION` | No | `3.0.0` | Version string |
| `ENVIRONMENT` | No | `development` | One of: `development`, `staging`, `production`, `testing` |
| `DEBUG` | No | `False` | Debug mode |
| `API_V1_PREFIX` | No | `/api/v1` | API route prefix |
| `SECRET_KEY` | **Yes** | — | Application secret (min 32 chars) |
| `LOG_LEVEL` | No | `INFO` | Python logging level |

---

## CORS

| Variable | Required | Default | Description |
|---|---|---|---|
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed origins |
| `CORS_ALLOW_CREDENTIALS` | No | `True` | Allow credentials |
| `CORS_ALLOW_METHODS` | No | `["*"]` | Allowed HTTP methods |
| `CORS_ALLOW_HEADERS` | No | `["*"]` | Allowed headers |

---

## Database

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | — | PostgreSQL URL (`postgresql+asyncpg://`) |
| `DB_POOL_SIZE` | No | `20` | Connection pool size (1–100) |
| `DB_MAX_OVERFLOW` | No | `10` | Extra connections beyond pool (0–50) |
| `DB_POOL_TIMEOUT` | No | `30` | Seconds to wait for connection (≥5) |
| `DB_POOL_RECYCLE` | No | `1800` | Recycle connections after seconds (≥60) |
| `DB_ECHO` | No | `False` | Log all SQL statements |

---

## Redis

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection string |
| `REDIS_MAX_CONNECTIONS` | No | `20` | Max pool connections |
| `REDIS_DECODER_RESPONSES` | No | `True` | Auto-decode bytes to strings |
| `REDIS_RETURN_DECODE_MESSAGES` | No | `False` | Decode Pub/Sub messages |

---

## Clerk Authentication

| Variable | Required | Default | Description |
|---|---|---|---|
| `CLERK_PUBLISHABLE_KEY` | **Yes** | — | Clerk publishable key (`pk_...`) |
| `CLERK_SECRET_KEY` | **Yes** | — | Clerk secret key (`sk_...`, min 20 chars) |
| `CLERK_JWT_VERIFICATION_KEY` | **Yes** | — | Clerk JWT public key (PEM format, RS256) |
| `CLERK_WEBHOOK_SECRET` | No | `""` | Clerk webhook signing secret (`whsec_...`) |
| `CLERK_JWT_TTL_MINUTES` | No | `15` | JWT cache TTL (1–60 minutes) |

---

## Email (Resend)

| Variable | Required | Default | Description |
|---|---|---|---|
| `RESEND_API_KEY` | **Yes** | — | Resend API key (`re_...`) |
| `EMAIL_FROM` | No | `hrms@localhost.com` | Sender address (must be verified in Resend) |
| `HR_EMAIL` | **Yes** | — | HR department notification email |

---

## AI: Ollama

| Variable | Required | Default | Description |
|---|---|---|---|
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_DEFAULT_MODEL` | No | `llama3` | Default LLM model |
| `OLLAMA_CHATBOT_MODEL` | No | `mistral` | Chatbot model (faster) |
| `OLLAMA_TIMEOUT` | No | `60` | Request timeout in seconds (≥10) |
| `OLLAMA_MAX_RETRIES` | No | `2` | Max retries (0–5) |

---

## AI: Whisper

| Variable | Required | Default | Description |
|---|---|---|---|
| `WHISPER_URL` | No | `http://localhost:9000` | Whisper ASR webservice URL |
| `WHISPER_MODEL` | No | `base` | Whisper model size |
| `WHISPER_TIMEOUT` | No | `60` | Request timeout in seconds (≥10) |

---

## File Upload / ClamAV

| Variable | Required | Default | Description |
|---|---|---|---|
| `CLAMAV_URL` | No | `http://localhost:3310` | ClamAV daemon URL |
| `MAX_DOCUMENT_SIZE_MB` | No | `5` | Max document upload size (1–50 MB) |
| `MAX_AUDIO_SIZE_MB` | No | `10` | Max audio upload size (1–100 MB) |
| `ALLOWED_DOCUMENT_MIMES` | No | `application/pdf, image/jpeg, image/png` | Allowed document MIME types |
| `ALLOWED_AUDIO_MIMES` | No | `audio/wav, audio/mpeg, audio/webm` | Allowed audio MIME types |
| `STORAGE_PATH` | No | `./storage` | Local file storage path |

---

## R2 Object Storage (Profile Pictures)

| Variable | Required | Default | Description |
|---|---|---|---|
| `R2_ACCOUNT_ID` | No | `""` | Cloudflare R2 account ID |
| `R2_ACCESS_KEY_ID` | No | `""` | R2 access key ID |
| `R2_SECRET_ACCESS_KEY` | No | `""` | R2 secret access key |
| `R2_BUCKET_NAME` | No | `hrms-assets` | R2 bucket name |
| `R2_PUBLIC_BASE_URL` | No | `""` | R2 public base URL |

---

## Geofence

| Variable | Required | Default | Description |
|---|---|---|---|
| `OFFICE_LAT` | No | `12.9716` | Office latitude |
| `OFFICE_LNG` | No | `77.5946` | Office longitude |
| `GEOFENCE_RADIUS_METERS` | No | `150` | Check-in radius (10–5000m) |

---

## Company

| Variable | Required | Default | Description |
|---|---|---|---|
| `COMPANY_NAME` | No | `HRMS Corp` | Company name for templates |

---

## Leave Defaults

| Variable | Required | Default | Description |
|---|---|---|---|
| `LEAVE_PAID_DEFAULT` | No | `12` | Default paid leave days (0–50) |
| `LEAVE_SICK_DEFAULT` | No | `10` | Default sick leave days (0–50) |
| `LEAVE_UNPAID_DEFAULT` | No | `999` | Default unpaid leave days |
| `LEAVE_BEREAVEMENT_DEFAULT` | No | `5` | Default bereavement days (0–20) |

---

## Payroll

| Variable | Required | Default | Description |
|---|---|---|---|
| `PAYROLL_PF_RATE` | No | `0.12` | Provident fund rate (0.0–0.5) |
| `PAYROLL_STANDARD_DEDUCTION` | No | `50000` | Standard deduction amount |

---

## Burnout Thresholds

| Variable | Required | Default | Description |
|---|---|---|---|
| `BURNOUT_MAX_CONSECUTIVE_DAYS` | No | `14` | Max consecutive working days (5–30) |
| `BURNOUT_MAX_WEEKLY_OVERTIME_HRS` | No | `10` | Max weekly overtime hours (1–40) |
| `BURNOUT_EXTREME_HOURS_THRESHOLD` | No | `5` | Extreme daily hours threshold (1–14) |

---

## Cache TTLs (seconds)

| Variable | Required | Default | Description |
|---|---|---|---|
| `CACHE_DASHBOARD_TTL` | No | `60` | Dashboard cache (≥10s) |
| `CACHE_ROLE_VERIFICATION_TTL` | No | `120` | Role verification cache (≥30s) |
| `CACHE_CHATBOT_CONTEXT_TTL` | No | `300` | Chatbot context cache (≥60s) |
| `CACHE_LEAVE_ADVISOR_TTL` | No | `3600` | Leave advisor cache (≥300s) |
| `CACHE_HEATMAP_TTL` | No | `3600` | Attendance heatmap cache (≥300s) |
| `CACHE_TEAM_HEALTH_TTL` | No | `21600` | Team health cache (≥3600s) |

---

## Rate Limiting

| Variable | Required | Default | Description |
|---|---|---|---|
| `RATE_LIMIT_PER_MINUTE` | No | `60` | General API rate limit per IP |
| `RATE_LIMIT_AI_PER_MINUTE` | No | `10` | AI endpoint rate limit per IP |

---

## Docker Compose

| Variable | Required | Default | Description |
|---|---|---|---|
| `POSTGRES_PASSWORD` | No | `hrms_secure_password_2025` | PostgreSQL password for docker-compose |

---

## ngrok (Docker Only)

| Variable | Required | Default | Description |
|---|---|---|---|
| `NGROK_ENABLED` | No | `false` | Enable ngrok tunnel (`true`/`false`) |
| `NGROK_AUTHTOKEN` | No | — | ngrok auth token (required if enabled) |
| `NGROK_REGION` | No | `us` | ngrok region (`us`/`eu`/`au`/`ap`) |

---

## Required vs Summary

**7 required variables** — app will not start without them:

1. `SECRET_KEY`
2. `DATABASE_URL`
3. `CLERK_PUBLISHABLE_KEY`
4. `CLERK_SECRET_KEY`
5. `CLERK_JWT_VERIFICATION_KEY`
6. `RESEND_API_KEY`
7. `HR_EMAIL`

All other variables have sensible defaults for development.

---

## Production Requirements

When `ENVIRONMENT=production`, additional validation applies:

- `DEBUG` must be `False`
- `DATABASE_URL` cannot contain `localhost`
- `REDIS_URL` cannot contain `localhost`
- `CORS_ORIGINS` must include a non-localhost domain

---

## Security Notes

- **Never commit `.env`** to version control — it's in `.gitignore`
- **Rotate secrets** regularly, especially `SECRET_KEY` and `CLERK_SECRET_KEY`
- Use `secrets.token_urlsafe(48)` to generate `SECRET_KEY`
- `CLERK_JWT_VERIFICATION_KEY` should be the PEM public key, not the secret
- In production, use a secrets manager (AWS SSM, Vault, etc.) instead of `.env` files
- `R2_SECRET_ACCESS_KEY` and `RESEND_API_KEY` should have minimal required permissions
