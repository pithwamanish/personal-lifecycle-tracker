#!/usr/bin/env python3
"""
Observability Alert Poller & Headless On-Call Agent Trigger.

Polls the Prometheus / Alertmanager Alert API every minute (default 60s).
When an alert fires:
1. Normalizes the alert details according to on-call-engineer/payload-schema.json
2. Generates incident JSON in _docs/incidents/incident-<id>.json
3. Renders the agent prompt in _docs/incidents/prompt-<id>.md
4. Passes the alert details and prompt context to the headless coding agent
5. Tracks resolution when alerts recover.
"""

import argparse
import datetime
import json
import logging
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
ON_CALL_DIR = SCRIPT_DIR
INCIDENTS_DIR = os.path.join(PROJECT_ROOT, "_docs", "incidents")
AUDIT_LOG = os.path.join(ON_CALL_DIR, "audit-trail.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("on-call-poller")

# Flag for graceful shutdown
running = True

def handle_signal(sig, frame):
    global running
    logger.info("Shutdown signal received. Stopping alert poller...")
    running = False

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def log_audit(event_type, details):
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    os.makedirs(ON_CALL_DIR, exist_ok=True)
    with open(AUDIT_LOG, "a") as f:
        f.write(f"[{timestamp}] {event_type}: {details}\n")


def normalize_api_url(url):
    url = url.strip()
    if url.endswith("/"):
        url = url[:-1]
    if not url.endswith("/api/v1/alerts") and not url.endswith("/api/v2/alerts"):
        url = f"{url}/api/v1/alerts"
    return url


def fetch_alerts(api_url, timeout=10):
    req = urllib.request.Request(
        api_url,
        headers={"Accept": "application/json", "User-Agent": "OnCallAlertPoller/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except urllib.error.URLError as e:
        logger.warning(f"Failed to reach alert API at {api_url}: {e.reason}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching alerts from {api_url}: {e}")
        return None


def parse_firing_alerts(data):
    """
    Extracts firing alerts from Prometheus or Alertmanager response.
    Returns list of alert dictionaries.
    """
    firing = []
    if not data:
        return firing

    # Prometheus format: {"status": "success", "data": {"alerts": [...]}}
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        raw_alerts = data["data"].get("alerts", [])
        for item in raw_alerts:
            state = item.get("state", "").lower()
            if state == "firing":
                firing.append(item)

    # Alertmanager format: [...] list of alerts
    elif isinstance(data, list):
        for item in data:
            status = item.get("status", {})
            state = status.get("state", "") if isinstance(status, dict) else str(status)
            if state.lower() == "firing":
                firing.append(item)

    # Top-level alerts key format
    elif isinstance(data, dict) and "alerts" in data and isinstance(data["alerts"], list):
        for item in data["alerts"]:
            state = item.get("state", item.get("status", "")).lower()
            if state == "firing":
                firing.append(item)

    return firing


def normalize_alert(alert_raw):
    """Normalizes raw alert item to schema."""
    labels = alert_raw.get("labels", {})
    annotations = alert_raw.get("annotations", {})

    alert_name = labels.get("alertname", labels.get("alert_name", "UnknownAlert"))
    severity = labels.get("severity", "warning")
    service_name = labels.get("service", labels.get("service_name", "api-backend"))
    deployment_env = labels.get("environment", labels.get("deployment_environment", "development"))
    version = labels.get("version", labels.get("service_version", "dev-latest"))
    
    summary = annotations.get("summary", f"Alert {alert_name} firing on {service_name}")
    description = annotations.get("description", "Observability metric breached threshold")
    
    observed_value = annotations.get("observed_value", alert_raw.get("value", None))
    if observed_value is not None:
        try:
            observed_value = float(observed_value)
        except (ValueError, TypeError):
            pass

    threshold = annotations.get("threshold", None)
    if threshold is not None:
        try:
            threshold = float(threshold)
        except (ValueError, TypeError):
            pass

    duration = annotations.get("duration", "1m")
    dashboard_url = annotations.get("dashboard_url", "http://localhost:3004/d/lifecycle-tracker-overview")
    runbook_url = annotations.get("runbook_url", f"on-call-engineer/runbook.md#{alert_name.lower()}")
    
    timestamp = alert_raw.get("activeAt", alert_raw.get("startsAt", datetime.datetime.now(datetime.timezone.utc).isoformat()))

    return {
        "alert_name": alert_name,
        "alert_state": "firing",
        "severity": severity,
        "service_name": service_name,
        "deployment_environment": deployment_env,
        "service_version": version,
        "summary": summary,
        "description": description,
        "observed_value": observed_value,
        "threshold": threshold,
        "duration": duration,
        "dashboard_url": dashboard_url,
        "runbook_url": runbook_url,
        "timestamp": timestamp,
        "labels": labels,
        "annotations": annotations
    }


def render_prompt_template(normalized):
    prompt_path = os.path.join(ON_CALL_DIR, "prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            template = f.read()
    else:
        template = "# On-Call Incident: {{alert_name}}\n\nService: {{service_name}}\nSummary: {{summary}}"

    rendered = template
    for key, val in normalized.items():
        placeholder = f"{{{{{key}}}}}"
        str_val = "" if val is None else str(val)
        rendered = rendered.replace(placeholder, str_val)
    return rendered


def get_alert_key(normalized):
    return f"{normalized['alert_name']}:{normalized['service_name']}:{normalized['deployment_environment']}"


def pass_to_headless_agent(normalized, agent_cmd=None):
    """
    Submits incident to responder engine and/or invokes headless coding agent.
    """
    try:
        sys.path.insert(0, ON_CALL_DIR)
        import responder
        res = responder.dispatcher.submit(normalized, {"alerts": [normalized]})
        incident_id = res.get("incident_id", "incident")
        logger.info(f"==> Dispatched incident to on-call responder: id={incident_id}, status={res.get('status')}")
        log_audit("ALERT_FIRING", f"alert='{normalized['alert_name']}', service='{normalized['service_name']}', severity='{normalized['severity']}', incident_id='{incident_id}'")
        return incident_id
    except Exception as e:
        logger.warning(f"Fallback to legacy dispatch: {e}")

    os.makedirs(INCIDENTS_DIR, exist_ok=True)
    ts = int(time.time())
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', normalized["alert_name"])
    
    incident_filename = f"incident-{ts}-{clean_name}.json"
    incident_file = os.path.join(INCIDENTS_DIR, incident_filename)
    with open(incident_file, "w") as f:
        json.dump(normalized, f, indent=2)

    prompt_filename = f"prompt-{ts}-{clean_name}.md"
    prompt_file = os.path.join(INCIDENTS_DIR, prompt_filename)
    rendered_prompt = render_prompt_template(normalized)
    with open(prompt_file, "w") as f:
        f.write(rendered_prompt)

    logger.info(f"==> Saved normalized incident: {incident_file}")
    logger.info(f"==> Rendered incident prompt: {prompt_file}")

    log_audit("ALERT_FIRING", f"alert='{normalized['alert_name']}', service='{normalized['service_name']}', severity='{normalized['severity']}'")

    # Command to invoke headless coding agent
    if not agent_cmd:
        agent_cmd = os.path.join(ON_CALL_DIR, "scripts", "invoke-agent")

    logger.info(f"==> Passing alert details to headless coding agent via: {agent_cmd}")
    env = os.environ.copy()
    env["ALERT_NAME"] = normalized["alert_name"]
    env["SEVERITY"] = normalized["severity"]
    env["SERVICE_NAME"] = normalized["service_name"]
    env["INCIDENT_FILE"] = incident_file
    env["PROMPT_FILE"] = prompt_file

    try:
        proc = subprocess.run(
            [agent_cmd, prompt_file, incident_file],
            env=env,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )
        if proc.stdout:
            for line in proc.stdout.strip().split("\n"):
                logger.info(f"[agent-runner] {line}")
        if proc.stderr:
            for line in proc.stderr.strip().split("\n"):
                logger.warning(f"[agent-runner-err] {line}")
        
        if proc.returncode == 0:
            logger.info("==> Headless coding agent completed dispatch successfully.")
            log_audit("AGENT_DISPATCH_SUCCESS", f"alert='{normalized['alert_name']}', code=0")
        else:
            logger.warning(f"==> Headless coding agent returned exit code {proc.returncode}")
            log_audit("AGENT_DISPATCH_WARN", f"alert='{normalized['alert_name']}', code={proc.returncode}")
    except Exception as e:
        logger.error(f"Failed to invoke headless coding agent: {e}")
        log_audit("AGENT_DISPATCH_FAILED", f"alert='{normalized['alert_name']}', error='{e}'")

    return incident_file


def fetch_ci_failures(limit=3):
    """
    Checks recent GitHub Actions runs. If the most recent run on the active branch
    has completed with a 'failure' conclusion, returns it as a firing alert.
    """
    try:
        cmd = ["gh", "run", "list", "--limit", str(limit), "--json", "databaseId,name,conclusion,status,headBranch,headSha,url,updatedAt"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            runs = json.loads(res.stdout)
            if runs:
                latest = runs[0]
                if latest.get("conclusion") == "failure" and latest.get("status") == "completed":
                    wf_name = latest.get("name", "CI/CD Pipeline")
                    run_id = latest.get("databaseId")
                    branch = latest.get("headBranch", "dev")
                    sha = latest.get("headSha", "latest")
                    short_sha = sha[:7] if sha else "latest"
                    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', wf_name)
                    return [{
                        "labels": {
                            "alertname": f"CiCdJobFailed_{clean_name}",
                            "severity": "critical",
                            "service": wf_name,
                            "environment": branch,
                            "version": short_sha,
                            "source": "github_actions",
                            "run_id": str(run_id)
                        },
                        "annotations": {
                            "summary": f"GitHub Actions {wf_name} failed on branch {branch} (run #{run_id})",
                            "description": f"CI/CD run {run_id} terminated with failure. To view logs: gh run view {run_id} --log-failed",
                            "dashboard_url": latest.get("url", f"https://github.com/pithwamanish/personal-lifecycle-tracker/actions/runs/{run_id}"),
                            "runbook_url": "on-call-engineer/runbook.md#3-github-actions-cicd-triage-guides"
                        },
                        "state": "firing",
                        "activeAt": latest.get("updatedAt", datetime.datetime.now(datetime.timezone.utc).isoformat())
                    }]
    except Exception as e:
        logger.debug(f"Unable to query GitHub Actions runs: {e}")
    return []


def poll_cycle(api_url, active_alerts, agent_cmd, mock_file=None, retrigger=False):
    """
    Executes a single poll cycle against the alert API and CI/CD pipelines.
    """
    if mock_file:
        logger.info(f"Loading alerts from mock file: {mock_file}")
        with open(mock_file, "r") as f:
            data = json.load(f)
    else:
        logger.info(f"Polling alert API at: {api_url}")
        data = fetch_alerts(api_url)

    firing_list = parse_firing_alerts(data)

    # Ingest GitHub Actions CI/CD failures
    if not mock_file:
        ci_failures = fetch_ci_failures()
        if ci_failures:
            logger.info(f"Detected {len(ci_failures)} failed GitHub Actions CI run(s).")
            firing_list.extend(ci_failures)

    current_cycle_keys = set()

    if not firing_list:
        logger.info("No firing alerts detected. System operational.")
    else:
        logger.info(f"Detected {len(firing_list)} firing alert(s).")

    for raw_alert in firing_list:
        normalized = normalize_alert(raw_alert)
        key = get_alert_key(normalized)
        current_cycle_keys.add(key)

        if key in active_alerts and not retrigger:
            logger.info(f"Alert '{normalized['alert_name']}' on '{normalized['service_name']}' is already firing (handled).")
        else:
            logger.warning(f"🔥 NEW FIRING ALERT: '{normalized['alert_name']}' [{normalized['severity'].upper()}] on '{normalized['service_name']}' ({normalized['deployment_environment']})")
            pass_to_headless_agent(normalized, agent_cmd=agent_cmd)
            active_alerts[key] = {
                "handled_at": time.time(),
                "normalized": normalized
            }

    # Check for resolved alerts
    resolved_keys = set(active_alerts.keys()) - current_cycle_keys
    for key in resolved_keys:
        prior = active_alerts.pop(key)
        alert_info = prior.get("normalized", {})
        alert_name = alert_info.get("alert_name", key)
        service = alert_info.get("service_name", "unknown")
        logger.info(f"✅ ALERT RESOLVED: Alert '{alert_name}' on '{service}' has cleared.")
        log_audit("ALERT_RESOLVED", f"alert='{alert_name}', service='{service}'")

    return len(firing_list)


def main():
    parser = argparse.ArgumentParser(
        description="Poll observability alert API and trigger headless coding agent when alerts fire."
    )
    default_url = os.environ.get("ALERT_API_URL", os.environ.get("PROMETHEUS_URL", "http://localhost:9091/api/v1/alerts"))
    default_interval = int(os.environ.get("ALERT_POLL_INTERVAL", os.environ.get("POLL_INTERVAL", "60")))

    parser.add_argument(
        "--url",
        default=default_url,
        help=f"Alert API endpoint URL (default: {default_url})"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=default_interval,
        help=f"Polling interval in seconds (default: {default_interval}s = 1 minute)"
    )
    parser.add_argument(
        "--agent-cmd",
        default=os.path.join(ON_CALL_DIR, "scripts", "invoke-agent"),
        help="Command/script to invoke for headless agent"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Execute single poll iteration and exit immediately"
    )
    parser.add_argument(
        "--mock-file",
        help="Path to JSON file containing mock alerts response (for testing/drills)"
    )
    parser.add_argument(
        "--retrigger",
        action="store_true",
        help="Retrigger agent on every poll even if alert was already handled"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    api_url = normalize_api_url(args.url)
    logger.info("================================================================")
    logger.info("          ON-CALL ENGINEER OBSERVABILITY ALERT POLLER           ")
    logger.info("================================================================")
    logger.info(f"Target Alert API: {api_url}")
    logger.info(f"Poll Interval:    {args.interval}s ({args.interval / 60:.1f} min)")
    logger.info(f"Agent Command:    {args.agent_cmd}")
    logger.info(f"Single Shot:      {args.once}")
    logger.info("================================================================")

    active_alerts = {}

    if args.once:
        count = poll_cycle(
            api_url=api_url,
            active_alerts=active_alerts,
            agent_cmd=args.agent_cmd,
            mock_file=args.mock_file,
            retrigger=args.retrigger
        )
        sys.exit(0)

    # Continuous 1-minute polling loop
    logger.info(f"Starting continuous polling loop (every {args.interval} seconds)...")
    while running:
        try:
            poll_cycle(
                api_url=api_url,
                active_alerts=active_alerts,
                agent_cmd=args.agent_cmd,
                mock_file=args.mock_file,
                retrigger=args.retrigger
            )
        except Exception as e:
            logger.error(f"Error during poll cycle: {e}")

        # Sleep for interval in small increments to allow responsive SIGINT
        sleep_elapsed = 0
        while running and sleep_elapsed < args.interval:
            time.sleep(1)
            sleep_elapsed += 1

    logger.info("Alert poller stopped cleanly.")
    sys.exit(0)


if __name__ == "__main__":
    main()
