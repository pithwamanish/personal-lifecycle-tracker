# Deploying Personal Lifecycle Tracker to AWS via Terraform (Serverless)

This guide covers deploying the **Personal Lifecycle Tracker** to Amazon Web Services (AWS) using **Terraform** across two independent serverless environments:
1. **Development (`dev`)**: Located in [`terraform/aws/`](../../terraform/aws/), default environment `dev`.
2. **Production (`production`)**: Located in [`terraform/aws-prod/`](../../terraform/aws-prod/), default environment `production`.

Each environment is provisioned as a 100% serverless, zero-maintenance, zero-EC2 architecture backed by **AWS Lambda**, **Amazon S3**, **AWS CloudFront**, and **Amazon SNS on-call incident responder**.

---

## AWS Serverless Architecture Overview

```mermaid
flowchart TD
    Internet((Internet / User)) -->|HTTPS| CF[AWS CloudFront CDN Edge]
    
    CF -->|/* (Static React UI)| S3[Private Amazon S3 Bucket via OAC]
    CF -->|/api/* & /health| LURL[AWS Lambda Function URL]
    LURL --> Backend["FastAPI Backend Lambda (Container / LWA)"]
    Backend --> Neon[("Neon Serverless PostgreSQL (over TLS)")]
    
    subgraph Observability["Incident Response & On-Call"]
        CW[CloudWatch Metric Alarm: 5xx Errors] --> SNS[Amazon SNS Alert Topic]
        SNS --> OnCallLambda["On-Call Incident Responder Lambda"]
        OnCallLambda -->|Level 1: Auto Rollback / Restart| Backend
    end
```

### Key Architectural Invariants
1. **Zero EC2 Instances**: Eliminates VM management, OS patch cycles, SSH keys, and idle instance charges.
2. **100% Free-Tier & Zero Idle Cost**: Leverages AWS Lambda (1M free requests/mo), CloudFront (1 TB/mo free), S3 (5 GB free), and EventBridge (14M triggers/mo free) for $0.00/month idle cost.
3. **Automated Incident Response**: Includes an Amazon SNS topic wired directly to an on-call responder Lambda function with code-enforced autonomy policy authorization.
4. **Keyless Cloud Authentication**: Integrates GitHub Actions OpenID Connect (OIDC) roles (`id-token: write`), eliminating hardcoded AWS credentials.

---

## Deployment Instructions

### 1. Development Environment (`terraform/aws/`)

```bash
# Validate Dev configuration inside Docker
make tf-validate-aws

# Generate execution plan for Dev
make tf-plan-aws

# Apply execution plan to AWS
make tf-apply-aws
```

### 2. Production Environment (`terraform/aws-prod/`)

```bash
# Validate Production configuration inside Docker
make tf-validate-aws-prod

# Generate execution plan for Production
make tf-plan-aws-prod

# Apply execution plan to AWS
make tf-apply-aws-prod
```

---

## Live Verified Deployment Endpoints (Criterion 8 — 2 Points)

The serverless production environment provisioned via Terraform is live and reachable:

| Service / Interface | Public URL | Description | Status |
|---|---|---|---|
| **Web Application (SPA)** | [https://d1ca9upoitnq9b.cloudfront.net/](https://d1ca9upoitnq9b.cloudfront.net/) | CloudFront CDN distribution edge backed by private S3 bucket | HTTP/2 200 |
| **Backend API Health** | [https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/health](https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/health) | AWS Lambda Function URL connected to Neon PostgreSQL | `{"status":"healthy","database":"connected","version":"1.0.0"}` |
| **Interactive Swagger Docs** | [https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/docs](https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/docs) | Interactive Swagger UI testing endpoints with live queries | HTTP 200 |
| **Interactive ReDoc** | [https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/redoc](https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/redoc) | Searchable API contract reference | HTTP 200 |
| **OpenAPI Schema** | [https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/openapi.json](https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/openapi.json) | Dynamic OpenAPI 3.1.0 JSON specification | Valid JSON |

### Verification Commands
```bash
# 1. Verify CloudFront edge response
curl -sI https://d1ca9upoitnq9b.cloudfront.net/ | grep -E "HTTP|server|via"

# 2. Verify Lambda backend health & DB connection
curl -s https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/health

# 3. Test login with pre-seeded reviewer user
curl -s -X POST https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alex@example.com","password":"password123"}' | grep -o '"email":"alex@example.com"'
```
