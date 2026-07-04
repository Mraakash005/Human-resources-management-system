# Docker Setup Guide

## Docker Compose Services Overview

The project uses Docker Compose to manage multiple services:

| Service | Description | Port |
|---------|-------------|------|
| **postgres** | PostgreSQL database | 5432 |
| **redis** | Redis cache/message broker | 6379 |
| **ollama** | Ollama AI model server | 11434 |
| **whisper** | OpenAI Whisper ASR | 9000 |
| **clamav** | ClamAV antivirus | 3310 |
| **backend** | FastAPI application | 8000 |
| **nginx** | Reverse proxy | 80, 443 |
| **ngrok** | Public tunnel (optional) | — |

### Docker Compose Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| (default) | postgres, redis, ollama, whisper, clamav, backend, nginx | Normal development |
| `ngrok` | all above + ngrok | Clerk webhook development |

## Building Images

### Build All Services
```bash
docker compose build
```

### Build Without Cache
```bash
docker compose build --no-cache
```

## Starting Services

### Start All Services (without ngrok)
```bash
docker compose up -d
```

### Start with ngrok Profile
```bash
docker compose --profile ngrok up -d
```

### Smart Launcher (auto-detects NGROK_ENABLED)
```bash
bash scripts/docker-start.sh
```

### Start Specific Services
```bash
# Start only database and cache
docker compose up -d postgres redis

# Start with Ollama
docker compose up -d postgres redis ollama
```

### Start with Build
```bash
docker compose up -d --build
```

## Stopping Services

### Stop All Services
```bash
docker compose down
```

### Stop All Services Including ngrok
```bash
docker compose --profile ngrok down
```

### Stop and Remove Volumes
```bash
docker compose down -v
```

## Viewing Logs

### View All Logs
```bash
docker compose logs
```

### View Logs for Specific Service
```bash
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f ollama
docker compose logs -f ngrok
```

### View Last N Lines
```bash
docker compose logs --tail=100 backend
```

## Exec into Containers

### Access PostgreSQL Shell
```bash
docker compose exec postgres psql -U postgres -d hrms_db
```

### Access Redis CLI
```bash
docker compose exec redis redis-cli
```

### Access Ollama CLI
```bash
docker compose exec ollama ollama list
```

### Access App Container Shell
```bash
docker compose exec backend /bin/bash
```

### Run One-off Commands
```bash
# Run migration
docker compose exec backend alembic upgrade head

# Run Python script
docker compose exec backend python script.py

# Install new package
docker compose exec backend pip install package-name
```

## ngrok Integration

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

### ngrok Commands
```bash
# Start with ngrok
docker compose --profile ngrok up -d

# View ngrok logs
docker compose --profile ngrok logs ngrok

# Restart ngrok
docker compose --profile ngrok restart ngrok

# Stop ngrok
docker compose --profile ngrok down

# Print tunnel URL
bash scripts/print-ngrok-url.sh
```

### ngrok Health Check
```bash
# Check ngrok API
curl http://localhost:4040/api/tunnels

# Check backend via tunnel
curl https://<tunnel-url>/health
```

For full ngrok documentation, see `docs/NGROK.md`.

## Volume Management

### List Volumes
```bash
docker volume ls
```

### Inspect Volumes
```bash
docker volume inspect hrms-backend_postgres_data
docker volume inspect hrms-backend_redis_data
```

### Remove Volumes
```bash
docker volume rm hrms-backend_postgres_data
docker-compose down -v
```

### Backup PostgreSQL Volume
```bash
docker-compose exec postgres pg_dump -U postgres hrms_db > backup.sql
cat backup.sql | docker-compose exec -T postgres psql -U postgres -d hrms_db
```

## Resource Limits

### Set Memory Limits in docker-compose.yml
```yaml
services:
  postgres:
    image: postgres:15
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  redis:
    image: redis:7-alpine
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M

  ollama:
    image: ollama/ollama
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Monitor Resource Usage
```bash
docker stats
docker stats hrms-backend-app-1
```

## Common Docker Commands

### List Running Containers
```bash
docker compose ps
```

### List All Containers (including stopped)
```bash
docker compose ps -a
```

### Restart Services
```bash
docker compose restart
docker compose restart backend
docker compose --profile ngrok restart ngrok
```

### View Docker Compose Configuration
```bash
docker compose config
```

### Pull Latest Images
```bash
docker compose pull
```

## Troubleshooting

### Container Won't Start
```bash
docker-compose logs <service-name>
docker-compose ps
docker-compose up -d --build
```

### ngrok Won't Start
```bash
# Check ngrok logs
docker compose --profile ngrok logs ngrok

# Verify NGROK_AUTHTOKEN is set
grep NGROK_AUTHTOKEN .env

# Check if ngrok API is accessible
curl http://localhost:4040/api/tunnels
```

### Database Connection Issues
```bash
docker compose ps postgres
docker compose exec postgres psql -U postgres -c "\l"
docker compose exec app env | grep DATABASE
```

### Port Conflicts
```bash
netstat -tulpn | grep 5432
# Stop conflicting service or change port in docker-compose.yml
```

### Disk Space Issues
```bash
docker system df
docker system prune -a
docker volume prune
```
