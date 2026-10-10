# On-Call Incident Triage Runbook — Personal Lifecycle Tracker

This runbook guides automated and human on-call engineers triaging alerts emitted by the Personal Lifecycle Tracker observability stack.

---

## 1. General Triage Procedure

1. **Acknowledge Alert**:
   - Inspect the normalized incident payload in `_docs/incidents/incident-<id>.json`.
   - Verify impacted service (`api-backend`, `web-frontend`), environment, and deployed version.

2. **Inspect Telemetry**:
   - **Grafana Dashboard**: [http://localhost:3004/d/lifecycle-tracker-overview](http://localhost:3004/d/lifecycle-tracker-overview)
   - **Backend Logs**:
     ```bash
     rtk docker compose logs --tail=100 -f backend
     ```
   - **OTel Collector Logs**:
     ```bash
     rtk docker compose -f observability/docker-compose.yaml logs --tail=100 otel-collector
     ```
   - **Prometheus Alert API**:
     ```bash
     rtk curl http://localhost:9091/api/v1/alerts
     ```

3. **Trace & Log Correlation**:
   - In Grafana (or Tempo at `http://localhost:3201`), filter for spans with `status.code = ERROR` or HTTP status `500`.
   - In Loki (`http://localhost:3101` or via Grafana Explore), query `{service_name="api-backend"} |= "error"`.

4. **Local Defect Reproduction**:
   - Run baseline container tests to confirm current state:
     ```bash
     docker compose run --rm backend pytest tests -m "not integration"
     ```
   - Author a test reproducing the defect in `backend/tests/test_repro_<incident_id>.py`.

5. **Remediation & Verification**:
   - Implement the smallest safe correction in `backend/app/`.
   - Re-run test suite inside container: `make test-backend`.
   - Verify that the Prometheus alert changes from `firing` to `resolved`.

---

## 2. Alert-Specific Triage Guides

### `HighHttpErrorRate`
- **Severity**: Critical
- **Trigger**: 5xx HTTP errors exceed 5% over 1 minute.
- **Likely Causes**:
  - Unhandled exception in FastAPI router (`backend/app/routers/`).
  - Database connectivity loss or connection pool exhaustion in `backend/app/database.py`.
  - Malformed JWT token parsing or missing environment variables.
- **Action**:
  1. Inspect recent commits: `git log -n 5`.
  2. Inspect backend logs for tracebacks: `docker compose logs --tail=100 backend`.
  3. Verify PostgreSQL status: `docker compose exec db pg_isready -U postgres -d lifecycle`.

### `HighHttpLatencyP99`
- **Severity**: Warning
- **Trigger**: p99 HTTP latency exceeds 1000ms over 2 minutes.
- **Likely Causes**:
  - Unindexed SQL queries over `items`, `reminders`, or `groups` tables.
  - Synchronous blocking I/O inside asynchronous async def endpoints.
  - High lock contention during batch updates.
- **Action**:
  1. Inspect Tempo traces to identify slow database or processing spans.
  2. Add indexes or optimize query plan in `backend/app/store.py` / `models.py`.

### `DailyDigestFailures`
- **Severity**: Critical
- **Trigger**: Morning email digest generation failure counter increments.
- **Likely Causes**:
  - SMTP connection failure or invalid email address formatting.
  - Template rendering failure when user has zero or overdue lifecycle items.
- **Action**:
  1. Check digest logs: `docker compose logs backend | grep -i digest`.
  2. Test digest endpoint locally via `curl -X POST http://localhost:8003/api/v1/digests/test-run`.

### `RepeatedItemCreationFailures` / `LifecycleItemCreationFailures`
- **Severity**: Critical
- **Trigger**: Lifecycle item creation failure rate exceeds 5% over 5 minutes.
- **Likely Causes**:
  - Database schema constraint violation (e.g. invalid lifecycle type).
  - Pydantic validation regression on renewal date or maintenance interval.
  - Auth token expiry or missing group permission.
- **Action**:
  1. Inspect validation errors in backend logs: `docker compose logs backend | grep -E "(422|500)"`.
  2. Verify payload matches `contracts/openapi.yaml` schema for `LifecycleItemCreate`.
