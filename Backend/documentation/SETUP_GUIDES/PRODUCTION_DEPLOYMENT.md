# Production Deployment Guide

## Server Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 40 GB SSD
- **OS**: Ubuntu 22.04 LTS / Debian 12
- **Network**: Public IP with ports 80, 443, 22 open

### Recommended Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **OS**: Ubuntu 22.04 LTS / Debian 12
- **Network**: Public IP with ports 80, 443, 22 open

### Software Requirements
- Docker Engine 24.0+
- Docker Compose v2.0+
- Git
- Nginx (reverse proxy)
- Certbot (SSL/TLS)

## Docker Compose Production Configuration

### Create docker-compose.prod.yml
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - CLERK_SECRET_KEY=${CLERK_SECRET_KEY}
      - CLERK_JWKS_URL=${CLERK_JWKS_URL}
      - RESEND_API_KEY=${RESEND_API_KEY}
      - OLLAMA_BASE_URL=http://ollama:11434
      - ENVIRONMENT=production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - hrms-network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15
    restart: always
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - hrms-network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - hrms-network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  ollama:
    image: ollama/ollama
    restart: always
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - hrms-network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

volumes:
  postgres_data:
  redis_data:
  ollama_data:

networks:
  hrms-network:
    driver: bridge
```

### Create .env.production
```env
# Database
POSTGRES_DB=hrms_db
POSTGRES_PASSWORD=your-secure-database-password

# Application
SECRET_KEY=your-super-secret-production-key
ENVIRONMENT=production

# Clerk
CLERK_SECRET_KEY=sk_live_your_clerk_secret_key
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json

# Email
RESEND_API_KEY=re_your_resend_api_key

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
```

## SSL/TLS with Let's Encrypt

### Install Certbot
```bash
# Update package index
sudo apt update

# Install Certbot
sudo apt install -y certbot python3-certbot-nginx
```

### Obtain SSL Certificate
```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Follow the prompts:
# - Enter email address
# - Agree to terms
# - Choose whether to share email
```

### Auto-Renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Check renewal timer
sudo systemctl list-timers | grep certbot

# Manual renewal
sudo certbot renew
```

### Certificate Files Location
```bash
# Certificate files
ls -la /etc/letsencrypt/live/yourdomain.com/

# privkey.pem  - Private key
# cert.pem     - Certificate
# chain.pem    - Certificate chain
# fullchain.pem - Full chain (certificate + chain)
```

## Nginx Production Configuration

### Install Nginx
```bash
sudo apt update
sudo apt install -y nginx
```

### Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/hrms-backend
```

### Configuration Content
```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

upstream app_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Logging
    access_log /var/log/nginx/hrms-backend.access.log;
    error_log /var/log/nginx/hrms-backend.error.log;
    
    # API Proxy
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://app_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://app_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files (if serving from Nginx)
    location /static/ {
        alias /opt/hrms-backend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://app_backend/health;
        access_log off;
    }
}
```

### Enable Configuration
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/hrms-backend /etc/nginx/sites-enabled/

# Remove default configuration
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Environment Variables for Production

### Required Variables
```env
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/hrms_db
POSTGRES_DB=hrms_db
POSTGRES_PASSWORD=very-secure-password-here

# Application
SECRET_KEY=your-256-bit-secret-key-here
ENVIRONMENT=production
DEBUG=false

# Authentication
CLERK_SECRET_KEY=sk_live_your_clerk_secret_key
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret

# Email
RESEND_API_KEY=re_your_resend_api_key

# AI
OLLAMA_BASE_URL=http://ollama:11434

# Redis
REDIS_URL=redis://redis:6379/0
```

### Generate Secure Keys
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate POSTGRES_PASSWORD
openssl rand -base64 32

# Generate CLERK_WEBHOOK_SECRET
openssl rand -hex 32
```

## Database Migrations in Production

### Run Migrations
```bash
# Access app container
docker-compose exec app bash

# Run migrations
alembic upgrade head

# Or run from host
docker-compose exec app alembic upgrade head
```

