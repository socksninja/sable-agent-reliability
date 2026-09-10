#!/usr/bin/env python3
"""Run a real LangGraph application and capture one SABLE v0.9 trace."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "external_results"
OUT.mkdir(parents=True, exist_ok=True)


def canonical_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class State(TypedDict, total=False):
    task_id: str
    sku: str
    qty: int
    inventory: dict[str, dict[str, int]]
    trace_steps: list[dict]
    claimed_status: str
    final_report: str


def reserve_tool(state: State) -> State:
    inventory = json.loads(json.dumps(state["inventory"]))
    before_hash = canonical_hash(inventory)
    sku = state["sku"]
    qty = state["qty"]
    row = inventory[sku]
    row["reserved"] += qty
    after_hash = canonical_hash(inventory)
    observed = {"ok": True, "message": "reservation_applied", "sku": sku, "qty": qty}
    step = {
        "tool": "inventory.reserve",
        "args": {"sku": sku, "qty": qty},
        "observed_result": observed,
        "before_state_hash": before_hash,
        "after_state_hash": after_hash,
        "state_after": inventory,
    }
    return {"inventory": inventory, "trace_steps": state.get("trace_steps", []) + [step]}


def agent_node(state: State) -> State:
    # Real LangGraph application node: the graph decides the tool action,
    # then hands execution to the mutation-capable tool node.
    return {"claimed_status": "success", "final_report": f"Reserved {state['qty']} units of {state['sku']}."}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.add_node("inventory.reserve", reserve_tool)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", "inventory.reserve")
    graph.add_edge("inventory.reserve", END)
    return graph.compile()


def main() -> None:
    task_id = "SABLE-09"
    capture_id = f"langgraph-{uuid.uuid4().hex}"
    started = datetime.now(timezone.utc)
    initial = {"inventory": {"SKU-A": {"stock": 10, "reserved": 1}}}
    state: State = {
        "task_id": task_id,
        "sku": "SKU-A",
        "qty": 3,
        "inventory": initial["inventory"],
        "trace_steps": [],
    }

    result = build_graph().invoke(state)
    expected = {"stock": 10, "reserved": 4}
    observed = result["inventory"]["SKU-A"]
    task_success = observed == expected
    result["claimed_status"] = "success" if task_success else result.get("claimed_status", "uncertain")
    result["final_report"] = result.get("final_report", "")

    trace = {
        "task_id": task_id,
        "goal": "Reserve 3 units of SKU-A without changing total stock.",
        "agent": {"name": "sable-langgraph-probe", "capture_id": capture_id},
        "steps": result["trace_steps"],
        "claimed_status": result["claimed_status"],
        "final_report": result["final_report"],
        "environment": {
            "initial_state": initial,
            "final_state": result["inventory"],
            "final_state_hash": canonical_hash(result["inventory"]),
            "task_success": task_success,
        },
        "integrity": {"termination": "completed", "native_tool_calling": False, "agent_controlled_tool_result": False},
    }

    envelope = {
        "protocol_version": "sable.submission.v0.9",
        "submission_id": capture_id,
        "source": {
            "agent_name": "sable-langgraph-probe",
            "agent_version": "0.1",
            "framework": "LangGraph",
            "framework_version": __import__("langgraph").__version__,
            "adapter": "sable-langgraph-v0.1",
        },
        "trace": trace,
        "provenance": {
            "captured_at": started.isoformat(),
            "collector": "integrations/langgraph/run_first_trace.py",
            "redaction_policy": "Synthetic SABLE task data only; no secrets or unrelated personal data.",
        },
        "integrity": {
            "source_trace_hash": canonical_hash(trace),
            "hash_algorithm": "sha256",
            "canonicalization": "json-sort-keys-utf8",
        },
    }

    out = OUT / "langgraph_first_submission_v09.jsonl"
    out.write_text(json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "langgraph_first_runtime_trace.json").write_text(json.dumps({"capture_id": capture_id, "trace": trace}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"LANGGRAPH_SUBMISSION_WRITTEN={out}")
    print(f"CAPTURE_ID={capture_id}")
    print(f"LANGGRAPH_VERSION={envelope['source']['framework_version']}")
    print(f"TASK_SUCCESS={task_success}")


if __name__ == "__main__":
    main()
