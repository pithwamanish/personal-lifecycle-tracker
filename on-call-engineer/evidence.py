"""Collect telemetry evidence for Personal Lifecycle Tracker incidents.

Every query here is read-only and scoped to the service. A failure in any one
backend (Prometheus, Loki, Tempo) is recorded as a non-fatal warning, so a
partial telemetry outage never blocks the overall incident response pipeline.
"""

import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9091")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3101")
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3201")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "api-backend")
LOOKBACK_MINUTES = int(os.getenv("EVIDENCE_LOOKBACK_MINUTES", "15"))
MAX_LOGS = int(os.getenv("EVIDENCE_MAX_LOGS", "30"))
MAX_TRACES = int(os.getenv("EVIDENCE_MAX_TRACES", "5"))


@dataclass
class Evidence:
    service_name: str
    window_start: str
    window_end: str
    requests_by_status: dict
    failing_routes: list
    error_logs: list
    error_trace_ids: list
    container_status: str
    recent_commits: list
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "service_name": self.service_name,
            "window": {"start": self.window_start, "end": self.window_end},
            "requests_by_status": self.requests_by_status,
            "failing_routes": self.failing_routes,
            "error_logs": self.error_logs,
            "error_trace_ids": self.error_trace_ids,
            "container_status": self.container_status,
            "recent_commits": self.recent_commits,
            "collection_errors": self.errors,
        }


def _http_get_json(url: str, params: dict | None = None, timeout: int = 5) -> dict:
    if params:
        query_string = urllib.parse.urlencode(params)
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{query_string}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "IncidentEvidence/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _safe_call(errors: list, source: str, func, *args):
    try:
        return func(*args)
    except Exception as exc:
        errors.append(f"{source}: {type(exc).__name__}: {exc}")
        return None


def _query_prometheus(end: datetime) -> tuple[dict, list]:
    # Query status breakdown
    query = f'sum by (http_status_code) (increase(app_http_requests_total{{service_name="{SERVICE_NAME}"}}[{LOOKBACK_MINUTES}m]))'
    data = _http_get_json(f"{PROMETHEUS_URL}/api/v1/query", {"query": query, "time": str(end.timestamp())})
    status_counts = {}
    if data and data.get("status") == "success":
        for r in data.get("data", {}).get("result", []):
            code = r["metric"].get("http_status_code", "unknown")
            try:
                status_counts[code] = round(float(r["value"][1]), 2)
            except (ValueError, TypeError, IndexError):
                status_counts[code] = 0

    # Query failing routes with 5xx
    routes_query = f'sum by (http_route) (increase(app_http_requests_total{{service_name="{SERVICE_NAME}", http_status_code=~"5.."}}[{LOOKBACK_MINUTES}m])) > 0'
    rdata = _http_get_json(f"{PROMETHEUS_URL}/api/v1/query", {"query": routes_query, "time": str(end.timestamp())})
    failing_routes = []
    if rdata and rdata.get("status") == "success":
        for r in rdata.get("data", {}).get("result", []):
            route = r["metric"].get("http_route")
            if route:
                failing_routes.append(route)

    return status_counts, failing_routes


def _query_loki_errors(start: datetime, end: datetime) -> list:
    query = f'{{service_name="{SERVICE_NAME}"}} |= "error"'
    params = {
        "query": query,
        "start": str(int(start.timestamp() * 1e9)),
        "end": str(int(end.timestamp() * 1e9)),
        "limit": str(MAX_LOGS),
        "direction": "backward",
    }
    data = _http_get_json(f"{LOKI_URL}/loki/api/v1/query_range", params)
    entries = []
    if data and data.get("status") == "success":
        for stream in data.get("data", {}).get("result", []):
            stream_labels = stream.get("stream", {})
            for ts, line in stream.get("values", []):
                try:
                    iso_ts = datetime.fromtimestamp(int(ts) / 1e9, timezone.utc).isoformat()
                except Exception:
                    iso_ts = str(ts)
                entries.append({
                    "timestamp": iso_ts,
                    "line": line.strip()[:300],
                    "trace_id": stream_labels.get("trace_id", ""),
                })
    return entries


