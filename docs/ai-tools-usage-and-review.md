# AI-Assisted Development Workflow & Review Documentation

This document records the end-to-end AI-assisted development workflow used to build, containerize, deploy, and operate the **Personal Lifecycle Tracker** repository.

---

## 1. AI Tooling Architecture & Roles

| Agent / Tool | Role in Project | Modality | Output Artifacts |
|---|---|---|---|
| **Antigravity / Gemini 3.8 Flash** | Lead Orchestrator, Architecture & Full-Stack Integration | Interactive Pair Programming | Overall codebase, Docker Compose, Terraform, OTel |
| **Claude Code (Sonnet 3.7)** | Refactoring, Pytest Test Suites, Playwright E2E | Terminal CLI Agent | `backend/tests/`, `e2e/`, `Makefile` |
| **Cursor / Copilot** | Inline Frontend React 19 Component Refactoring | In-Editor IDE Autocomplete | `frontend/src/components/` |
| **Autonomous Incident Responder** | On-Call Monitoring & Alert Remediation | Headless Poller Loop | `on-call-engineer/poll-alerts.py`, fix patches |

---

## 2. Context Files & System Prompts

Rather than relying on vague prompts, the development workflow anchored all coding agents using deterministic project context files:

1. [`AGENTS.md`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/AGENTS.md): Loaded into every session. Enforced the zero-host-runtime mandate, directory confinement, and RTK command wrappers.
2. [`product-spec.md`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/product-spec.md): Grounded all entity models, field definitions, and business logic before any code was written.
3. [`contracts/openapi.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/contracts/openapi.yaml): Served as the frozen API contract ensuring zero drift between frontend service clients and FastAPI router implementations.
4. [`docker-compose.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docker-compose.yaml): Standardized local execution across all developers and agents.

---

## 3. Step-by-Step AI Prompt Progression & Task Delegation

### Stage 1: Specification & Scoping
- **Prompt**:
  > *"I want to build a tool for managing renewals, maintenance, and warranties across independent users and shared groups. Help me set the scope for this project precisely. Ask me one question at a time and keep output short. Output the final plan to `_docs/plan.md`."*
- **Context Provided**: Initial domain ideas, user personas, common entity fields.
- **Review Gate**: Human operator reviewed `_docs/plan.md` and pruned out attachments and third-party calendar sync to keep MVP strictly bounded.

### Stage 2: Frontend Prototype with Mock Service Layer
- **Prompt**:
  > *"Build the frontend for the app described in `product-spec.md`. Put it in `frontend/`. Centralize every backend call in `src/services/api.ts` and create a mock implementation so the whole app runs without a backend. Make the UI interactive with React 19 and Tailwind CSS."*
- **Review Gate**: Tested the UI interactively on `http://localhost:3003`. Verified that changing tabs (Renewals vs Maintenance vs Warranties) accurately filtered items.

### Stage 3: API Contract Freeze
- **Prompt**:
  > *"Read the frontend API client in `frontend/src/services/api.ts`. Create `contracts/openapi.yaml` defining every endpoint, method, path, request/response schema, and bearer authentication requirements."*
- **Review Gate**: Validated OpenAPI 3.0.3 syntax using Swagger UI and confirmed parameter consistency.

### Stage 4: Backend Implementation & Database Persistence
- **Prompt**:
  > *"Build a FastAPI backend in `backend/` implementing `contracts/openapi.yaml`. Start with an in-memory store and seed data. Next, implement PostgreSQL persistence via SQLAlchemy ORM with automatic table creation. Add bcrypt password hashing and PyJWT token generation."*
- **Review Gate**: Ran containerized Pytest suite: `docker compose run --rm backend pytest`. All 27 unit tests passed.

### Stage 5: Containerization & Reverse Proxy
- **Prompt**:
  > *"Create a production Dockerfile and `docker-compose.prod.yml` using Caddy 2 as a reverse proxy. Caddy should serve static React assets at `/` and reverse proxy `/api/*` and `/health` to the FastAPI backend on port 8088."*
- **Review Gate**: Ran `make prod-up` and verified `curl -f http://localhost:8088/health` returned HTTP 200.

### Stage 6: Observability & OpenTelemetry Instrumentation
- **Prompt**:
  > *"Instrument the FastAPI backend with OpenTelemetry traces and Prometheus metrics. Create `observability/` with OpenTelemetry Collector, Prometheus, Loki, Tempo, and Grafana in a standalone Docker Compose project."*
- **Review Gate**: Inspected Grafana dashboard at `http://localhost:3004`, verifying that backend HTTP requests generated spans in Tempo and logs in Loki.

### Stage 7: Autonomous Incident Responder
- **Prompt**:
  > *"Add `on-call-engineer/` with a poller that queries Prometheus alerts. When an alert fires, dispatch the alert payload to a headless coding agent adhering to `autonomy-policy.json`. Provide a triage runbook in `runbook.md`."*
- **Review Gate**: Executed `make on-call-verify` proving that simulated alert triggers resulted in accurate alert parsing and log capture.

---

## 4. Human-in-the-Loop Review & Verification Methodology

1. **Deterministic Test Execution**:
   Never accepted AI-generated code without automated test proof. Ran `make test` inside Docker before committing.
2. **Static Code Review**:
   Reviewed every git diff for hallucinated packages, unnecessary abstractions, or hardcoded secrets.
3. **Multi-User Browser Validation**:
   Executed 17 Playwright E2E browser tests across isolated browser contexts, validating that User A's changes in Group 1 were reflected in User B's session.
