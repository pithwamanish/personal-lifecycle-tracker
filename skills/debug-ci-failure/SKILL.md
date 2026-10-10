---
name: "debug-ci-failure"
description: "Diagnoses and remediates automated test and build failures in containerized CI environments."
version: "1.0.0"
---

# Debug CI Failure Workflow

Use this skill when local tests pass but CI pipelines fail, or when local `act` runs report errors.

## Workflow Steps:

1. **Collect CI Telemetry**:
   - Run `scripts/fetch-ci-logs.sh` to extract the failing job step and stderr.
2. **Consult Common CI Patterns**:
   - Inspect `references/common-ci-failures.md` for environmental discrepancies (missing env vars, container timing, unmigrated schemas).
3. **Reproduce Locally in Container**:
   - Never debug on host. Run `docker compose run --rm backend pytest` (or project test runner).
4. **Formulate Minimal Safe Fix**:
   - Fix the root cause with zero host runtime assumptions.
