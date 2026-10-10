# Personal Lifecycle Tracker — Deployment Guide

This directory contains the Infrastructure as Code (IaC) templates, configurations, and step-by-step operational playbooks for deploying the **Personal Lifecycle Tracker** to production.

The application uses a 3-tier containerized architecture:
1. **Frontend**: React 19 + TypeScript, served by **Caddy 2** reverse proxy (handling static assets, SPA client-side routing, and reverse-proxying `/api/*` and `/health` to the backend).
2. **Backend**: FastAPI (Python 3.11), Uvicorn, SQLAlchemy, Pydantic v2.
3. **Database**: PostgreSQL 16 with automated table creation on boot.

---

## Supported Deployment Options

| Target Platform | Tooling / IaC | Architecture Model | Cost / Tier | Guide Link |
|---|---|---|---|---|
| **Render** | Render Blueprint (`render.yaml`) | Managed PostgreSQL + Docker Web Services (Backend + Caddy Frontend) | Free / Starter | [Render Deployment Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/render.md) |
| **Render** | Terraform (`terraform/render/`) | Declarative infrastructure management via Render Terraform Provider | Free / Starter | [Render Deployment Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/render.md) |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) | Parallel Tests + Docker Compose E2E + GitHub OIDC Auth + Render Deploy + Health Validation | Free Tier Eligible | [CI/CD Pipeline Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/ci-cd.md) |
| **AWS** | Terraform (`terraform/aws/`) | EC2 (`t3.micro`/Free Tier) + Elastic IP + SSM Session Manager + Production Docker Compose | Free Tier Eligible (~$0/mo) | [AWS Terraform Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/aws-terraform.md) |
| **AWS** | CloudFormation (`cloudformation/`) | 1-Click CloudFormation Stack (VPC, Security Group, EC2, Elastic IP, SSM) | Free Tier Eligible (~$0/mo) | [AWS CloudFormation Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/aws-cloudformation.md) |

---

## Zero-Host-Runtime Tooling (via Docker)

In accordance with the **Zero-Host-Runtime Mandate**, you do not need Terraform, AWS CLI, Python, or Node installed on your local workstation. All validations, formatting, and operations can be executed via containerized Makefile targets:

```bash
# Validate Terraform configurations
make tf-validate-aws
make tf-validate-render

# Format all Terraform files
make tf-fmt

# Validate CloudFormation template
make cf-validate

# Test the production container stack locally
make prod-up
make prod-ps
make prod-logs
make prod-down
```

---

## Directory Structure

```
.
├── render.yaml                             # Render Blueprint specification (1-click deploy)
├── cloudformation/
│   └── aws-ec2-compose.yaml                # AWS CloudFormation EC2 template
├── terraform/
│   ├── aws/                                # AWS Terraform module
│   │   ├── versions.tf
│   │   ├── variables.tf
│   │   ├── vpc.tf
│   │   ├── security_groups.tf
│   │   ├── iam.tf
│   │   ├── user_data.sh                    # Cloud-init Docker Compose bootstrapper
│   │   ├── ec2.tf
│   │   ├── eip.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.example
│   └── render/                             # Render Terraform module
│       ├── versions.tf
│       ├── variables.tf
│       ├── main.tf
│       ├── outputs.tf
│       └── terraform.tfvars.example
└── docs/deployment/
    ├── README.md                           # This overview index
    ├── ci-cd.md                            # GitHub Actions CI/CD & Render OIDC deployment guide
    ├── render.md                           # Render Blueprint & Terraform guide
    ├── aws-terraform.md                    # AWS Terraform execution guide
    └── aws-cloudformation.md               # AWS CloudFormation execution guide
```
