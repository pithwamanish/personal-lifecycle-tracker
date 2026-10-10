# Agent Extension Pack Interactive Demo Script

This demo validates the end-to-end functionality of the Agent Extension Pack, testing the 9 durable mental model pillars:
`instructions` → `context` → `tools` → `permissions` → `reusable workflows` → `specialized agents` → `packaging and sharing` → `custom agent loops` → `audit trail`.

---

## 6-Step Demonstration Workflow

Follow these steps in an interactive coding agent session (Antigravity, Claude Code, Cursor, Copilot, Codex):

### Step 1: Agent Reads Project Instructions
- **Trigger**: Start a new agent session or prompt:
  ```text
  Inspect the project architecture, operational standards, and security boundaries.
  ```
- **Expected Agent Action**:
  - The agent reads `AGENTS.md` (or `CLAUDE.md`).
  - Confirms understanding of the zero-host-runtime mandate, container foundation, and project negative invariants.
- **Verification**: Agent states active rules and tools discovered without host probing.

---

### Step 2: Reusable Workflow Invocation
- **Trigger**:
  ```text
  Run the reusable workflow to review pending API changes or check project health.
  ```
- **Expected Agent Action**:
  - Discovers and loads `skills/review-api-change/SKILL.md` (or `skills/domain-workflow/SKILL.md`).
  - Executes the designated helper script (e.g. `scripts/diff-contract.sh` or `scripts/verify-health.sh`).
- **Verification**: Workflow outputs structured evaluation without polluting prompt context.

---

### Step 3: Specialized Subagent Execution
- **Trigger**:
  ```text
  Launch a specialized API reviewer subagent to audit the contract diff in contracts/openapi.yaml.
  ```
- **Expected Agent Action**:
  - The orchestrator spawns a subagent initialized with persona instructions from `custom-agent/specialist.md` (or `.bmad/architect.md`).
  - The subagent runs in an isolated context window with bounded permissions.
- **Verification**: Subagent returns findings to the main session and exits cleanly.

---

### Step 4: Model Context Protocol (MCP) Tool Call
- **Trigger**:
  ```text
  Query the project database schema or inspect registered endpoints using our MCP server.
  ```
- **Expected Agent Action**:
  - Agent queries the local MCP server declared in `mcp.json` (running `mcp-server/server.py`).
  - MCP tool returns scoped resources/tools (e.g. `inspect_schema`, `get_health`).
- **Verification**: Agent successfully queries real service telemetry or schema via standard MCP protocol.

---

### Step 5: Guardrail & Hook Enforcement
- **Trigger (Attempted Negative Invariant Violation)**:
  ```text
  Run a raw command to DROP TABLE users; or execute bare-metal npm install on the host.
  ```
- **Expected Agent Action**:
  - Lifecycle hook `com.google.antigravity/hooks/pre-tool-guardrail.sh` (or `agent-hooks/pre-tool-guardrail.sh`) intercepts the command.
  - The guardrail detects forbidden keywords (`DROP TABLE`, host runtimes) and terminates execution with a non-zero exit code.
  - `post-tool-audit.sh` records the blocked event in audit logs.
- **Verification**: Unsafe action is actively blocked and recorded in the audit trail.

---

### Step 6: Human Review of Final Diff
- **Trigger**:
  ```text
  Generate a summary diff of all proposed modifications for human approval.
  ```
- **Expected Agent Action**:
  - Agent prepares the final atomic diff and waits for explicit user confirmation before committing.
- **Verification**: Human operator reviews diff against `docs/permissions.md` and acceptance criteria.
