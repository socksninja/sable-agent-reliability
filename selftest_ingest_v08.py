#!/usr/bin/env python3
"""SABLE v0.8 ingestion self-test; no model/API required."""
from __future__ import annotations
import json
from pathlib import Path
from trace_ingest_v08 import normalize


def sample(task_id="EXT-001"):
    return {
        "schema_version": "external.agent.trace.v1",
        "task_id": task_id,
        "goal": "Move draft.txt to archive/.",
        "agent": {"model": "external-synthetic", "provider_base_url": "external"},
        "steps": [{
            "tool": "file.move",
            "args": {"source": "draft.txt", "destination": "archive/draft.txt"},
            "observed_result": {"ok": True, "message": "moved"},
            "before_state_hash": "a" * 64,
            "after_state_hash": "b" * 64,
        }],
        "claimed_status": "success",
        "final_report": "done",
        "environment": {"task_success": True, "checks_passed": 2, "checks_total": 2, "final_state_hash": "b" * 64},
        "integrity": {"native_tool_calling": True, "tool_results_observed_by_sandbox": True, "agent_controlled_tool_result": False, "termination": "final"},
    }


def main():
    row = normalize(sample())
    assert row["schema_version"] == "sable.v0.5"
    assert row["ingestion"]["schema_version"] == "sable.ingest.v0.8"
    assert len(row["ingestion"]["trace_hash"]) == 64
    assert row["steps"][0]["tool"] == "file.move"
    try:
        normalize({k: v for k, v in sample().items() if k != "integrity"})
    except ValueError:
        pass
    else:
        raise AssertionError("missing integrity must be rejected")
    out = {"schema_version":"sable.v0.8","status":"PASS","normalized_traces":1}
    Path("results").mkdir(exist_ok=True)
    Path("results/selftest_ingest_v08.json").write_text(json.dumps(out, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__": main()
