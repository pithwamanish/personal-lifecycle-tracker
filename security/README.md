# Security, Audit & Hardening Index

This directory documents the security architecture, deterministic static application security testing (SAST), PR audit reports, agent permission boundaries, and AI data policies for the **Personal Lifecycle Tracker** system.

---

## Security Documentation Map

| Document | Purpose | Standard / Tool | Status |
|---|---|---|---|
| [`pr-audit.md`](pr-audit.md) | PR Security Review & Automated Gating | OWASP Top 10, Auth Boundaries | `VERIFIED` |
| [`deterministic-scan.md`](deterministic-scan.md) | Deterministic Static Analysis & CVE Audit | Semgrep, Bandit, npm audit, Trufflehog | `0 HIGH / 0 CRITICAL` |
| [`agent-extension-security.md`](agent-extension-security.md) | Agent Pack, MCP & Hook Security Analysis | Agent Plugins 1.0, Least Privilege | `COMPLIANT` |
| [`ai-tool-data-policy.md`](ai-tool-data-policy.md) | AI Tool Usage & Enterprise Data Governance | Human-in-the-Loop, Zero-Leakage Policy | `ENFORCED` |

---

## Automated Security Principles

1. **Zero Unauthenticated Access**:
   All lifecycle items and group endpoints require valid cryptographically signed JWT bearer tokens. Passwords are salted with `bcrypt` (work factor 12).
2. **Deterministic SAST in CI**:
   Static analysis runs before test execution. Any high or critical findings block pipeline advancement.
3. **Agent Sandboxing & Containment**:
   Headless AI coding agents operate within strict directory boundaries and must pass pre-tool execution guardrails (`com.google.antigravity/hooks/pre-tool-guardrail.sh`) before mutating files or running shell commands.
4. **Keyless Cloud Authentication**:
   GitHub Actions authenticates with AWS via OpenID Connect (OIDC) roles (`id-token: write`), eliminating permanent AWS access keys.
