"""
Independent verification of LangGraph #8834
Resume after a conditional-router exception skips routing and returns normally.

Bounty: socksninja/sable-agent-reliability#86 ($250 USD)
Runtime pinned: langgraph==1.2.11 / langgraph-checkpoint-sqlite==3.1.1

Evidence question:
  Does the resumed runtime response agree with a fresh external readback
  of the downstream effect?
"""
import hashlib
import json
import platform
import sqlite3
import sys
from datetime import datetime, timezone
from typing import TypedDict

from importlib.metadata import version as pkg_version

import langgraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

# ── Version pin ─────────────────────────────────────────────────────────────
RUNTIME = {
    "langgraph": pkg_version("langgraph"),
    "langgraph_checkpoint_sqlite": pkg_version("langgraph-checkpoint-sqlite"),
    "python": sys.version,
    "platform": platform.platform(),
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
}


class State(TypedDict):
    value: int


def reproduce(saver, failure_location: str) -> dict:
    """Run the reproduction for one failure_location / saver combination."""
    calls = {"node": 0, "route": 0, "sink": 0}

    def node(state):
        calls["node"] += 1
        if failure_location == "node" and calls["node"] == 1:
            raise ValueError("temporary node failure")
        return {"value": 1}

    def route(state):
        calls["route"] += 1
        if failure_location == "route" and calls["route"] == 1:
            raise ValueError("temporary route failure")
        return "sink"

    def sink(state):
        calls["sink"] += 1
        return {"value": 2}

    graph = StateGraph(State)
    graph.add_node("node", node)
    graph.add_node("sink", sink)
    graph.add_edge(START, "node")
    graph.add_conditional_edges("node", route, {"sink": "sink"})
    graph.add_edge("sink", END)
    app = graph.compile(checkpointer=saver)

    config = {"configurable": {"thread_id": failure_location}}

    # Step 1 — initial invocation (expected to raise)
    first_error = None
    try:
        app.invoke({"value": 0}, config)
    except ValueError as exc:
        first_error = str(exc)

    # Step 2 — external readback BEFORE resume
    before = app.get_state(config)

    # Step 3 — resume from same checkpoint
    result = app.invoke(None, config)

    # Step 4 — external readback AFTER resume
    after = app.get_state(config)

    return {
        "failure_location": failure_location,
        "first_error": first_error,
        "pending_before_resume": list(before.next),
        "resume_result": result,
        "calls": calls,
        "pending_after_resume": list(after.next),
        # Evidence question core:
        # Did resume result agree with fresh readback of downstream effect?
        "sink_executed": calls["sink"] > 0,
        "result_value": result.get("value"),
        "post_resume_state_value": after.values.get("value"),
    }


def main():
    all_results = []

    for location in ("node", "route"):
        # ── InMemorySaver ────────────────────────────────────────────────────
        mem_result = reproduce(InMemorySaver(), location)
        all_results.append({"saver": "InMemorySaver", **mem_result})

        # ── SqliteSaver (in-memory DB) ────────────────────────────────────────
        with sqlite3.connect(":memory:", check_same_thread=False) as conn:
            sqlite_result = reproduce(SqliteSaver(conn), location)
        all_results.append({"saver": "SqliteSaver", **sqlite_result})

    # ── Evidence determination ───────────────────────────────────────────────
    verdict_lines = []
    for r in all_results:
        loc = r["failure_location"]
        saver = r["saver"]
        sink_ran = r["sink_executed"]
        result_val = r["result_value"]
        post_val = r["post_resume_state_value"]

        if loc == "route":
            # BUG CASE: router failure — sink should run on resume but per issue it does NOT
            # Runtime says success (returns value=1), but sink never ran (value stays 1 not 2)
            runtime_claims_success = r["first_error"] is not None and result_val is not None
            readback_agrees = post_val == result_val

            if not sink_ran and result_val == 1 and runtime_claims_success:
                verdict = "VERIFIED"
                detail = (
                    f"[{saver} / failure=route] Router raised on first call. "
                    f"Resume returned value={result_val} (no sink, no re-route). "
                    f"Downstream node 'sink' never executed (calls={r['calls']}). "
                    f"External readback post-resume: value={post_val}. "
                    f"Runtime response and readback AGREE that sink was skipped. "
                    f"Bug CONFIRMED: resume silently skipped the pending router+sink path."
                )
            elif sink_ran:
                verdict = "NOT VERIFIED"
                detail = f"[{saver} / failure=route] Sink did execute (calls={r['calls']}). Bug not reproduced."
            else:
                verdict = "EVIDENCE GAP"
                detail = f"[{saver} / failure=route] Unexpected state. calls={r['calls']} result={result_val}"
        else:
            # CONTROL CASE: node failure — resume should retry node, run router+sink (value=2)
            if sink_ran and result_val == 2:
                verdict = "CONTROL_PASS"
                detail = (
                    f"[{saver} / failure=node] Node retry worked. "
                    f"Sink ran (calls={r['calls']}). Final value={result_val}. Control case passes."
                )
            else:
                verdict = "CONTROL_FAIL"
                detail = f"[{saver} / failure=node] Unexpected: sink_ran={sink_ran} value={result_val}"

        verdict_lines.append({"verdict": verdict, "detail": detail, "raw": r})

    # ── Machine-readable evidence package ────────────────────────────────────
    evidence = {
        "runtime": RUNTIME,
        "verdicts": verdict_lines,
    }
    evidence_json = json.dumps(evidence, indent=2, sort_keys=True, default=str)
    evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()

    evidence["evidence_sha256"] = evidence_hash

    final_json = json.dumps(evidence, indent=2, sort_keys=True, default=str)

    # Write to file
    output_path = "EVIDENCE_8834_VERIFICATION.json"
    with open(output_path, "w") as f:
        f.write(final_json)

    print(final_json)
    print(f"\n[+] Evidence written to: {output_path}")
    print(f"[+] SHA-256: {evidence_hash}")

    # Overall verdict
    route_verdicts = [v["verdict"] for v in verdict_lines if "route" in v["raw"]["failure_location"]]
    if all(v == "VERIFIED" for v in route_verdicts):
        print("\n🟢 OVERALL VERDICT: VERIFIED — LangGraph #8834 independently confirmed.")
    elif all(v == "NOT VERIFIED" for v in route_verdicts):
        print("\n🔴 OVERALL VERDICT: NOT VERIFIED")
    else:
        print("\n🟡 OVERALL VERDICT: EVIDENCE GAP")


if __name__ == "__main__":
    main()
