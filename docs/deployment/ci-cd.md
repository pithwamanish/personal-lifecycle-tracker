# CI/CD Pipeline & Automated Render Deployment Guide

This guide details the continuous integration and continuous deployment (CI/CD) pipeline for the **Personal Lifecycle Tracker** implemented via GitHub Actions ([`.github/workflows/ci.yml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/.github/workflows/ci.yml)).

---

## 1. Pipeline Architecture

```mermaid
flowchart TD
    subgraph Trigger["Pipeline Triggers"]
        PR["Pull Request to main or dev"]
        PushDev["Push to dev / develop -> Deploy Dev"]
        PushMain["Push to main -> Deploy Production Copy"]
        Dispatch["Workflow Dispatch (Select Env: dev / production)"]
    end

    subgraph ParallelTests["Phase 1: Parallel Unit & Contract Tests"]
        direction LR
        BackendJob["test-backend\n- Backend Container Build\n- FastAPI Pytest Suite\n- SQLite In-Memory Isolation"]
        FrontendJob["test-frontend\n- Frontend Container Build\n- TypeScript Static Typecheck\n- Vitest Component & Unit Tests"]
    end

    subgraph ComposeStack["Phase 2: Docker Compose Integration & E2E"]
        direction TB
        BuildStack["docker compose build"]
        StartStack["docker compose up -d (db, backend, frontend)"]
        WaitHealth["Wait for Backend Healthcheck :8003/health"]
        IntegTests["PostgreSQL Integration Tests (Pytest)"]
        E2ETests["Playwright E2E Tests (17 User Journeys)"]
        TearDown["docker compose down -v"]

        BuildStack --> StartStack --> WaitHealth --> IntegTests --> E2ETests --> TearDown
    end

    subgraph DeployGate["Phase 3: Multi-Environment Render Deployment"]
        direction TB
        ResolveEnv["Resolve TARGET_ENV\n(main -> production, dev -> dev)"]
        OIDCAuth["GitHub OIDC Token Exchange\n(id-token: write)\nAssume AWS IAM Role"]
        FetchSecrets["Fetch Render Credentials\n(AWS Secrets Manager / SSM)"]
        TriggerRender["Trigger Render Deployment\n(Dev or Production Service)"]
        ValidateHealth["Poll & Validate Environment Health Endpoint\n(Dev or Prod Frontend :80/health)"]

        ResolveEnv --> OIDCAuth --> FetchSecrets --> TriggerRender --> ValidateHealth
    end

    Trigger --> ParallelTests
    BackendJob --> ComposeStack
    FrontendJob --> ComposeStack
    ComposeStack --> DeployGate
```

---

## 2. Key Architectural Invariants

### A. Parallel Test Execution
To optimize feedback loops and token consumption:
- The **Backend Unit Test Job** (`test-backend`) and **Frontend Unit Test Job** (`test-frontend`) run simultaneously in parallel without interdependencies.
- Unit tests use zero host dependencies: both execute strictly inside Docker containers via `docker compose run --rm --no-deps`.

### B. Full Docker Compose Stack Verification
- Integration tests require a live, running database and API stack.
- The `integration-and-e2e` job starts the complete Compose topology (`db`, `backend`, `frontend`), waits for the backend `/health` endpoint to report HTTP 200, and sequentially executes:
  1. **PostgreSQL Integration Tests** (`backend/tests/integration/`): 27 end-to-end integration workflows covering authentication, cascades, group collaboration, and daily digest generation.
  2. **Playwright E2E Tests** (`e2e/`): 17 browser tests verifying complete user flows in headless Chromium.

### C. Keyless Cloud Authentication (GitHub OIDC)
- In compliance with enterprise security standards, static, long-lived deployment credentials are never hardcoded in GitHub Actions.
- GitHub Actions mints an OpenID Connect (OIDC) JWT token (`id-token: write`).
- The pipeline authenticates against AWS STS using `aws-actions/configure-aws-credentials@v4` with a least-privilege IAM role.
- Once authenticated, the job retrieves the Render deployment hook or API token dynamically from **AWS Secrets Manager** (`personal-lifecycle/render`) or **AWS SSM Parameter Store**.
- Fallback support is provided for direct GitHub repository secrets if operating outside AWS IAM.

### D. Automated Health Endpoint Validation
- Triggering a deployment is only half the release contract: the pipeline must verify that the deployed service actually boots, connects to the database, and serves traffic.
- The pipeline enters a resilient polling loop querying the live Render healthcheck endpoint (e.g., `https://personal-lifecycle-frontend.onrender.com/health`):
  - Checks every 10 seconds for up to 30 attempts (5 minutes).
  - Verifies HTTP 200 OK status code.
  - Inspects the JSON body to verify `"status": "healthy"` and database connectivity.
  - Fails the build if the health endpoint fails to stabilize within the threshold.

---

## 3. GitHub Secrets Configuration Matrix

Configure these secrets under **Settings > Secrets and variables > Actions** in your GitHub repository:

| Secret Name | Required? | Purpose | Example Value |
|---|---|---|---|
| `RENDER_OIDC_ROLE_ARN` | Recommended | AWS IAM Role ARN assumed via GitHub Actions OIDC | `arn:aws:iam::123456789012:role/personal-lifecycle-tracker-github-oidc-render-deployer-production` |
| `AWS_ROLE_TO_ASSUME` | Optional | Alternative alias for the OIDC IAM role ARN | `arn:aws:iam::123456789012:role/...` |
| `AWS_REGION` | Optional | AWS Region where secrets are stored | `us-east-1` (default) |
| `RENDER_DEPLOY_HOOK_URL` | Optional | Render 1-click Deploy Hook URL (direct fallback) | `https://api.render.com/deploy/srv-c1234567890abcdef?key=secretkey` |
| `RENDER_API_KEY` | Optional | Render API Key for REST API deployment | `rnd_abcdef1234567890` |
| `RENDER_SERVICE_ID` | Optional | Render Service ID targeted for deployment | `srv-c1234567890abcdef` |
| `RENDER_HEALTH_URL` | Optional | Custom live healthcheck URL to validate | `https://personal-lifecycle-frontend.onrender.com/health` |
| `STRICT_HEALTH_CHECK` | Optional | Enforce pipeline failure on healthcheck timeout (`true` / `false`) | `true` (default: `true`) |

---

## 4. Provisioning the GitHub OIDC Role via Terraform

The repository includes a ready-to-use Terraform module ([`terraform/aws/oidc.tf`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/aws/oidc.tf)) that creates:
1. The **GitHub OIDC Identity Provider** (`token.actions.githubusercontent.com`).
2. The **IAM Role** scoped strictly to your GitHub repository with `sts:AssumeRoleWithWebIdentity`.
3. An **IAM Policy** granting access to `personal-lifecycle/render` in Secrets Manager and SSM.

### Steps to Provision:

1. Edit `terraform/aws/terraform.tfvars`:
   ```hcl
   enable_github_oidc = true
   github_repo        = "your-username/your-repo-name"
   ```

2. Validate and apply inside Docker:
   ```bash
   make tf-validate-aws
   make tf-plan-aws
   ```

3. Note the output `github_oidc_role_arn`:
   ```text
   github_oidc_role_arn = "arn:aws:iam::123456789012:role/personal-lifecycle-tracker-github-oidc-render-deployer-production"
   ```

4. Store your Render deploy credentials in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret \
     --name personal-lifecycle/render \
     --secret-string '{"deploy_hook_url":"https://api.render.com/deploy/srv-xxx?key=yyy"}'
   ```

---

## 5. Local Validation with `act`

You can validate the pipeline syntax and test jobs locally before pushing:

```bash
# Validate workflow syntax with dry run
rtk act -n -W .github/workflows/ci.yml

# Run backend test job locally
rtk act -j test-backend -W .github/workflows/ci.yml

# Run frontend test job locally
rtk act -j test-frontend -W .github/workflows/ci.yml
```

---

## 6. End-to-End Verification Checklist

- [x] Backend and Frontend unit tests execute in parallel.
- [x] Docker Compose stack builds cleanly without host tools.
- [x] Integration tests pass against PostgreSQL 16 container.
- [x] Playwright E2E suite passes all 17 user journeys.
- [x] GitHub OIDC role assumption exchanges temporary credentials without static keys.
- [x] Render deployment triggered via Deploy Hook or REST API.
- [x] Health check polling loop validates live HTTP 200 and `"status": "healthy"`.
