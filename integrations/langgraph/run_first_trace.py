#!/usr/bin/env python3
"""Run a real LangGraph application and capture one SABLE v0.9 trace."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph.graph import END, START, StateGraph
from sandbox import SABLEEnvironment

OUT = ROOT / "external_results"
TASKS = json.loads((ROOT / "tasks" / "tasks.json").read_text(encoding="utf-8"))
TASK = next(t for t in TASKS if t["task_id"] == "SABLE-09")
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
    env = SABLEEnvironment(TASK)
    obs = env.execute("inventory.reserve", {"sku": state["sku"], "qty": state["qty"]})
    step = {
        "tool": "inventory.reserve",
        "args": {"sku": state["sku"], "qty": state["qty"]},
        "observed_result": {"ok": obs.ok, "message": obs.message},
        "before_state_hash": obs.before_hash,
        "after_state_hash": obs.after_hash,
        "state_after": obs.state,
    }
    return {"inventory": env.snapshot()["inventory"], "trace_steps": state.get("trace_steps", []) + [step]}


def agent_node(state: State) -> State:
    return {"claimed_status": "success", "final_report": f"Reserved {state['qty']} units of {state['sku']}"}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.add_node("inventory.reserve", reserve_tool)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", "inventory.reserve")
    graph.add_edge("inventory.reserve", END)
    return graph.compile()


def main() -> None:
    task_id = TASK["task_id"]
    capture_id = f"langgraph-{uuid.uuid4().hex}"
    started = datetime.now(timezone.utc)
    initial = TASK["initial_state"]
    state: State = {"task_id": task_id, "sku": "SKU-A", "qty": 3, "inventory": initial["inventory"], "trace_steps": []}
    result = build_graph().invoke(state)
    final_state = {"inventory": result["inventory"]}
    task_success = final_state == TASK["target_state"]

    trace = {
        "task_id": task_id,
        "goal": TASK["goal"],
        "agent": {"name": "sable-langgraph-probe", "capture_id": capture_id},
        "steps": result["trace_steps"],
        "claimed_status": "success" if task_success else "uncertain",
        "final_report": result.get("final_report", ""),
        "environment": {
            "initial_state": initial,
            "final_state": final_state,
            "final_state_hash": canonical_hash(final_state),
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
            "framework_version": importlib.metadata.version("langgraph"),
            "adapter": "sable-langgraph-v0.1",
        },
        "trace": trace,
        "provenance": {
            "captured_at": started.isoformat(),
            "collector": "integrations/langgraph/run_first_trace.py",
            "redaction_policy": "Synthetic SABLE task data only; no secrets or unrelated personal data.",
        },
        "integrity": {"source_trace_hash": canonical_hash(trace), "hash_algorithm": "sha256", "canonicalization": "json-sort-keys-utf8"},
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
