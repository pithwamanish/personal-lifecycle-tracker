# Personal Lifecycle Tracker — Agent Instructions & Operating Guide

Welcome to the **Personal Lifecycle Tracker** repository. This project manages Renewals, Maintenance, and Warranties for independent users and shared groups, including action summaries, in-app notifications, and scheduled daily morning email digests.
It is governed by the AI-Native Meta-Environment (`meta-environment`) capability framework and strict zero-host-runtime container standards.

---

## 1. Project Overview & Architecture

- **Backend**: FastAPI (Python 3.11), Uvicorn, Pydantic v2, PyJWT, SQLAlchemy, psycopg2.
- **Frontend**: React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide icons.
- **Database**: PostgreSQL 16 containerized (`postgres:16-alpine`) or SQLite fallback.
- **Orchestration**: Docker Compose multi-service architecture (Database + Backend + Frontend).
- **Production Gateway**: Caddy 2 minimal reverse proxy with SPA fallback and security headers.
- **Contract**: OpenAPI 3.0.3 specification frozen in [`contracts/openapi.yaml`](contracts/openapi.yaml).

### Network & Port Layout
| Service | Container Port | Host Port (Configurable) | Health / Status Endpoint |
|---|---|---|---|
| **Database (PostgreSQL)** | `5432` | `5434` (`${POSTGRES_PORT:-5434}`) | `pg_isready -U postgres -d lifecycle` |
| **Backend (Dev)** | `8000` | `8003` (`${BACKEND_PORT:-8003}`) | `http://localhost:8003/health` |
| **Backend Metrics (Prometheus)** | `8000` | `8003` (`${BACKEND_PORT:-8003}`) | `http://localhost:8003/metrics` |
| **Frontend (Dev)** | `3000` | `3003` (`${FRONTEND_PORT:-3003}`) | `http://localhost:3003/` |
| **API Docs (Swagger)** | `8000` | `8003` | `http://localhost:8003/docs` |
| **Interactive ReDoc** | `8000` | `8003` | `http://localhost:8003/redoc` |
| **Production Stack (Caddy)** | `80` | `8088` (`${PROD_PORT:-8088}`) | `http://localhost:8088/health` |
| **OTel Collector (gRPC)** | `4317` | `4327` (`${OTEL_GRPC_PORT:-4327}`) | Internal gRPC OTLP receiver |
| **OTel Collector (HTTP)** | `4318` | `4328` (`${OTEL_HTTP_PORT:-4328}`) | `http://localhost:4328/v1/traces` |
| **OTel Metrics (Prometheus)** | `8889` | `8899` (`${OTEL_METRICS_PORT:-8899}`) | `http://localhost:8899/metrics` |
| **Prometheus Server** | `9090` | `9091` (`${PROMETHEUS_PORT:-9091}`) | `http://localhost:9091` |
| **Loki Log Engine** | `3100` | `3101` (`${LOKI_PORT:-3101}`) | `http://localhost:3101/ready` |
| **Tempo Trace Engine** | `3200` | `3201` (`${TEMPO_PORT:-3201}`) | `http://localhost:3201/ready` |
| **Grafana UI & Dashboards** | `3000` | `3004` (`${GRAFANA_PORT:-3004}`) | `http://localhost:3004/api/health` |

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
- **Prometheus Metrics Endpoint**: [http://localhost:8003/metrics](http://localhost:8003/metrics)
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

### C. Observability Mode (Decoupled LGTM + OTel Stack)

Start the independent observability stack (OpenTelemetry Collector, Prometheus, Loki, Tempo, Grafana):
```bash
# Using Makefile
make obs-up

# Or directly with Docker Compose
docker compose -f observability/docker-compose.yaml up -d
```

Verify running status:
```bash
make obs-ps
# or: docker compose -f observability/docker-compose.yaml ps
```

Access observability dashboards & engines:
- **Grafana UI**: [http://localhost:3004](http://localhost:3004) (`admin` / `admin`)
- **Prometheus UI**: [http://localhost:9091](http://localhost:9091)
- **Tempo Status**: [http://localhost:3201/ready](http://localhost:3201/ready)
- **Loki Status**: [http://localhost:3101/ready](http://localhost:3101/ready)
- **OTel Collector OTLP HTTP Receiver**: [http://localhost:4328/v1/traces](http://localhost:4328/v1/traces)
- **OTel Collector App Metrics Exporter**: [http://localhost:8899/metrics](http://localhost:8899/metrics)

Stream observability logs:
```bash
make obs-logs
# Or specific component:
docker compose -f observability/docker-compose.yaml logs -f otel-collector
```

Tear down observability stack:
```bash
make obs-down
# or: docker compose -f observability/docker-compose.yaml down -v
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

### Run End-to-End Tests (Playwright in Docker)
```bash
make test-e2e
# Or directly via Compose:
docker compose run --rm e2e
```

---

## 5. Environment Variables & Overrides

Create an optional `.env` file in the project root to override defaults:

```ini
# Host port mappings
BACKEND_PORT=8003
FRONTEND_PORT=3003
PROD_PORT=8088
POSTGRES_PORT=5434

# Application environment
APP_ENV=development
PYTHONUNBUFFERED=1

# Database connection (PostgreSQL default in Compose, or SQLite e.g. sqlite:///./lifecycle.db)
DATABASE_URL=postgresql://postgres:postgres@db:5432/lifecycle

# PostgreSQL service credentials (used when running via Docker Compose)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=lifecycle

# Frontend API routing
VITE_API_URL=http://localhost:8003
VITE_BACKEND_URL=http://backend:8000
```

---

## 6. Project Layout

```
.
├── AGENTS.md                  # Project constitution & instructions
├── README.md                  # Project overview & documentation
├── Makefile                   # Docker Compose & containerized IaC automation targets
├── .github/
│   └── workflows/
│       ├── ci.yml             # Automated CI/CD pipeline (tests, compose e2e, render deploy)
│       └── promote-dev-to-prod.yml # Manual dev-to-production promotion & release workflow
├── render.yaml                # Render Blueprint declarative 1-click deployment
├── docker-compose.yaml        # Development multi-app composition
├── docker-compose.prod.yml    # Production multi-stage Caddy composition
├── observability/             # Decoupled Observability Compose project
│   ├── docker-compose.yaml    # OpenTelemetry Collector, Prometheus, Loki, Tempo, Grafana
│   ├── otel-collector-config.yaml # OTLP pipelines to Tempo, Prometheus, and Loki
│   ├── prometheus.yml         # Prometheus scrape configuration
│   ├── loki-config.yaml       # Loki filesystem & TSDB storage configuration
│   ├── tempo-config.yaml      # Tempo local trace storage configuration
│   ├── .env.example           # Configurable port and container overrides
│   ├── README.md              # Observability guide, architecture & verification
│   └── grafana/
│       ├── dashboards/        # Pre-provisioned Golden Signals overview dashboard
│       └── provisioning/      # Automated datasources (Loki, Tempo, Prometheus) & dashboards
├── on-call-engineer/          # Autonomous On-Call Incident Responder
│   ├── poll-alerts.py         # Observability alert poller (runs every minute)
│   ├── payload-schema.json    # JSON schema for normalized incident payloads
│   ├── autonomy-policy.json   # Code-enforced autonomy levels & permissions
│   ├── prompt.md              # Prompt template for headless coding agent
│   ├── runbook.md             # Triage runbook for Prometheus alerts
│   ├── README.md              # On-call operating guide & commands
│   ├── scripts/               # Poller, agent invoker & verification scripts
│   └── cloud-simulator/       # Local AWS Serverless On-Call Simulator (SNS, Lambda, Fargate, S3)
├── openapi.yaml               # Root API contract
├── contracts/
│   └── openapi.yaml           # Frozen canonical contract
├── docs/
│   ├── spec.md                # Functional specification & scope
│   └── deployment/            # Production deployment playbooks & architecture
│       ├── README.md          # Deployment index & decision matrix
│       ├── render.md          # Render Blueprint & Terraform guide
│       ├── aws-terraform.md   # AWS EC2 Docker Compose Terraform guide
│       └── aws-cloudformation.md # AWS CloudFormation 1-click guide
├── cloudformation/
│   ├── aws-ec2-compose.yaml   # AWS CloudFormation (Dev Environment: 10.1.0.0/16)
│   └── aws-ec2-compose-prod.yaml # AWS CloudFormation (Production Copy: 10.0.0.0/16)
├── render.yaml                # Render Blueprint (Dev Environment)
├── render.prod.yaml           # Render Blueprint (Production Environment Copy)
├── terraform/
│   ├── aws/                   # AWS Terraform (Dev Environment: 10.1.0.0/16)
│   │   ├── versions.tf
│   │   ├── variables.tf
│   │   ├── vpc.tf
│   │   ├── security_groups.tf
│   │   ├── iam.tf
│   │   ├── user_data.sh       # Cloud-init bootstrapper
│   │   ├── ec2.tf
│   │   ├── eip.tf
│   │   ├── oidc.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.dev
│   ├── aws-prod/              # AWS Terraform (Production Environment Copy: 10.0.0.0/16)
│   │   ├── versions.tf
│   │   ├── variables.tf
│   │   ├── vpc.tf
│   │   ├── security_groups.tf
│   │   ├── iam.tf
│   │   ├── user_data.sh
│   │   ├── ec2.tf
│   │   ├── eip.tf
│   │   ├── oidc.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.prod
│   ├── render/                # Render Terraform (Dev Environment: free plan)
│   │   ├── versions.tf
│   │   ├── variables.tf
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.dev
│   └── render-prod/           # Render Terraform (Production Environment Copy: starter plan)
│       ├── versions.tf
│       ├── variables.tf
│       ├── main.tf
│       ├── outputs.tf
│       └── terraform.tfvars.prod
├── backend/
│   ├── Dockerfile             # Python 3.11 base image with healthchecks
│   ├── requirements.txt       # Backend dependencies
│   ├── pyproject.toml         # Pytest configuration
│   ├── app/                   # FastAPI application & routers
│   └── tests/                 # Backend pytest test suite
├── frontend/
│   ├── Dockerfile             # Multi-stage: dev, builder, prod (Caddy)
│   ├── Caddyfile              # Production Caddy 2 reverse proxy config
│   ├── package.json           # Frontend dependencies & scripts
│   ├── vite.config.ts         # Vite server, host & backend proxy config
│   └── src/                   # React components, UI views & services
└── e2e/
    ├── Dockerfile             # Microsoft Playwright v1.50 container
    ├── package.json           # Playwright dependencies
    ├── playwright.config.ts   # Test configuration targeting dev stack
    ├── helpers.ts             # Test reset helper and auth utilities
    ├── auth.spec.ts           # Authentication & account switching tests
    ├── groups.spec.ts         # Shared groups & member management tests
    ├── lifecycle-items.spec.ts# Renewal/maintenance/warranty CRUD & filters
    ├── reminders-digest.spec.ts# Reminders drawer & email digest tests
    └── spec-compliance.spec.ts# Comprehensive Section 6 acceptance journey
```

---

## 7. Cloud Deployment Automation (Dev & Production)

Execute all validations and formatting inside Docker without host dependencies:

- **Render**:
  - Dev Blueprint: [`render.yaml`](render.yaml) | Prod Blueprint Copy: [`render.prod.yaml`](render.prod.yaml)
  - Dev Terraform: [`terraform/render/`](terraform/render/) | Prod Terraform Copy: [`terraform/render-prod/`](terraform/render-prod/)
  - Validation: `make tf-validate-render` and `make tf-validate-render-prod`
- **AWS**:
  - Dev Terraform: [`terraform/aws/`](terraform/aws/) | Prod Terraform Copy: [`terraform/aws-prod/`](terraform/aws-prod/)
  - Dev CloudFormation: [`cloudformation/aws-ec2-compose.yaml`](cloudformation/aws-ec2-compose.yaml) | Prod CloudFormation Copy: [`cloudformation/aws-ec2-compose-prod.yaml`](cloudformation/aws-ec2-compose-prod.yaml)
  - Validation: `make tf-validate` (validates all Terraform environments) and `make cf-validate` (validates both CloudFormation templates)

---

## 8. Two-Stage Container Registry Pipeline (Amazon ECR)

The CI/CD pipeline decouples image creation from serving:

1. **Build Stage (`build-and-push-ecr`)**:
   - Compiles container images (`backend` and `frontend`).
   - Tags each image using the `YYYYMMDD-HHMMSS-shortsha` pattern (e.g. `20260818-163457-83242da`) and pushes to Amazon ECR.
   - Records the deployed image tag in AWS SSM Parameter Store (`/personal-lifecycle/${TARGET_ENV}/image_tag`).

2. **Deploy Stage (`deploy`)**:
   - Pulls pre-built images from Amazon ECR.
   - Serves containers via Docker Compose (`docker compose -f docker-compose.prod.yml up -d --no-build`). Zero image building occurs on the deployment host.
   - Validates live `/health` endpoint (HTTP 200).

3. **Dev to Production Image Promotion (`promote-dev-to-prod.yml`)**:
   - Discovers and pulls the currently deployed dev image from Amazon ECR.
   - Re-tags the verified dev image with the promotion timestamp tag (`YYYYMMDD-HHMMSS-shortsha`), semantic release tag (`vX.Y.Z`), and `prod-latest`.
   - Pushes promoted tags to ECR and deploys to production without building from source.

regularly commit code to git

<!-- BEGIN AWS Agent Toolkit rules -->
# AWS Guidance for the new AWS experience

This user has signed up for the new AWS experience. This experience lets you sign into AWS using a social provider and requires the following additional context.

Where this guidance conflicts with the project's own instructions, the project's instructions take precedence.

## Context

### Terminology:

- Say "project" instead of "account" — a project contains an AWS account and settings for sharing with other collaborators
- Say "team member" instead of "IAM user" — users are invited by email, not created or federated in IAM
- Say "AWS Settings" when referring to management tasks at [settings.aws.com](https://settings.aws.com/) (project management, billing, team members, spend limits). Users view their actual AWS resources in the AWS Management Console.
- Say "selected Region" when referring to the user's Region — not "home Region"
- The user has a managed IAM experience. This includes a managed service control policies (SCP) and resource control policies (RCP) that govern the use of AWS. They will still need to use IAM to create policies to let services work with each other. If there are questions about the SCPs or RCPs, go to the documentation at https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html

### Constraints:

- All projects share a single AWS Region determined by the user's contact address. Resources cannot be created in other Regions
- When developing:
  - MUST create all Regional resources in the project's assigned Region
  - You CAN create AWS WAF and Cloudwatch Logs resources in us-east-1 when there are global resources (like a global WAF instance) that require a connection to dependencies in us-east-1. You should not use these for any other reason, because resources in the selected Region will provide lower cost (due to no cross-Region traffic), increased availability (due to no cross-Region traffic), and easier manageability (due to not needing to look in another Region). When you need to do an inventory of resources, you need to look in both the selected Region and us-east-1 for Cloudwatch Logs or WAF resources.
  - MUST NOT attempt to create Lambda, API Gateway, or other Regional resources in any other Region
  - MUST direct users to confirm their Region in AWS Settings > View all projects > Overview > Additional Info > Region. If the user cannot confirm their Region, check in ~/.aws/config
  - MUST NOT use Lambda@Edge — excluded from both Lambda and CloudFront
  - MUST NOT use CloudFormation StackSets — no multi-account or multi-Region deployments
  - MUST NOT attempt cross-Region actions — no cross-Region replication for DynamoDB/S3/RDS, no multi-Region KMS keys
  - MUST NOT use Route 53 cross-Region routing — geolocation, latency-based, and failover routing policies are not available
  - CloudFront is a global service and its actions ARE allowed in `us-east-1`. A user can create a CloudFront distribution pointing to their project-region Lambda function URL or API Gateway. However, Lambda and API Gateway themselves MUST NOT be created in `us-east-1` — they must be in the project Region.
  - Reduced availability in `eu-north-1` specifically: Amazon Rekognition, Amazon Textract, Amazon Personalize, AWS App Runner are not available in that Region.
- IAM permissions for human access are managed by AWS. Don't assign roles to team members unless absolutely necessary
- The user may have a spend limit if they are on the paid plan. The limit that pauses their project if it's exceeded. If resources suddenly become inaccessible, ask if they have a spend limit configured. Only project owners can modify a spend limit.
- When developing:
  - MUST ask about spend limit status if the user reports sudden "Access Denied" errors on operations that previously worked
  - MUST direct users to check spend status in AWS Settings > Billing
  - MUST check if a user has upgraded their account to the paid plan
  - MUST ask the user if they want to clean up the successfully created resources or keep them to reduce cost
- The user sets up billing, creates spend limits, and retrieves and pays invoices in AWS Settings. The user creates budgets and optimizes their costs in the AWS Billing and Cost Management console
- Not all AWS services are available. If a service isn't working, do the following:
  1. Run the command `aws freetier get-account-plan-state`
  2. If accountPlanType": "FREE", check the [Free Tier supported services list](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html#supported-services-free-tier) next,
  3. If accountPlanType": "PAID", check the [Paid Tier supported services list](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html#supported-services-paid-plan).
  4. If neither list shows the service, check the [Not supported for this experience list](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html#unsupported-services). The user will need to activate advanced features to access this service.
- Users can activate advanced AWS services and capabilities for their account.
- Before starting a task, check whether a relevant AWS skill is available. Load the skill with retrieve_skill and prefer its guidance over general knowledge.

### Help level

- help_level (required): LOW, MEDIUM, or HIGH. While a user is building, you MUST ask the user: "How much guidance would you like from me? Low (I only flag security risks), medium (I ask a couple of clarifying questions if something seems off), or high (I explain what I'm doing, suggest alternatives, and flag best practices)."

You CAN update this rule file to save a user's help_level.

Constraints for each level:

**LOW:**

- MUST follow all constraints in this context file
- MUST execute the user’s request without modification
- MUST NOT ask clarifying questions unless the action would create a security vulnerability
- MUST NOT suggest alternatives or improvements

**MEDIUM:**

- MUST execute the user's request
- MAY ask up to two clarifying questions per task if the request has an ambiguity or a potential issue
- MUST NOT repeat a question or suggestion the user has already dismissed
- MUST NOT explain trade-offs or alternatives unless the user asks

**HIGH:**

- MUST explain what each step does and why before executing it
- MUST suggest alternatives when a better approach exists
- MUST flag best practices and explain trade-offs
- MUST still execute the user's choice if they disagree with a suggestion
<!-- END AWS Agent Toolkit rules -->


