#!/usr/bin/env python3
"""Validate the SABLE three-runtime cross-runtime evidence matrix v1.1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_FINAL_STATE_HASH = "937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354"
EXPECTED_INITIAL_STATE_HASH = "5568307329d5e3a4b463a6f4ea1299a61226fc595a36f6dc95bde056c5d6ecec"


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_positive(evidence: dict[str, Any], permission: dict[str, Any]) -> dict[str, Any]:
    agent = evidence["agent"]
    state = evidence["state"]
    replay = evidence["replay"]
    outcome = evidence["outcome"]
    assert evidence["schema_version"] == "sable.evidence.v0.6"
    assert outcome["task_success"] is True
    assert outcome["checks_passed"] == outcome["checks_total"] == 2
    assert state["initial_state_hash"] == EXPECTED_INITIAL_STATE_HASH
    assert state["final_state_hash"] == EXPECTED_FINAL_STATE_HASH
    assert replay["task_success"] is True
    assert replay["replay_match"] is True
    assert permission["protocol"] == "sable.permission.v0.1"
    assert permission["decision"] == "ALLOW"
    assert permission["verified"] is True
    return {
        "runtime": agent["framework"],
        "framework_version": agent["framework_version"],
        "runtime_trace_id": agent["runtime_trace_id"],
        "final_state_hash": state["final_state_hash"],
        "permission": permission["decision"],
        "replay": "MATCH",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langgraph-evidence", required=True)
    ap.add_argument("--langgraph-permission", required=True)
    ap.add_argument("--crewai-evidence", required=True)
    ap.add_argument("--crewai-permission", required=True)
    ap.add_argument("--openai-agents-evidence", required=True)
    ap.add_argument("--openai-agents-permission", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = [
        validate_positive(load(args.langgraph_evidence), load(args.langgraph_permission)),
        validate_positive(load(args.crewai_evidence), load(args.crewai_permission)),
        validate_positive(load(args.openai_agents_evidence), load(args.openai_agents_permission)),
    ]

    runtimes = {r["runtime"] for r in rows}
    versions = {f'{r["runtime"]}@{r["framework_version"]}' for r in rows}
    hashes = {r["final_state_hash"] for r in rows}
    assert len(runtimes) == 3, "three distinct runtime identities required"
    assert len(versions) == len(rows), "runtime/version identities must remain distinct"
    assert hashes == {EXPECTED_FINAL_STATE_HASH}, "verified final state did not converge"

    result = {
        "schema_version": "sable.cross_runtime.v1.1",
        "runtime_count": len(runtimes),
        "runtime_versions": sorted(versions),
        "common_verified_final_state_hash": EXPECTED_FINAL_STATE_HASH,
        "all_replay_matches": all(r["replay"] == "MATCH" for r in rows),
        "all_permissions_allow": all(r["permission"] == "ALLOW" for r in rows),
        "rows": rows,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
