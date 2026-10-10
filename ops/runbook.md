# Operations Runbook: Alert Response & Disaster Recovery

**Service**: Personal Lifecycle Tracker  
**Target Environments**: `dev`, `production`  
**Observability Suite**: Prometheus (`:9091`), Loki (`:3101`), Tempo (`:3201`), Grafana (`:3004`)

---

## 1. High-Priority Alert Response Procedures

### Alert: `HighServerErrorRate` (5xx Errors > 1%)
- **Condition**: 5xx HTTP response rate exceeds 1% of total traffic over a 2-minute sliding window.
- **Immediate Diagnostic Steps**:
  1. Open Grafana Golden Signals Dashboard at `http://localhost:3004/d/lifecycle-golden-signals`.
  2. Filter by `Environment: production` and isolate failing routes.
  3. Query Loki logs in Grafana: `{service="backend"} |= "ERROR"`.
  4. Copy failing `TraceID` and paste into Tempo Trace Search.
  5. Check if PostgreSQL database is reachable: `make test-integration` or `docker compose ps db`.
- **Mitigation**:
  - If due to database connection exhaustion, restart container or scale pool: `docker compose restart backend`.
  - If due to software bug, engage the on-call engineer or trigger headless remediation loop: `make on-call-verify`.

---

### Alert: `HighP95Latency` (Latency > 500ms)
- **Condition**: 95th percentile response latency exceeds 500ms over a 5-minute sliding window.
- **Diagnostic Steps**:
  1. Inspect PostgreSQL query durations in Prometheus: `pg_stat_activity`.
  2. Check for missing indexes or unpaginated list requests.
  3. Check CPU/Memory constraints: `docker stats`.

---

## 2. Backup & Disaster Recovery Procedures

### Automated Database Backup
Run daily PostgreSQL logical backup inside container:
```bash
docker compose exec -T db pg_dump -U postgres -d lifecycle | gzip > backups/lifecycle_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Database Restore & Recovery Verification
Test backup restoration into an isolated test container:
```bash
gunzip < backups/latest.sql.gz | docker compose exec -T db psql -U postgres -d lifecycle_restore_test
```

---

## 3. Deployment Rollback Workflow

If a production release introduces regression:
1. Revert to previous verified container image tag in AWS SSM parameter `/personal-lifecycle/production/image_tag`:
   ```bash
   aws ssm put-parameter --name "/personal-lifecycle/production/image_tag" --value "PREVIOUS_TAG" --type String --overwrite
   ```
2. Re-trigger the deploy job without rebuilding:
   ```bash
   docker compose -f docker-compose.prod.yml pull
   docker compose -f docker-compose.prod.yml up -d --no-build
   ```
3. Confirm health check returns HTTP 200:
   ```bash
   curl -f http://localhost:8088/health
   ```
