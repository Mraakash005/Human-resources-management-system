#!/bin/bash
# docker-start.sh - Smart Docker Compose launcher
# Automatically detects NGROK_ENABLED and includes ngrok profile if needed
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "[docker-start] ERROR: .env file not found at ${ENV_FILE}"
  echo "  Run: cp .env.example .env && ./scripts/setup.sh"
  exit 1
fi

NGROK_ENABLED=$(grep -E '^NGROK_ENABLED=' "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d ' "')

if [ -z "$NGROK_ENABLED" ]; then
  NGROK_ENABLED="false"
fi

COMPOSE_PROFILES=""

if [ "$NGROK_ENABLED" = "true" ] || [ "$NGROK_ENABLED" = "1" ] || [ "$NGROK_ENABLED" = "yes" ]; then
  NGROK_AUTHTOKEN=$(grep -E '^NGROK_AUTHTOKEN=' "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d ' "')
  if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo "[docker-start] WARNING: NGROK_ENABLED=true but NGROK_AUTHTOKEN is not set in .env"
    echo "  ngrok will fail to authenticate. Add NGROK_AUTHTOKEN to .env"
    echo "  Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken"
  fi
  COMPOSE_PROFILES="ngrok"
  echo "[docker-start] ngrok profile ENABLED (NGROK_ENABLED=true)"
else
  echo "[docker-start] ngrok profile DISABLED (NGROK_ENABLED=false)"
fi

echo "[docker-start] Starting Docker Compose..."
cd "$PROJECT_DIR"

if [ -n "$COMPOSE_PROFILES" ]; then
  exec docker compose --profile "$COMPOSE_PROFILES" up "$@"
else
  exec docker compose up "$@"
fi
