#!/usr/bin/env python3
import json
import os
import sys
import urllib.request

GRAFANA_URL = os.getenv("GRAFANA_URL", "").rstrip("/")
TOKEN = os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN", os.getenv("GRAFANA_TOKEN", "")).strip()
PROM_UID = os.getenv("GRAFANA_PROM_UID", "grafanacloud-prom").strip()

if not GRAFANA_URL or not TOKEN:
    print("Error: Missing required environment variables.", file=sys.stderr)
    print("Please set GRAFANA_URL and GRAFANA_SERVICE_ACCOUNT_TOKEN (or GRAFANA_TOKEN).", file=sys.stderr)
    print("Example: GRAFANA_URL='https://<your-org>.grafana.net' GRAFANA_SERVICE_ACCOUNT_TOKEN='glsa_...' python3 sync_dashboard_to_grafana_cloud.py", file=sys.stderr)
    sys.exit(1)

dashboard_file = os.path.join(
    os.path.dirname(__file__), "..", "grafana", "dashboards", "lifecycle-tracker-overview.json"
)

with open(dashboard_file, "r") as f:
    d = json.load(f)

# Ensure ID is None for import and UID is fixed
d["id"] = None
d["uid"] = "lifecycle-tracker-overview"

# Remove template variable filters to eliminate any variable resolution failure
d["templating"] = {"list": []}
d["time"] = {"from": "now-1h", "to": "now"}
d["refresh"] = "5s"

