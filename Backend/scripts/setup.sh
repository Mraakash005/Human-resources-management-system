#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# HRMS One-Command Setup Script
# Sets up the complete HRMS backend from scratch
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "  HRMS Enterprise Backend — Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Install from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed."
    exit 1
fi

PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "✅ Docker: $(docker --version)"
echo "✅ Python: $($PYTHON_CMD --version)"
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    $PYTHON_CMD scripts/configure_env.py
else
    echo "✅ .env file already exists"
fi

# Create SSL directory for development
if [ ! -d ssl ]; then
    echo "Creating SSL certificates for development..."
    mkdir -p ssl
    openssl req -x509 -newkey rsa:2048 -keyout ssl/key.pem -out ssl/cert.pem \
        -days 365 -nodes -subj '/CN=localhost' 2>/dev/null
    echo "✅ SSL certificates created"
fi

# Create storage directories
mkdir -p storage/paystubs storage/avatars
echo "✅ Storage directories created"

# Start all services
echo ""
echo "Starting all services..."
docker compose up -d --build

# Wait for PostgreSQL
echo ""
echo "Waiting for PostgreSQL..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker compose exec backend python -c "
import asyncio
from app.core.database import db_manager
from app.core.config import get_settings
from app.models import Base
async def init():
    await db_manager.connect()
    async with db_manager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await db_manager.disconnect()
    print('✅ Database tables created')
asyncio.run(init())
"

# Pull AI models
echo ""
echo "Pulling AI models (this may take a few minutes)..."
docker compose exec ollama ollama pull llama3 2>/dev/null || echo "⚠️  Could not pull llama3 — do it manually later"
docker compose exec ollama ollama pull mistral 2>/dev/null || echo "⚠️  Could not pull mistral — do it manually later"

# Update ClamAV signatures
echo ""
echo "Updating ClamAV virus definitions..."
docker compose exec clamav freshclam 2>/dev/null || echo "⚠️  Could not update ClamAV — do it manually later"

# Verify services
echo ""
echo "Running health check..."
$PYTHON_CMD scripts/healthcheck.py

# Check ngrok status
NGROK_ENABLED=$(grep -E '^NGROK_ENABLED=' .env 2>/dev/null | cut -d'=' -f2 | tr -d ' "')
if [ "$NGROK_ENABLED" = "true" ] || [ "$NGROK_ENABLED" = "1" ] || [ "$NGROK_ENABLED" = "yes" ]; then
  echo ""
  echo "ngrok is enabled — printing tunnel URL..."
  sleep 5
  bash scripts/print-ngrok-url.sh || echo "⚠️  ngrok URL not yet available — retry: bash scripts/print-ngrok-url.sh"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ HRMS Backend is ready!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  API:        http://localhost:8000"
echo "  Health:     http://localhost:8000/health"
echo "  Docs:       http://localhost:8000/docs"
echo "  PostgreSQL: localhost:5432"
echo "  Redis:      localhost:6379"
echo "  Ollama:     http://localhost:11434"
echo "  Whisper:    http://localhost:9000"
if [ "$NGROK_ENABLED" = "true" ] || [ "$NGROK_ENABLED" = "1" ] || [ "$NGROK_ENABLED" = "yes" ]; then
  echo "  ngrok:      http://localhost:4040 (Inspector)"
  echo ""
  echo "  Run: bash scripts/print-ngrok-url.sh  to show tunnel URL"
fi
echo ""
echo "  Next: Configure Clerk authentication in .env"
echo "  Then start the frontend: cd ../frontend && npm run dev"
echo ""
