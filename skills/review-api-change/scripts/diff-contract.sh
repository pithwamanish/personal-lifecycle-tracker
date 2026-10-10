#!/usr/bin/env bash
set -euo pipefail

# Diffs current openapi.yaml against git HEAD or main
CONTRACT_FILE="openapi.yaml"
if [ ! -f "${CONTRACT_FILE}" ] && [ -f "contracts/openapi.yaml" ]; then
  CONTRACT_FILE="contracts/openapi.yaml"
fi

if [ ! -f "${CONTRACT_FILE}" ]; then
  echo "ERROR: Contract file not found (checked openapi.yaml and contracts/openapi.yaml)" >&2
  exit 1
fi

echo "==> Reviewing API Contract changes in ${CONTRACT_FILE}..."
if git rev-parse --git-dir >/dev/null 2>&1; then
  git diff HEAD -- "${CONTRACT_FILE}" || true
else
  echo "Not inside a git repository; displaying contract summary:"
  head -n 25 "${CONTRACT_FILE}"
fi
