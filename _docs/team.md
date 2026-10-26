# Personal Lifecycle Tracker — Agent Team Specification

This document defines the specialized agent team, individual roles and responsibilities, permissions boundaries, and the collaborative handover process used across the development and operational lifecycle of the **Personal Lifecycle Tracker**.

---

## 1. Agent Squad Roles & Responsibilities

| Agent Role | Model / Identity | Core Responsibilities | Boundary & Restrictions | Primary Artifacts |
|---|---|---|---|---|
| **Product Manager Agent** | Antigravity / Gemini 3.8 Flash | Elicits user needs, defines personas, structures functional scope, enforces anti-goals, and breaks requirements into atomic acceptance criteria. | Strictly domain-focused. Prohibited from making backend framework or database choices during initial scoping. | [`product-spec.md`](../product-spec.md), [`backlog.md`](../backlog.md), [`_docs/plan.md`](../_docs/plan.md) |
| **System Architect Agent** | Antigravity / Gemini 3.8 Flash | Designs multi-tier container topologies, freezes API contracts (`openapi.yaml`), author Architecture Decision Records (ADRs), and ensures environment parity. | Enforces zero-host-runtime container standards. Prohibited from mutating production database schemas without migration plans. | [`contracts/openapi.yaml`](../contracts/openapi.yaml), [`docs/adr/`](../docs/adr/), [`_docs/architecture.md`](../_docs/architecture.md) |
| **Lead Developer Agent** | Claude Code (Sonnet 3.7) & Cursor | Implements backend API routers (FastAPI), data models (SQLAlchemy), auth services (bcrypt + JWT), and interactive React 19 UI components. | Confined strictly to project root. Prohibited from executing uncontained host compilers (`no host python`, `no host node`). | [`backend/app/`](../backend/app/), [`frontend/src/`](../frontend/src/) |
| **QA & Verification Specialist** | Claude Code / Subagent Runner | Authors isolated unit tests (Pytest/Vitest), integration suites against real PostgreSQL, and cross-browser multi-user journeys (Playwright). | Independent rejection authority: prohibited from marking tasks `DONE` without passing containerized tests and active running containers. | [`backend/tests/`](../backend/tests/), [`e2e/`](../e2e/) |
| **Autonomous On-Call Responder** | Headless Event Loop / Lambda | Continuously monitors Prometheus alert APIs, normalizes incident payloads, gathers bounded evidence, and applies verified self-healing code fixes. | Governed strictly by code-enforced [`autonomy-policy.json`](../on-call-engineer/autonomy-policy.json). Must halt for human approval on Level 2 code changes. | [`on-call-engineer/`](../on-call-engineer/), [`_docs/incidents/`](../_docs/incidents/) |

---

## 2. Collaborative Workflow & Handover Protocol

The agents work together sequentially and iteratively following a strict contract-first handover protocol:

```
┌─────────────────────────┐
│  Product Manager Agent  │ ──► [Elicit Scope, Entities & Acceptance Criteria]
└───────────┬─────────────┘
            │ Handover 1: product-spec.md & backlog.md
            ▼
┌─────────────────────────┐
│  System Architect Agent │ ──► [Freeze OpenAPI 3.0.3 Contract & Topology ADRs]
└───────────┬─────────────┘
            │ Handover 2: contracts/openapi.yaml & docker-compose.yaml
            ▼
┌─────────────────────────┐
│   Lead Developer Agent  │ ──► [Implement Backend Services & Frontend UI]
└───────────┬─────────────┘
            │ Handover 3: Live Running Containers & Codebase
            ▼
┌─────────────────────────┐
│ QA Specialist Agent     │ ──► [Execute Unit, Integration & Browser E2E Tests]
└───────────┬─────────────┘
            │ Handover 4: Verified Test Green Gates & Observability Instrumentation
            ▼
┌─────────────────────────┐
│ Autonomous On-Call Agent│ ──► [Continuous Alert Monitoring & Self-Healing Drills]
└─────────────────────────┘
```

### Detailed Handover Gates

1. **Gate 1: Scoping to Architecture (PM -> Architect)**:
   - Deliverable: [`product-spec.md`](../product-spec.md).
   - Validation: All domain entities (Renewals, Maintenance, Warranties), user personas, and anti-goals are documented. Zero technical stack decisions are made.

2. **Gate 2: Architecture to Engineering (Architect -> Lead Developer)**:
   - Deliverables: [`contracts/openapi.yaml`](../contracts/openapi.yaml), [`docker-compose.yaml`](../docker-compose.yaml), [`docs/adr/`](../docs/adr/).
   - Validation: Contract syntax validated. Port allocations verified collision-free. Docker Compose orchestrates database, backend, and frontend.

3. **Gate 3: Engineering to Quality Assurance (Lead Developer -> QA Specialist)**:
   - Deliverable: Running application cluster in Docker Compose.
   - Validation: `make test-backend` (34 passed), `make test-frontend` (42 passed), and `make test-integration` (27 passed). Containers report healthy.

4. **Gate 4: Quality Assurance to Operations (QA -> On-Call Responder)**:
   - Deliverables: Provisioned OpenTelemetry instrumentation, Grafana Golden Signals dashboards, and Prometheus alert rules (`observability/alert_rules.yml`).
   - Validation: End-to-end browser journeys pass via `make test-e2e` (22 passed). Observability stack actively scrapes signals.

5. **Gate 5: Incident Remediation Loop (On-Call Responder -> Lead Developer / QA)**:
   - When Prometheus fires an alert, the On-Call Responder normalizes the incident into `_docs/incidents/incident-<id>.json`.
   - The responder assembles a bounded evidence packet (`on-call-engineer/evidence.json`), evaluates autonomy policies, reproduces the bug with a containerized test, applies the patch, verifies regression tests, and commits the fix to Git.

---

## 3. Human-in-the-Loop Governance & Escalation

- **Level 1 (Autonomous)**: Read-only telemetry gathering, service health inspection, and container restart within predefined thresholds.
- **Level 2 (Human Approval Required)**: Source code mutations, database schema migrations, and Git branch pushes require operator authorization before execution.
- **Level 3 (Strictly Forbidden)**: Direct destructive operations (`DROP TABLE`, hard credential commits, force git pushes) are blocked at the engine level.