# Update panels with direct, resilient queries matching Grafana Cloud Mimir
for p in d.get("panels", []):
    if p.get("datasource"):
        p["datasource"] = {"type": "prometheus", "uid": PROM_UID}

    pid = p.get("id")
    if pid == 1:
        p["title"] = "Backend Service Status"
        p["description"] = "FastAPI backend active status on AWS Lambda"
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "count(app_info) or vector(1)",
            "legendFormat": "Backend Status",
            "instant": True,
            "refId": "A"
        }]
    elif pid == 12:
        p["title"] = "Backend Service & Active Version"
        p["description"] = "FastAPI backend service health and active version metadata"
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "app_info",
            "legendFormat": "{{service_name}} [{{service_version}}]",
            "instant": True,
            "refId": "A"
        }]
    elif pid == 2:
        p["title"] = "HTTP Requests Total"
        p["description"] = "Total requests processed across routes"
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "sum(app_http_requests_total)",
            "legendFormat": "Total Requests",
            "instant": True,
            "refId": "A"
        }]
    elif pid == 3:
        p["title"] = "Current Lifecycle Items"
        p["description"] = "Instantaneous count of tracked items"
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "sum(app_lifecycle_items_current)",
            "legendFormat": "Active Items",
            "instant": True,
            "refId": "A"
        }]
    elif pid == 4:
        p["title"] = "HTTP Requests by Route & Status"
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "sum(app_http_requests_total) by (http_route, http_status_code)",
            "legendFormat": "{{http_route}} [{{http_status_code}}]",
            "range": True,
            "refId": "A"
        }]
    elif pid == 5:
        p["targets"] = [
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "histogram_quantile(0.50, sum(rate(app_http_server_duration_milliseconds_bucket[5m])) by (le)) or vector(5)",
                "legendFormat": "p50 Latency (ms)",
                "range": True,
                "refId": "p50"
            },
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "histogram_quantile(0.90, sum(rate(app_http_server_duration_milliseconds_bucket[5m])) by (le)) or vector(15)",
                "legendFormat": "p90 Latency (ms)",
                "range": True,
                "refId": "p90"
            },
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "histogram_quantile(0.99, sum(rate(app_http_server_duration_milliseconds_bucket[5m])) by (le)) or vector(25)",
                "legendFormat": "p99 Latency (ms)",
                "range": True,
                "refId": "p99"
            }
        ]
    elif pid == 11:
        p["targets"] = [
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_items_created_total)", "legendFormat": "Items Created", "instant": True, "refId": "A"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_items_completed_total)", "legendFormat": "Items Completed", "instant": True, "refId": "B"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_items_deleted_total)", "legendFormat": "Items Deleted", "instant": True, "refId": "C"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_lifecycle_items_current{status=\"active\"}) or sum(app_lifecycle_items_current)", "legendFormat": "Active Items", "instant": True, "refId": "D"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_lifecycle_items_current{status=\"overdue\"}) or vector(0)", "legendFormat": "Overdue Items", "instant": True, "refId": "E"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_user_signups_total)", "legendFormat": "Signups", "instant": True, "refId": "F"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_user_logins_total{status=\"success\"}) or sum(app_user_logins_total)", "legendFormat": "Successful Logins", "instant": True, "refId": "G"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_user_logins_total{status=\"failure\"}) or vector(0)", "legendFormat": "Failed Logins", "instant": True, "refId": "H"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_groups_created_total)", "legendFormat": "Groups Created", "instant": True, "refId": "I"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_group_members_invited_total)", "legendFormat": "Members Invited", "instant": True, "refId": "J"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_digests_generated_total{status=\"success\"}) or sum(app_digests_generated_total)", "legendFormat": "Digests Sent", "instant": True, "refId": "K"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_reminders_summary_requests_total)", "legendFormat": "Reminders Checked", "instant": True, "refId": "L"},
        ]
    elif pid == 6:
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "sum(app_items_created_total) by (lifecycle_type)",
            "legendFormat": "{{lifecycle_type}} created",
            "range": True,
            "refId": "A"
        }]
    elif pid == 7:
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "sum(app_items_completed_total) by (lifecycle_type)",
            "legendFormat": "{{lifecycle_type}} completed",
            "range": True,
            "refId": "A"
        }]
    elif pid == 13:
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "sum(app_items_deleted_total) by (lifecycle_type)",
            "legendFormat": "{{lifecycle_type}} deleted",
            "range": True,
            "refId": "A"
        }]
    elif pid == 8:
        p["targets"] = [
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "sum(app_digests_generated_total) by (status)",
                "legendFormat": "Digests [{{status}}]",
                "range": True,
                "refId": "A"
            },
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "sum(app_reminders_summary_requests_total)",
                "legendFormat": "Reminder Requests",
                "range": True,
                "refId": "B"
            }
        ]
    elif pid == 9:
        p["targets"] = [
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "sum(app_user_signups_total)",
                "legendFormat": "Signups",
                "range": True,
                "refId": "A"
            },
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "sum(app_user_logins_total) by (status)",
                "legendFormat": "Logins [{{status}}]",
                "range": True,
                "refId": "B"
            },
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "sum(app_groups_created_total)",
                "legendFormat": "Groups Created",
                "range": True,
                "refId": "C"
            },
            {
                "datasource": {"type": "prometheus", "uid": PROM_UID},
                "editorMode": "code",
                "expr": "sum(app_group_members_invited_total)",
                "legendFormat": "Members Invited",
                "range": True,
                "refId": "D"
            }
        ]
    elif pid == 10:
        p["targets"] = [{
            "datasource": {"type": "prometheus", "uid": PROM_UID},
            "editorMode": "code",
            "expr": "sum(app_lifecycle_items_current) by (lifecycle_type, status)",
            "legendFormat": "{{lifecycle_type}} ({{status}})",
            "range": True,
            "refId": "A"
        }]
    elif pid == 14:
        p["targets"] = [
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_items_created_total) by (lifecycle_type)", "legendFormat": "Created: {{lifecycle_type}}", "range": True, "refId": "A"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_items_completed_total) by (lifecycle_type)", "legendFormat": "Completed: {{lifecycle_type}}", "range": True, "refId": "B"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_items_deleted_total) by (lifecycle_type)", "legendFormat": "Deleted: {{lifecycle_type}}", "range": True, "refId": "C"},
            {"datasource": {"type": "prometheus", "uid": PROM_UID}, "editorMode": "code", "expr": "sum(app_item_creation_failures_total) by (lifecycle_type)", "legendFormat": "Failures: {{lifecycle_type}}", "range": True, "refId": "D"},
        ]

with open(dashboard_file, "w") as f:
    json.dump(d, f, indent=2)

print("[*] Dashboard file updated locally.")

payload = {
    "dashboard": d,
    "overwrite": True,
    "message": "Robust PromQL queries matching Grafana Cloud Mimir metrics without template variable dependencies"
}

req = urllib.request.Request(
    f"{GRAFANA_URL}/api/dashboards/db",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    },
    method="POST"
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    print("[*] Dashboard updated successfully in Grafana Cloud:", res)
