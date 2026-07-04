#!/bin/bash
# print-ngrok-url.sh - Print ngrok tunnel URL and webhook configuration
# Run after docker compose up to display the current ngrok URL
set -e

NGROK_API="http://localhost:4040"

check_ngrok() {
  wget -qO- "$NGROK_API/api/tunnels" > /dev/null 2>&1
}

if ! check_ngrok; then
  echo "[ngrok] ERROR: ngrok API not reachable at ${NGROK_API}"
  echo "  Make sure ngrok container is running: docker compose --profile ngrok ps"
  exit 1
fi

TUNNEL_JSON=$(wget -qO- "$NGROK_API/api/tunnels")
TUNNEL_URL=$(echo "$TUNNEL_JSON" | grep -oP '"public_url":"https://[^"]+' | head -1 | sed 's/"public_url":"//')
TUNNEL_NAME=$(echo "$TUNNEL_JSON" | grep -oP '"name":"[^"]+' | head -1 | sed 's/"name":"//')

if [ -z "$TUNNEL_URL" ]; then
  echo "[ngrok] ERROR: No active tunnel found"
  echo "  Check ngrok logs: docker compose --profile ngrok logs ngrok"
  exit 1
fi

WEBHOOK_URL="${TUNNEL_URL}/api/v1/webhooks/clerk"

echo ""
echo "============================================"
echo "  ngrok Tunnel Status"
echo "============================================"
echo "  Tunnel Name:    ${TUNNEL_NAME:-default}"
echo "  Public URL:     ${TUNNEL_URL}"
echo "  Webhook URL:    ${WEBHOOK_URL}"
echo "============================================"
echo ""
echo "Clerk Webhook Setup:"
echo "  1. Open https://dashboard.clerk.com"
echo "  2. Go to Webhooks"
echo "  3. Click 'Add Endpoint'"
echo "  4. Paste: ${WEBHOOK_URL}"
echo "  5. Select events: user.created, user.updated, user.deleted"
echo "  6. Copy the Signing Secret to .env as CLERK_WEBHOOK_SECRET"
echo ""
echo "ngrok Inspector: http://localhost:4040"
echo "============================================"
