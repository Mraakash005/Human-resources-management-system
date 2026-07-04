# Backup and Restore Procedures

## Overview

This document covers backup and restore procedures for all HRMS data stores: PostgreSQL, Redis, and application storage.

---

## PostgreSQL Backup

### Manual Backup with pg_dump

```bash
# Full database dump (custom format — recommended)
pg_dump -h localhost -U hrms -d hrms_db \
  -F c -b -v \
  -f /backups/hrms_db_$(date +%Y%m%d_%H%M%S).dump

# SQL text dump (human-readable, slower restore)
pg_dump -h localhost -U hrms -d hrms_db \
  -F p -v \
  -f /backups/hrms_db_$(date +%Y%m%d_%H%M%S).sql

# Schema-only backup (no data)
pg_dump -h localhost -U hrms -d hrms_db \
  --schema-only -F c \
  -f /backups/hrms_schema_$(date +%Y%m%d_%H%M%S).dump

# Backup a single table
pg_dump -h localhost -U hrms -d hrms_db \
  -t employees -F c \
  -f /backups/hrms_employees_$(date +%Y%m%d_%H%M%S).dump
```

### Automated pg_dump Script

```bash
#!/usr/bin/env bash
# scripts/backup_postgres.sh
set -euo pipefail

BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="${BACKUP_DIR}/hrms_db_${TIMESTAMP}.dump"

# Source environment
source /app/.env 2>/dev/null || true

# Extract connection details from DATABASE_URL
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-hrms_db}"
DB_USER="${DB_USER:-hrms}"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting PostgreSQL backup..."

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -F c -b -v -f "$DUMP_FILE"

# Compress the dump
gzip "$DUMP_FILE"

# Delete backups older than retention period
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +${RETENTION_DAYS} -delete

LATEST=$(ls -t "$BACKUP_DIR"/*.dump.gz 2>/dev/null | head -1)
SIZE=$(du -h "$LATEST" | cut -f1)
echo "[$(date)] Backup complete: $LATEST ($SIZE)"
```

### Continuous Archiving (WAL Shipping)

```ini
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/wal_archive/%f'
max_wal_senders = 3
```

---

## Redis Backup

### RDB Snapshot

```bash
# Trigger immediate RDB save
redis-cli BGSAVE

# Check last save time
redis-cli LASTSAVE

# Copy the RDB file
cp /var/lib/redis/dump.rdb /backups/redis/dump_$(date +%Y%m%d_%H%M%S).rdb
```

### AOF Backup

```bash
# Rewrite AOF to minimize size
redis-cli BGREWRITEAOF

# Copy the AOF file
cp /var/lib/redis/appendonly.aof /backups/redis/aof_$(date +%Y%m%d_%H%M%S).aof
```

### Automated Redis Backup Script

```bash
#!/usr/bin/env bash
# scripts/backup_redis.sh
set -euo pipefail

BACKUP_DIR="/backups/redis"
RETENTION_DAYS=3
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting Redis backup..."

redis-cli BGSAVE
sleep 2

# Wait for background save to complete
while [ "$(redis-cli LASTSAVE)" == "$LAST_SAVE" ]; do
  sleep 1
done

cp /var/lib/redis/dump.rdb "$BACKUP_DIR/dump_${TIMESTAMP}.rdb"
gzip "$BACKUP_DIR/dump_${TIMESTAMP}.rdb"

find "$BACKUP_DIR" -name "*.rdb.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Redis backup complete"
```

---

## Application Storage Backup

```bash
# Backup uploaded files (profile pictures, documents)
tar czf /backups/storage/storage_$(date +%Y%m%d_%H%M%S).tar.gz \
  ./storage/

# Backup logs
tar czf /backups/logs/logs_$(date +%Y%m%d_%H%M%S).tar.gz \
  ./logs/
```

---

## Automated Backup Scheduling

### Cron Setup

```cron
# /etc/cron.d/hrms-backups

# PostgreSQL — daily at 2 AM
0 2 * * * hrms /app/scripts/backup_postgres.sh >> /var/log/hrms/backup.log 2>&1

# Redis — every 6 hours
0 */6 * * * hrms /app/scripts/backup_redis.sh >> /var/log/hrms/backup.log 2>&1

# Application storage — weekly on Sunday at 3 AM
0 3 * * 0 hrms tar czf /backups/storage/storage_$(date +\%Y\%m\%d).tar.gz /app/storage/

# Cleanup old backups — daily at 4 AM
0 4 * * * hrms find /backups -type f -mtime +30 -delete
```

### Docker Cron Setup

