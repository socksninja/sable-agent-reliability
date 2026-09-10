#!/usr/bin/env python3
"""Run a real LangGraph runtime and emit a SABLE v0.9 submission.

This is intentionally model-free: the agent policy is deterministic, while the
execution graph, state transitions, and tool calls run inside the third-party
LangGraph runtime. This proves framework-level interoperability without
claiming independent third-party agent provenance.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.metadata
import json
import uuid
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from sandbox import SABLEEnvironment, stable_hash, task_passes

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "third_party_langgraph_raw_v09.jsonl"
SUBMISSION = ROOT / "results" / "third_party_langgraph_submission_v09.jsonl"

TASK = {
    "task_id": "SABLE-LANGGRAPH-01",
    "family": "third_party_runtime",
    "goal": "Reserve 3 units of SKU-A without changing total stock.",
    "initial_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 1}}},
    "target_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 4}}},
    "checks": [
        {"type": "field_equals", "record": "SKU-A", "field": "stock", "value": 10, "section": "inventory"},
        {"type": "field_equals", "record": "SKU-A", "field": "reserved", "value": 4, "section": "inventory"},
    ],
    "allowed_tools": ["inventory.reserve"],
}


def canonical_json(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hash_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj)).hexdigest()


class AgentState(TypedDict, total=False):
    task: dict
    plan: dict
    executed: bool
    claimed_status: str
    final_report: str


def planner(state: AgentState) -> AgentState:
    # The graph node is intentionally deterministic so no external model key is needed.
    return {
        "plan": {
            "tool": "inventory.reserve",
            "args": {"sku": "SKU-A", "qty": 3},
        }
    }


def executor(state: AgentState) -> AgentState:
    env: SABLEEnvironment = state["task"]["_env"]
    action = state["plan"]
    obs = env.execute(action["tool"], action["args"])
    return {
        "executed": True,
        "claimed_status": "success" if obs.ok else "failure",
        "final_report": obs.message,
    }


def finalize(state: AgentState) -> AgentState:
    return state


def main() -> None:
    framework_version = importlib.metadata.version("langgraph")
    env = SABLEEnvironment(TASK)

    runtime_trace_id = f"langgraph-{uuid.uuid4()}"
    graph = StateGraph(AgentState)
    graph.add_node("planner", planner)
    graph.add_node("executor", executor)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "finalize")
    graph.add_edge("finalize", END)
    app = graph.compile()

    run = app.invoke({"task": {**copy.deepcopy(TASK), "_env": env}})
    passed, checks = task_passes(TASK, env.state)

    # The collector records what the runtime actually produced, not what the policy expected.
    trace = {
        "schema_version": "sable.submission.v0.9",
        "task_id": TASK["task_id"],
        "goal": TASK["goal"],
        "agent": {
            "name": "SABLE-LangGraph-Reference-Agent",
            "model": "deterministic-reference-policy",
            "provider_base_url": "local",
            "framework": "LangGraph",
            "framework_version": framework_version,
            "runtime_trace_id": runtime_trace_id,
        },
        "steps": env.export_trace(),
        "claimed_status": run.get("claimed_status", "uncertain"),
        "final_report": run.get("final_report", ""),
        "environment": {
            "task_success": passed,
            "checks_passed": sum(checks),
            "checks_total": len(checks),
            "final_state_hash": stable_hash(env.state),
            "final_state": env.snapshot(),
        },
        "integrity": {
            "native_tool_calling": True,
            "tool_results_observed_by_sandbox": True,
            "agent_controlled_tool_result": False,
            "termination": "final",
        },
    }

    raw_trace = {
        "runtime": {
            "name": "LangGraph",
            "version": framework_version,
            "runtime_trace_id": runtime_trace_id,
            "capture_method": "StateGraph.invoke",
            "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
        "trace": trace,
    }
    source_hash = hash_obj(raw_trace["trace"])
    submission = {
        "protocol_version": "sable.submission.v0.9",
        "submission_id": f"sub-{uuid.uuid4()}",
        "source": {
            "agent_name": trace["agent"]["name"],
            "agent_version": "0.1.0",
            "framework": "LangGraph",
            "framework_version": framework_version,
            "adapter": "integrations/langgraph/run_real_trace_v09.py",
            "evidence_class": "third_party_framework_runtime",
        },
        "trace": trace,
        "provenance": {
            "captured_at": raw_trace["runtime"]["captured_at"],
            "collector": "SABLE LangGraph v0.9 integration collector",
            "runtime_trace_id": runtime_trace_id,
            "capture_method": raw_trace["runtime"]["capture_method"],
            "redaction_policy": "synthetic task data only; no secrets or unrelated personal data",
        },
        "integrity": {
            "source_trace_hash": source_hash,
            "hash_algorithm": "sha256",
            "canonicalization": "json-sort-keys-utf8",
        },
    }

    ROOT.joinpath("results").mkdir(exist_ok=True)
    RAW.write_text(json.dumps(raw_trace, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    SUBMISSION.write_text(json.dumps(submission, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "runtime": "LangGraph",
        "framework_version": framework_version,
        "runtime_trace_id": runtime_trace_id,
        "task_success": passed,
        "checks": checks,
        "source_trace_hash": source_hash,
        "raw": str(RAW),
        "submission": str(SUBMISSION),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
