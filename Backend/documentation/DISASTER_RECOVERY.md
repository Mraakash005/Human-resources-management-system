# Disaster Recovery Plan

## Overview

This document defines recovery objectives, failover procedures, and step-by-step recovery playbooks for the HRMS system.

---

## Recovery Objectives

### Recovery Time Objective (RTO)

| Scenario                        | Target RTO | Priority |
|---------------------------------|------------|----------|
| Application server failure      | 5 minutes  | P1       |
| PostgreSQL failure              | 15 minutes | P1       |
| Redis failure                   | 5 minutes  | P2       |
| Full infrastructure loss        | 60 minutes | P0       |
| Ollama/Whisper failure          | 30 minutes | P3       |
| Email service failure           | 60 minutes | P3       |

### Recovery Point Objective (RPO)

| Data Type         | Target RPO | Backup Frequency |
|-------------------|------------|------------------|
| Employee records  | 1 hour     | Hourly WAL       |
| Attendance logs   | 15 minutes | WAL shipping     |
| Payroll data      | 24 hours   | Daily pg_dump    |
| Chat messages     | 0 (no RPO) | Real-time writes |
| Audit logs        | 0 (no RPO) | Real-time writes |
| Cache (Redis)     | 0 (no RPO) | Ephemeral data   |

---

## Failover Procedures

### PostgreSQL Failover

#### Primary to Replica Promotion

```bash
# 1. Check replication status
psql -h primary_host -U hrms -c "SELECT * FROM pg_stat_replication;"

# 2. Promote the replica
psql -h replica_host -U postgres -c "SELECT pg_promote();"

# 3. Update application DATABASE_URL
# Change in .env or environment variables:
# DATABASE_URL=postgresql+asyncpg://hrms:password@replica_host:5432/hrms_db

# 4. Restart the backend
docker compose restart backend

# 5. Verify health
curl http://localhost:8000/health
```

#### Automatic Failover with Patroni

```yaml
# patroni.yml
scope: hrms-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.0.1:8008

etcd3:
  hosts: 10.0.0.10:2379

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.0.1:5432
  data_dir: /var/lib/postgresql/data
  authentication:
    replication:
      username: replicator
      password: ${REPLICATION_PASSWORD}
    superuser:
      username: postgres
      password: ${POSTGRES_PASSWORD}

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 100
        shared_buffers: 256MB
        wal_level: replica
        max_wal_senders: 5
```

### Redis Failover

#### Sentinel Configuration

```conf
# sentinel.conf
port 26379
sentinel monitor hrms-redis 127.0.0.1 6379 2
sentinel down-after-milliseconds hrms-redis 5000
sentinel failover-timeout hrms-redis 10000
sentinel parallel-syncs hrms-redis 1
```

#### Connecting via Sentinel

```python
# In app/core/redis.py
from redis.sentinel import Sentinel

sentinel = Sentinel(
    [("sentinel1", 26379), ("sentinel2", 26379)],
    socket_timeout=0.5,
)
master = sentinel.master_for("hrms-redis", socket_timeout=0.5)
slave = sentinel.slave_for("hrms-redis", socket_timeout=0.5)
```

### Application Server Failover

```nginx
# nginx upstream with health checks
upstream hrms_backend {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    location / {
        proxy_pass http://hrms_backend;
        proxy_next_upstream error timeout http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
    }
}
```

---

## Recovery Playbooks

### Playbook 1: Database Corruption

```
SEVERITY: Critical
RTO: 30 minutes
RPO: 1 hour

Steps:
1. Stop application writes
   docker compose stop backend

2. Check PostgreSQL logs for corruption
   docker compose logs postgres --tail=100

3. If corruption detected, restore from latest backup
   pg_dump -h localhost -U hrms -d hrms_db -f /tmp/pre_restore.dump 2>/dev/null || true

   psql -h localhost -U postgres -c "DROP DATABASE hrms_db;"
   psql -h localhost -U postgres -c "CREATE DATABASE hrms_db OWNER hrms;"
   pg_restore -h localhost -U hrms -d hrms_db /backups/postgres/latest.dump

4. Apply WAL logs for point-in-time recovery if available

5. Restart and verify
   docker compose start backend
   curl http://localhost:8000/health
```

### Playbook 2: Redis Data Loss

