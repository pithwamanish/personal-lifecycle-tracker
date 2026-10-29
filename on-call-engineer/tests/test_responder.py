"""Unit tests for the autonomous on-call incident responder."""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import responder
from evidence import Evidence

FAKE_RESULT_BASE = {
    "command": ["claude"],
    "exit_code": 0,
    "timed_out": False,
    "duration_s": 0.1,
    "model": "fake-model",
    "permission_mode": "dontAsk",
    "tools": ["Read", "Edit", "Bash"],
    "num_turns": 1,
    "cost_usd": 0.01,
    "is_error": False,
    "permission_denials": [],
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(responder, "INCIDENTS_DIR", tmp_path)
    monkeypatch.setattr(responder, "client_allowed", lambda host: True)
    responder.dispatcher = responder.Dispatcher()
    return TestClient(responder.app)


def wait_for_status(incidents_dir: Path, incident_id: str, statuses: set[str], timeout: float = 3.0):
    deadline = time.monotonic() + timeout
    record = None
    while time.monotonic() < deadline:
        path = incidents_dir / incident_id / "incident.json"
        if path.exists():
            try:
                record = json.loads(path.read_text())
                if record.get("status") in statuses:
                    return record
            except json.JSONDecodeError:
                pass
        time.sleep(0.02)
    return record


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_rejects_disallowed_client(tmp_path, monkeypatch):
    monkeypatch.setattr(responder, "INCIDENTS_DIR", tmp_path)
    monkeypatch.setattr(responder, "client_allowed", lambda host: False)
    disallowed_client = TestClient(responder.app)
    response = disallowed_client.post("/alerts", json={"alerts": []})
    assert response.status_code == 403


def test_test_alert_declines_to_act_and_closes(client, monkeypatch):
    fake_evidence = Evidence("api-backend", "t0", "t1", {}, [], [], [], "healthy", [])
    monkeypatch.setattr(responder.evidence_module, "collect", lambda: fake_evidence)

    fake_result = {
        **FAKE_RESULT_BASE,
        "answer_text": "ACTION: none\nSUMMARY: Synthetic test drill; no incident to fix.",
        "last_line": "SUMMARY: Synthetic test drill; no incident to fix.",
    }
    monkeypatch.setattr(responder.agent_runner, "run", lambda *a, **k: fake_result)

    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "SyntheticResponderTest", "test": "true"},
                "annotations": {"summary": "Drill test notification; no code changes"},
            }
        ]
    }
    response = client.post("/alerts", json=payload)
    assert response.status_code == 202
    incident_id = response.json()["results"][0]["incident_id"]

    record = wait_for_status(responder.INCIDENTS_DIR, incident_id, {"closed", "recovered", "escalated"})
    assert record is not None
    assert record["status"] == "closed"

    answer = json.loads((responder.INCIDENTS_DIR / incident_id / "answer.json").read_text())
    assert answer["action"] == "none"
    assert "no incident to fix" in answer["summary"]


def test_real_alert_runs_full_flow_redeploy_and_recovers(client, monkeypatch):
    fake_evidence = Evidence(
        service_name="api-backend",
        window_start="t0",
        window_end="t1",
        requests_by_status={"500": 12},
        failing_routes=["/api/v1/items/summary"],
        error_logs=[{"timestamp": "t", "line": "TypeError: store date error", "trace_id": "tr-123"}],
        error_trace_ids=["tr-123"],
        container_status="healthy",
        recent_commits=["abc: test commit"],
    )
    monkeypatch.setattr(responder.evidence_module, "collect", lambda: fake_evidence)

    answer_text = (
        "INCIDENT: test-incident\n"
        "ROOT_CAUSE: offset-naive vs aware date comparison in store.py\n"
        "FIX: backend/app/store.py\n"
        "TESTS: pytest tests/test_items.py passed\n"
        "ACTION: fixed\n"
        "SUMMARY: Corrected datetime timezone normalization in store.py"
    )
    fake_result = {
        **FAKE_RESULT_BASE,
        "answer_text": answer_text,
        "last_line": "SUMMARY: Corrected datetime timezone normalization in store.py",
    }
    monkeypatch.setattr(responder.agent_runner, "run", lambda *a, **k: fake_result)
    monkeypatch.setattr(responder, "redeploy", lambda: {"exit_code": 0, "output": "rebuilt successfully"})
    monkeypatch.setattr(responder, "verify_recovery", lambda paths: {"paths": paths, "exit_code": 0, "output": "RECOVERED"})

    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "DateComparisonTypeError", "severity": "critical"},
                "annotations": {"summary": "Elevated 5xx errors on items endpoint"},
            }
        ]
    }
    response = client.post("/alerts", json=payload)
    incident_id = response.json()["results"][0]["incident_id"]

    record = wait_for_status(responder.INCIDENTS_DIR, incident_id, {"recovered", "escalated"})
    assert record is not None
    assert record["status"] == "recovered"

    answer = json.loads((responder.INCIDENTS_DIR / incident_id / "answer.json").read_text())
    assert answer["action"] == "fixed"
    assert answer["root_cause"] == "offset-naive vs aware date comparison in store.py"


