# Deploying Personal Lifecycle Tracker to AWS via Terraform

This guide covers deploying the **Personal Lifecycle Tracker** to Amazon Web Services (AWS) using **Terraform** across two independent environments:
1. **Development (`dev`)**: Located in [`terraform/aws/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/aws/), default environment `dev`, isolated VPC CIDR `10.1.0.0/16`.
2. **Production (`production`)**: Located in [`terraform/aws-prod/`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/terraform/aws-prod/), default environment `production`, isolated VPC CIDR `10.0.0.0/16`.

Each environment is provisioned as an isolated, Free-Tier eligible Amazon EC2 instance running the multi-container Docker Compose stack (`docker-compose.prod.yml`) with automated reverse proxying managed by Caddy 2.

---

## AWS Architecture Overview

```mermaid
flowchart TD
    Internet((Internet / User)) -->|HTTP :80 / HTTPS :443| IGW[Internet Gateway]
    IGW --> VPC[Isolated VPC: 10.1.0.0/16 (Dev) or 10.0.0.0/16 (Prod)]
    VPC --> Subnet[Public Subnet: 10.1.1.0/24 (Dev) or 10.0.1.0/24 (Prod)]
    Subnet --> SG[Security Group: 80, 443, 8088, 22]
    SG --> EIP[Elastic IP]
    EIP --> EC2["EC2 Instance (t3.micro - Free Tier)"]
    
    subgraph EC2["EC2 Instance"]
        SSM["AWS SSM Agent (No SSH Key Required)"]
        Docker["Docker Engine & Compose Plugin"]
        Systemd["systemd service: personal-lifecycle-tracker"]
        
        subgraph Containers["Docker Compose Network"]
            Caddy["Frontend Service (Caddy 2 + React 19) :80"]
            Backend["Backend Service (FastAPI) :8000"]
            DB[("PostgreSQL 16 :5432")]
            
            Caddy -->|/api & /health| Backend
            Backend --> DB
        end
    end
```

### Key Architectural Invariants
1. **Complete Environment Independence**:
   - Dev VPC CIDR: `10.1.0.0/16`, Subnet: `10.1.1.0/24`.
   - Production VPC CIDR: `10.0.0.0/16`, Subnet: `10.0.1.0/24`.
   - Non-overlapping CIDRs prevent IP collisions and allow cross-environment VPC peering if needed.
2. **Shared AWS Account OIDC Safety**: Both modules support `existing_oidc_provider_arn` to prevent duplicate GitHub Actions OIDC provider conflicts when deployed into the same AWS account.
3. **Free-Tier Eligible**: Runs on `t3.micro` or `t4g.micro` with 20 GB GP3 encrypted storage ($0/month under AWS Free Tier).
4. **Zero Open SSH Ports Needed**: Comes pre-configured with an IAM Role with `AmazonSSMManagedInstanceCore` for AWS Systems Manager Session Manager access.

---

## Deployment Instructions

### 1. Development Environment (`terraform/aws/`)

```bash
# Validate Dev configuration
make tf-validate-aws

# Generate execution plan for Dev
make tf-plan-aws

# Apply Dev infrastructure
make tf-apply-aws
```

Variables are configured in `terraform/aws/terraform.tfvars.dev`:
```hcl
aws_region   = "us-east-1"
project_name = "personal-lifecycle-tracker"
environment  = "dev"
vpc_cidr     = "10.1.0.0/16"
subnet_cidr  = "10.1.1.0/24"
instance_type= "t3.micro"
app_port     = 80
repo_branch  = "main"
```

---

### 2. Production Environment Copy (`terraform/aws-prod/`)

```bash
# Validate Production configuration
make tf-validate-aws-prod

# Generate execution plan for Production
make tf-plan-aws-prod

# Apply Production infrastructure
make tf-apply-aws-prod
```

Variables are configured in `terraform/aws-prod/terraform.tfvars.prod`:
```hcl
aws_region   = "us-east-1"
project_name = "personal-lifecycle-tracker"
environment  = "production"
vpc_cidr     = "10.0.0.0/16"
subnet_cidr  = "10.0.1.0/24"
instance_type= "t3.micro"
app_port     = 80
repo_branch  = "main"
```

---

## Verifying Deployment

Each environment outputs:
- `application_url`: Public HTTP entrypoint.
- `healthcheck_url`: Public `/health` endpoint.
- `instance_id`: EC2 Instance ID.
- `public_ip`: Elastic IP address.
- `ssm_session_command`: AWS CLI command to connect securely via AWS SSM.

```bash
# Test Dev health
curl -f http://<dev_public_ip>/health

# Test Production health
curl -f http://<prod_public_ip>/health
```

---

## Teardown & Clean Up

To destroy an environment and eliminate ongoing AWS charges:

```bash
# Destroy Dev
docker run --rm -it \
  -v $(PWD)/terraform/aws:/workspace \
  -w /workspace \
  -v $HOME/.aws:/root/.aws:ro \
  -e AWS_PROFILE=${AWS_PROFILE:-default} \
  hashicorp/terraform:1.7.5 destroy -var-file=terraform.tfvars.dev

# Destroy Production
docker run --rm -it \
  -v $(PWD)/terraform/aws-prod:/workspace \
  -w /workspace \
  -v $HOME/.aws:/root/.aws:ro \
  -e AWS_PROFILE=${AWS_PROFILE:-default} \
  hashicorp/terraform:1.7.5 destroy -var-file=terraform.tfvars.prod
```
