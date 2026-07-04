#!/bin/bash
# ngrok-entrypoint.sh - Custom entrypoint for ngrok container
# Waits for backend to be ready, then starts ngrok tunnel
set -e

BACKEND_HOST="${BACKEND_HOST:-backend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
NGROK_LOG="${NGROK_LOG:-/tmp/ngrok.log}"

log() {
  echo "[ngrok-entrypoint] $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log "Waiting for backend at ${BACKEND_HOST}:${BACKEND_PORT}..."
until wget -qO- "http://${BACKEND_HOST}:${BACKEND_PORT}/health" > /dev/null 2>&1; do
  sleep 2
done
log "Backend is healthy."

log "Starting ngrok tunnel to ${BACKEND_HOST}:${BACKEND_PORT}..."
exec ngrok http "${BACKEND_HOST}:${BACKEND_PORT}" --log=stdout --log-format=json 2>&1 &
NGROK_PID=$!

sleep 3

if ! kill -0 $NGROK_PID 2>/dev/null; then
  log "ERROR: ngrok failed to start"
  exit 1
fi

log "ngrok tunnel established (PID: ${NGROK_PID})"
log "Checking tunnel status..."

TUNNEL_URL=""
for i in $(seq 1 10); do
  TUNNEL_URL=$(wget -qO- http://localhost:4040/api/tunnels 2>/dev/null | grep -oP '"public_url":"https://[^"]+' | head -1 | sed 's/"public_url":"//')
  if [ -n "$TUNNEL_URL" ]; then
    break
  fi
  sleep 1
done

if [ -n "$TUNNEL_URL" ]; then
  WEBHOOK_URL="${TUNNEL_URL}/api/v1/webhooks/clerk"
  echo ""
  echo "============================================"
  echo "  ngrok Tunnel Active"
  echo "============================================"
  echo "  Public URL:      ${TUNNEL_URL}"
  echo "  Webhook URL:     ${WEBHOOK_URL}"
  echo "  Webhook Secret:  Set CLERK_WEBHOOK_SECRET in .env"
  echo "============================================"
  echo ""
  echo "Clerk Dashboard Setup:"
  echo "  1. Go to https://dashboard.clerk.com"
  echo "  2. Navigate to Webhooks"
  echo "  3. Add Endpoint: ${WEBHOOK_URL}"
  echo "  4. Subscribe to: user.created, user.updated, user.deleted"
  echo ""
  echo "  ngrok Inspector: http://localhost:4040"
  echo "============================================"
else
  log "WARNING: Could not retrieve tunnel URL. Check ngrok logs."
  echo "ngrok API: http://localhost:4040"
fi

wait $NGROK_PID
