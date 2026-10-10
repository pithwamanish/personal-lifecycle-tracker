# Personal Lifecycle Tracker

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.0-4169E1.svg?logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker)](https://www.docker.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg?logo=githubactions&logoColor=white)](.github/workflows/ci.yml)
[![Terraform](https://img.shields.io/badge/Terraform-1.7+-7B42BC.svg?logo=terraform)](https://www.terraform.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Manage Renewals, Maintenance, and Warranties for independent users and shared groups, with action summaries, in-app reminders, and daily morning email digests.

---

## Architecture Overview

```
                                      ┌────────────────────────────────────────────────────────┐
                                      │                      Production                        │
                                      │  ┌──────────────────────────────────────────────────┐  │
                                      │  │ Caddy 2 Reverse Proxy (Frontend Container) :80    │  │
                                      │  │ ├── /        -> React 19 SPA (Static Dist)       │  │
                                      │  │ ├── /api/*   -> Reverse proxy to Backend :8000   │  │
                                      │  │ └── /health  -> Reverse proxy to Backend :8000   │  │
                                      │  └───────────────────────┬──────────────────────────┘  │
                                      │                          │                             │
                                      │  ┌───────────────────────▼──────────────────────────┐  │
                                      │  │ FastAPI Backend Service (Python 3.11) :8000      │  │
                                      │  │ ├── Auth & Multi-User JWT Engine                 │  │
                                      │  │ ├── Lifecycle Items (Renewals, Warranties, Maint)│  │
                                      │  │ ├── Groups & Invitation Engine                   │  │
                                      │  │ └── Reminders & Daily Digest Service             │  │
                                      │  └───────────────────────┬──────────────────────────┘  │
                                      │                          │                             │
                                      │  ┌───────────────────────▼──────────────────────────┐  │
                                      │  │ PostgreSQL 16 Database :5432                     │  │
                                      │  │ └── Automatic schema migration & pooling         │  │
                                      │  └──────────────────────────────────────────────────┘  │
                                      └────────────────────────────────────────────────────────┘
```

- **Backend**: FastAPI (Python 3.11), SQLAlchemy, Pydantic v2, PyJWT, psycopg2.
- **Frontend**: React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide icons.
- **Reverse Proxy & Web Server**: Caddy 2 with automated gzip/zstd, security headers, and single-port reverse proxying.
- **Database**: PostgreSQL 16 (or local SQLite fallback).
- **API Contract**: Frozen OpenAPI 3.0.3 specification in [`contracts/openapi.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/contracts/openapi.yaml).

---

## Quick Start (Development)

Run the full stack with hot reloading (zero local toolchain required, powered entirely by Docker):

```bash
# Start all services (Database, Backend on :8003, Frontend on :3003)
make up

# Check status of running containers
make ps

# Stream logs
make logs

# Stop containers
make down
```

- **Web Application**: [http://localhost:3003](http://localhost:3003)
- **API Health Check**: [http://localhost:8003/health](http://localhost:8003/health)
- **Swagger UI**: [http://localhost:8003/docs](http://localhost:8003/docs)

---

## Production Mode (Caddy Reverse Proxy)

Test the unified production build locally on port 8088 (single port, Caddy reverse-proxying API & static SPA):

```bash
# Build and start production stack
make prod-up

# Verify health
curl -f http://localhost:8088/health

# Stop production stack
make prod-down
```

---

## Observability Infrastructure (Decoupled LGTM + OTel Stack)

Personal Lifecycle Tracker includes an independent, containerized observability project in `observability/` featuring **OpenTelemetry Collector**, **Prometheus**, **Loki**, **Tempo**, and **Grafana**:

```bash
# Start observability stack
make obs-up

# Check container status
make obs-ps

# View live telemetry logs
make obs-logs

# Stop observability stack
make obs-down
```

- **Grafana Dashboard**: [http://localhost:3004](http://localhost:3004) (`admin` / `admin`)
- **Prometheus UI**: [http://localhost:9091](http://localhost:9091)
- **OTel Collector OTLP HTTP Endpoint**: `http://localhost:4328`
- **Tempo Trace Ingestion**: `http://localhost:3201`
- **Loki Log Ingestion**: `http://localhost:3101`

For details on configuration and telemetry specifications, see [`observability/README.md`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/observability/README.md) and [`_docs/telemetry.md`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/_docs/telemetry.md).

---

## Cloud Infrastructure & Environments (Dev & Production)

We maintain two independent copies of our infrastructure:
- **Development (`dev`)**: Uses the baseline infrastructure configured for development workloads, isolated non-overlapping VPC networks (`10.1.0.0/16`), and free tier plans.
- **Production (`production`)**: A second, independent copy of the infrastructure provisioned for high availability and production workloads (`10.0.0.0/16` VPC).

| Cloud Platform | Dev Environment | Production Copy | Architecture |
|---|---|---|---|
| **Render** | [`render.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/render.yaml) | [`render.prod.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/render.prod.yaml) | Managed PostgreSQL + FastAPI + React/Caddy |
| **Render (Terraform)** | [`terraform/render/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/render/) | [`terraform/render-prod/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/render-prod/) | Declarative IaC via Render Terraform Provider |
| **AWS (Terraform)** | [`terraform/aws/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/aws/) (`10.1.0.0/16`) | [`terraform/aws-prod/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/aws-prod/) (`10.0.0.0/16`) | EC2 (`t3.micro`/Free Tier) + Elastic IP + SSM |
| **AWS (CloudFormation)**| [`cloudformation/aws-ec2-compose.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose.yaml) | [`cloudformation/aws-ec2-compose-prod.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose-prod.yaml) | 1-Click AWS Stack (VPC, Subnet, SG, EC2, EIP, SSM) |

### Zero-Host-Runtime IaC Commands (Dockerized)
```bash
# Validate ALL Terraform environments simultaneously (AWS Dev, AWS Prod, Render Dev, Render Prod)
make tf-validate

# Validate individual environments
make tf-validate-aws        # AWS Dev
make tf-validate-aws-prod   # AWS Production copy
make tf-validate-render     # Render Dev
make tf-validate-render-prod# Render Production copy

# Format all Terraform files
make tf-fmt
```

For complete instructions, see the [Deployment Documentation Index](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/README.md).

---

## Continuous Integration & Deployment (CI/CD)

The automated GitHub Actions workflow ([`.github/workflows/ci.yml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/.github/workflows/ci.yml)) provides test-gated delivery structured into two distinct stages:

1. **Parallel Unit Tests**: Backend (FastAPI Pytest) and Frontend (TypeScript lint + Vitest) run concurrently.
2. **Docker Compose Integration & E2E**: Builds the full stack, starts PostgreSQL, backend, and frontend containers, runs 27 integration tests, and executes 17 Playwright E2E browser journeys.
3. **Stage 1 (Build)**: Compiles backend and frontend container images, tags each image using the `YYYYMMDD-HHMMSS-shortsha` pattern (e.g. `20260818-163457-83242da`), and pushes them to Amazon ECR.
4. **Stage 2 (Deploy)**: Pulls the pre-built image artifacts from Amazon ECR and serves them via Docker Compose (`docker compose -f docker-compose.prod.yml up -d --no-build`), completely eliminating image building during deployment.
5. **Keyless Cloud Authentication (GitHub OIDC)**: Uses GitHub OIDC (`id-token: write`) to assume an AWS IAM role (`terraform/aws/oidc.tf`) to authenticate with ECR and AWS SSM.
6. **Healthcheck Verification**: Resilient polling loop validates that the deployed health endpoint returns HTTP 200 with `"status": "healthy"`.

For configuration and secrets setup, see the [CI/CD Pipeline Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/ci-cd.md).

### Dev to Production Promotion Workflow

A manual GitHub Actions workflow ([`.github/workflows/promote-dev-to-prod.yml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/.github/workflows/promote-dev-to-prod.yml)) promotes verified versions from `dev` to the production branch (`main`):
- **Pre-Flight Conflict & Test Gates**: Verifies zero merge conflicts, then executes backend tests, frontend lint & Vitest, and PostgreSQL integration tests in Docker.
- **Automated SemVer Tagging & Release**: Merges `dev` into `main`, auto-increments semantic version tags (e.g., `v1.0.0` → `v1.0.1` or accepts custom tag), compiles release notes, tags the commit, and cuts a GitHub Release.
- **Dev Image Pull & Promotion to Prod**: Pulls the currently deployed dev image directly from Amazon ECR (discovered via SSM parameter `/personal-lifecycle/dev/image_tag`), re-tags the exact verified artifact using the `YYYYMMDD-HHMMSS-shortsha` pattern and release version tag, pushes to ECR, and serves it on production without rebuilding from source.
- **Live Production Health Verification**: Polls the live health endpoint until HTTP 200 `"status": "healthy"` is confirmed.
- **Dry-Run Capability**: Operators can simulate promotion, tests, and changelog generation safely without pushing commits or deploying.


---

## Testing & Verification

All test suites execute in isolated container environments:

```bash
# Run all tests (Backend unit & integration, Frontend Vitest, E2E Playwright)
make test

# Run backend tests only
make test-backend

# Run backend integration tests with PostgreSQL
make test-integration

# Run frontend unit tests
make test-frontend

# Run frontend typecheck & lint
make lint

# Run Playwright E2E browser tests
make test-e2e
```
