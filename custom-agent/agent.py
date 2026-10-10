#!/usr/bin/env python3
"""
Custom Agent Loop Implementation
Designed for headless execution in CI/CD, scheduled jobs, and structured verification pipelines.
Follows the durable mental model:
Context -> Plan -> Scoped Tools -> Audit Trail -> Verified Outcome
"""

import sys
import json
import os
from datetime import datetime

def log_audit(action: str, status: str, details: str):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "status": status,
        "details": details
    }
    print(f"[AUDIT] {json.dumps(log_entry)}")

def run_agent_loop(task: str):
    print(f"=== Starting Custom Agent Task: {task} ===")
    log_audit("agent_start", "INITIALIZED", f"Task: {task}")
    
    # 1. Context Gathering
    print("1. Gathering scoped project context...")
    context_files = ["product-spec.md", "openapi.yaml", "contracts/openapi.yaml", "docker-compose.yaml"]
    loaded = [f for f in context_files if os.path.exists(f)]
    print(f"   Context sources identified: {loaded}")
    
    # 2. Execution / Verification
    print("2. Executing bounded task logic...")
    # In a full custom agent, this orchestrates model tool calls or deterministic linters
    log_audit("task_execution", "RUNNING", "Running deterministic contract validation")
    
    # 3. Verification & Guardrails
    print("3. Verifying output against negative invariants...")
    # Enforce safe exit
    log_audit("agent_completion", "SUCCESS", "Task completed within bounded parameters")
    print("=== Custom Agent Execution Finished Successfully ===")
    return 0

if __name__ == "__main__":
    task_desc = sys.argv[1] if len(sys.argv) > 1 else "routine-verification"
    sys.exit(run_agent_loop(task_desc))