def test_unverified_fix_is_escalated(client, monkeypatch):
    fake_evidence = Evidence("api-backend", "t0", "t1", {"500": 5}, ["/health"], [], [], "healthy", [])
    monkeypatch.setattr(responder.evidence_module, "collect", lambda: fake_evidence)

    fake_result = {
        **FAKE_RESULT_BASE,
        "answer_text": "ACTION: fixed\nSUMMARY: Agent mistakenly claims bug is fixed",
        "last_line": "SUMMARY: Agent mistakenly claims bug is fixed",
    }
    monkeypatch.setattr(responder.agent_runner, "run", lambda *a, **k: fake_result)
    monkeypatch.setattr(responder, "redeploy", lambda: {"exit_code": 0, "output": "rebuilt"})
    # verify_recovery fails!
    monkeypatch.setattr(responder, "verify_recovery", lambda paths: {"paths": paths, "exit_code": 1, "output": "NOT RECOVERED"})

    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "HighHttpErrorRate"},
                "annotations": {},
            }
        ]
    }
    response = client.post("/alerts", json=payload)
    incident_id = response.json()["results"][0]["incident_id"]

    record = wait_for_status(responder.INCIDENTS_DIR, incident_id, {"recovered", "escalated"})
    assert record is not None
    assert record["status"] == "escalated"
    assert "verification failed" in record["timeline"][-1]["note"]


def test_failed_redeploy_is_escalated_without_verifying(client, monkeypatch):
    fake_evidence = Evidence("api-backend", "t0", "t1", {}, ["/health"], [], [], "healthy", [])
    monkeypatch.setattr(responder.evidence_module, "collect", lambda: fake_evidence)

    fake_result = {
        **FAKE_RESULT_BASE,
        "answer_text": "ACTION: fixed\nSUMMARY: claim fix",
        "last_line": "SUMMARY: claim fix",
    }
    monkeypatch.setattr(responder.agent_runner, "run", lambda *a, **k: fake_result)
    monkeypatch.setattr(responder, "redeploy", lambda: {"exit_code": 1, "output": "docker compose build failed"})

    def fail_if_verify_called(paths):
        raise AssertionError("Must never call verify_recovery when redeploy failed!")

    monkeypatch.setattr(responder, "verify_recovery", fail_if_verify_called)

    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "BuildBreakAlert"},
                "annotations": {},
            }
        ]
    }
    response = client.post("/alerts", json=payload)
    incident_id = response.json()["results"][0]["incident_id"]

    record = wait_for_status(responder.INCIDENTS_DIR, incident_id, {"recovered", "escalated"})
    assert record is not None
    assert record["status"] == "escalated"
    assert "redeploy failed" in record["timeline"][-1]["note"]


def test_duplicate_firing_alert_is_deduped(client, monkeypatch):
    fake_evidence = Evidence("api-backend", "t0", "t1", {}, [], [], [], "healthy", [])
    monkeypatch.setattr(responder.evidence_module, "collect", lambda: fake_evidence)
    monkeypatch.setattr(responder.agent_runner, "run", lambda *a, **k: {**FAKE_RESULT_BASE, "answer_text": "ACTION: none\nSUMMARY: ok", "last_line": "SUMMARY: ok"})

    payload = {"alerts": [{"status": "firing", "labels": {"alertname": "RepeatedAlert"}}]}
    first = client.post("/alerts", json=payload).json()["results"][0]
    second = client.post("/alerts", json=payload).json()["results"][0]

    assert first["status"] == "accepted"
    assert second["status"] == "duplicate"


def test_resolved_alert_is_ignored(client):
    payload = {"alerts": [{"status": "resolved", "labels": {"alertname": "ClearedAlert"}}]}
    response = client.post("/alerts", json=payload)
    assert response.json()["results"][0]["status"] == "ignored"
    assert response.json()["results"][0]["reason"] == "resolved"


def test_parse_answer_variations():
    text = """
    ```text
    - INCIDENT: INC-999
    * ROOT_CAUSE: Division by zero in calc
    > FIX: app/math.py
    TESTS: pytest passed
    ACTION: fixed
    SUMMARY: Patched zero check
    ```
    """
    parsed = responder.parse_answer(text, "raw last line", "INC-999")
    assert parsed["incident"] == "INC-999"
    assert parsed["root_cause"] == "Division by zero in calc"
    assert parsed["fix"] == "app/math.py"
    assert parsed["tests"] == "pytest passed"
    assert parsed["action"] == "fixed"
    assert parsed["summary"] == "Patched zero check"
    assert parsed["last_line"] == "SUMMARY: Patched zero check"
