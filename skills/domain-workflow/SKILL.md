---
name: domain-workflow
description: Domain-specific procedural workflow aligned with project specifications and API contracts.
version: 1.0.0
---

# Domain Workflow Instructions

This skill provides a reusable procedural workflow customized for the project's domain entities and operations.

## Purpose & Scope
- Automates verification of domain logic and entity state transitions.
- Executes safe pre-flight inspections before database schema migrations or batch operations.
- Validates live endpoints against the frozen `openapi.yaml` contract.

## When to Use
- When executing domain verification routines during testing or deployment.
- When inspecting entity integrity or performing diagnostic checks against live services.

## Instructions & Execution
1. Inspect the target entities defined in `product-spec.md`.
2. Execute the verification script:
   ```bash
   ./skills/domain-workflow/scripts/verify-health.sh
   ```
3. Validate API contract conformance against `openapi.yaml`.
4. Consult `references/schema-notes.md` for entity boundaries, constraints, and data models.
