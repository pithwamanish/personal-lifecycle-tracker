# Personal Lifecycle Tracker — Project Constitution & Immutable Invariants

**Version:** 1.0.0  
**Status:** Approved & Immutable  
**Scope:** Universal Repository Law (AI Agents, Subagents & Contributors)

---

## 1. Core Mission & Inviolable Boundaries

The Personal Lifecycle Tracker manages **Renewals**, **Maintenance**, and **Warranties** across independent accounts and collaborative groups. All development, refactoring, and automated changes are bound by the following negative invariants and non-negotiable architectural constraints.

---

## 2. Immutable Negative Invariants

1. **Strict Project Directory Confinement**:
   - Zero directory traversal: Reads, writes, searches, and subprocess executions MUST NEVER escape the project root directory.
   - Traversing to parent directories (`..`) or adjacent workspaces is an immediate security violation.

2. **Universal Zero-Host-Runtime Mandate**:
   - The host machine is strictly a headless container runner.
   - Zero host runtimes permitted: No direct host executions of `node`, `npm`, `npx`, `python`, `pip`, `pytest`, `cargo`, `go`.
   - All compilation, testing, formatting, and server executions MUST run strictly inside isolated Docker containers.

3. **Contract-First Freeze (`contracts/openapi.yaml`)**:
   - Zero API drift: The OpenAPI 3.0.3 specification in `contracts/openapi.yaml` is the immutable single source of truth.
   - No backend route or frontend client may introduce or mutate request/response shapes, headers, or query parameters without prior contract freeze approval.

4. **Multi-Tenant Data Isolation & Persistence**:
   - No cross-tenant data leaks: Users may only view and mutate their own items or items belonging to shared groups in which they hold active membership.
   - Group item ownership persistence: When a group member departs or is removed, shared group items remain with the group.
   - Account deletion cascading: Deleting a user account cascade-deletes personal items, owned groups, and associated group records cleanly.

5. **Closed Schema & Least-Privilege Agent Extension Pack**:
   - Agent manifest `plugin.json` adheres strictly to the closed schema defined in Agent Plugins 1.0/1.1 (zero arbitrary inline component schemas).
   - MCP tools run with strictly scoped filesystem boundaries within the project root.
   - Safety hooks (`com.google.antigravity/hooks/`) enforce pre-tool command filtering and audit logging on every tool invocation.

---

## 3. Mandatory Verification Gates

Prior to releasing changes or advancing lifecycle stages:
- `docker compose run --rm backend pytest`: 100% backend unit and integration test pass rate.
- `docker compose run --rm frontend npm test`: 100% Vitest component test pass rate.
- `docker compose run --rm frontend npm run lint`: 0 TypeScript compiler errors.
- `verify-repo-contents .`: 100% Expected Repository Contents checklist compliance.
- `evaluate-extension-pack .`: 100% Agent Extension Pack conformance scorecard.
- `validate-environment .`: 100% Meta-Environment compliance verification.
