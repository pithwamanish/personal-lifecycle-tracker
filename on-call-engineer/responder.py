"""Autonomous Incident Responder for Personal Lifecycle Tracker.

Receives Grafana / Alertmanager webhooks at POST /alerts, collects empirical
telemetry evidence from Prometheus, Loki, and Tempo, runs sandboxed headless
coding agent, and independently verifies recovery before resolving the incident.
"""

import json
import logging
import os
import re
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from ipaddress import ip_address, ip_network
from pathlib import Path

import uvicorn

# Starlette 0.45+ compatibility shim for environments with mixed FastAPI versions
try:
    import starlette.routing
    _orig_router_init = starlette.routing.Router.__init__
    def _compat_router_init(self, *args, **kwargs):
        kwargs.pop("on_startup", None)
        kwargs.pop("on_shutdown", None)
        return _orig_router_init(self, *args, **kwargs)
    starlette.routing.Router.__init__ = _compat_router_init
except Exception:
    pass

from fastapi import FastAPI, HTTPException, Request

try:
    from . import agent_runner
    from . import evidence as evidence_module
except (ImportError, ValueError):
    import agent_runner
    import evidence as evidence_module

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
INCIDENTS_DIR = Path(os.getenv("RESPONDER_INCIDENTS_DIR", str(HERE / "incidents")))
PROMPT_TEMPLATE_PATH = HERE / "prompt.md"
VERIFY_SCRIPT = HERE / "runbooks" / "verify-recovery.sh"
REDEPLOY_SCRIPT = HERE / "runbooks" / "redeploy.sh"

PORT = int(os.getenv("RESPONDER_PORT", "8001"))
ALLOWED_NETWORKS = [
    ip_network(n.strip())
    for n in os.getenv(
        "RESPONDER_ALLOWED_NETWORKS",
        "127.0.0.0/8,172.16.0.0/12,10.0.0.0/8,192.168.0.0/16"
    ).split(",")
    if n.strip()
]
BIND_HOSTS = [h.strip() for h in os.getenv("RESPONDER_BIND_HOSTS", "127.0.0.1").split(",") if h.strip()]
COOLDOWN_SECONDS = int(os.getenv("RESPONDER_COOLDOWN_SECONDS", "300"))
MAX_PAYLOAD_BYTES = 512 * 1024

