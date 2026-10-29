#!/usr/bin/env bash
# Verifies service recovery by issuing HTTP requests to specified endpoints.
# Fails immediately if any target endpoint responds with 5xx or fails to respond.
#
# Usage: verify-recovery.sh [/health] [/api/v1/items ...]
set -euo pipefail

BASE_URL="http://127.0.0.1:${BACKEND_PORT:-8003}"
ATTEMPTS="${VERIFY_ATTEMPTS:-3}"
PATHS=("$@")

if [ "${#PATHS[@]}" -eq 0 ]; then
  PATHS=("/health")
fi

echo "==> [VERIFY-RECOVERY] Checking endpoint recovery against ${BASE_URL} (Attempts: ${ATTEMPTS})..."

failed=0
for path in "${PATHS[@]}"; do
  # Validate safe endpoint path format (prevent injection/traversal)
  if [[ ! "$path" =~ ^/[A-Za-z0-9_./{}~-]+$ ]]; then
    echo "REJECTED invalid path format: ${path}"
    failed=1
    continue
  fi

  endpoint_ok=0
  for attempt in $(seq 1 "${ATTEMPTS}"); do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "${BASE_URL}${path}" || true)"
    echo "  Attempt ${attempt}: GET ${path} -> HTTP ${code}"
    if [[ "$code" =~ ^[23]..$ ]]; then
      endpoint_ok=1
      break
    elif [[ "$code" == "401" || "$code" == "403" || "$code" == "404" ]]; then
      # Client error is valid response (service is up and processing requests)
      endpoint_ok=1
      break
    else
      sleep 1
    fi
  done

  if [ "${endpoint_ok}" -ne 1 ]; then
    echo "ERROR: Endpoint ${path} failed recovery check (Code: ${code})"
    failed=1
  fi
done

if [ "$failed" -ne 0 ]; then
  echo "RESULT: NOT RECOVERED"
  exit 1
fi

echo "RESULT: RECOVERED"
exit 0
