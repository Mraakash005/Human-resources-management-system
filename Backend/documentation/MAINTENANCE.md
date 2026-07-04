# Maintenance Procedures

## Overview

Regular maintenance tasks to keep the HRMS system running optimally. Tasks are organized by frequency.

---

## Daily Tasks

### Health Check Verification

```bash
# Run the health check script
python scripts/healthcheck.py

# Check all services
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "environment": "production",
  "database": true,
  "redis": true
}
```

### Log Review

```bash
# Check application logs for errors
docker compose logs backend --tail=500 | grep -i "error\|warning"

# Check PostgreSQL logs
docker compose logs postgres --tail=100 | grep -i "error\|fatal"

# Check Redis logs
docker compose logs redis --tail=50
```

### Disk Space Check

```bash
# Check disk usage
df -h /var/lib/postgresql/data
df -h /var/lib/redis
df -h /app/storage

# Alert if usage exceeds 80%
du -sh /var/lib/postgresql/data
du -sh /var/lib/redis
du -sh /app/storage
```

---

## Weekly Tasks

### Database Statistics Update

```sql
-- Update table statistics for query planner
ANALYZE employees;
ANALYZE attendance;
ANALYZE leave_requests;
ANALYZE payroll_records;
ANALYZE chat_messages;
ANALYZE audit_logs;

-- Or update all tables at once
ANALYZE;
```

### Cache Audit

```bash
# Check Redis memory usage
redis-cli INFO memory

# Check key count
redis-cli DBSIZE

# Check for keys with no TTL
redis-cli --scan | head -20
```

### Log Rotation Verification

```bash
# Verify logrotate is running
cat /etc/logrotate.d/hrms

# Test configuration
logrotate -d /etc/logrotate.d/hrms

# Force rotation
logrotate -f /etc/logrotate.d/hrms
```

Example logrotate config:
```
/app/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 hrms hrms
    sharedscripts
    postrotate
        docker compose kill -s USR1 backend
    endscript
}
```

---

## Monthly Tasks

### PostgreSQL Vacuum and Analyze

```sql
-- Full vacuum analyze (returns space to OS)
VACUUM ANALYZE employees;
VACUUM ANALYZE attendance;
VACUUM ANALYZE leave_requests;
VACUUM ANALYZE payroll_records;
VACUUM ANALYZE chat_messages;
VACUUM ANALYZE audit_logs;
VACUUM ANALYZE nudges;
VACUUM ANALYZE burnout_alerts;

-- Check table bloat
SELECT
  schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  n_dead_tup,
  n_live_tup,
  ROUND(n_dead_tup::float / NULLIF(n_live_tup, 0) * 100, 2) AS dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

### PostgreSQL Index Maintenance

```sql
-- Check index usage
SELECT
  schemaname, tablename, indexname,
  idx_scan AS times_used,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Reindex bloated indexes
REINDEX INDEX idx_employees_clerk_user_id;
REINDEX INDEX idx_attendance_employee_date;
```

### Database Size Report

```sql
-- Overall database size
SELECT pg_size_pretty(pg_database_size('hrms_db'));

