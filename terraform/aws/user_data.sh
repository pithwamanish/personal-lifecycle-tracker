#!/usr/bin/env bash
set -euo pipefail

exec > >(tee -a /var/log/app-bootstrap.log) 2>&1
echo "=== Starting Personal Lifecycle Tracker Provisioning at $(date) ==="

# 1. System updates & prerequisites
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    git \
    make \
    jq

# 2. Install Docker Engine & Docker Compose Plugin
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$${VERSION_CODENAME}")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu || true

# 3. Prepare Application Directory
APP_DIR="/opt/personal-lifecycle-tracker"
mkdir -p "$APP_DIR"

echo "Cloning repository ${REPO_URL} (branch: ${REPO_BRANCH})..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git fetch origin
    git checkout "${REPO_BRANCH}"
    git pull origin "${REPO_BRANCH}"
else
    git clone --branch "${REPO_BRANCH}" "${REPO_URL}" "$APP_DIR"
fi

cd "$APP_DIR"

# 4. Generate Environment Configuration
cat <<EOF > "$APP_DIR/.env"
# Host port mapping
PROD_PORT=${APP_PORT}
BACKEND_PORT=8003
FRONTEND_PORT=3003
POSTGRES_PORT=5434

# Application environment
APP_ENV=${ENVIRONMENT}
PYTHONUNBUFFERED=1

# PostgreSQL credentials
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=lifecycle

# Database URL for backend
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/lifecycle

# CORS configuration
CORS_ORIGINS=*
EOF

chmod 600 "$APP_DIR/.env"
chown -R ubuntu:ubuntu "$APP_DIR"

# 5. Create Systemd Service for Auto-Start on System Boot
cat <<EOF > /etc/systemd/system/personal-lifecycle-tracker.service
[Unit]
Description=Personal Lifecycle Tracker Multi-Container Stack (${ENVIRONMENT})
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable personal-lifecycle-tracker.service

# 6. Authenticate to ECR, Pull Images from Registry and Serve (Zero Host Build)
echo "Authenticating to Amazon ECR via instance IAM role..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)
if [ -n "$AWS_ACCOUNT_ID" ]; then
    ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.${AWS_REGION}.amazonaws.com"
    echo "Logging into Amazon ECR: $ECR_REGISTRY..."
    aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "$ECR_REGISTRY" || true

    # Check for deployed image tag in SSM Parameter Store
    DEPLOYED_TAG=$(aws ssm get-parameter --name "/personal-lifecycle/${ENVIRONMENT}/image_tag" --query Parameter.Value --output text 2>/dev/null || true)
    if [ -n "$DEPLOYED_TAG" ]; then
        echo "Configuring deployed ECR image tag from SSM: $DEPLOYED_TAG"
        echo "BACKEND_IMAGE=$ECR_REGISTRY/${PROJECT_NAME}-backend-${ENVIRONMENT}:$DEPLOYED_TAG" >> "$APP_DIR/.env"
        echo "FRONTEND_IMAGE=$ECR_REGISTRY/${PROJECT_NAME}-frontend-${ENVIRONMENT}:$DEPLOYED_TAG" >> "$APP_DIR/.env"
    fi
fi

echo "Pulling container images from registry..."
if docker compose -f docker-compose.prod.yml pull; then
    echo "Images pulled successfully from container registry. Serving containers..."
    docker compose -f docker-compose.prod.yml up -d
else
    echo "Notice: Registry pull unavailable or first bootstrap; fallback to local container build..."
    docker compose -f docker-compose.prod.yml up -d --build
fi

# 7. Healthcheck Verification
echo "Verifying service health on port ${APP_PORT}..."
MAX_ATTEMPTS=30
ATTEMPT=0
until curl -fs "http://127.0.0.1:${APP_PORT}/health" > /dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
        echo "WARNING: Healthcheck did not pass after $MAX_ATTEMPTS attempts. Inspect container logs:"
        docker compose -f docker-compose.prod.yml ps
        docker compose -f docker-compose.prod.yml logs --tail 50
        break
    fi
    sleep 3
done

if [ "$ATTEMPT" -lt "$MAX_ATTEMPTS" ]; then
    echo "SUCCESS: Personal Lifecycle Tracker is healthy and running on port ${APP_PORT}!"
fi

echo "=== Provisioning Completed at $(date) ==="
