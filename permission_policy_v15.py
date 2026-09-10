#!/usr/bin/env python3
"""SABLE Permission Policy v1.5: turn verified execution evidence into auditable policy profiles."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

POLICY_VERSION = "sable.permission_policy.v1.5"


def load_many(path: str) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, list) else [obj]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def canonical_hash(obj: object) -> str:
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def build(evidence_paths: list[str], permission_paths: list[str]) -> dict:
    if len(evidence_paths) != len(permission_paths):
        raise SystemExit("evidence/permission file counts must match")

    observations: list[dict] = []
    for ep, pp in zip(evidence_paths, permission_paths):
        evs, pms = load_many(ep), load_many(pp)
        if len(evs) != len(pms):
            raise SystemExit(f"record counts must match: {ep} vs {pp}")
        for ev, pm in zip(evs, pms):
            task = ev.get("task", {})
            agent = ev.get("agent", {})
            outcome = ev.get("outcome", {})
            execution = ev.get("execution", {})
            observations.append({
                "task_id": task.get("task_id"),
                "family": task.get("family", "unknown"),
                "runtime": agent.get("framework", "unknown"),
                "framework_version": agent.get("framework_version"),
                "model": agent.get("model"),
                "provider": agent.get("provider_base_url"),
                "permission": pm.get("decision"),
                "verified": pm.get("verified") is True,
                "task_success": outcome.get("task_success") is True,
                "replay_match": ev.get("replay", {}).get("replay_match") is True,
                "failure_labels": sorted(outcome.get("failure_labels", [])),
                "termination": execution.get("termination"),
                "reasons": sorted(pm.get("reasons", [])),
                "evidence_hash": ev.get("evidence_hash"),
            })

    profiles: dict[str, dict] = defaultdict(lambda: {
        "observations": 0,
        "allow": 0,
        "deny": 0,
        "replay_mismatch": 0,
        "failure_labels": defaultdict(int),
        "deny_reasons": defaultdict(int),
    })
    for row in observations:
        p = profiles[row["runtime"]]
        p["observations"] += 1
        p["allow"] += row["permission"] == "ALLOW"
        p["deny"] += row["permission"] == "DENY"
        p["replay_mismatch"] += not row["replay_match"]
        for label in row["failure_labels"]:
            p["failure_labels"][label] += 1
        for reason in row["reasons"]:
            p["deny_reasons"][reason] += 1

    rendered = {}
    for runtime, p in sorted(profiles.items()):
        rendered[runtime] = {
            "observations": p["observations"],
            "allow": p["allow"],
            "deny": p["deny"],
            "replay_mismatch": p["replay_mismatch"],
            "allow_rate_observed": p["allow"] / p["observations"] if p["observations"] else 0.0,
            "policy_state": "eligible" if p["observations"] >= 1 and p["replay_mismatch"] == 0 else "blocked",
            "failure_labels": dict(sorted(p["failure_labels"].items())),
            "deny_reasons": dict(sorted(p["deny_reasons"].items())),
        }

    decision = {
        "minimum_evidence": {
            "environment_success": True,
            "observed_tool_execution": True,
            "final_termination": True,
            "native_tool_calling_attested": True,
            "sandbox_observation_attested": True,
            "agent_controlled_tool_result_excluded": True,
            "every_step_successful": True,
            "state_hash_present": True,
            "replay_match": True,
        },
        "deny_overrides": [
            "environment_state_not_verified",
            "no_observed_tool_execution",
            "non_final_termination",
            "sandbox_observation_not_attested",
            "tool_result_control_not_excluded",
            "replay_mismatch",
        ],
    }
    result = {
        "schema_version": POLICY_VERSION,
        "observation_count": len(observations),
        "decision_contract": decision,
        "runtime_profiles": rendered,
        "observations": observations,
    }
    result["policy_hash"] = canonical_hash({k: v for k, v in result.items() if k != "policy_hash"})
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", nargs="+", required=True)
    ap.add_argument("--permission", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = build(args.evidence, args.permission)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"observations": result["observation_count"], "policy_hash": result["policy_hash"]}, indent=2))


if __name__ == "__main__":
    main()