-- Top 10 largest tables
SELECT
  schemaname||'.'||tablename AS table_name,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
  pg_size_pretty(pg_indexes_size((schemaname||'.'||tablename)::regclass)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

### Redis Maintenance

```bash
# Check memory usage and fragmentation
redis-cli INFO memory | grep -E "used_memory_human|mem_fragmentation_ratio"

# Clean up expired keys (Redis does this automatically, but verify)
redis-cli INFO keyspace

# Check slow log
redis-cli SLOWLOG GET 10

# Rewrite AOF (if using AOF persistence)
redis-cli BGREWRITEAOF
```

### Dependency Updates

```bash
# Check for outdated packages
pip list --outdated

# Update requirements
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# Verify after update
python -c "import app; print('Import OK')"
pytest tests/unit/ -x -q
```

---

## Ollama Model Maintenance

### Check Model Status

```bash
# List installed models
curl http://localhost:11434/api/tags

# Check model size and last modified
docker compose exec ollama ls -la /root/.ollama/models/

# Check Ollama disk usage
docker compose exec ollama du -sh /root/.ollama/
```

### Update Models

```bash
# Pull latest version of a model
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull mistral

# Remove unused models to free space
docker compose exec ollama ollama rm <model_name>

# Verify model works
curl http://localhost:11434/api/generate \
  -d '{"model":"llama3","prompt":"Say hello","stream":false}'
```

### Model Performance Check

```bash
# Benchmark model response time
time curl -s http://localhost:11434/api/generate \
  -d '{"model":"llama3","prompt":"What is 2+2?","stream":false}' \
  | jq .eval_count

# Check GPU usage (if available)
nvidia-smi
```

---

## Quarterly Tasks

### Security Audit

```bash
# Check for vulnerable dependencies
pip-audit

# Update security patches
pip install --upgrade --security-only -r requirements.txt

# Review access logs
docker compose logs backend | grep -i "unauthorized\|forbidden"

# Rotate secrets (if required)
# Generate new SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### Performance Review

```sql
-- Slow query analysis
SELECT
  calls,
  ROUND(total_exec_time::numeric, 2) AS total_ms,
  ROUND(mean_exec_time::numeric, 2) AS avg_ms,
  ROUND(stddev_exec_time::numeric, 2) AS stddev_ms,
  rows,
  LEFT(query, 100) AS query_preview
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

### Backup Drill

```bash
# Verify backup can be restored
./scripts/verify_backup.sh /backups/postgres/latest.dump

# Test full recovery procedure (in staging)
# Document any issues found
```

---

## Scheduled Maintenance Windows

| Task                  | Frequency | Window        | Downtime Required |
|-----------------------|-----------|---------------|-------------------|
| DB Vacuum             | Monthly   | Sunday 2 AM   | No                |
| Ollama Model Update   | Monthly   | Sunday 3 AM   | No                |
| Dependency Updates    | Monthly   | Friday 6 PM   | Restart only      |
| Security Patches      | Quarterly | Weekend       | Possible restart  |
| Full DR Drill         | Quarterly | Weekend       | Yes (staging)     |
| Log Archival          | Weekly    | Sunday 1 AM   | No                |
| Disk Cleanup          | Weekly    | Sunday 4 AM   | No                |

---

## Maintenance Scripts

### Full Monthly Maintenance

```bash
#!/usr/bin/env bash
# scripts/monthly_maintenance.sh
set -euo pipefail

LOG="/var/log/hrms/maintenance_$(date +%Y%m%d).log"
exec > >(tee -a "$LOG") 2>&1

echo "=== Monthly Maintenance: $(date) ==="

# 1. Database maintenance
echo "[1/6] Running VACUUM ANALYZE..."
psql -h localhost -U hrms -d hrms_db -c "VACUUM ANALYZE;"

# 2. Update statistics
echo "[2/6] Updating statistics..."
psql -h localhost -U hrms -d hrms_db -c "ANALYZE;"

# 3. Check for bloated tables
echo "[3/6] Checking table bloat..."
psql -h localhost -U hrms -d hrms_db -c "
  SELECT tablename, n_dead_tup, n_live_tup
  FROM pg_stat_user_tables
  WHERE n_dead_tup > 10000
  ORDER BY n_dead_tup DESC;"

# 4. Redis maintenance
echo "[4/6] Redis maintenance..."
redis-cli BGREWRITEAOF
redis-cli MEMORY DOCTOR

# 5. Clean old logs
echo "[5/6] Cleaning old logs..."
find /var/log/hrms -name "*.log" -mtime +30 -delete

# 6. Backup verification
echo "[6/6] Verifying backups..."
./scripts/verify_backup.sh /backups/postgres/latest.dump

echo "=== Maintenance complete: $(date) ==="
```

### Disk Cleanup Script

```bash
#!/usr/bin/env bash
# scripts/disk_cleanup.sh
set -euo pipefail

echo "=== Disk Cleanup: $(date) ==="

# Clean Docker images
docker image prune -f

# Clean old backup files
find /backups -name "*.dump.gz" -mtime +30 -delete
find /backups -name "*.rdb.gz" -mtime +7 -delete

# Clean old log files
find /var/log/hrms -name "*.log" -mtime +14 -delete
find /var/log/hrms -name "*.log.gz" -mtime +30 -delete

# Clean temp files
find /tmp -name "hrms_*" -mtime +1 -delete

# Report disk usage
df -h /var/lib/postgresql/data
df -h /var/lib/redis
df -h /app/storage

echo "=== Cleanup complete ==="
```

---

## Monitoring Alerts

Configure these alerts for proactive maintenance:

| Metric                         | Threshold  | Action                    |
|--------------------------------|------------|---------------------------|
| Disk usage                     | > 80%      | Run disk cleanup          |
| Database dead tuples           | > 50000    | Run VACUUM                |
| Redis memory usage             | > 80%      | Check key expiry          |
| Ollama response time           | > 5s       | Check model health        |
| Slow queries (>1s)             | > 10/hour  | Review query performance  |
| Backup age                     | > 26 hours | Investigate backup job    |
| Connection pool usage          | > 80%      | Increase pool size        |