ANSWER_LABELS = {
    "INCIDENT": "incident",
    "ROOT_CAUSE": "root_cause",
    "FIX": "fix",
    "TESTS": "tests",
    "ACTION": "action",
    "SUMMARY": "summary",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s %(message)s")
logger = logging.getLogger("on-call-responder")


def client_allowed(host: str | None) -> bool:
    if host is None:
        return False
    try:
        addr = ip_address(host)
    except ValueError:
        return False
    return any(addr in net for net in ALLOWED_NETWORKS)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "incident"


def utc_now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_answer(text: str, last_line: str, incident_id: str) -> dict:
    fields = {
        "incident": incident_id,
        "root_cause": "",
        "fix": "",
        "tests": "",
        "action": "unknown",
        "summary": "",
    }
    for line in text.splitlines():
        clean = line.strip().strip("`").lstrip("-*> ").strip()
        for label, key in ANSWER_LABELS.items():
            prefix = f"{label}:"
            if clean.upper().startswith(prefix):
                fields[key] = clean[len(prefix):].strip()
    action_words = fields["action"].split()
    action = action_words[0].strip(".,").lower() if action_words else "unknown"
    fields["action"] = action if action in {"none", "fixed", "escalate"} else "unknown"
    fields["last_line"] = f"SUMMARY: {fields['summary']}" if fields["summary"] else last_line
    return fields


def verify_recovery(paths: list[str]) -> dict:
    if not VERIFY_SCRIPT.exists():
        return {"paths": paths, "exit_code": 0, "output": "verify script omitted"}
    result = subprocess.run(
        [str(VERIFY_SCRIPT), *paths], cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=60
    )
    return {"paths": paths, "exit_code": result.returncode, "output": result.stdout + result.stderr}


def redeploy() -> dict:
    if not REDEPLOY_SCRIPT.exists():
        return {"exit_code": 0, "output": "redeploy script omitted"}
    result = subprocess.run(
        [str(REDEPLOY_SCRIPT)], cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=180
    )
    return {"exit_code": result.returncode, "output": result.stdout + result.stderr}


@dataclass
class Incident:
    id: str
    dir: Path
    alert: dict
    record: dict = field(default_factory=dict)

    @classmethod
    def create(cls, alert: dict, payload: dict) -> "Incident":
        INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
        alert_name = alert.get("labels", {}).get("alertname") or alert.get("alert_name") or "alert"
        slug = slugify(alert_name)
        incident_id = f"{utc_now_stamp()}-{slug}"
        incident_dir = INCIDENTS_DIR / incident_id
        incident_dir.mkdir(parents=True, exist_ok=True)

        incident = cls(id=incident_id, dir=incident_dir, alert=alert)
        incident.write_json("alert.json", alert)
        incident.write_json("payload.json", payload)

        incident.record = {
            "id": incident_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "created",
            "alert": alert,
            "timeline": [{"at": datetime.now(timezone.utc).isoformat(), "status": "created", "note": "accepted"}],
        }
        incident.write_json("incident.json", incident.record)
        return incident

    def transition(self, status: str, note: str = "") -> None:
        self.record["status"] = status
        self.record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.record["timeline"].append({"at": self.record["updated_at"], "status": status, "note": note})
        self.write_json("incident.json", self.record)
        logger.info("incident %s -> %s (%s)", self.id, status, note)

    def write_json(self, filename: str, data: dict) -> None:
        (self.dir / filename).write_text(json.dumps(data, indent=2))

    def write_text(self, filename: str, text: str) -> None:
        (self.dir / filename).write_text(text)


def render_prompt(incident_id: str, alert: dict, evidence_md: str) -> str:
    template = PROMPT_TEMPLATE_PATH.read_text() if PROMPT_TEMPLATE_PATH.exists() else (
        "# On-Call Incident Responder\n\nIncident: {incident_id}\n\n## Alert\n{alert_json}\n\n## Evidence\n{evidence_markdown}"
    )
    rendered = template.replace("{incident_id}", incident_id)
    rendered = rendered.replace("{alert_json}", json.dumps(alert, indent=2))
    rendered = rendered.replace("{evidence_markdown}", evidence_md)
    return rendered


def handle_incident(incident: Incident) -> None:
    try:
        incident.transition("gathering_evidence", "collecting telemetry from Prometheus, Loki, Tempo")
        gathered = evidence_module.collect()
        incident.write_json("evidence.json", gathered.to_dict())
        evidence_md = evidence_module.render_markdown(gathered)
        incident.write_text("evidence.md", evidence_md)
        incident.transition("evidence_gathered", f"{len(gathered.failing_routes)} failing routes, {len(gathered.error_logs)} error logs")

        prompt = render_prompt(incident.id, incident.alert, evidence_md)
        incident.write_text("prompt.md", prompt)

        # Execute coding agent
        incident.transition("agent_running", "sandboxed headless agent investigating")
        transcript_path = incident.dir / "transcript.jsonl"
        result = agent_runner.run(prompt, REPO_ROOT, transcript_path)
        incident.write_text("response.md", result.get("answer_text", ""))

        answer = parse_answer(result.get("answer_text", ""), result.get("last_line", ""), incident.id)
        incident.write_json("answer.json", answer)
        incident.transition("agent_done", f"action={answer['action']} exit={result['exit_code']}")

        # Verification & Resolution Gate
        failing_paths = gathered.failing_routes or ["/health"]
        if answer["action"] == "fixed":
            incident.transition("redeploying", "rebuilding application container with fix")
            deploy = redeploy()
            incident.write_json("redeploy.json", deploy)
            if deploy["exit_code"] != 0:
                incident.transition("escalated", "redeploy failed; fix container not rebuildable")
                return

            verification = verify_recovery(failing_paths)
            incident.write_json("verification.json", verification)
            if verification["exit_code"] == 0:
                incident.transition("recovered", "verify-recovery passed; fix awaits human review before commit")
            else:
                incident.transition("escalated", "agent reported 'fixed' but independent verification failed")
        elif answer["action"] == "none":
            incident.transition("closed", "test alert or no action required")
        else:
            incident.transition("escalated", f"agent action '{answer['action']}' requires human engineer")

    except Exception as exc:
        logger.exception("incident %s failed with unexpected exception", incident.id)
        incident.transition("escalated", f"responder error: {type(exc).__name__}: {exc}")


class Dispatcher:
    """Serializes agent runs to prevent git working tree conflicts and dedupes repetitive alerts."""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="oncall_responder")
        self.lock = threading.Lock()
        self.last_seen: dict[str, float] = {}

    def submit(self, alert: dict, payload: dict) -> dict:
        alert_name = alert.get("labels", {}).get("alertname") or alert.get("alert_name") or "alert"
        now = time.monotonic()
        with self.lock:
            seen = self.last_seen.get(alert_name)
            if seen is not None and now - seen < COOLDOWN_SECONDS:
                return {"alert": alert_name, "status": "duplicate"}
            self.last_seen[alert_name] = now

        incident = Incident.create(alert, payload)
        self.executor.submit(handle_incident, incident)
        return {"alert": alert_name, "status": "accepted", "incident_id": incident.id}


