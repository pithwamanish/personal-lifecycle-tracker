"""Run headless, sandboxed coding agent as a first responder for an incident.

Safety is enforced via defense-in-depth:
  1. `--restricted` initializes the session with no code-running tools and ignores user settings.
  2. `--tools` explicitly allows only Read, Grep, Glob, Edit, Bash.
  3. `--allowedTools` and `--disallowedTools` constrain paths and bash commands.
  4. `--permission-mode dontAsk` + `--permission-prompts none` guarantee that anything unallowlisted
     is rejected without hanging.
  5. Budget cap `--max-budget-usd` limits spend per incident.
"""

import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

AGENT_BIN = os.getenv("RESPONDER_AGENT_BIN", "claude")
AGENT_TIMEOUT_SECONDS = int(os.getenv("RESPONDER_AGENT_TIMEOUT", "900"))
AGENT_MAX_BUDGET_USD = os.getenv("RESPONDER_MAX_BUDGET_USD", "2")

ALLOWED_TOOLS = [
    "Edit(./backend/app/**)",
    "Edit(./backend/tests/**)",
    "Bash(docker compose run --rm -T --no-deps backend pytest:*)",
    "Bash(on-call-engineer/runbooks/redeploy.sh)",
    "Bash(on-call-engineer/runbooks/verify-recovery.sh:*)",
    "Bash(git status:*)",
    "Bash(git diff:*)",
    "Bash(git log:*)",
]

DISALLOWED_TOOLS = [
    "Bash(git commit:*)",
    "Bash(git push:*)",
    "Bash(git reset:*)",
    "Bash(git checkout:*)",
    "Bash(docker compose down:*)",
    "Bash(rm -rf:*)",
]

_SESSION_VAR = re.compile(r"^CLAUDE(CODE$|_CODE_|_PID$|_EFFORT$)")
_KEEP_VARS = {"CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX"}


def _agent_env() -> dict:
    return {k: v for k, v in os.environ.items() if k in _KEEP_VARS or not _SESSION_VAR.match(k)}


def build_command() -> list[str]:
    return [
        AGENT_BIN,
        "-p",
        "--restricted",
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", "dontAsk",
        "--permission-prompts", "none",
        "--strict-mcp-config",
        "--max-budget-usd", AGENT_MAX_BUDGET_USD,
        "--tools", "Read,Grep,Glob,Edit,Bash",
        "--allowedTools", *ALLOWED_TOOLS,
        "--disallowedTools", *DISALLOWED_TOOLS,
    ]


def run(prompt: str, repo_root: Path, transcript_path: Path, simulation_answer: str | None = None) -> dict:
    """Run coding agent to completion, streaming events to transcript_path.

    Returns exit code, timing, model/tool metadata, cost, and parsed answer.
    """
    started = time.monotonic()

    # Simulation mode (used in test drills or CI environments without active LLM credentials)
    if (
        os.getenv("SIMULATE_AGENT", "false").lower() == "true"
        or os.getenv("EXECUTE_AGENT", "true").lower() == "false"
        or os.getenv("DRY_RUN", "false").lower() == "true"
        or simulation_answer is not None
    ):
        answer_text = simulation_answer or (
            "INCIDENT: test-simulated\n"
            "ROOT_CAUSE: Synthetic test defect triggered for validation\n"
            "FIX: backend/app/main.py\n"
            "TESTS: pytest passed\n"
            "ACTION: fixed\n"
            "SUMMARY: Synthetic incident simulated successfully."
        )
        answer_lines = [l for l in answer_text.splitlines() if l.strip()]
        last_line = answer_lines[-1] if answer_lines else ""

        with transcript_path.open("w") as f:
            f.write(json.dumps({"type": "system", "subtype": "init", "model": "simulation-model"}) + "\n")
            f.write(json.dumps({"type": "result", "result": answer_text, "total_cost_usd": 0.0, "num_turns": 1}) + "\n")

        return {
            "command": ["simulated-agent"],
            "exit_code": 0,
            "timed_out": False,
            "duration_s": 0.1,
            "model": "simulation-model",
            "permission_mode": "dontAsk",
            "tools": ["Read", "Edit", "Bash"],
            "num_turns": 1,
            "cost_usd": 0.0,
            "is_error": False,
            "permission_denials": [],
            "answer_text": answer_text,
            "last_line": last_line,
        }

    command = build_command()
    init_event, result_event = {}, {}

    with transcript_path.open("w") as transcript:
        process = subprocess.Popen(
            command,
            cwd=str(repo_root),
            env=_agent_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        timer = threading.Timer(AGENT_TIMEOUT_SECONDS, process.kill)
        timer.start()
        try:
            process.stdin.write(prompt)
            process.stdin.close()
            for line in process.stdout:
                transcript.write(line)
                transcript.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "system" and event.get("subtype") == "init":
                    init_event = event
                elif event.get("type") == "result":
                    result_event = event
            exit_code = process.wait()
        finally:
            timer.cancel()

    answer_text = (result_event.get("result") or "").strip()
    answer_lines = [line for line in answer_text.splitlines() if line.strip()]

    return {
        "command": command,
        "exit_code": exit_code,
        "timed_out": time.monotonic() - started >= AGENT_TIMEOUT_SECONDS,
        "duration_s": round(time.monotonic() - started, 1),
        "model": init_event.get("model", "unknown"),
        "permission_mode": init_event.get("permissionMode", "dontAsk"),
        "tools": init_event.get("tools", []),
        "num_turns": result_event.get("num_turns", 0),
        "cost_usd": result_event.get("total_cost_usd", 0.0),
        "is_error": result_event.get("is_error", False),
        "permission_denials": result_event.get("permission_denials", []),
        "answer_text": answer_text,
        "last_line": answer_lines[-1] if answer_lines else "",
    }
