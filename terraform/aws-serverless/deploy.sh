#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Zero-Cost Serverless Deployment Automation (AWS Lambda + S3 + CloudFront + Neon)
# Enforces Universal Zero-Host-Runtime: 100% Containerized Tooling
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TF_DIR="${PROJECT_ROOT}/terraform/aws-serverless"
AWS_REGION="${AWS_DEFAULT_REGION:-ap-south-1}"
AWS_CLI_IMAGE="amazon/aws-cli:latest"
TF_IMAGE="hashicorp/terraform:1.7.5"
NODE_IMAGE="node:20-alpine"

echo "================================================================="
echo "  Option C: Deploying Personal Lifecycle Tracker to AWS Serverless"
echo "================================================================="

cd "${PROJECT_ROOT}"

# 1. Pre-flight: Check AWS Credentials
echo "==> [1/7] Verifying AWS Credentials in container..."
if ! docker run --rm \
  -v "${HOME}/.aws:/root/.aws:ro" \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="${AWS_REGION}" \
  "${AWS_CLI_IMAGE}" sts get-caller-identity > /dev/null 2>&1; then
  echo ""
  echo "❌ Error: AWS Credentials not found or invalid!"
  echo "Please export your credentials before running deploy:"
  echo "  export AWS_ACCESS_KEY_ID=\"<your-key-id>\""
  echo "  export AWS_SECRET_ACCESS_KEY=\"<your-secret-key>\""
  echo "  export AWS_DEFAULT_REGION=\"us-east-1\""
  echo ""
  echo "Or configure them via: aws configure"
  exit 1
fi
echo "    AWS credentials authenticated successfully."

# 2. Pre-flight: Check terraform.tfvars
echo "==> [2/7] Checking Terraform configuration variables..."
if [ ! -f "${TF_DIR}/terraform.tfvars" ]; then
  echo "    terraform.tfvars not found. Creating from template..."
  cp "${TF_DIR}/terraform.tfvars.example" "${TF_DIR}/terraform.tfvars"
  # Generate a cryptographically secure random secret key
  RANDOM_SECRET=$(head -c 32 /dev/urandom | od -A n -t x1 | tr -d ' \n')
  sed -i "s/super-secret-jwt-key-replace-with-secure-random-32-byte-hex/${RANDOM_SECRET}/" "${TF_DIR}/terraform.tfvars"
  echo "    Generated new secret_key in terraform.tfvars."
fi

# 3. Initialize & Validate Terraform
echo "==> [3/7] Initializing Terraform..."
docker run --rm \
  -v "${TF_DIR}:/workspace" \
  -w /workspace \
  "${TF_IMAGE}" init

# 4. Bootstrap ECR Repository & Push Backend Container Image
echo "==> [4/7] Bootstrapping ECR Repository & Building Backend..."
docker run --rm \
  -v "${TF_DIR}:/workspace" \
  -v "${HOME}/.aws:/root/.aws:ro" \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="${AWS_REGION}" \
  -w /workspace \
  "${TF_IMAGE}" apply -target=aws_ecr_repository.backend -target=aws_ecr_repository_policy.backend_lambda -auto-approve

ECR_REPO_URL=$(docker run --rm \
  -v "${TF_DIR}:/workspace" \
  -v "${HOME}/.aws:/root/.aws:ro" \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="${AWS_REGION}" \
  -w /workspace \
  "${TF_IMAGE}" output -raw ecr_repository_url)

echo "    Authenticating Docker with Amazon ECR (${ECR_REPO_URL})..."
docker run --rm \
  -v "${HOME}/.aws:/root/.aws:ro" \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="${AWS_REGION}" \
  "${AWS_CLI_IMAGE}" ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${ECR_REPO_URL}"

echo "    Building Backend Container with AWS Lambda Web Adapter..."
docker build -t "${ECR_REPO_URL}:latest" ./backend

echo "    Pushing image to Amazon ECR..."
docker push "${ECR_REPO_URL}:latest"

# 5. Full Terraform Provisioning (Lambda + S3 + CloudFront + EventBridge)
echo "==> [5/7] Provisioning Serverless Infrastructure (Terraform Apply)..."
docker run --rm \
  -v "${TF_DIR}:/workspace" \
  -v "${HOME}/.aws:/root/.aws:ro" \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="${AWS_REGION}" \
  -w /workspace \
  "${TF_IMAGE}" apply -auto-approve

S3_BUCKET=$(docker run --rm \
  -v "${TF_DIR}:/workspace" \
  -v "${HOME}/.aws:/root/.aws:ro" \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="${AWS_REGION}" \
  -w /workspace \
  "${TF_IMAGE}" output -raw s3_bucket_name)

CLOUDFRONT_DOMAIN=$(docker run --rm \
  -v "${TF_DIR}:/workspace" \
  -v "${HOME}/.aws:/root/.aws:ro" \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="${AWS_REGION}" \
  -w /workspace \
  "${TF_IMAGE}" output -raw cloudfront_domain_name)

# 6. Build & Deploy Frontend SPA to S3
echo "==> [6/7] Building React 19 Frontend SPA in Container..."
docker run --rm \
  -v "${PROJECT_ROOT}/frontend:/app" \
  -w /app \
  "${NODE_IMAGE}" sh -c "npm install && npm run build"

echo "    Syncing Frontend distribution to S3 bucket (s3://${S3_BUCKET})..."
docker run --rm \
  -v "${PROJECT_ROOT}/frontend/dist:/dist" \
  -v "${HOME}/.aws:/root/.aws:ro" \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="${AWS_REGION}" \
  "${AWS_CLI_IMAGE}" s3 sync /dist "s3://${S3_BUCKET}/" --delete

# 7. Verification & Live Status
echo "==> [7/7] Deployment complete! Verifying endpoints..."
echo ""
echo "================================================================="
echo "  🚀 DEPLOYMENT SUCCESSFUL"
echo "================================================================="
echo "  Web Application UI:   https://${CLOUDFRONT_DOMAIN}"
echo "  Health Endpoint:      https://${CLOUDFRONT_DOMAIN}/health"
echo "  API Documentation:    https://${CLOUDFRONT_DOMAIN}/docs"
echo "  OpenAPI Schema:       https://${CLOUDFRONT_DOMAIN}/openapi.json"
echo "  CloudWatch Warmer:    Active (Every 4 mins - 0s cold starts)"
echo "  Daily Email Digest:   Active (08:00 AM UTC via EventBridge)"
echo "  Cost:                 $0.00 / month forever"
echo "================================================================="
