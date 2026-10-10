# Personal Lifecycle Tracker

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.0-4169E1.svg?logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker)](https://www.docker.com)
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

## Production Cloud Deployment (AWS & Render)

We provide comprehensive Infrastructure as Code (IaC) packages supporting both **AWS** and **Render**:

| Target Cloud | Tooling | Architecture | Guide |
|---|---|---|---|
| **Render** | Render Blueprint (`render.yaml`) | Managed PostgreSQL + Docker Web Services (FastAPI + Caddy) | [Render Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/render.md) |
| **Render** | Terraform (`terraform/render/`) | Declarative IaC via Render Terraform Provider | [Render Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/render.md) |
| **AWS** | Terraform (`terraform/aws/`) | EC2 (`t3.micro`/Free Tier) + Elastic IP + SSM Session Manager + Docker Compose | [AWS Terraform Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/aws-terraform.md) |
| **AWS** | CloudFormation (`cloudformation/`) | 1-Click AWS Stack (VPC, Subnet, Security Group, EC2, Elastic IP, SSM) | [AWS CloudFormation Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/aws-cloudformation.md) |

### Zero-Host-Runtime IaC Commands (Dockerized)
```bash
# Validate AWS Terraform
make tf-validate-aws

# Validate Render Terraform
make tf-validate-render

# Format all Terraform files
make tf-fmt
```

For complete instructions, see the [Deployment Documentation Index](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/README.md).

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