```
SEVERITY: Medium
RTO: 5 minutes
RPO: 0 (cache data is ephemeral)

Steps:
1. Check if Redis process is running
   docker compose ps redis

2. If process is down, restart it
   docker compose restart redis

3. If data directory is corrupted, flush and restart
   redis-cli FLUSHALL
   docker compose restart redis

4. Application will rebuild cache on next request
   curl http://localhost:8000/health
```

### Playbook 3: Full Infrastructure Loss

```
SEVERITY: Critical
RTO: 60 minutes
RPO: 1 hour

Steps:
1. Provision new infrastructure (scripts/terraform apply)

2. Restore PostgreSQL from latest backup
   pg_restore -h new_db_host -U hrms -d hrms_db /backups/s3/latest.dump

3. Restore Redis (or start fresh — cache is ephemeral)
   docker compose up -d redis

4. Deploy backend
   docker compose up -d backend

5. Update DNS/load balancer to point to new infrastructure

6. Verify all services
   python scripts/healthcheck.py

7. Monitor for 30 minutes
   docker compose logs -f backend
```

### Playbook 4: Ollama Service Failure

```
SEVERITY: Low
RTO: 30 minutes
RPO: 0

Steps:
1. Check Ollama process
   docker compose ps ollama
   curl http://localhost:11434/api/tags

2. If Ollama is down, restart it
   docker compose restart ollama

3. Wait for model to load (check /api/tags)
   watch -n 5 'curl -s http://localhost:11434/api/tags | jq .'

4. Test inference
   curl http://localhost:11434/api/generate \
     -d '{"model":"llama3","prompt":"Hello","stream":false}'

5. If model is corrupted, pull again
   docker compose exec ollama ollama pull llama3
```

---

## Circuit Breaker Status

The application includes circuit breakers for external services:

| Service   | Failure Threshold | Reset Timeout | Fallback                     |
|-----------|-------------------|---------------|------------------------------|
| Ollama    | 5 failures        | 60 seconds    | Return generic error         |
| ClamAV    | 3 failures        | 30 seconds    | Skip virus scan (log warning)|
| Whisper   | 3 failures        | 30 seconds    | Return transcription error   |
| Resend    | 3 failures        | 60 seconds    | Queue email for retry        |

### Checking Circuit Breaker State

```bash
# Check application logs for circuit breaker status
docker compose logs backend | grep "circuit breaker"

# Reset circuit breaker by restarting backend
docker compose restart backend
```

---

## Communication Plan

### During Incident

| Stakeholder       | Notification Method | Timing       |
|-------------------|---------------------|--------------|
| Engineering Lead  | Slack + Phone       | Immediate    |
| DevOps Team       | Slack               | 5 minutes    |
| HR Department     | Email               | 30 minutes   |
| End Users         | Status page         | 1 hour       |
| Management        | Email               | 2 hours      |

### Post-Incident

1. **Root Cause Analysis (RCA)**: Within 48 hours
2. **Incident Report**: Within 72 hours
3. **Process Improvements**: Within 1 week
4. **Runbook Updates**: Within 1 week

---

## Testing the DR Plan

### Quarterly DR Drills

```bash
#!/usr/bin/env bash
# scripts/dr_drill.sh
echo "=== DR Drill: Simulating PostgreSQL Failure ==="

# 1. Take fresh backup
/app/scripts/backup_postgres.sh

# 2. Stop primary PostgreSQL
docker compose stop postgres

# 3. Measure recovery time
START=$(date +%s)

# 4. Restore to new instance
docker compose up -d postgres-new
pg_restore -h localhost -p 5433 -U hrms -d hrms_db /backups/latest.dump

# 5. Update connection and restart
END=$(date +%s)
DURATION=$((END - START))

echo "Recovery completed in ${DURATION} seconds"
echo "RTO target: 1800 seconds"

# 6. Cleanup
docker compose rm -f postgres-new
docker compose start postgres
```

---

## Backup Verification Checklist

- [ ] PostgreSQL backup restores successfully
- [ ] Redis backup restores successfully
- [ ] Application storage backup is complete
- [ ] Backup files are encrypted at rest
- [ ] Offsite backup copy exists (S3)
- [ ] WAL archiving is functioning
- [ ] Cron jobs are running on schedule
- [ ] Monitoring alerts are configured
- [ ] DR drill completed this quarter
