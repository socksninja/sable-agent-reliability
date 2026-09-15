#!/usr/bin/env python3
"""SABLE v0.1 verified-execution permission gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def decide(row: dict, report: dict | None = None) -> dict:
    env = row.get("environment", {})
    integrity = row.get("integrity", {})
    steps = row.get("steps", [])

    reasons: list[str] = []
    if not env.get("task_success", False):
        reasons.append("environment_state_not_verified")
    if not steps:
        reasons.append("no_observed_tool_execution")
    if integrity.get("termination") != "final":
        reasons.append("non_final_termination")
    if integrity.get("native_tool_calling") is not True:
        reasons.append("native_tool_calling_not_attested")
    if integrity.get("tool_results_observed_by_sandbox") is not True:
        reasons.append("sandbox_observation_not_attested")
    if integrity.get("agent_controlled_tool_result") is not False:
        reasons.append("tool_result_control_not_excluded")

    if report is not None:
        if report.get("pass_rate") != 1.0:
            reasons.append("evaluation_not_fully_passed")
        if report.get("replay_match_rate") != 1.0:
            reasons.append("replay_not_fully_verified")

    for i, step in enumerate(steps, start=1):
        obs = step.get("observed_result", {})
        if obs.get("ok") is not True:
            reasons.append(f"step_{i}_failed")
        if not step.get("after_state_hash"):
            reasons.append(f"step_{i}_missing_state_hash")

    decision = "ALLOW" if not reasons else "DENY"
    return {
        "protocol": "sable.permission.v0.1",
        "decision": decision,
        "reasons": reasons,
        "task_id": row.get("task_id"),
        "verified": decision == "ALLOW",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()

    rows = [
        json.loads(line)
        for line in Path(args.input).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = json.loads(Path(args.report).read_text(encoding="utf-8")) if args.report else None
    decisions = [decide(row, report) for row in rows]
    Path(args.output).write_text(
        "\n".join(json.dumps(d, ensure_ascii=False, sort_keys=True) for d in decisions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "count": len(decisions),
        "allow": sum(d["decision"] == "ALLOW" for d in decisions),
        "deny": sum(d["decision"] == "DENY" for d in decisions),
    }, indent=2))


if __name__ == "__main__":
    main()
