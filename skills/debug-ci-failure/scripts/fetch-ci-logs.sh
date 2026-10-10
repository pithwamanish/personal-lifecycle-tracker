#!/usr/bin/env bash
set -euo pipefail

# Inspects recent container logs or CI workflow runs
echo "==> Fetching recent container logs..."
if command -v docker >/dev/null 2>&1; then
  docker compose logs --tail 50 2>/dev/null || docker ps -a
else
  echo "Docker command unavailable"
fi
