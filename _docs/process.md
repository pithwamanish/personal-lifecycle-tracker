# Personal Lifecycle Tracker — Development & Operational Process

This document defines the formal software engineering and operational lifecycle process used by human operators and AI agents throughout the development of the **Personal Lifecycle Tracker**.

---

## 1. Lifecycle Governance Gates

Every feature, refactoring, and infrastructure change must advance through these sequential lifecycle gates:

```
[Gate 1: Specification] ──► [Gate 2: Prototype] ──► [Gate 3: Verification Journey]
                                                                  │
                                                                  ▼
[Gate 6: Tech Stack/ADR] ◄── [Gate 5: Contract Freeze] ◄── [Gate 4: Governance]
        │
        ▼
[Gate 7: Containerization] ──► [Gate 8: Backlog & Makefile] ──► [Gate 9: Active Containers]
                                                                        │
                                                                        ▼
[Gate 12: On-Call Responder] ◄── [Gate 11: Alerting] ◄── [Gate 10: Observability]
```

### Gate Descriptions & Exit Criteria

1. **Gate 1: Scoping & Functional Specification**:
   - Focus: Functional user personas, domain entities (Renewals, Maintenance, Warranties), reminder thresholds, and anti-goals.
   - Deliverable: [`product-spec.md`](../product-spec.md).
   - Invariant: Zero technology stack decisions in this phase.

2. **Gate 2: Interface & Prototype Confirmation**:
   - Focus: Interactive UI views and client component hierarchy.
   - Deliverable: Frontend React 19 application with mock service layer (`src/services/api.ts`).

3. **Gate 3: Manual Verification Journey**:
   - Focus: Concrete step-by-step user acceptance scenario validating multi-user collaboration and deadline tracking.
   - Deliverable: Manual test script in [`_docs/manual-test.md`](test-scenarios/001-primary-flow.md) and Playwright compliance suite [`e2e/spec-compliance.spec.ts`](../e2e/spec-compliance.spec.ts).

4. **Gate 4: Governance Setup & Agent Squad Scaffold**:
   - Focus: Project instructions, role specifications, and operating boundaries.
   - Deliverables: [`AGENTS.md`](../AGENTS.md), [`CLAUDE.md`](../CLAUDE.md), [`_docs/team.md`](team.md), [`_docs/process.md`](process.md).

5. **Gate 5: Contract Freeze**:
   - Focus: Strict typed interface boundary decoupling frontend and backend.
   - Deliverables: [`contracts/openapi.yaml`](../contracts/openapi.yaml) and root [`openapi.yaml`](../openapi.yaml).

6. **Gate 6: Architecture Decision Records (ADRs) & Stack Evaluation**:
   - Focus: Architectural decisions, database persistence choice, and local cloud emulator parity.
   - Deliverables: [`docs/adr/0001-adoption-architecture.md`](../docs/adr/0001-adoption-architecture.md), [`_docs/stack.md`](stack.md).

7. **Gate 7: Scaffolding & Container Foundation**:
   - Focus: Reproducible zero-host-runtime container environments.
   - Deliverables: [`backend/Dockerfile`](../backend/Dockerfile), [`frontend/Dockerfile`](../frontend/Dockerfile), [`docker-compose.yaml`](../docker-compose.yaml).

8. **Gate 8: Makefile Automation & Task Tracker**:
   - Focus: Atomic backlog decomposition and single-command make targets.
   - Deliverables: [`backlog.md`](../backlog.md), [`Makefile`](../Makefile).

9. **Gate 9: Active Running Containers & Live Verification**:
   - Focus: Live integration between frontend, backend, and PostgreSQL 16 database.
   - Exit Criteria: `docker compose ps` confirms all services `Up (healthy)`. Live `curl http://localhost:8003/health` returns HTTP 200.

10. **Gate 10: OpenTelemetry Full-Stack Instrumentation**:
    - Focus: Distributed tracing, Prometheus metrics, Loki log shipping, and Grafana Golden Signals dashboards.
    - Deliverables: [`backend/app/telemetry.py`](../backend/app/telemetry.py), [`observability/`](../observability/).

11. **Gate 11: Alerting on User Impact**:
    - Focus: Alerts triggered by real user degradation (5xx error rate, item creation failures, latency) rather than raw host metrics.
    - Deliverables: [`observability/alert_rules.yml`](../observability/alert_rules.yml).

12. **Gate 12: Autonomous On-Call Incident Responder**:
    - Focus: Continuous alert polling, normalized incident schema, bounded evidence collection, and automated drill verification.
    - Deliverables: [`on-call-engineer/`](../on-call-engineer/).

---

## 2. Testing Pyramid & Verification Gates

All code changes must pass the automated testing hierarchy inside Docker before merge:

| Test Tier | Scope | Framework | Execution Command | Gate Invariant |
|---|---|---|---|---|
| **Tier 1: Backend Unit** | FastAPI routers, store logic, auth, reminders | Pytest in Docker | `make test-backend` | 34 passing tests, 0 failures |
| **Tier 2: Frontend Unit** | Date utilities, API client, lifecycle state | Vitest in Docker | `make test-frontend` | 42 passing tests, 0 failures |
| **Tier 3: PostgreSQL Integration** | Auth flows, group permissions, item persistence | Pytest + Postgres 16 | `make test-integration` | 27 passing tests, 0 failures |
| **Tier 4: Browser E2E** | Multi-user collaboration, daily digest simulation | Playwright in Docker | `make test-e2e` | 22 passing tests, 0 failures |
| **Tier 5: Static Security** | SAST vulnerability scan, dependency audit | Semgrep + npm audit | `make security-audit` | 0 high/critical CVEs |

---

## 3. Deployment & Promotion Workflow

1. **Continuous Integration (`.github/workflows/ci.yml`)**:
   - Trigger: Every pull request and push to `main`, `dev`, or `develop`.
   - Actions: Parallel execution of backend tests, frontend tests, integration tests, and Playwright E2E browser tests.
   - Artifact: Builds container images tagged with `YYYYMMDD-HHMMSS-shortsha` and deploys to development.

2. **Manual Production Promotion (`.github/workflows/promote-dev-to-prod.yml`)**:
   - Trigger: Operator `workflow_dispatch`.
   - Actions: Pre-promotion test validation, SemVer release tagging (`vX.Y.Z`), GitHub release generation, and zero-downtime serving from Amazon ECR.