### Backup Before Migration
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres hrms_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore if needed
cat backup_20240101_120000.sql | docker-compose exec -T postgres psql -U postgres -d hrms_db
```

### Migration Best Practices
1. Always backup before running migrations
2. Test migrations in staging environment first
3. Run migrations during low-traffic periods
4. Monitor application after migration
5. Have a rollback plan ready

## Monitoring Setup

### Install Monitoring Tools
```bash
# Install htop
sudo apt install -y htop

# Install netdata (optional)
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

### Docker Monitoring
```bash
# View container stats
docker stats

# View specific container stats
docker stats hrms-backend-app-1

# View container logs
docker-compose logs -f --tail=100
```

### Application Health Check
```bash
# Test health endpoint
curl http://localhost:8000/health

# Check response time
curl -o /dev/null -s -w '%{time_total}\n' http://localhost:8000/health
```

### Set Up Log Rotation
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/hrms-backend

# Add configuration
/var/log/nginx/hrms-backend.*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
    endscript
}
```

## Backup Strategy

### Database Backup
```bash
# Create backup script
sudo nano /opt/hrms-backend/scripts/backup-db.sh

# Add content
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/hrms-backend/backups"
BACKUP_FILE="$BACKUP_DIR/hrms_db_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U postgres hrms_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### Schedule Backups
```bash
# Make script executable
chmod +x /opt/hrms-backend/scripts/backup-db.sh

# Add to crontab
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/hrms-backend/scripts/backup-db.sh >> /var/log/hrms-backup.log 2>&1
```

### Restore Backup
```bash
# Restore from backup
gunzip < /opt/hrms-backend/backups/hrms_db_20240101_020000.sql.gz | docker-compose exec -T postgres psql -U postgres -d hrms_db
```

### Backup Verification
```bash
# Verify backup integrity
gunzip -t /opt/hrms-backend/backups/hrms_db_20240101_020000.sql.gz

# Check backup size
ls -lh /opt/hrms-backend/backups/
```

## Scaling Considerations

### Horizontal Scaling
```yaml
# docker-compose.prod.yml
services:
  app:
    deploy:
      replicas: 3
```

### Load Balancer Configuration
```nginx
# Nginx upstream with multiple backends
upstream app_backend {
    least_conn;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

### Database Scaling
```bash
# Read replicas (PostgreSQL)
# Configure streaming replication

# Connection pooling (PgBouncer)
# Add PgBouncer service to docker-compose
```

### Caching Strategy
```bash
# Redis clustering
# Configure Redis Sentinel for high availability

# Application-level caching
# Cache frequently accessed data
```

### Resource Monitoring
```bash
# Set up Prometheus + Grafana
# Monitor CPU, memory, disk usage
# Set up alerts for high usage
```

## Deployment Checklist

- [ ] Server provisioned and secured
- [ ] Docker and Docker Compose installed
- [ ] Environment variables configured
- [ ] Docker Compose production file created
- [ ] SSL/TLS certificates obtained
- [ ] Nginx configured and tested
- [ ] Database migrations run
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Logs configured
- [ ] Security headers added
- [ ] Rate limiting configured
- [ ] Health checks working
- [ ] Application tested
- [ ] Documentation updated

## Common Production Issues

### High Memory Usage
```bash
# Check memory usage
free -h
docker stats

# Restart containers
docker-compose restart

# Increase server RAM
```

### SSL Certificate Expired
```bash
# Renew certificate
sudo certbot renew

# Restart Nginx
sudo systemctl restart nginx
```

### Database Connection Pool Exhausted
```bash
# Check connections
docker-compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max connections
docker-compose exec postgres psql -U postgres -c "ALTER SYSTEM SET max_connections = 200;"

# Restart PostgreSQL
docker-compose restart postgres
```

### Disk Space Full
```bash
# Check disk usage
df -h

# Clean Docker resources
docker system prune -a

# Remove old logs
sudo journalctl --vacuum-time=7d
```

## Useful Resources

- Docker Production Best Practices: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
- PostgreSQL Production Setup: https://www.postgresql.org/docs/current/runtime.html
- Nginx Production Configuration: https://nginx.org/en/docs/
- Let's Encrypt Documentation: https://letsencrypt.org/docs/
