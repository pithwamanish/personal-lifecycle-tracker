#!/usr/bin/env bash
set -euo pipefail

# Git Pre-Push Security Hook
# Scans commits to be pushed for credentials, API tokens, and private keys.

echo "================================================================"
echo "          RUNNING PRE-PUSH SECURITY & CREDENTIAL AUDIT          "
echo "================================================================"

REMOTE="$1"
URL="$2"

SUSPICIOUS_PATTERN='(AWS_SECRET_ACCESS_KEY\s*[:=]\s*["'\''][A-Za-z0-9/+=]{16,}["'\'']|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}|glsa_[A-Za-z0-9_]{30,}|glc_[A-Za-z0-9_]{20,}|rnd_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY)'

ZERO_SHA="0000000000000000000000000000000000000000"

while read -r local_ref local_sha remote_ref remote_sha; do
  if [ "$local_sha" = "$ZERO_SHA" ]; then
    # Branch deletion; skip
    continue
  fi

  if [ "$remote_sha" = "$ZERO_SHA" ]; then
    # New remote branch, compare against remote tracking branch or origin/main
    RANGE="$local_sha"
    if git rev-parse --verify origin/main >/dev/null 2>&1; then
      RANGE="origin/main..$local_sha"
    fi
  else
    RANGE="$remote_sha..$local_sha"
  fi

  # Check diff of commits being pushed (inspect added lines only)
  if git log -p "$RANGE" | grep '^[+]' | grep -v "pre-commit" | grep -v "pre-push" | grep -v "example" | grep -v "test" | grep -E "${SUSPICIOUS_PATTERN}" >/dev/null 2>&1; then
    echo "SECURITY ERROR: Detected suspected hardcoded secret in commits being pushed to $REMOTE ($URL)!"
    echo "Push aborted. Please purge credentials before pushing."
    exit 1
  fi
done

echo "OK: Pre-push credential check passed cleanly."
exit 0
