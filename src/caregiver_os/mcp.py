"""Model Context Protocol (MCP) stdio server wrapper with Consent Gates."""

from __future__ import annotations

import json
import sys
from typing import Any

from .ai import explain_shift
from .services import today_summary
from .store import Store

# List of tools declared to the MCP client
TOOLS = [
    {
        "name": "list_today",
        "description": "Get a summary of today's care recipient details, upcoming appointments, due medications, and recent incidents.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_care_plan",
        "description": "Retrieve the clinical care plan guidelines and protocols.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "explain_last_shift",
        "description": "Generate an AI summary explaining the latest caregiver shift log.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lang": {"type": "string", "description": "Language code: 'en' (default) or 'ro'"}
            }
        }
    },
    {
        "name": "add_medication",
        "description": "Add a new medication. (Write operation - requires caregiver approval).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of medication"},
                "dose": {"type": "string", "description": "Dose details, e.g. '20mg' or '1 tablet'"},
                "times": {"type": "string", "description": "Comma-separated HH:MM times, e.g. '09:00, 21:00'"},
                "instructions": {"type": "string", "description": "Usage instructions"},
                "refill_at": {"type": "integer", "description": "Days left threshold for refill alerts"}
            },
            "required": ["name", "dose"]
        }
    },
    {
        "name": "deactivate_medication",
        "description": "Deactivate an active medication by ID. (Write operation - requires caregiver approval).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "med_id": {"type": "string", "description": "UUID of the medication to deactivate"}
            },
            "required": ["med_id"]
        }
    },
    {
        "name": "add_appointment",
        "description": "Add a clinical/medical appointment. (Write operation - requires caregiver approval).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "Doctor name or clinic provider"},
                "at": {"type": "string", "description": "ISO 8601 date-time string, e.g. '2026-06-01T14:30:00'"},
                "purpose": {"type": "string", "description": "Purpose of the visit"},
                "location": {"type": "string", "description": "Location details"}
            },
            "required": ["provider", "at"]
        }
    },
    {
        "name": "complete_appointment",
        "description": "Mark an appointment as completed. (Write operation - requires caregiver approval).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "appt_id": {"type": "string", "description": "UUID of the appointment to complete"}
            },
            "required": ["appt_id"]
        }
    },
    {
        "name": "log_incident",
        "description": "Report an incident occurring during the active shift. (Write operation - requires caregiver approval).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["fall", "confusion", "missed_meal", "medication_refusal", "other"]},
                "severity": {"type": "string", "enum": ["info", "warning", "alert"]},
                "description": {"type": "string", "description": "Detailed incident notes"}
            },
            "required": ["kind", "description"]
        }
    }
]


def send_response(msg_id: int | str | None, result: dict[str, Any]) -> None:
    """Print standard JSON-RPC response to stdout."""
    resp = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": result
    }
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()


def send_error(msg_id: int | str | None, code: int, message: str) -> None:
    """Print standard JSON-RPC error to stdout."""
    resp = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {
            "code": code,
            "message": message
        }
    }
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()


def handle_tool_call(name: str, arguments: dict[str, Any], store: Store) -> dict[str, Any]:
    """Execute read tool directly, or route write tools through the consent gate."""
    # 1. Read Tools (Execute Immediately)
    if name == "list_today":
        try:
            summary = today_summary(store)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(summary.model_dump(mode="json"), indent=2)
                    }
                ]
            }
        except RuntimeError as e:
            return {
                "content": [{"type": "text", "text": f"Error: {e}"}]
            }

    elif name == "get_care_plan":
        versions = store.list_careplan_versions()
        if not versions:
            plan_text = "No care plan configured."
        else:
            versions.sort(key=lambda x: x.version, reverse=True)
            plan_text = f"Care Plan (v{versions[0].version}):\n\n{versions[0].markdown}"
        return {
            "content": [{"type": "text", "text": plan_text}]
        }

    elif name == "explain_last_shift":
        handoffs = sorted(store.list_handoffs(), key=lambda x: x.shift_start, reverse=True)
        if not handoffs:
            return {"content": [{"type": "text", "text": "No shifts logged yet."}]}
        
        lang = arguments.get("lang", "en")
        summary_md = explain_shift(handoffs[0], store, lang=lang)
        return {
            "content": [{"type": "text", "text": summary_md}]
        }

    # 2. Write Tools (Consent Gate routing)
    elif name in ["add_medication", "deactivate_medication", "add_appointment", "complete_appointment", "log_incident"]:
        approval_id = store.add_pending_approval(name, arguments)
        gate_msg = (
            f"[PENDING_APPROVAL] The requested action '{name}' requires manual caregiver consent.\n"
            f"Approval ID: {approval_id}\n"
            f"Please approve this action in the Caregiver OS Web UI under the 'AI Approvals' tab, "
            f"or via the CLI using: caregiver-os approvals approve {approval_id}"
        )
        return {
            "content": [{"type": "text", "text": gate_msg}],
            "isPending": True,
            "approval_id": str(approval_id)
        }

    else:
        raise ValueError(f"Unknown tool: {name}")


def run_mcp_server() -> None:
    """Main stdio loop parsing JSON-RPC messages from MCP clients."""
    store = Store()
    
    # Set stdin/stdout binary-safe encoding fallback if needed
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            req = json.loads(line)
        except Exception:
            send_error(None, -32700, "Parse error")
            continue

        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            send_response(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {
                    "name": "caregiver-os",
                    "version": "2026.5.24"
                }
            })
            
        elif method == "tools/list":
            send_response(msg_id, {"tools": TOOLS})
            
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result = handle_tool_call(tool_name, tool_args, store)
                send_response(msg_id, result)
            except Exception as e:
                send_error(msg_id, -32603, f"Internal error: {e}")
                
        elif method == "notifications/initialized":
            # Ignore client initialized lifecycle ping
            continue
        else:
            send_error(msg_id, -32601, f"Method not found: {method}")
