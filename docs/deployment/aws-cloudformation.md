# Deploying Personal Lifecycle Tracker to AWS via CloudFormation (Serverless)

This guide covers deploying the **Personal Lifecycle Tracker** to Amazon Web Services using **AWS CloudFormation** across two independent serverless environments:
1. **Development Environment (`dev`)**: [`cloudformation/aws-serverless-lambda.yaml`](../../cloudformation/aws-serverless-lambda.yaml) — Default environment `dev`, 100% serverless with Lambda + S3 + CloudFront + SNS on-call responder.
2. **Production Environment Copy (`production`)**: [`cloudformation/aws-serverless-lambda-prod.yaml`](../../cloudformation/aws-serverless-lambda-prod.yaml) — Default environment `production`, independent copy with CloudWatch alarms and automated on-call responder.

Both templates deploy self-contained, Free-Tier eligible infrastructure stacks with **zero EC2 instances, zero servers to maintain, and $0.00/month idle cost**.

---

## Comparison Matrix

| Property | Development (`aws-serverless-lambda.yaml`) | Production (`aws-serverless-lambda-prod.yaml`) |
|---|---|---|
| **Default Stack Name** | `personal-lifecycle-tracker-dev` | `personal-lifecycle-tracker-prod` |
| **Environment Parameter** | `dev` | `production` |
| **Backend Compute** | AWS Lambda Function URL (`512 MB`) | AWS Lambda Function URL (`512 MB`) |
| **Frontend CDN** | CloudFront CDN + Private S3 Origin (OAC) | CloudFront CDN + Private S3 Origin (OAC) |
| **Database** | Neon Serverless PostgreSQL (over TLS) | Neon Serverless PostgreSQL (over TLS) |
| **On-Call Incident Responder** | Amazon SNS + Lambda Responder Function | Amazon SNS + Lambda Responder Function |
| **Idle Cost** | **$0.00 / month** | **$0.00 / month** |

---

## Deployment Option 1: AWS Management Console (1-Click Upload)

1. **Log in to the AWS Console**:
   Navigate to the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation).

2. **Create Stack**:
   - Click **"Create stack"** -> **"With new resources (standard)"**.
   - Under *Prerequisite - Prepare template*, choose **"Choose an existing template"**.
   - Under *Template source*, choose **"Upload a template file"**.
   - Select:
     - For Dev: [`cloudformation/aws-serverless-lambda.yaml`](../../cloudformation/aws-serverless-lambda.yaml)
     - For Production: [`cloudformation/aws-serverless-lambda-prod.yaml`](../../cloudformation/aws-serverless-lambda-prod.yaml)
   - Click **Next**.

3. **Specify Stack Details**:
   - **Stack name**: `personal-lifecycle-tracker-dev` (or `personal-lifecycle-tracker-prod`)
   - **Environment**: `dev` or `production`
   - **DatabaseUrl**: Your Neon serverless postgres pooled connection string
   - **SecretKey**: Secure JWT signing key (at least 32 characters)
   - Click **Next**.

4. **Review and Acknowledge**:
   - Check the box: **"I acknowledge that AWS CloudFormation might create IAM resources."**
   - Click **Submit**.

---

## Deployment Option 2: Containerized Makefile Validation & Deployment

In accordance with the **Zero-Host-Runtime Mandate**, validate and deploy inside Docker without host dependencies:

```bash
# Validate both dev and prod CloudFormation templates
make cf-validate

# Deploy Dev Environment via CloudFormation
make cf-deploy-dev

# Deploy Production Environment via CloudFormation
make cf-deploy-prod

# Check Stack Deployment Status
make cf-status-dev
make cf-status-prod
```
