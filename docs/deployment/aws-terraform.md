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
