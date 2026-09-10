#!/usr/bin/env python3
"""SABLE v0.6 evidence-layer self-test; no model or API required."""
from __future__ import annotations
import json
from pathlib import Path
from evidence_v06 import build_evidence


def main() -> None:
    tasks = json.loads(Path("tasks/tasks_smoke_10.json").read_text(encoding="utf-8"))
    checks = []
    for task in tasks:
        row = {
            "task_id": task["task_id"],
            "agent": {"model": "synthetic", "provider_base_url": "none"},
            "steps": [],
            "claimed_status": "uncertain",
            "environment": {
                "task_success": False,
                "checks_passed": 0,
                "checks_total": len(task["checks"]),
                "final_state": task["initial_state"],
                "final_state_hash": "",
            },
            "integrity": {
                "native_tool_calling": False,
                "tool_results_observed_by_sandbox": True,
                "agent_controlled_tool_result": False,
                "termination": "max_turns",
            },
        }
        e = build_evidence(task, row)
        checks.append(
            e["schema_version"] == "sable.evidence.v0.6"
            and len(e["evidence_hash"]) == 64
            and e["replay"]["replay_match"] is True
            and e["outcome"]["failure_labels"]
        )
    assert all(checks), "evidence self-test failed"
    report = {"schema_version":"sable.v0.6","tasks":len(tasks),"evidence_packs":len(tasks),"all_checks_pass":True}
    Path("results").mkdir(exist_ok=True)
    Path("results/selftest_v06.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
