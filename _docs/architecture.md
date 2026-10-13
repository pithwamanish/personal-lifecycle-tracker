# Personal Lifecycle Tracker — Architecture Specification

## 1. System Topology & Tiers

The Personal Lifecycle Tracker implements a zero-trust, multi-service architecture:

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

## 2. Component Breakdown

- **Frontend**: React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide icons.
- **Backend API**: FastAPI (Python 3.11), SQLAlchemy, Pydantic v2, PyJWT, psycopg2, Uvicorn.
- **Database**: PostgreSQL 16 Alpine containerized with SQLAlchemy ORM and schema migration.
- **Gateway**: Caddy 2 minimal reverse proxy with single-port entrypoint and SPA fallback.
- **Observability**: OpenTelemetry Collector, Prometheus, Loki, Tempo, Grafana.
- **Contract**: OpenAPI 3.0.3 specification frozen in `contracts/openapi.yaml`.