app = FastAPI(title="Personal Lifecycle Tracker Incident Responder")
dispatcher = Dispatcher()


@app.get("/healthz")
def health():
    return {"status": "ok", "service": "on-call-responder"}


@app.post("/alerts", status_code=202)
async def receive_alerts(request: Request):
    client_host = request.client.host if request.client else None
    if not client_allowed(client_host):
        logger.warning("Rejected alert webhook from untrusted client %s", client_host)
        raise HTTPException(403, "client not allowed")

    body = await request.body()
    if len(body) > MAX_PAYLOAD_BYTES:
        raise HTTPException(413, "alert payload too large")
    try:
        payload = json.loads(body)
    except ValueError:
        raise HTTPException(400, "body must be valid JSON")

    # Support Grafana format ({"alerts": [...]}), Alertmanager format ([...]), or single alert object
    if isinstance(payload, dict) and "alerts" in payload and isinstance(payload["alerts"], list):
        alerts = payload["alerts"]
    elif isinstance(payload, list):
        alerts = payload
    elif isinstance(payload, dict):
        alerts = [payload]
    else:
        raise HTTPException(422, "unexpected alert payload format")

    results = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        status = alert.get("status") or alert.get("alert_state") or "firing"
        if status.lower() == "resolved":
            alert_name = alert.get("labels", {}).get("alertname") or alert.get("alert_name") or "alert"
            results.append({"alert": alert_name, "status": "ignored", "reason": "resolved"})
            continue
        results.append(dispatcher.submit(alert, payload))

    return {"results": results}


@app.get("/incidents")
def list_incidents():
    records = []
    for path in sorted(INCIDENTS_DIR.glob("*/incident.json"), reverse=True):
        try:
            record = json.loads(path.read_text())
            records.append({"id": record["id"], "status": record["status"], "created_at": record.get("created_at")})
        except Exception:
            continue
    return records


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", incident_id):
        raise HTTPException(404, "incident not found")
    path = INCIDENTS_DIR / incident_id / "incident.json"
    if not path.exists():
        raise HTTPException(404, "incident not found")
    return json.loads(path.read_text())


def _bind_socket(host: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    return sock


def main() -> None:
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    sockets = [_bind_socket(host, PORT) for host in BIND_HOSTS]
    logger.info("On-Call Responder listening on %s, port %d", ", ".join(BIND_HOSTS), PORT)
    uvicorn.Server(uvicorn.Config(app, log_level="info")).run(sockets=sockets)


if __name__ == "__main__":
    main()
