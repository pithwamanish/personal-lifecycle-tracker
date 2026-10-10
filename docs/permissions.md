# Extension Pack Security & Permissions Policy

This document defines the security boundaries, authorization tiers, and permission constraints for AI agents interacting with this project.

---

## 1. Principle of Least Privilege

Autonomous AI agents and subagents operate under **strict read-preferred, bounded-write** constraints:
- **Default Stance**: Read-only observation and bounded analysis.
- **Write Actions**: Limited strictly to files inside the repository root.
- **Execution**: Restricted to containerized environments (`docker compose`, `docker run`) or allowlisted inspection commands.

---

## 2. Permission Tiers

| Tier | Scope | Permissions Granted | Authorization Requirement |
|------|-------|---------------------|---------------------------|
| **Tier 1 (Read-Only)** | File inspection, git log, OTel telemetry, metrics, MCP tool queries | Unrestricted within project bounds | Fully Autonomous |
| **Tier 2 (Safe Non-Destructive)** | Test execution, container startup (`docker compose up`), local build | Container execution permitted | Autonomous with Audit Log |
| **Tier 3 (Modifying Source)** | Code edits, test creation, configuration updates | Scoped to project files | Bounded Autonomy (Git-tracked) |
| **Tier 4 (Privileged / Destructive)** | Database schema dropping, hard resets, force pushing | **STRICTLY BLOCKED** | Requires Explicit Human Approval |

---

## 3. Allowlisted & Forbidden Commands

### Allowlisted Commands
- `docker compose ps` / `docker compose logs` / `docker compose up -d` / `docker compose down`
- `docker compose run --rm <service> <test_cmd>`
- `git status` / `git diff` / `git log`
- `curl -s http://localhost:<PORT>/health`
- `python3 mcp-server/server.py`

### Forbidden / Blocked Commands (Enforced by `agent-hooks/pre-tool-guardrail.sh`)
- `rm -rf /` or `rm -rf ~`
- `DROP DATABASE`, `TRUNCATE TABLE`, unconstrained `DELETE`
- `git push --force` to protected branches (`main`, `master`)
- Direct execution of unvetted host shell scripts outside repository boundaries

---

## 4. MCP Server Security & Tool Permissions

All Model Context Protocol tools declared in `mcp-server/mcp.json` operate with read-only inspection scopes:
1. `inspect_project_health`: Reads container status via Docker Compose; does not stop or mutate containers.
2. `inspect_openapi_contract`: Reads `contracts/openapi.yaml`; does not write or modify contracts.

---

## 5. Audit Logging

Every agent action and hook outcome is captured in `agent-hooks/audit.log` for post-run compliance review.
