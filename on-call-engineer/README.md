# On-Call Engineer & Autonomous Incident Response (`on-call-engineer/`)

This directory provides the automated alert monitoring and autonomous incident remediation pipeline for the **Personal Lifecycle Tracker** system.
It combines push-based webhooks (FastAPI daemon on port 8001), continuous observability polling (Prometheus/Alertmanager API), sandboxed headless coding agent execution, and independent recovery verification.

---

## 1. Overview & Architecture

```
[Prometheus / Grafana / Alertmanager]
           │
           ├──► [POST /alerts (FastAPI Webhook Server :8001)] (responder.py)
           │                                 │
           └──► [GET /api/v1/alerts (Every 60s)] (poll-alerts.py)
                                             ▼
                               [on-call-engineer/responder.py]
                                             │
             ┌───────────────────────────────┴───────────────────────────────┐
             │ 1. Ingest Alert & Enforce Cooldown / Dedup                    │
             │ 2. Telemetry Harvester: Prometheus + Loki + Tempo (evidence.py)│
             │ 3. Create Isolated Incident Folder: incidents/<incident-id>/  │
             │    ├── alert.json, payload.json, evidence.json, evidence.md   │
             │    └── prompt.md (data-sandboxed prompt template)             │
             │ 4. Run Sandboxed Agent Runner (agent_runner.py)               │
             │    ├── claude -p --restricted --output-format stream-json     │
             │    ├── --tools Read,Grep,Glob,Edit,Bash                       │
             │    ├── --allowedTools Edit(./backend/app/**)...               │
             │    ├── --disallowedTools Bash(git commit:*),Bash(git push:*)  │
             │    └── Stream JSON lines -> transcript.jsonl                  │
             │ 5. Parse Structured Answer (response.schema.json)             │
             │    └── answer.json                                            │
             │ 6. Automated Redeploy & Self-Verification Loop                │
             │    ├── Rebuild Container: runbooks/redeploy.sh                │
             │    ├── Verify Endpoints: runbooks/verify-recovery.sh          │
             │    ├── If pass: status -> 'recovered'                         │
             │    └── If fail: status -> 'escalated' (never trust agent claim)│
             └───────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
                               [Audit & Deliverables]
                    incidents/<incident-id>/ (10 standardized files)
```

---

## 2. Directory Structure

```text
on-call-engineer/
├── responder.py              # FastAPI webhook responder daemon (port 8001) with serialization queue
├── agent_runner.py           # Sandboxed Claude Code CLI runner (budget caps, path restrictions, stream-json)
├── evidence.py               # Read-only telemetry harvester (Prometheus 9091, Loki 3101, Tempo 3201)
├── poll-alerts.py            # Continuous polling daemon for Prometheus alerts & CI/CD failures
├── payload-schema.json       # JSON schema for incoming normalized alerts
├── response.schema.json      # JSON schema for agent answers (INCIDENT, ROOT_CAUSE, FIX, TESTS, ACTION, SUMMARY)
├── autonomy-policy.json      # Code-enforced autonomy permission levels (Level 1, Level 2, Level 3)
├── prompt.md                 # Context-injected prompt template enforcing safety & response contracts
├── runbook.md                # Alert-specific triage runbook
├── audit-trail.log           # Timestamped audit log of all incident transitions & agent actions
├── runbooks/
│   ├── redeploy.sh           # Rebuilds and restarts backend container with --wait
│   └── verify-recovery.sh    # Re-curls target endpoints; fails on 5xx or connection drops
├── scripts/
│   ├── poll-alerts           # Executable wrapper for poll-alerts.py
│   ├── invoke-agent          # CLI entrypoint for sandboxed agent dispatch
│   ├── receive-alert         # Standalone receiver for webhook payloads or stdin
│   ├── collect-evidence      # CLI wrapper for telemetry evidence collection
│   ├── authorize-action      # Code-enforced policy evaluator outside the model
│   ├── run-real-incident-drill # End-to-end defect injection & verified recovery drill
│   ├── run-code-fix-drill    # Level 2 code fix & human approval drill
│   ├── run-aws-incident-drill # Cloud simulator incident drill
│   ├── trigger-test-incident # Synthetic alert trigger for drill verification
│   └── verify                # Comprehensive validation suite (tests + runbooks + drills)
├── tests/
│   └── test_responder.py     # Pytest unit test suite covering full responder lifecycle
├── incidents/                # Dedicated per-incident audit directories (<id>/)
│   └── <incident-id>/        # 10 isolated incident artifacts
│       ├── alert.json        # Raw incoming alert payload
│       ├── payload.json      # Complete webhook payload
│       ├── evidence.json     # Telemetry metrics and error logs in JSON
│       ├── evidence.md       # Rendered markdown evidence
│       ├── prompt.md         # Context prompt delivered to agent
│       ├── transcript.jsonl  # Claude Code stream-json execution log
│       ├── response.md       # Raw answer text from agent
│       ├── answer.json       # Parsed fields conforming to response.schema.json
│       ├── redeploy.json     # Output of container rebuild
│       ├── verification.json # Output of endpoint verification check
│       └── incident.json     # Complete lifecycle timeline and status transitions
└── README.md                 # This documentation file
```

