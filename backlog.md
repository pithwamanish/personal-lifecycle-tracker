# Personal Lifecycle Tracker — Development Backlog

This backlog deconstructs [`product-spec.md`](product-spec.md) and [`_docs/plan.md`](_docs/plan.md) into atomic, verifiable implementation tasks.

---

## Task Backlog Overview

| Task ID | Component | Description | Status | Verification Criteria |
|---|---|---|---|---|
| **TASK-01** | Data Layer | Database schema & SQLAlchemy models (Users, Groups, Items) | `DONE` | Pytest `test_database.py`, tables migrated |
| **TASK-02** | Backend Auth | User registration, bcrypt hashing, JWT access tokens | `DONE` | Pytest `test_auth.py`, 401 on missing token |
| **TASK-03** | Groups API | Shared groups, invitations, member permissions | `DONE` | Pytest `test_groups.py`, owner/member rules |
| **TASK-04** | Items API | Lifecycle items CRUD (Renewals, Maintenance, Warranties) | `DONE` | Pytest `test_items.py`, common fields validation |
| **TASK-05** | Reminders | Overdue/upcoming detection and action summaries | `DONE` | Pytest `test_reminders.py`, due date filters |
| **TASK-06** | Daily Digest | Morning digest generation and email delivery simulator | `DONE` | Pytest digest endpoint, grouped summaries |
| **TASK-07** | Frontend Client | Centralized API client service (`src/services/api.ts`) | `DONE` | Unit tests with mock fallback |
| **TASK-08** | Frontend UI | React 19 dashboard, guided creation modal, filtering | `DONE` | Vitest component tests, responsive views |
| **TASK-09** | Containerization | Docker Compose multi-service topology (DB + App + Caddy) | `DONE` | `make up`, healthy `/health` checks |
| **TASK-10** | Integration QA | Multi-user PostgreSQL integration & Playwright E2E | `DONE` | 27 integration tests, 17 E2E tests passing |
| **TASK-11** | Observability | OpenTelemetry traces, Prometheus metrics, Loki, Grafana | `DONE` | OTel Collector pipeline & dashboards active |
| **TASK-12** | Local K8s | Declarative Kind deployment manifests and PVC storage | `DONE` | `make kind-deploy`, pod readiness verified |
| **TASK-13** | CI/CD & Deploy | Two-stage ECR pipeline, dev/prod environments, Terraform | `DONE` | Keyless GitHub Actions OIDC deploy |
| **TASK-14** | Autonomous Ops | Headless on-call incident poller, policy, and runbooks | `DONE` | `on-call-engineer/poll-alerts.py` verified |

---

## Detailed Task Specifications

### Task 1: Core Domain Models & Database Schema
- **Objective**: Establish the relational database foundation supporting both PostgreSQL and SQLite fallback.
- **Entities**:
  - `User`: `id`, `email`, `password_hash`, `full_name`, `created_at`.
  - `Group`: `id`, `name`, `owner_id`, `created_at`.
  - `GroupMember`: `group_id`, `user_id`, `role`, `joined_at`.
  - `LifecycleItem`: `id`, `name`, `type` (`renewal` | `maintenance` | `warranty`), `due_date`, `status` (`active` | `completed`), `user_id`, `group_id`, `created_at`, `updated_at`.
- **Deliverables**: [`backend/app/db_models.py`](backend/app/db_models.py), [`backend/app/database.py`](backend/app/database.py).

### Task 2: Authentication & Token Authorization Service
- **Objective**: Implement stateless JWT authentication preventing unauthenticated access to personal or group resources.
- **Endpoints**: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
- **Security**: Passwords salted and hashed with `bcrypt`, access tokens signed with HMAC-SHA256, expiration enforced.
- **Deliverables**: [`backend/app/routers/auth.py`](backend/app/routers/auth.py), [`backend/app/auth.py`](backend/app/auth.py).

### Task 3: Shared Groups & Membership Access Layer
- **Objective**: Provide group collaboration where group members share lifecycle item tracking while maintaining group ownership boundaries.
- **Endpoints**: `GET /api/v1/groups`, `POST /api/v1/groups`, `POST /api/v1/groups/{id}/members`, `DELETE /api/v1/groups/{id}/members/{user_id}`.
- **Rules**: Group creator is designated `owner`. Members can view and edit shared items. Group items persist when members leave.
- **Deliverables**: [`backend/app/routers/groups.py`](backend/app/routers/groups.py).

### Task 4: Lifecycle Items CRUD & Type Filtering
- **Objective**: Core CRUD API for the 3 supported lifecycle types (Renewals, Maintenance, Warranties).
- **Endpoints**: `GET /api/v1/items`, `POST /api/v1/items`, `GET /api/v1/items/{id}`, `PUT /api/v1/items/{id}`, `DELETE /api/v1/items/{id}`.
- **Filters**: Filter by `type`, `status`, `group_id`, `due_before`, `due_after`.
- **Deliverables**: [`backend/app/routers/items.py`](backend/app/routers/items.py).

### Task 5: Reminders Engine & Action Summaries
- **Objective**: Aggregate upcoming (due within 30 days) and overdue items into an instant action summary.
- **Endpoints**: `GET /api/v1/reminders`, `GET /api/v1/reminders/summary`.
- **Deliverables**: [`backend/app/routers/reminders.py`](backend/app/routers/reminders.py).

### Task 6: Daily Morning Email Digest Simulator
- **Objective**: Simulate daily 8:00 AM notification digests delivering scheduled reminders to registered users.
- **Endpoints**: `POST /api/v1/reminders/digest/send`, `GET /api/v1/reminders/digest/history`.
- **Deliverables**: Background digest dispatcher in backend with delivery logging.

### Task 7: Centralized Frontend API Client
- **Objective**: Abstract all HTTP requests behind a single typed API client layer with mock fallback capability.
- **Deliverables**: [`frontend/src/services/api.ts`](frontend/src/services/api.ts).

### Task 8: Interactive React 19 Frontend Components
- **Objective**: Modern, accessible UI implementing full lifecycle management.
- **Components**: Navigation, Auth modals, Item tables, Guided type creation wizard, Reminders drawer.
- **Deliverables**: [`frontend/src/App.tsx`](frontend/src/App.tsx), [`frontend/src/components/`](frontend/src/components/).

### Task 9: Containerization & Docker Compose Foundation
- **Objective**: Fully containerized local execution with zero host dependencies.
- **Deliverables**: [`docker-compose.yaml`](docker-compose.yaml), [`docker-compose.prod.yml`](docker-compose.prod.yml), [`Makefile`](Makefile).

### Task 10: PostgreSQL Integration & Playwright E2E Testing
- **Objective**: Isolated integration tests against real PostgreSQL and browser journeys using Playwright.
- **Deliverables**: [`backend/tests/integration/`](backend/tests/integration/), [`e2e/`](e2e/).
