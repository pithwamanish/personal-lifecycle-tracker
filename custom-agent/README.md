# Custom Agents & Specialized Subagents

This directory contains definitions and implementations for specialist subagents and custom agent loops.

---

## Interactive Coding Agents vs. Custom Agents

| Scenario | Interactive Coding Agent (Antigravity, Claude Code, Cursor) | Custom Autonomous Agent (`agent.py`) |
| :--- | :--- | :--- |
| **Primary Use** | Interactive feature planning, exploratory coding, iterative human-in-the-loop development | Headless CI/CD verification, scheduled triage, structured evaluation pipelines |
| **Context Window** | Conversational session with human guidance | Bounded single-objective loop with deterministic exit criteria |
| **Execution Trigger**| User terminal prompt or chat modal | Automated webhook, GitHub Action, cron schedule |
| **Permissions** | Dynamic human approvals for sensitive actions | Strict declarative policy matrix (`autonomy-policy.json` / `permissions.md`) |

---

## Multi-Agent Worktrees Pattern

When multiple subagents operate simultaneously:
1. **Isolated Contexts**: Each subagent executes in its own session context to prevent cognitive amnesia and context pollution.
2. **Git Worktrees**: Each subagent works in an isolated git worktree branch (e.g. `worktrees/task-101/`).
3. **Orchestrator Role**: The main session acts as the coordinator, managing task assignment, review gates, and serial merges into `main`.

---

## Contents

- `specialist.md`: Specialist subagent persona definition with explicit tool permissions and bounded scope.
- `agent.py`: Standalone script for non-interactive autonomous pipeline execution (e.g. CI/CD automated review or verification).
