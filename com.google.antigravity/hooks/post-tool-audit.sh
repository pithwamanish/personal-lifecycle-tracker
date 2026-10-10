#!/usr/bin/env bash
set -euo pipefail

# Post-Tool Execution Audit Logger
# Appends structured audit logs of agent operations for reviewability and compliance.

TOOL_NAME="${1:-unknown}"
STATUS="${2:-success}"
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

LOG_DIR="${AUDIT_LOG_DIR:-_docs}"
[ ! -d "${LOG_DIR}" ] && LOG_DIR="docs"
[ ! -d "${LOG_DIR}" ] && mkdir -p "${LOG_DIR}"

LOG_FILE="${LOG_DIR}/agent-audit.log"
echo "[${TIMESTAMP}] tool=${TOOL_NAME} status=${STATUS}" >> "${LOG_FILE}"

# Guardrail verification check
if echo "${TOOL_NAME} ${STATUS}" | grep -qiE "rm[[:space:]]+-(r|f|rf)|DROP[[:space:]]+TABLE"; then
  echo "WARNING [AUDIT BLOCKED]: Destructive operation flagged during post-execution audit." >&2
  exit 1
fi

exit 0
