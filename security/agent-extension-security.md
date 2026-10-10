# Agent Extension Pack & MCP Security Analysis

**Component**: Agent Extension Pack (`plugin.json`, `mcp.json`, `skills/`, `mcp-server/`, `custom-agent/`, `agent-hooks/`)  
**Standard**: Agent Plugins 1.0/1.1 Open Standard & Agent Capabilities Standard  
**Evaluation Status**: `AUDITED & SECURE — 100% CONFORMANCE`

---

## 1. Threat Modeling for Coding Agents

Autonomous and interactive AI coding agents possess file reading, editing, and terminal execution capabilities. Without strict architectural boundaries, coding agents introduce several attack vectors:
1. **Prompt Injection / Jailbreaking**: Malicious inputs tricking the agent into executing arbitrary system commands.
2. **Blast-Radius Overreach**: Agents deleting databases, editing production credentials, or dropping tables.
3. **Privilege Escalation**: Modifying root-level files, `.git/` metadata, or parent directories outside the project boundary.
4. **Supply Chain Corruption**: Unchecked package installation from unverified sources.

---

## 2. Implemented Defense-in-Depth Controls

### A. Pre-Tool Safety Guardrails (`agent-hooks/pre-tool-guardrail.sh`)
Every tool call and shell execution triggered by coding agents passes through a deterministic interceptor:
- **Destructive File Deletion Blocking**: Detects and aborts commands containing `rm -rf`, `rm -f /`, `rmdir`.
- **Database Destructive Mutation Blocking**: Intercepts unmigrated SQL operations (`DROP TABLE`, `DROP DATABASE`, `TRUNCATE TABLE`, unbounded `DELETE FROM`).
- **Plaintext Secret Injection Blocking**: Halts tool executions introducing plaintext AWS or database secrets into project files.

### B. Standard Stdio MCP Server Isolation (`mcp-server/server.py`)
- **Transport Security**: The MCP server operates strictly over standard input/output (`stdio`), completely eliminating open network ports, unauthorized HTTP listening sockets, or external network attack surfaces.
- **Filesystem Containment**: All relative paths are constrained within the project repository root. Path traversal attempts (`../`) are detected and rejected.
- **Strict JSON-RPC Schema**: Inputs to tools like `inspect_project_health` and `inspect_openapi_contract` are typed and sanitized against JSON schemas.

### C. Principle of Least Privilege (`docs/permissions.md`)
Permissions granted to subagents and autonomous responders follow least-privilege policies:
- **Read Permissions**: Read-only access to source code, contracts, logs, and metrics.
- **Write Permissions**: Restricted to domain logic in `backend/app/`, frontend views in `frontend/src/`, and tests.
- **Prohibited Write Targets**: Prohibited from modifying `.github/workflows/`, production Terraform state files, or `.env` credentials without explicit human approval.

### D. Audit Logging (`agent-hooks/post-tool-audit.sh`)
Every tool execution records an audit log entry in `_docs/agent-audit.log` containing:
- ISO 8601 UTC timestamp
- Tool name and invocation arguments
- Execution status (`success`, `failure`, `blocked`)
- Exit code
