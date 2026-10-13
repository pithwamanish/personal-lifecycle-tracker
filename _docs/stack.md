# Personal Lifecycle Tracker — Technology Stack & Cloud Infrastructure Decision

## 1. Stack Evaluation & Rationale

| Tier | Chosen Technology | Evaluated Alternatives | Rationale |
|---|---|---|---|
| **Frontend** | React 19 + Vite 8 + TS | Vue, Svelte, Next.js | High performance, instant HMR, strict type safety, zero host builds |
| **Backend** | FastAPI + Python 3.11 | Express/Node, Go/Gin | Automatic OpenAPI generation, Pydantic validation, async performance |
| **Database** | PostgreSQL 16 Alpine | MongoDB, MySQL, DynamoDB | Relational integrity, foreign key cascades, JSONB flexibility |
| **Containerization** | Docker Compose | Standalone Dockerfiles | Multi-service local parity with healthchecks and internal networks |
| **Reverse Proxy** | Caddy 2 | Nginx, Traefik | Automatic HTTPS, minimal configuration, native reverse proxying |
| **Cloud Deployment** | Render + AWS (EC2 & Serverless) | Fly.io, Heroku, GCP | Generous free tier, infrastructure parity, declarative IaC (Terraform) |
| **Observability** | OpenTelemetry + LGTM | Datadog, New Relic | Vendor-neutral standard, local Docker stack, zero license costs |

## 2. Infrastructure as Code (IaC)

- **Render**: Blueprint `render.yaml` & `render.prod.yaml`, Terraform `terraform/render/` & `terraform/render-prod/`.
- **AWS**: Terraform `terraform/aws/` (`10.1.0.0/16`) & `terraform/aws-prod/` (`10.0.0.0/16`), CloudFormation `cloudformation/aws-ec2-compose.yaml` & `cloudformation/aws-ec2-compose-prod.yaml`.
