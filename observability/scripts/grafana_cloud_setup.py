#!/usr/bin/env python3
"""
Automated Grafana Cloud Setup & Team Seat Invitation Utility.
Connects to Grafana (Cloud or self-hosted) via Grafana REST API & MCP,
configures Prometheus data source, imports production dashboards,
and invites team members.
"""
import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

CLOUDFRONT_METRICS_URL = "https://d1ca9upoitnq9b.cloudfront.net/metrics"
DASHBOARD_FILE = os.path.join(
    os.path.dirname(__file__), "..", "grafana", "dashboards", "lifecycle-tracker-overview.json"
)

class GrafanaClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token.strip()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {"status": status}
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("message", err_body)
            except Exception:
                msg = err_body
            raise RuntimeError(f"Grafana API error ({err.code} {err.reason}) on {method} {path}: {msg}")
        except urllib.error.URLError as err:
            raise RuntimeError(f"Connection failed to {url}: {err.reason}")

    def check_health(self) -> Dict[str, Any]:
        return self._request("GET", "/api/health")

    def get_org(self) -> Dict[str, Any]:
        return self._request("GET", "/api/org")

    def ensure_datasource(self, name: str = "AWS-CloudFront-Prometheus", url: str = CLOUDFRONT_METRICS_URL) -> Dict[str, Any]:
        """Ensure Prometheus datasource pointing to CloudFront /metrics exists."""
        datasources = self._request("GET", "/api/datasources")
        for ds in datasources:
            if ds.get("name") == name:
                print(f"[*] Datasource '{name}' already exists (id={ds.get('id')}). Updating...")
                update_payload = {
                    "name": name,
                    "type": "prometheus",
                    "access": "proxy",
                    "url": url,
                    "isDefault": True,
                    "jsonData": {
                        "httpMethod": "GET"
                    }
                }
                return self._request("PUT", f"/api/datasources/{ds['id']}", update_payload)

        print(f"[*] Creating new Prometheus datasource '{name}' pointing to {url}...")
        create_payload = {
            "name": name,
            "type": "prometheus",
            "access": "proxy",
            "url": url,
            "isDefault": True,
            "jsonData": {
                "httpMethod": "GET"
            }
        }
        return self._request("POST", "/api/datasources", create_payload)

    def import_dashboard(self, dashboard_path: str = DASHBOARD_FILE, ds_uid: Optional[str] = None) -> Dict[str, Any]:
        """Import the production Lifecycle Tracker Overview dashboard."""
        if not os.path.exists(dashboard_path):
            raise FileNotFoundError(f"Dashboard file not found: {dashboard_path}")

        with open(dashboard_path, "r", encoding="utf-8") as f:
            dashboard_json = json.load(f)

        # Remove id for new import
        dashboard_json["id"] = None
        dashboard_json["uid"] = "lifecycle-tracker-overview"

        if ds_uid:
            dashboard_str = json.dumps(dashboard_json)
            dashboard_str = dashboard_str.replace('"uid": "prometheus"', f'"uid": "{ds_uid}"')
            dashboard_json = json.loads(dashboard_str)

        payload = {
            "dashboard": dashboard_json,
            "overwrite": True,
            "message": "Automated import via Coding Agent Grafana Setup"
        }
        print(f"[*] Importing dashboard '{dashboard_json.get('title')}' into Grafana...")
        result = self._request("POST", "/api/dashboards/db", payload)
        return result

    def invite_team_member(self, email: str, role: str = "Viewer", name: str = "") -> Dict[str, Any]:
        """Invite a team member to the Grafana organization."""
        payload = {
            "name": name or email.split("@")[0],
            "email": email,
            "role": role,  # Viewer, Editor, Admin
            "sendEmail": True
        }
        print(f"[*] Inviting team member {email} with role '{role}'...")
        return self._request("POST", "/api/org/invites", payload)

    def list_invites(self) -> Dict[str, Any]:
        return self._request("GET", "/api/org/invites")


def main():
    grafana_url = os.getenv("GRAFANA_URL", "").strip()
    grafana_token = os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN", "").strip()

    if len(sys.argv) >= 3:
        grafana_url = sys.argv[1].strip()
        grafana_token = sys.argv[2].strip()

    if not grafana_url or not grafana_token:
        print("Usage:")
        print("  python3 grafana_cloud_setup.py <GRAFANA_URL> <SERVICE_ACCOUNT_TOKEN> [INVITE_EMAIL_1] [INVITE_EMAIL_2] ...")
        print("Or set environment variables:")
        print("  export GRAFANA_URL=\"https://<your-org>.grafana.net\"")
        print("  export GRAFANA_SERVICE_ACCOUNT_TOKEN=\"glsa_...\"")
        sys.exit(1)

    print(f"[*] Connecting to Grafana at: {grafana_url}")
    client = GrafanaClient(grafana_url, grafana_token)

    health = client.check_health()
    print(f"[+] Grafana connection healthy: version={health.get('version', 'unknown')}, commit={health.get('commit', 'unknown')}")

    try:
        org = client.get_org()
        print(f"[+] Connected to Organization: {org.get('name')} (id={org.get('id')})")
    except Exception as e:
        print(f"[!] Note: Org fetch: {e}")

    # 1. Identify Prometheus Datasource (e.g. grafanacloud-prom)
    datasources = client._request("GET", "/api/datasources")
    prom_ds = None
    for ds in datasources:
        if ds.get("uid") == "grafanacloud-prom":
            prom_ds = ds
            break
        elif ds.get("type") == "prometheus" and not prom_ds:
            prom_ds = ds

    ds_uid = prom_ds.get("uid") if prom_ds else "grafanacloud-prom"
    ds_name = prom_ds.get("name") if prom_ds else "grafanacloud-prom"
    print(f"[+] Binding Dashboard to hosted Prometheus Datasource: {ds_name} (UID={ds_uid})")

    # 2. Import Dashboard
    dash_res = client.import_dashboard(ds_uid=ds_uid)
    dash_url = dash_res.get("url", "/d/lifecycle-tracker-overview")
    full_dash_url = f"{client.base_url}{dash_url}"
    print(f"[+] Dashboard imported successfully!")
    print(f"    👉 Live Dashboard URL: {full_dash_url}")

    # 3. Handle any invited emails passed as CLI args
    invite_emails = sys.argv[3:]
    for email in invite_emails:
        try:
            client.invite_team_member(email, role="Viewer")
            print(f"[+] Successfully invited {email}!")
        except Exception as e:
            print(f"[-] Failed to invite {email}: {e}")

    print("\n=================================================================")
    print("  Grafana Cloud Setup Complete!")
    print("=================================================================")
    print(f"  • Grafana Dashboard: {full_dash_url}")
    print(f"  • Loki Logs Explorer: {client.base_url}/explore?left=%7B\"datasource\":\"grafanacloud-logs\"%7D")
    print(f"  • Tempo Traces Explorer: {client.base_url}/explore?left=%7B\"datasource\":\"grafanacloud-traces\"%7D")
    print(f"  • Team Management: {client.base_url}/admin/users")
    print("=================================================================")


if __name__ == "__main__":
    main()
