#!/usr/bin/env python3
"""Lightweight stdio Model Context Protocol (MCP) server for project inspection.

Zero-dependency standard library implementation compliant with MCP JSON-RPC
specifications.
"""

import json
import os
import subprocess
import sys


def read_message():
  line = sys.stdin.readline()
  if not line:
    return None
  return json.loads(line)


def write_message(obj):
  sys.stdout.write(json.dumps(obj) + "\n")
  sys.stdout.flush()


def tool_inspect_health(args):
  service = args.get("service")
  try:
    cmd = ["docker", "compose", "ps", "--format", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode == 0:
      output = proc.stdout.strip()
      return {
          "status": "success",
          "containers": output or "No active containers",
      }
    return {
        "status": "unknown",
        "message": "Docker Compose not running or available",
    }
  except Exception as e:
    return {"status": "error", "error": str(e)}


def tool_inspect_contract(args):
  contract_path = os.path.join(os.getcwd(), "contracts", "openapi.yaml")
  if not os.path.exists(contract_path):
    return {
        "status": "missing",
        "message": "No contracts/openapi.yaml found in project root",
    }
  try:
    with open(contract_path, "r", encoding="utf-8") as f:
      content = f.read(2048)  # Sample first 2KB
    return {
        "status": "found",
        "path": "contracts/openapi.yaml",
        "preview": content,
    }
  except Exception as e:
    return {"status": "error", "error": str(e)}


def main():
  while True:
    try:
      msg = read_message()
      if msg is None:
        break

      req_id = msg.get("id")
      method = msg.get("method")
      params = msg.get("params", {})

      if method == "initialize":
        write_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "project-mcp-server", "version": "1.0.0"},
            },
        })
      elif method == "tools/list":
        write_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "inspect_project_health",
                        "description": (
                            "Checks the status of project containers and API"
                            " endpoints"
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "service": {
                                    "type": "string",
                                    "description": (
                                        "Optional specific service to check"
                                    ),
                                }
                            },
                        },
                    },
                    {
                        "name": "inspect_openapi_contract",
                        "description": (
                            "Reads and summarizes endpoints from"
                            " contracts/openapi.yaml"
                        ),
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ]
            },
        })
      elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if tool_name == "inspect_project_health":
          res = tool_inspect_health(arguments)
        elif tool_name == "inspect_openapi_contract":
          res = tool_inspect_contract(arguments)
        else:
          res = {"error": f"Unknown tool: {tool_name}"}

        write_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(res, indent=2)}]
            },
        })
      elif method == "ping":
        write_message({"jsonrpc": "2.0", "id": req_id, "result": {}})
      else:
        write_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method {method} not found"},
        })
    except Exception as ex:
      write_message({
          "jsonrpc": "2.0",
          "id": None,
          "error": {"code": -32603, "message": str(ex)},
      })


if __name__ == "__main__":
  main()
