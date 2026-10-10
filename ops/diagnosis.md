# Operational Incident Diagnosis & Post-Mortem Report

**Incident ID**: `INC-20261010-500-SPIKE`  
**Severity**: Severity 1 (High Impact)  
**Trigger**: Alert `HighServerErrorRate` fired on Prometheus (`http://localhost:9091`)  
**Affected Service**: `backend` (`http://localhost:8003/api/v1/reminders/summary`)  
**Status**: `RESOLVED & VERIFIED`

---

## 1. Incident Summary

At 08:00:15 UTC, the Prometheus alerting engine fired a P1 alert indicating a spike in HTTP 500 errors exceeding the 1% error threshold over a 2-minute rolling window on the `/api/v1/reminders/summary` endpoint. The autonomous on-call poller (`on-call-engineer/poll-alerts.py`) ingested the alert payload, triggered the diagnostic workflow, localized the root cause via distributed tracing, reproduced the defect in an isolated test, applied a minimal safe patch, and verified that metric error rates returned to 0.

---

## 2. Telemetry Evidence & Investigation Timeline

### A. Alert Notification Payload
```json
{
  "alertname": "HighServerErrorRate",
  "service": "personal-lifecycle-tracker-backend",
  "environment": "production",
  "endpoint": "/api/v1/reminders/summary",
  "severity": "critical",
  "value": "8.4%",
  "dashboard": "http://localhost:3004/d/lifecycle-golden-signals"
}
```

### B. Prometheus Metrics Analysis
- **Metric**: `rate(http_requests_total{status=~"5.."}[2m]) / rate(http_requests_total[2m])`
- **Observation**: Error rate climbed from 0.0% to 8.4% starting at 08:00:12 UTC following morning cron digest requests.

### C. Loki Log Telemetry Correlation
Querying Loki (`{app="backend"} |= "ERROR"`):
```text
2026-10-10T08:00:14.238Z [ERROR] TraceID=4bf92f3577b34da6a3ce929d0e0e4736 
Exception in calculate_upcoming_reminders: TypeError: '<=' not supported between instances of 'NoneType' and 'datetime.date'
File "app/routers/reminders.py", line 47, in get_reminders_summary
  if item.due_date <= target_date:
```

### D. Tempo Distributed Trace Inspection
- **Trace ID**: `4bf92f3577b34da6a3ce929d0e0e4736`
- **Span Hierarchy**:
  - `GET /api/v1/reminders/summary` (HTTP 500, duration 42ms)
    - `db.query: select_items_by_user` (duration 6ms)
    - `python.eval: reminder_filtering` (Exception recorded, duration 1ms)

---

## 3. Root Cause Analysis (RCA)

- **Root Cause**: The domain specification permits lifecycle items without mandatory due dates (`due_date` is optional for warranties and long-running equipment). When users registered warranties with `due_date = None`, the reminders summary calculator executed direct relational comparisons (`item.due_date <= target_date`) without validating that `item.due_date is not None`.
- **Trigger**: Multiple users added undated warranty cards during morning onboarding, causing subsequent calls to `/api/v1/reminders/summary` to fail with unhandled `TypeError`.

---

## 4. Remediation & Fix Implementation

1. **Local Test Reproduction**:
   Created a regression test in `backend/tests/test_reminders.py`:
   ```python
   def test_reminders_summary_with_null_due_date(client, auth_headers):
       # Item with due_date = None
       client.post("/api/v1/items", json={"name": "TV Warranty", "type": "warranty", "due_date": None}, headers=auth_headers)
       response = client.get("/api/v1/reminders/summary", headers=auth_headers)
       assert response.status_code == 200
       assert response.json()["total_undated"] >= 1
   ```
2. **Minimal Safe Code Correction**:
   Updated `backend/app/routers/reminders.py` to defensively guard against `None` due dates:
   ```python
   # Defensively filter items with valid due dates
   if item.due_date and item.due_date <= target_date:
       upcoming_items.append(item)
   elif item.due_date is None:
       undated_items.append(item)
   ```
3. **Containerized Test Execution**:
   Executed `make test-backend` inside Docker. All 27 unit and integration tests passed.

---

## 5. Post-Remediation Telemetry Verification

- **Endpoint Validation**: `curl -f http://localhost:8003/api/v1/reminders/summary` returns HTTP 200 OK.
- **Prometheus Metric**: `http_requests_total{status="500"}` flattened; 5-minute error rate returned to 0.0%.
- **Alert Resolution**: Prometheus marked `HighServerErrorRate` as `resolved`.
- **Audit Trail**: Recorded in `on-call-engineer/audit-trail.log`.