---

## 3. How to Run the Incident Responder

### A. Run Webhook Daemon (`responder.py`)
Listens on port `8001` (restricted to loopback and Docker bridge networks):
```bash
# Using Makefile
make on-call-responder

# Direct Python invocation
python3 on-call-engineer/responder.py
```

### B. Run Continuous Observability Poller (`poll-alerts.py`)
Polls Prometheus Alert API every 60s and watches GitHub Actions CI/CD runs:
```bash
# Using Makefile
make on-call-poll

# Direct Python invocation
python3 on-call-engineer/poll-alerts.py
```

### C. Run Unit Test Suite
Executes all 9 automated unit tests inside the containerized backend:
```bash
make on-call-test
```

### D. Run End-to-End Real Incident Drill
Injects a live HTTP 500 defect, harvests telemetry, executes sandboxed repair, verifies container redeployment, and confirms recovery:
```bash
make on-call-real-drill
# or: bash on-call-engineer/scripts/run-real-incident-drill
```

---

## 4. Key Additions & Architectural Hardening

1. **Fine-Grained Agent Sandboxing (`agent_runner.py`)**:
   - Executes `claude` with:
     - `--restricted`: Starts session with zero tools, ignoring ambient host configs.
     - `--permission-mode dontAsk --permission-prompts none`: Denies unallowlisted commands without hanging.
     - `--max-budget-usd 2`: Hard spend cap per incident.
     - `--allowedTools`:
       `Edit(./backend/app/**)`, `Edit(./backend/tests/**)`, `Bash(docker compose run --rm -T --no-deps backend pytest:*)`, `Bash(on-call-engineer/runbooks/redeploy.sh)`, `Bash(on-call-engineer/runbooks/verify-recovery.sh:*)`, `Bash(git status:*)`, `Bash(git diff:*)`, `Bash(git log:*)`.
     - `--disallowedTools`:
       `Bash(git commit:*)`, `Bash(git push:*)`, `Bash(git reset:*)`, `Bash(git checkout:*)`, `Bash(docker compose down:*)`, `Bash(rm -rf:*)`.
   - Streams JSON output line-by-line into `transcript.jsonl`, tracking turns, token cost in USD, and permission denials.

2. **Automated Post-Fix Redeploy & Self-Verification**:
   - The agent is never permitted to mark an incident resolved on faith.
   - When the agent returns `ACTION: fixed`:
     1. Responder executes [`runbooks/redeploy.sh`](runbooks/redeploy.sh) (`docker compose up --build -d --wait --no-deps backend`).
     2. Responder executes [`runbooks/verify-recovery.sh`](runbooks/verify-recovery.sh) against all failing routes.
     3. Only if `verify-recovery.sh` exits 0 with HTTP 200/2xx does the incident transition to `recovered`.
     4. If verification or rebuild fails, the incident immediately escalates to a human engineer (`escalated`).

3. **Per-Incident Directory Isolation (`incidents/<id>/`)**:
   - Replaced overwriting single shared files with dedicated incident directories containing 10 explicit artifacts:
     `alert.json`, `evidence.json`, `evidence.md`, `prompt.md`, `transcript.jsonl`, `response.md`, `answer.json`, `redeploy.json`, `verification.json`, `incident.json`.

4. **Standardized Response Contract (`response.schema.json`)**:
   - Enforces machine-parseable answer format:
     ```text
     INCIDENT: {incident_id}
     ROOT_CAUSE: <one sentence description>
     FIX: <files and changes applied>
     TESTS: <test command executed and status>
     ACTION: none | fixed | escalate
     SUMMARY: <concise audit log message>
     ```

5. **Pruning & Cleanup**:
   - Removed redundant root bash wrapper `poll-alerts` (consolidated into `scripts/poll-alerts`).
   - Removed deceptive synthetic fake proposal fallback in `invoke-agent`.
   - Removed root-level `evidence.json` overwrite to guarantee state isolation.
