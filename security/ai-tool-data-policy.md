# AI Tool & Data Governance Policy

**Project**: Personal Lifecycle Tracker  
**Governance Scope**: Developers, Operators, Coding Agents (Antigravity, Claude Code, Cursor, Copilot, Codex)  
**Effective Date**: 2026 Cohort Standard  
**Compliance Requirement**: Mandatory for all contributors and automated subagents

---

## 1. Core Principles

1. **Human-in-the-Loop Authority**:
   AI coding assistants are force multipliers and pair programmers, not sovereign decision-makers. All pull requests, production deployments, and architecture modifications require human verification and explicit approval.
2. **Zero Plaintext Secret Transmission**:
   Developers and agents are strictly forbidden from pasting real user credentials, production API keys, database connection URIs with embedded passwords, or customer PII into prompts or LLM context windows.
3. **Reproducibility & Verification Mandate**:
   Every line of AI-generated code must be accompanied by automated unit, integration, or end-to-end tests that pass inside containerized environments (`docker compose`).

---

## 2. Permitted AI Tool Usage

| Tool Category | Permitted Usage | Prohibited Usage |
|---|---|---|
| **Interactive Coding Agents** (Antigravity, Claude Code, Cursor) | Brainstorming specs, writing boilerplate, generating tests, debugging errors, refactoring | Committing directly to production branches without testing or peer review |
| **Autonomous Incident Responders** (`on-call-engineer/`) | Polling alert webhooks, inspecting telemetry, reproducing bugs in tests, generating candidate patches | Dropping production tables, scaling down live infrastructure, modifying IAM roles |
| **Model Context Protocol (MCP)** | Querying health status, reading OpenAPI contracts via stdio | Providing unconstrained bash execution to remote untrusted models |

---

## 3. Data Classification & Redaction Rules

- **Public Data (Green)**: OpenAPI contracts, public documentation, open-source dependencies, test fixtures. Allowed in any LLM context.
- **Internal Engineering Data (Yellow)**: Application source code, architectural schemas, mock database seed scripts. Allowed with enterprise-grade models under zero-data-retention agreements.
- **Restricted Confidential Data (Red)**: Production customer data, database backup dumps, AWS private keys, JWT signing keys. **STRICTLY PROHIBITED** from AI tool input.

---

## 4. Code Review & Verification Protocol

Before merging any AI-generated code:
1. **Visual Diff Inspection**: Run `git diff` to review all modified files for unintended side effects or hallucinated dependencies.
2. **Deterministic Build Verification**: Run `make test` inside Docker to prove zero regression.
3. **Security Audit**: Verify that newly introduced endpoints enforce authentication and parameter validation against `contracts/openapi.yaml`.
