# Operations & Reliability Engineering Index

This directory provides operational incident diagnosis, telemetry runbooks, alert configurations, and automated incident remediation procedures for the **Personal Lifecycle Tracker** platform.

---

## Operations Documentation Map

| Document | Purpose | Target Audience | Status |
|---|---|---|---|
| [`diagnosis.md`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/ops/diagnosis.md) | Real Incident Investigation, Telemetry Root Cause & Verification | On-Call Engineers, Autonomous Agents | `RESOLVED` |
| [`runbook.md`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/ops/runbook.md) | Standard Operating Procedures (SOPs) & Alert Response Workflows | DevOps, SRE | `ACTIVE` |
| [`on-call-engineer/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/on-call-engineer/README.md) | Autonomous Alert Poller, Autonomy Policies, and Dispatcher | Autonomous Subagent Loop | `OPERATIONAL` |

---

## Reliability & Service Level Objectives (SLOs)

- **Availability Objective**: 99.9% uptime for core API endpoints (`/health`, `/api/v1/items`, `/api/v1/auth`).
- **Latency Objective (p95)**: < 250ms response time under peak load.
- **Error Rate Objective**: Server error rate (`5xx`) < 0.1% over a 5-minute rolling window.
- **Mean Time to Detection (MTTD)**: < 60 seconds via Prometheus alert rules.
- **Mean Time to Resolution (MTTR)**: < 5 minutes via automated root-cause isolation and test-gated hotfix deployment.