def _query_tempo_error_traces(start: datetime, end: datetime) -> list:
    query = f'{{ resource.service.name="{SERVICE_NAME}" && status=error }}'
    params = {
        "q": query,
        "start": str(int(start.timestamp())),
        "end": str(int(end.timestamp())),
        "limit": str(MAX_TRACES),
    }
    data = _http_get_json(f"{TEMPO_URL}/api/search", params)
    traces = []
    if data and isinstance(data, dict):
        for t in data.get("traces", []):
            if "traceID" in t:
                traces.append(t["traceID"])
    return traces


def _query_git_commits() -> list:
    try:
        res = subprocess.run(
            ["git", "log", "-n", "3", "--pretty=format:%h: %s"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0 and res.stdout.strip():
            return [line.strip() for line in res.stdout.strip().split("\n")]
    except Exception:
        pass
    return []


def _query_container_status() -> str:
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", "name=personal-lifecycle", "--format", "{{.Names}}: {{.Status}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().replace("\n", " | ")
    except Exception:
        pass
    return "unknown"


def collect(now: datetime | None = None) -> Evidence:
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(minutes=LOOKBACK_MINUTES)
    errors: list = []

    prom_res = _safe_call(errors, "prometheus", _query_prometheus, now)
    requests_by_status, failing_routes = prom_res if prom_res else ({}, [])

    error_logs = _safe_call(errors, "loki", _query_loki_errors, start, now) or []
    error_trace_ids = _safe_call(errors, "tempo", _query_tempo_error_traces, start, now) or []
    container_status = _query_container_status()
    recent_commits = _query_git_commits()

    return Evidence(
        service_name=SERVICE_NAME,
        window_start=start.isoformat(),
        window_end=now.isoformat(),
        requests_by_status=requests_by_status,
        failing_routes=failing_routes,
        error_logs=error_logs,
        error_trace_ids=error_trace_ids,
        container_status=container_status,
        recent_commits=recent_commits,
        errors=errors,
    )


def render_markdown(evidence: Evidence) -> str:
    lines = [
        f"### Empirical Telemetry Evidence Packet ({evidence.service_name})",
        f"**Window**: `{evidence.window_start}` to `{evidence.window_end}`",
        f"**Container Status**: `{evidence.container_status}`",
        "",
        "#### HTTP Requests by Status Code (Last 15m):",
    ]
    if evidence.requests_by_status:
        for status, count in sorted(evidence.requests_by_status.items()):
            lines.append(f"- **HTTP {status}**: {count} requests")
    else:
        lines.append("- *(No metrics returned or baseline zero)*")

    lines.append("")
    failing = ", ".join(evidence.failing_routes) if evidence.failing_routes else "(None detected)"
    lines.append(f"#### Failing Routes: `{failing}`")

    lines.append("")
    lines.append("#### Recent Error Logs (Loki):")
    if evidence.error_logs:
        for entry in evidence.error_logs[:15]:
            trace_part = f" [trace_id={entry['trace_id']}]" if entry.get("trace_id") else ""
            lines.append(f"- `{entry['timestamp']}`{trace_part}: `{entry['line']}`")
    else:
        lines.append("- *(No 5xx error logs found in lookback window)*")

    lines.append("")
    traces = ", ".join(evidence.error_trace_ids) if evidence.error_trace_ids else "(None found)"
    lines.append(f"#### Error Trace IDs (Tempo): `{traces}`")

    lines.append("")
    lines.append("#### Recent Repository Commits:")
    if evidence.recent_commits:
        for commit in evidence.recent_commits:
            lines.append(f"- `{commit}`")
    else:
        lines.append("- *(Unable to inspect git commits)*")

    if evidence.errors:
        lines.append("")
        lines.append("#### Telemetry Harvest Warnings:")
        for err in evidence.errors:
            lines.append(f"- ⚠️ {err}")

    return "\n".join(lines)


if __name__ == "__main__":
    ev = collect()
    print(render_markdown(ev))
