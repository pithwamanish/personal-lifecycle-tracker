#!/usr/bin/env bash
set -euo pipefail

# Git Pre-Commit Security Hook
# Executes fast deterministic secret detection & Semgrep SAST on staged files before commit.

echo "================================================================"
echo "          RUNNING PRE-COMMIT SECURITY & SAST AUDIT              "
echo "================================================================"

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "${STAGED_FILES}" ]; then
  exit 0
fi

# 1. Check for actual hardcoded secret values (excluding the hook script itself and example/test files)
SUSPICIOUS_ASSIGNMENTS='(AWS_SECRET_ACCESS_KEY\s*[:=]\s*["'\''][A-Za-z0-9/+=]{16,}["'\'']|ghp_[A-Za-z0-9]{36}|BEGIN (RSA|EC|OPENSSH) PRIVATE KEY)'
if git diff --cached | grep -v "pre-commit" | grep -v "example" | grep -v "test" | grep -E "${SUSPICIOUS_ASSIGNMENTS}" >/dev/null 2>&1; then
  echo "SECURITY ERROR: Detected suspected hardcoded secret in staged diff!"
  echo "Review your staged files before committing."
  exit 1
fi

# 2. Run containerized Semgrep SAST if backend files are modified
if echo "${STAGED_FILES}" | grep -E "^backend/" >/dev/null 2>&1; then
  echo "==> Backend changes detected. Running Semgrep SAST..."
  if command -v docker >/dev/null 2>&1; then
    docker run --rm -v "$(pwd):/src" returntocorp/semgrep semgrep --config=p/python --config=p/secrets --config=p/jwt --error /src/backend || {
      echo "SECURITY ERROR: Semgrep SAST scan failed! Fix security issues before committing."
      exit 1
    }
  fi
fi

echo "OK: Pre-commit security audit passed cleanly."
exit 0
