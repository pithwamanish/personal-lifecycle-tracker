---
name: "review-api-change"
description: "Audits pending API changes against frozen contracts (contracts/openapi.yaml) to detect breaking changes."
version: "1.0.0"
---

# Review API Change Workflow

Use this skill when modifying, adding, or removing HTTP endpoints, query parameters, or payload schemas.

## Workflow Steps:

1. **Inspect Frozen Contract**:
   - Read `contracts/openapi.yaml` (or `openapi.yaml`).
2. **Execute Contract Diff**:
   - Run `scripts/diff-contract.sh` to extract changes between the current branch and main.
3. **Audit Against Breaking Changes Guide**:
   - Consult `references/breaking-changes-guide.md`.
   - Verify that no required fields are added to existing request bodies without defaults.
   - Verify that no existing endpoints or status codes are removed without deprecation notice.
4. **Report & Socratic Gate**:
   - If breaking changes are detected, pause and request confirmation before committing.