```yaml
# docker-compose.cron.yml
services:
  backup:
    image: postgres:16
    volumes:
      - ./scripts/backup_postgres.sh:/backup.sh:ro
      - backups:/backups
    environment:
      PGPASSWORD: ${POSTGRES_PASSWORD}
    entrypoint: /bin/bash
    command: >
      -c "echo '0 2 * * * /backup.sh' | crontab - && cron -f"
    depends_on:
      - postgres
```

---

## Restore Procedures

### PostgreSQL Restore

```bash
# Restore from custom format dump
pg_restore -h localhost -U hrms -d hrms_db \
  --clean --if-exists \
  -v /backups/hrms_db_20260101_020000.dump

# Restore from SQL dump
psql -h localhost -U hrms -d hrms_db \
  -f /backups/hrms_db_20260101_020000.sql

# Restore into a fresh database
createdb -h localhost -U hrms hrms_db_restored
pg_restore -h localhost -U hrms -d hrms_db_restored \
  -v /backups/hrms_db_20260101_020000.dump
```

### Full Recovery Procedure

```bash
# 1. Stop the application
docker compose stop backend

# 2. Drop and recreate the database
psql -h localhost -U postgres -c "DROP DATABASE hrms_db;"
psql -h localhost -U postgres -c "CREATE DATABASE hrms_db OWNER hrms;"

# 3. Restore from backup
pg_restore -h localhost -U hrms -d hrms_db \
  --clean --if-exists \
  /backups/postgres/hrms_db_latest.dump

# 4. Run any pending migrations
alembic upgrade head

# 5. Restart the application
docker compose start backend

# 6. Verify health
curl http://localhost:8000/health
```

### Redis Restore

```bash
# Stop Redis
docker compose stop redis

# Replace dump file
cp /backups/redis/dump_latest.rdb /data/dump.rdb

# Start Redis
docker compose start redis

# Verify data
redis-cli DBSIZE
```

### Point-in-Time Recovery (PostgreSQL)

```bash
# 1. Stop writes to database
# 2. Create recovery target timeline
pg_restore -h localhost -U hrms -d hrms_db \
  --target-time '2026-07-01 14:30:00' \
  --restore-in-progress \
  /backups/postgres/hrms_db_20260701_120000.dump

# 3. Verify data consistency
psql -h localhost -U hrms -d hrms_db \
  -c "SELECT COUNT(*) FROM employees;"
```

---

## Backup Verification

```bash
#!/usr/bin/env bash
# scripts/verify_backup.sh
set -euo pipefail

BACKUP_FILE="$1"
TEST_DB="hrms_verify_$(date +%s)"

echo "Verifying backup: $BACKUP_FILE"

createdb -h localhost -U hrms "$TEST_DB"

if pg_restore -h localhost -U hrms -d "$TEST_DB" "$BACKUP_FILE" 2>/dev/null; then
  COUNT=$(psql -h localhost -U hrms -d "$TEST_DB" \
    -t -c "SELECT COUNT(*) FROM employees;")
  echo "Backup verified: $COUNT employees found"
  RESULT=0
else
  echo "Backup verification FAILED"
  RESULT=1
fi

dropdb -h localhost -U hrms "$TEST_DB"
exit $RESULT
```

---

## Storage Locations

| Backup Type      | Local Path                  | Remote Path                  | Retention |
|------------------|-----------------------------|------------------------------|-----------|
| PostgreSQL       | `/backups/postgres/`        | S3:hrms-backups/postgres/    | 30 days   |
| Redis            | `/backups/redis/`           | S3:hrms-backups/redis/       | 7 days    |
| App Storage      | `/backups/storage/`         | S3:hrms-backups/storage/     | 30 days   |
| WAL Archive      | `/backups/wal_archive/`     | S3:hrms-backups/wal/         | 14 days   |

### Remote Sync

```bash
# Sync backups to S3
aws s3 sync /backups/postgres/ s3://hrms-backups/postgres/ \
  --storage-class STANDARD_IA

aws s3 sync /backups/redis/ s3://hrms-backups/redis/ \
  --storage-class STANDARD_IA
```

---

## Monitoring Backup Jobs

```python
# Add to app/jobs/scheduler.py
async def _verify_backups() -> None:
    """Verify latest backups are within expected age."""
    import os
    from datetime import datetime, timedelta

    max_age_hours = 26  # Should be backed up daily
    backup_dir = "/backups/postgres"

    if not os.path.exists(backup_dir):
        logger.error("Backup directory missing: %s", backup_dir)
        return

    files = sorted(os.listdir(backup_dir), reverse=True)
    if not files:
        logger.warning("No backups found in %s", backup_dir)
        return

    latest = os.path.join(backup_dir, files[0])
    age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(latest))).total_seconds() / 3600

    if age_hours > max_age_hours:
        logger.error("Latest backup is %.1f hours old (max: %d)", age_hours, max_age_hours)
    else:
        logger.debug("Latest backup is %.1f hours old", age_hours)
```
