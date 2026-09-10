#!/usr/bin/env python3
"""Build a compact cross-runtime evidence matrix from committed SABLE artifacts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

CASES = [
    ("LangGraph", "results/third_party_langgraph_submission_v09.jsonl", "results/third_party_langgraph_evidence.json", "results/third_party_langgraph_permission.json"),
    ("CrewAI", "results/third_party_crewai_submission_v09.jsonl", "results/third_party_crewai_evidence.json", "results/third_party_crewai_permission.json"),
]


def one(runtime: str, sub_path: str, evidence_path: str, permission_path: str) -> dict:
    submission = json.loads((ROOT / sub_path).read_text(encoding="utf-8"))
    evidence = json.loads((ROOT / evidence_path).read_text(encoding="utf-8"))
    permission = json.loads((ROOT / permission_path).read_text(encoding="utf-8"))
    return {
        "runtime": runtime,
        "framework_version": submission["source"]["framework_version"],
        "task_id": submission["trace"]["task_id"],
        "trace_hash": submission["integrity"]["source_trace_hash"],
        "final_state_hash": submission["trace"]["environment"]["final_state_hash"],
        "task_success": evidence["outcome"]["task_success"],
        "replay_match": evidence["replay"]["replay_match"],
        "permission": permission["decision"],
        "verified": permission["verified"],
    }


def main() -> None:
    rows = [one(*c) for c in CASES]
    successful = [r for r in rows if r["task_success"]]
    same_target = len({r["final_state_hash"] for r in successful}) == 1
    result = {
        "schema_version": "sable.cross_runtime_matrix.v0.1",
        "runtimes": rows,
        "cross_runtime": {
            "runtime_count": len(rows),
            "successful_case_count": len(successful),
            "common_verified_final_state": same_target,
            "common_final_state_hash": successful[0]["final_state_hash"] if same_target and successful else None,
        },
    }
    (RESULTS / "cross_runtime_matrix.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# SABLE Cross-Runtime Evidence Matrix v0.1",
        "",
        "| Runtime | Version | Task Success | Replay | Permission | Final State Hash |",
        "|---|---|---:|---:|---|---|",
    ]
    for r in rows:
        md.append(f"| {r['runtime']} | {r['framework_version']} | {r['task_success']} | {r['replay_match']} | **{r['permission']}** | `{r['final_state_hash'][:12]}…` |")
    md += [
        "",
        f"**Common verified final state:** `{result['cross_runtime']['common_final_state_hash']}`" if same_target else "**Common verified final state:** NOT ESTABLISHED",
        "",
        "This matrix demonstrates whether multiple agent runtimes converge on the same SABLE evidence and permission semantics.",
    ]
    (ROOT / "CROSS_RUNTIME_MATRIX_V01.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
