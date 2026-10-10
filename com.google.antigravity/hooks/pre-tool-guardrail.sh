#!/usr/bin/env bash
set -euo pipefail

# Pre-Tool Execution Safety Guardrail
# Intercepts agent tool calls and enforces non-negotiable negative invariants from constitution.md

TOOL_NAME="${1:-}"
TOOL_ARGS="${2:-}"

# 1. Block destructive file deletion commands
if echo "${TOOL_ARGS}" | grep -qiE "rm[[:space:]]+-(r|f|rf|fr)[[:space:]]+(\/|[[:space:]]|\.)|rmdir"; then
  echo "ERROR [GUARDRAIL BLOCK]: Destructive recursive deletion command detected in arguments." >&2
  exit 1
fi

# 2. Block destructive database mutations without migrations
if echo "${TOOL_ARGS}" | grep -qiE "DROP[[:space:]]+(TABLE|DATABASE|SCHEMA)|TRUNCATE[[:space:]]+TABLE|DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z0-9_]+[[:space:]]*(;|$)"; then
  echo "ERROR [GUARDRAIL BLOCK]: Unbounded destructive database mutation blocked by safety policy." >&2
  exit 1
fi

# 3. Block hardcoded secret insertions
if echo "${TOOL_ARGS}" | grep -qiE "(AWS_SECRET_ACCESS_KEY|PRIVATE_KEY|DATABASE_PASSWORD)[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_\-\+]{8,}['\"]"; then
  echo "ERROR [GUARDRAIL BLOCK]: Plain-text credentials detected in tool invocation." >&2
  exit 1
fi

exit 0
