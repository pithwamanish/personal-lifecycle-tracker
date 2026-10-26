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

## 3. Cloud Serverless Architecture & Verified Endpoints (Criterion 8 — 2 Points)

The production architecture is deployed serverless on AWS:
```
[User Browser] ──HTTPS──> [AWS CloudFront CDN Edge]
                               │
            ┌──────────────────┴──────────────────┐
     /* (React 19 SPA)                     /api/* & /health
            │                                     │
            ▼                                     ▼
    [Amazon S3 Private]                 [AWS Lambda Web Adapter]
                                                  │
                                                  ▼
                                      [FastAPI Backend Container]
                                                  │
                                                  ▼
                                       [Neon Serverless Postgres]
```

- **Live Public Web Application**: [https://d1ca9upoitnq9b.cloudfront.net/](https://d1ca9upoitnq9b.cloudfront.net/)
- **Live Public API Health**: [https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/health](https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/health)
- **Interactive Swagger Docs**: [https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/docs](https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/docs)
- **Pre-Seeded Credentials**: `alex@example.com` / `password123`
