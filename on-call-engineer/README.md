# On-Call Engineer & Autonomous Incident Response (`on-call-engineer/`)

This directory provides the automated alert monitoring and autonomous incident remediation pipeline for the **Personal Lifecycle Tracker** system.

---

## 1. Overview & Architecture

The on-call system continuously polls the observability alerting API. When Prometheus or Alertmanager emits an active `firing` alert, the pipeline normalizes the payload, generates an incident prompt with telemetry context, and passes it to a headless coding agent.

```
[Prometheus / Alertmanager] (:9091 /api/v1/alerts)
           │
           │ (every 60 seconds)
           ▼
[on-call-engineer/poll-alerts.py]
           │
     (State = firing?)
           ├──► [Normalize to payload-schema.json]
           ├──► [Archive incident to _docs/incidents/incident-<id>.json]
           ├──► [Render agent prompt to _docs/incidents/prompt-<id>.md]
           ▼
[on-call-engineer/scripts/invoke-agent]
           │
           ├──► Headless AI Coding Agent (agy / claude -p / autonomous loop)
           │      1. Collect bounded read-only evidence (scripts/collect-evidence)
           │      2. Evaluate autonomy policy (scripts/authorize-action)
           │      3. Reproduce bug with failing test inside Docker container
           │      4. Apply minimal safe correction preserving contracts
           │      5. Verify metric recovery and alert resolution
           ▼
[on-call-engineer/audit-trail.log]
```

---

## 2. Directory Structure

```text
on-call-engineer/
├── poll-alerts.py          # Primary polling script (default: polls every 60s)
├── poll-alerts             # Executable bash wrapper
├── payload-schema.json     # JSON schema for normalized incident payloads
├── autonomy-policy.json    # Code-enforced autonomy permission levels
├── prompt.md               # Context-injected prompt template for headless agent
├── runbook.md              # Alert-specific triage runbook
├── audit-trail.log         # Timestamped audit log of all polling & agent actions
├── evidence.json           # Read-only bounded evidence packet (generated on incident)
├── scripts/
│   ├── poll-alerts         # Script entrypoint for polling
│   ├── invoke-agent        # Dispatches headless coding agent with incident context
│   ├── receive-alert       # Standalone receiver for webhooks or stdin JSON
│   ├── collect-evidence    # Read-only telemetry harvester (Prometheus, Loki, git)
│   ├── authorize-action    # Code-enforced policy evaluator outside the model
│   ├── trigger-test-incident # Synthetic alert trigger for drill verification
│   └── verify              # Deterministic test script proving the pipeline
└── README.md               # This documentation file
```

---

## 3. How to Run the Alert Poller

### Continuous Polling (Default: Every 1 Minute)
```bash
# Using Python directly
python3 on-call-engineer/poll-alerts.py

# Using the bash wrapper
./on-call-engineer/poll-alerts

# Using Makefile
make on-call-poll
```

### CLI Options
| Flag | Description | Default |
|---|---|---|
| `--interval <sec>` | Polling frequency in seconds | `60` (1 minute) |
| `--url <url>` | Target Alert API endpoint | `http://localhost:9091/api/v1/alerts` |
| `--once` | Run a single poll cycle and exit immediately | `false` |
| `--mock-file <path>` | Read alerts from local JSON file (for drills/tests) | `None` |
| `--agent-cmd <cmd>` | Custom command/script to invoke the headless agent | `on-call-engineer/scripts/invoke-agent` |
| `--retrigger` | Re-dispatch agent on every poll even if alert was already handled | `false` (stateful deduplication) |
| `--verbose`, `-v` | Enable debug logging | `false` |

### Environment Variables
- `ALERT_API_URL` or `PROMETHEUS_URL`: Override default Prometheus endpoint (default: `http://localhost:9091/api/v1/alerts`).
- `ALERT_POLL_INTERVAL` or `POLL_INTERVAL`: Override default polling interval (default: `60`).

---

## 4. Headless Coding Agent Dispatch

When an alert enters the `firing` state:
1. **Normalization**: The raw alert labels and annotations are extracted and structured according to [`payload-schema.json`](payload-schema.json).
2. **Persistence**:
   - Incident data: `_docs/incidents/incident-<timestamp>-<alert_name>.json`
   - Rendered prompt: `_docs/incidents/prompt-<timestamp>-<alert_name>.md`
3. **Agent Invocation** (`scripts/invoke-agent`):
   - **Antigravity CLI**: If `agy` is installed, runs `agy --prompt "$(cat prompt.md)"`.
   - **Claude Code**: If `claude` is installed, runs `claude -p "$(cat prompt.md)"`.
   - **Autonomous Headless Responder**: If running headless in container/CI, runs the autonomous triage loop: gathers evidence via `collect-evidence`, verifies against `authorize-action`, logs the session, and prepares a repro test.
4. **Resolution Tracking**: When the alert recovers and is no longer returned as firing, the poller logs `ALERT_RESOLVED` and clears the alert fingerprint.

---

## 5. Verification & Testing

Execute the automated end-to-end verification script:
```bash
bash on-call-engineer/scripts/verify

# Or via Makefile
make on-call-verify
```

The verification script confirms:
- All required schemas, policies, and runbooks exist.
- Alert normalization operates correctly.
- Live Prometheus alert API is queried successfully (`--once`).
- Mock firing alerts trigger incident generation and headless agent dispatch.
- Read-only evidence collection and code-enforced autonomy policy checks succeed.

---

## 6. Local Cloud Production Simulation (SNS -> Lambda -> ECS/Fargate -> S3 & CloudWatch)

We emulate the full AWS enterprise serverless incident response architecture locally using containerized emulators without cloud spend:

```
[Prometheus / Alertmanager]
          │ (Alert Fires)
          ▼
[Amazon SNS / EventBridge] (Floci S3/SNS Topic)
          │
          │ (SNS Event Notification)
          ▼
[AWS Lambda Dispatcher] (cloud-simulator/lambda/dispatcher.py)
          │
          │ (Runs ephemeral task via ECS run_task)
          ▼
[AWS ECS / Fargate Ephemeral Container] (cloud-simulator/fargate-task/task-runner.sh --rm)
          │
          ├──► Headless AI Coding Agent: Gathers telemetry evidence
          ├──► Evaluates code-enforced autonomy policy
          ├──► Generates root-cause reproduction & minimal git diff patch
          ├──► Emits live logs to CloudWatch Log Stream
          │
          ▼
[Audit & Archival]
   ├──► Archives deliverables to Amazon S3: `s3://lifecycle-on-call-incidents/<incident-id>/`
   │      - `incident.json` (normalized alert payload)
   │      - `prompt.md` (agent context prompt)
   │      - `evidence.json` (bounded telemetry packet)
   │      - `diff.patch` (minimal code correction)
   │      - `transcript.log` (complete execution audit trail)
   └──► Ephemeral compute container terminates and destroys immediately (`--rm`)
```

### Running the Cloud Simulation
```bash
# Using Makefile
make on-call-simulate-cloud

# Or direct bash script
bash on-call-engineer/cloud-simulator/scripts/run-cloud-simulation
```

The simulation validates that:
1. The SNS alert topic is created and accepts messages in the emulator.
2. The Lambda dispatcher receives the SNS event, extracts the payload, and dispatches the Fargate task.
3. The Fargate task executes headlessly in an isolated container.
4. All artifacts (`diff.patch`, `evidence.json`, `transcript.log`) are securely uploaded to S3.
5. The container terminates immediately, leaving 0 lingering compute containers.

