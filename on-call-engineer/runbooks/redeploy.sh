#!/usr/bin/env bash
# Rebuild and restart the backend application container from the current working tree.
# The telemetry stack (OTel Collector/Prometheus/Loki/Tempo/Grafana) and database remain running.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "==> [REDEPLOY] Rebuilding and restarting backend container..."
cd "${PROJECT_ROOT}"

docker compose up --build -d --wait --no-deps backend
docker compose ps backend

echo "==> [REDEPLOY] Backend container successfully updated and healthy."
