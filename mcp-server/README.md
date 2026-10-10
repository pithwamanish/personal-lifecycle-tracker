# Model Context Protocol (MCP) Server

This directory contains the project's scoped Model Context Protocol (MCP) server implementation, declared in root `mcp.json`.

---

## Purpose & Architecture

Rather than providing autonomous agents with broad, unconstrained system access, the MCP server provides a **scoped set of tools, resources, and prompts**:
- **Tools**: Controlled executable actions (e.g. `query_schema`, `verify_health`, `read_service_metrics`).
- **Resources**: Read-only structured data sources (e.g. database schemas, OpenAPI contracts, environment configs).
- **Prompts**: Standardized operational prompt templates for specialized workflows.

---

## Server Details

- **Entrypoint**: `server.py`
- **Transport**: Standard I/O (`stdio`) or streamable HTTP / SSE as configured in `mcp.json`.
- **Zero Plaintext Secrets**: Credentials must never be hardcoded in this server or in `mcp.json`. Use environment variables (`${VAR_NAME}`).

---

## Local Verification

Run the server inside Docker or using the standard test harness:

```bash
docker compose run --rm backend python mcp-server/server.py
```
