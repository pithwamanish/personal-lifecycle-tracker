# Domain Schema & Architectural References

This document records the architectural constraints, entity models, and domain rules derived from the project's specifications (`product-spec.md`) and API contracts (`openapi.yaml`).

## 1. Domain Entities
- Refer to `product-spec.md` for primary entity definitions, field validations, and entity life-cycles.
- Ensure all automated actions respect business validation invariants (e.g. status transition guards, tenant isolation).

## 2. API Contract Alignments
- Frozen OpenAPI specification: `openapi.yaml` (or `contracts/openapi.yaml`).
- All tool calls and automation scripts must target documented endpoints and respect parameter types.

## 3. Database & Storage Rules
- All mutations must be executed through application endpoints or versioned migration scripts.
- Direct ad-hoc SQL table alterations or deletions without migrations are strictly forbidden by `constitution.md`.
