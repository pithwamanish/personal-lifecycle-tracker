# Project Agent Extension Pack Documentation

This project provides an **Agent Extension Pack** conforming to the [Agent Plugins Open Standard](https://agent-plugins.org/) (backed by AAIF and AWS). It bundles project instructions, reusable workflows, specialist personas, MCP tools, and security guardrails into a portable, cross-client extension layer.

---

## 1. Extension Pack Overview

```
project-root/
├── plugin.json                 # Agent Plugins v1.0.0 root specification manifest
├── agent-capabilities/         # Reusable procedural workflows and capabilities
│   └── sample-workflow/
│       ├── SKILL.md            # Capability instructions & task steps
│       └── scripts/            # Executable workflow automation
├── agent-hooks/                # Event interceptors & security guardrails
│   ├── hooks.json              # Hook event declarations
│   ├── pre-tool-guardrail.sh   # Pre-execution safety enforcement
│   └── post-tool-audit.sh      # Post-execution audit logging
├── mcp-server/                 # Model Context Protocol tools & server
│   ├── mcp.json                # MCP tool definitions and schemas
│   └── server.py               # Lightweight stdio MCP server
├── custom-agent/               # Specialist subagent definitions & system prompts
│   └── specialist.md           # Domain specialist role and execution pattern
└── docs/                       # Extension documentation & governance
    ├── agent-extension-pack.md # This guide & project instructions
    └── permissions.md          # Security boundaries & least privilege rules
```

---

## 2. Project Instructions for AI Agents

When interacting with this repository, AI agents (Claude Code, Cursor, Antigravity, Copilot, Bedrock) MUST observe the following rules:

1. **Check Plugin Manifest**:
   - Inspect `plugin.json` to discover registered tools, specialists, and hooks.
2. **Consult Permissions Policy**:
   - Read `docs/permissions.md` before executing any commands or making structural changes.
3. **Invoke Specialist Subagents**:
   - For domain audits or contract reviews, spawn or delegate to `custom-agent/specialist.md`.
4. **Utilize Reusable Workflows**:
   - Prefer capabilities declared in `agent-capabilities/` (e.g. `agent-capabilities/sample-workflow/SKILL.md`) over ad-hoc host commands.
5. **Comply with Guardrail Hooks**:
   - Every tool call is validated by `agent-hooks/pre-tool-guardrail.sh`. Attempting destructive actions (drops, deletes, force pushes) will be blocked immediately.

---

## 3. Registered Components

### A. Reusable Workflows (`agent-capabilities/`)
- **`sample-workflow`**: Health and database readiness check (`verify-health.sh`).

### B. Specialist Personas (`custom-agent/` or `plugins/`)
- **`project-specialist`**: Dedicated agent for schema validation, contract consistency, and deployment verification.

### C. MCP Server & Tools (`mcp-server/`)
- **`inspect_project_health`**: Probes running Docker containers and endpoints.
- **`inspect_openapi_contract`**: Summarizes `contracts/openapi.yaml`.

### D. Guardrails & Hooks (`agent-hooks/`)
- **`destructive-command-guardrail`**: Intercepts shell executions to reject destructive actions.
- **`audit-logger`**: Appends tool executions to `agent-hooks/audit.log`.

---

## 4. Verification & Testing

To verify the extension pack structure and compliance:
```bash
verify-extension-pack
```
