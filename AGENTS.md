# Personal Lifecycle Tracker — Agent Instructions & Operating Guide

Welcome to the **Personal Lifecycle Tracker** repository. This project manages Renewals, Maintenance, and Warranties for independent users and shared groups, including action summaries, in-app notifications, and scheduled daily morning email digests.

---

## 1. Project Overview & Architecture

- **Backend**: FastAPI (Python 3.11), Uvicorn, Pydantic v2, PyJWT.
- **Frontend**: React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide icons.
- **Orchestration**: Docker Compose multi-service architecture (Backend + Frontend).
- **Production Gateway**: Caddy 2 minimal reverse proxy with SPA fallback and security headers.
- **Contract**: OpenAPI 3.0.3 specification frozen in [`contracts/openapi.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/contracts/openapi.yaml).

### Network & Port Layout
| Service | Container Port | Host Port (Configurable) | Health / Status Endpoint |
|---|---|---|---|
| **Backend (Dev)** | `8000` | `8003` (`${BACKEND_PORT:-8003}`) | `http://localhost:8003/health` |
| **Frontend (Dev)** | `3000` | `3003` (`${FRONTEND_PORT:-3003}`) | `http://localhost:3003/` |
| **API Docs (Swagger)** | `8000` | `8003` | `http://localhost:8003/docs` |
| **Production Stack (Caddy)** | `80` | `8088` (`${PROD_PORT:-8088}`) | `http://localhost:8088/health` |

---

## 2. Universal Operating Invariants

1. **Strict Project Directory Boundary**:
   - Confine all file reads, writes, searches, and terminal executions strictly to this project repository root.
   - Never traverse to parent (`..`) or sibling directories.

2. **Universal Zero-Host-Runtime Mandate**:
   - The host system is treated strictly as a headless Docker runner.
   - **Never** execute builds, tests, package installations, or servers directly on the host shell (`no host python`, `no host pip`, `no host node`, `no host npm`).
   - All builds, test runs, linting, and services MUST execute inside Docker containers via `docker compose`.

3. **Pre-Flight Port Collision Check**:
   - Prior to launching containers, verify that configured ports (`8003`, `3003`, `8088`) are free:
     ```bash
     rtk docker ps --filter "publish=8003"
     rtk docker ps --filter "publish=3003"
     ```

4. **RTK Command Wrapper**:
   - Always prefix bash commands with `rtk` (e.g. `rtk docker compose ps`, `rtk make test`).

---

## 3. How to Run the Project

### A. Development Mode (With Hot-Reloading)

Start the full stack (backend + frontend) in detached mode:
```bash
# Using Makefile
make up

# Or directly with Docker Compose
docker compose up -d --build
```

Verify service status and health:
```bash
# Check status of running containers
make ps
# or: docker compose ps
```
Both containers will report `Up (healthy)`.

Access the application:
- **Web Application UI**: [http://localhost:3003](http://localhost:3003)
- **API Health Endpoint**: [http://localhost:8003/health](http://localhost:8003/health)
- **Interactive OpenAPI / Swagger UI**: [http://localhost:8003/docs](http://localhost:8003/docs)
- **Interactive ReDoc Documentation**: [http://localhost:8003/redoc](http://localhost:8003/redoc)

Stream live application logs:
```bash
make logs
# Or specific service logs:
docker compose logs -f backend
docker compose logs -f frontend
```

Stop and clean up containers:
```bash
make down
# or: docker compose down -v
```

---

### B. Production Mode (Caddy Reverse Proxy)

Build and run the production image artifacts using Caddy 2 reverse proxy:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Verify production endpoints:
- **Production Gateway & Web App**: [http://localhost:8088](http://localhost:8088)
- **Healthcheck via Reverse Proxy**: [http://localhost:8088/health](http://localhost:8088/health)

Tear down production stack:
```bash
docker compose -f docker-compose.prod.yml down -v
```

---

## 4. Testing & Quality Verification

All verification commands execute in isolated container environments:

### Run Full Test Suite (Backend + Frontend)
```bash
make test
```

### Run Backend Tests Only (FastAPI & Store Pytest Suite)
```bash
make test-backend
# Or directly via Compose:
docker compose run --rm backend pytest
```

### Run Frontend Unit Tests (Vitest)
```bash
make test-frontend
# Or directly via Compose:
docker compose run --rm frontend npm test
```

### Run Frontend Static Typecheck
```bash
make lint
# Or directly via Compose:
docker compose run --rm frontend npm run lint
```

---

## 5. Environment Variables & Overrides

Create an optional `.env` file in the project root to override defaults:

```ini
# Host port mappings
BACKEND_PORT=8003
FRONTEND_PORT=3003
PROD_PORT=8088

# Application environment
APP_ENV=development
PYTHONUNBUFFERED=1

# Database connection (SQLite default, or PostgreSQL e.g. postgresql://user:pass@host:5432/db)
DATABASE_URL=sqlite:///./lifecycle.db

# Frontend API routing
VITE_API_URL=http://localhost:8003
VITE_BACKEND_URL=http://backend:8000
```

---

## 6. Project Layout

```
.
├── AGENTS.md                  # Project constitution & instructions
├── Makefile                   # Docker Compose automation targets
├── docker-compose.yaml        # Development multi-app composition
├── docker-compose.prod.yml    # Production multi-stage Caddy composition
├── openapi.yaml               # Root API contract
├── contracts/
│   └── openapi.yaml           # Frozen canonical contract
├── docs/
│   └── spec.md                # Functional specification & scope
├── backend/
│   ├── Dockerfile             # Python 3.11 base image with healthchecks
│   ├── requirements.txt       # Backend dependencies
│   ├── pyproject.toml         # Pytest configuration
│   ├── app/                   # FastAPI application & routers
│   └── tests/                 # Backend pytest test suite
└── frontend/
    ├── Dockerfile             # Multi-stage: dev, builder, prod (Caddy)
    ├── Caddyfile              # Production Caddy 2 reverse proxy config
    ├── package.json           # Frontend dependencies & scripts
    ├── vite.config.ts         # Vite server, host & backend proxy config
    └── src/                   # React components, UI views & services
```

regularly commit code to git 
