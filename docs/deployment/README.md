# Personal Lifecycle Tracker — Deployment & Infrastructure Guide

This directory contains the Infrastructure as Code (IaC) templates, configurations, and step-by-step operational playbooks for deploying the **Personal Lifecycle Tracker** across two completely independent environments:
1. **Development (`dev`)**: Uses the existing infrastructure baseline, configured for development testing, zero cost / free tier resources, isolated non-overlapping VPC networks (`10.1.0.0/16`), and dev service identifiers.
2. **Production (`production`)**: A second, independent copy of the infrastructure provisioned for high availability and production workloads, utilizing isolated VPC networks (`10.0.0.0/16`), production service identifiers, and production security policies.

---

## Environment Architecture Matrix

| Capability / Resource | Development Environment (`dev`) | Production Environment (`production`) |
|---|---|---|
| **Render Blueprint** | [`render.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/render.yaml) | [`render.prod.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/render.prod.yaml) / [`render-prod.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/render-prod.yaml) |
| **Render Services** | `personal-lifecycle-*-dev` | `personal-lifecycle-*-prod` |
| **Render Plan** | Free tier (`free`) | Starter tier (`starter`) |
| **Render Terraform** | [`terraform/render/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/render/) (`default = "dev"`) | [`terraform/render-prod/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/render-prod/) (`default = "production"`) |
| **AWS Terraform** | [`terraform/aws/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/aws/) | [`terraform/aws-prod/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/aws-prod/) |
| **AWS VPC CIDR** | `10.1.0.0/16` (Public Subnet: `10.1.1.0/24`) | `10.0.0.0/16` (Public Subnet: `10.0.1.0/24`) |
| **AWS CloudFormation**| [`cloudformation/aws-ec2-compose.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose.yaml) | [`cloudformation/aws-ec2-compose-prod.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose-prod.yaml) |
| **CI/CD Triggers** | Pushes to `dev`/`develop` or manual dispatch | Pushes to `main` or manual dispatch |
| **Local Compose** | `docker-compose.yaml` (Ports: `8003`, `3003`, `5434`) | `docker-compose.prod.yml` (Port: `8088`, Caddy Proxy) |

---

## Supported Deployment Options

| Target Platform | Tooling / IaC | Architecture Model | Cost / Tier | Guide Link |
|---|---|---|---|---|
| **Render (Dev)** | Render Blueprint (`render.yaml`) | Managed PostgreSQL + Docker Web Services (Backend + Caddy Frontend) | Free | [Render Deployment Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/render.md) |
| **Render (Prod)** | Render Blueprint (`render.prod.yaml`) | Managed PostgreSQL + Docker Web Services (Independent Copy) | Free / Starter | [Render Deployment Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/render.md) |
| **Render (IaC)** | Terraform (`terraform/render/` & `terraform/render-prod/`) | Declarative infrastructure management via Render Terraform Provider | Free / Starter | [Render Deployment Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/render.md) |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) | Parallel Tests + Docker Compose E2E + GitHub OIDC Auth + Multi-Env Render Deploy | Free Tier Eligible | [CI/CD Pipeline Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/ci-cd.md) |
| **Production Promotion** | GitHub Actions (`.github/workflows/promote-dev-to-prod.yml`) | Manual dev→production promotion, conflict check, test gates, SemVer tagging, GitHub Release & live deploy | Free Tier Eligible | [Production Promotion Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/ci-cd.md#7-dev-to-production-manual-promotion-workflow-promote-dev-to-prodyml) |
| **AWS (Dev)** | Terraform (`terraform/aws/`) | EC2 (`t3.micro`/Free Tier) + Elastic IP + SSM Session Manager (`10.1.0.0/16` VPC) | Free Tier Eligible (~$0/mo) | [AWS Terraform Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/aws-terraform.md) |
| **AWS (Prod)** | Terraform (`terraform/aws-prod/`) | EC2 (`t3.micro`/Free Tier) + Elastic IP + SSM Session Manager (`10.0.0.0/16` VPC) | Free Tier Eligible (~$0/mo) | [AWS Terraform Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/aws-terraform.md) |
| **AWS (CFN)** | CloudFormation (`cloudformation/`) | 1-Click CloudFormation Stacks (`aws-ec2-compose.yaml` and `aws-ec2-compose-prod.yaml`) | Free Tier Eligible (~$0/mo) | [AWS CloudFormation Guide](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/docs/deployment/aws-cloudformation.md) |

---

## Zero-Host-Runtime Tooling (via Docker)

In accordance with the **Zero-Host-Runtime Mandate**, you do not need Terraform, AWS CLI, Python, or Node installed on your local workstation. All validations, formatting, and operations can be executed via containerized Makefile targets:

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

# Validate CloudFormation templates
make cf-validate            # Validates both dev and prod templates
make cf-validate-dev        # Dev template
make cf-validate-prod       # Production copy template

# Test the local container stacks
make up                     # Local development stack (hot reload)
make prod-up                # Local production stack (Caddy reverse proxy)
make prod-ps
make prod-down
```

---

## Directory Layout

```
.
├── render.yaml                             # Render Blueprint (Dev Environment)
├── render.prod.yaml                        # Render Blueprint (Production Environment Copy)
├── render-prod.yaml                        # Alias for production blueprint
├── cloudformation/
│   ├── aws-ec2-compose.yaml                # AWS CloudFormation (Dev Environment: 10.1.0.0/16)
│   └── aws-ec2-compose-prod.yaml           # AWS CloudFormation (Production Copy: 10.0.0.0/16)
├── terraform/
│   ├── aws/                                # AWS Terraform (Dev Environment)
│   │   ├── versions.tf
│   │   ├── variables.tf                    # Default environment: dev, VPC: 10.1.0.0/16
│   │   ├── vpc.tf
│   │   ├── security_groups.tf
│   │   ├── iam.tf
│   │   ├── user_data.sh                    # Cloud-init Docker Compose bootstrapper
│   │   ├── ec2.tf
│   │   ├── eip.tf
│   │   ├── oidc.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars.dev
│   │   └── terraform.tfvars.example
│   ├── aws-prod/                           # AWS Terraform (Production Environment Copy)
│   │   ├── versions.tf
│   │   ├── variables.tf                    # Default environment: production, VPC: 10.0.0.0/16
│   │   ├── vpc.tf
│   │   ├── security_groups.tf
│   │   ├── iam.tf
│   │   ├── user_data.sh
│   │   ├── ec2.tf
│   │   ├── eip.tf
│   │   ├── oidc.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars.prod
│   │   └── terraform.tfvars.example
│   ├── render/                             # Render Terraform (Dev Environment)
│   │   ├── versions.tf
│   │   ├── variables.tf                    # Default environment: dev, plan: free
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars.dev
│   │   └── terraform.tfvars.example
│   └── render-prod/                        # Render Terraform (Production Environment Copy)
│       ├── versions.tf
│       ├── variables.tf                    # Default environment: production, plan: starter
│       ├── main.tf
│       ├── outputs.tf
│       ├── terraform.tfvars.prod
│       └── terraform.tfvars.example
└── docs/deployment/
    ├── README.md                           # This overview index
    ├── ci-cd.md                            # GitHub Actions CI/CD & Multi-Env deployment guide
    ├── render.md                           # Render Blueprint & Terraform guide (Dev & Prod)
    ├── aws-terraform.md                    # AWS Terraform execution guide (Dev & Prod)
    └── aws-cloudformation.md               # AWS CloudFormation execution guide (Dev & Prod)
```
