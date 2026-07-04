# ngrok Integration — HRMS Docker Infrastructure

ngrok provides a secure public tunnel to your local Docker backend, enabling Clerk webhook delivery without exposing your network.

## Prerequisites

- Docker Desktop installed and running
- An ngrok account (free tier works): https://ngrok.com
- Your ngrok authtoken: https://dashboard.ngrok.com/get-started/your-authtoken

## Quick Start

### 1. Set environment variables

Edit `.env` and set:

```bash
NGROK_ENABLED=true
NGROK_AUTHTOKEN=your_actual_authtoken_here
NGROK_REGION=us
```

### 2. Start with ngrok profile

```bash
# Option A: Use the wrapper script (recommended)
bash scripts/docker-start.sh

# Option B: Direct Docker Compose command
docker compose --profile ngrok up -d
```

### 3. Get your public tunnel URL

```bash
bash scripts/print-ngrok-url.sh
```

This prints something like:

```
============================================
  ngrok Tunnel Status
============================================
  Tunnel Name:    default
  Public URL:     https://abc123.ngrok-free.app
  Webhook URL:    https://abc123.ngrok-free.app/api/v1/webhooks/clerk
============================================
```

### 4. Configure Clerk webhook

1. Open [Clerk Dashboard](https://dashboard.clerk.com)
2. Navigate to **Webhooks**
3. Click **Add Endpoint**
4. Paste the **Webhook URL** from step 3
5. Select events: `user.created`, `user.updated`, `user.deleted`
6. Copy the **Signing Secret** and set it in `.env` as `CLERK_WEBHOOK_SECRET`
7. Restart backend: `docker compose restart backend`

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Clerk Cloud │────▶│  ngrok       │────▶│  Backend     │
│  (webhooks)  │     │  (tunnel)    │     │  (FastAPI)   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                     ┌──────┴──────┐
                     │  Public     │
                     │  URL        │
                     └─────────────┘
```

- **ngrok container**: Official `ngrok/ngrok:latest` Docker image
- **Tunnel target**: `backend:8000` (Docker service name)
- **Local API**: Port `4040` (ngrok Inspector)
- **Profile**: `ngrok` (only starts when profile is active)

## Commands

| Command | Description |
|---------|-------------|
| `bash scripts/docker-start.sh` | Smart launcher — auto-detects ngrok profile |
| `docker compose --profile ngrok up -d` | Start all services + ngrok |
| `docker compose --profile ngrok down` | Stop all services including ngrok |
| `bash scripts/print-ngrok-url.sh` | Print current tunnel URL |
| `docker compose --profile ngrok logs ngrok` | View ngrok logs |
| `docker compose --profile ngrok restart ngrok` | Restart ngrok tunnel |

## How It Works

1. Docker Compose starts the `ngrok` service (only when `--profile ngrok` is active)
2. ngrok waits for `backend` to pass health check
3. ngrok creates a tunnel to `backend:8000`
4. ngrok prints the public URL to container logs
5. The `print-ngrok-url.sh` script queries the ngrok API (port 4040) to display the URL

## Troubleshooting

### ngrok fails to start

```bash
docker compose --profile ngrok logs ngrok
```

Common issues:
- **"invalid auth token"**: Check `NGROK_AUTHTOKEN` in `.env`
- **"tunnel limit reached"**: Free tier allows 1 tunnel — close other sessions
- **"backend not healthy"**: Wait for backend health check to pass

### Tunnel URL changed

ngrok generates a new URL on each restart (free tier). After restart:
1. Run `bash scripts/print-ngrok-url.sh`
2. Update the webhook URL in Clerk Dashboard

### Webhook not receiving events

1. Verify tunnel is active: `bash scripts/print-ngrok-url.sh`
2. Check ngrok Inspector: http://localhost:4040
3. Verify `CLERK_WEBHOOK_SECRET` matches the Clerk signing secret
4. Check backend logs: `docker compose logs backend | grep webhook`

### Getting a stable URL (paid plan)

Set `NGROK_DOMAIN` in `.env`:

```bash
NGROK_DOMAIN=your-custom-domain.ngrok.io
```

Update the ngrok command in `docker-compose.yml`:

```yaml
command: http backend:8000 --domain=${NGROK_DOMAIN}
```

## Security Notes

- ngrok tunnel is for **development only** — never use in production
- The ngrok Inspector (port 4040) is only accessible locally
- Never commit `NGROK_AUTHTOKEN` to version control
- The `.env` file is gitignored and will not be committed

## Production Alternative

For production, use:
- **Clerk webhook retries**: Clerk automatically retries failed webhooks
- **Direct internet exposure**: Deploy backend behind a reverse proxy (nginx/cloudflared)
- **Cloudflare Tunnel**: For production-grade tunneling without ngrok
