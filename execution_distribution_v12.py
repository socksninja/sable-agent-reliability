#!/usr/bin/env python3
"""Aggregate SABLE v0.9/v0.6 evidence into an auditable execution distribution.

This intentionally refuses to label tiny samples as a stable reliability estimate.
It reports observed counts and rates, splits agent failures from infrastructure
failures, and preserves per-runtime/model/provider dimensions.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

MIN_OBSERVATIONS_FOR_RATE = 5


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def classify(evidence: dict[str, Any], permission: dict[str, Any]) -> tuple[str, str]:
    outcome = evidence["outcome"]
    execution = evidence.get("execution", {})
    integrity = evidence.get("integrity", {})
    if outcome["task_success"] and permission.get("decision") == "ALLOW":
        return "verified_allow", "agent"
    if execution.get("infrastructure_error") or integrity.get("infrastructure_error"):
        return "infrastructure_failure", "infrastructure"
    if permission.get("decision") == "DENY":
        return "verified_deny", "agent"
    return "unverified", "unknown"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="append", nargs=2, metavar=("EVIDENCE", "PERMISSION"), required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows: list[dict[str, Any]] = []
    for evidence_path, permission_path in args.record:
        evidence = load(evidence_path)
        permission = load(permission_path)
        classification, fault_domain = classify(evidence, permission)
        agent = evidence.get("agent", {})
        rows.append({
            "task_id": evidence.get("task", {}).get("task_id"),
            "runtime": agent.get("framework"),
            "framework_version": agent.get("framework_version"),
            "model": agent.get("model"),
            "provider": agent.get("provider_base_url"),
            "classification": classification,
            "fault_domain": fault_domain,
            "task_success": evidence["outcome"]["task_success"],
            "replay_match": evidence["replay"]["replay_match"],
            "permission": permission.get("decision"),
            "evidence_hash": evidence.get("evidence_hash"),
        })

    counts = Counter(r["classification"] for r in rows)
    runtime_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        runtime_counts[row["runtime"]][row["classification"]] += 1

    n = len(rows)
    verified = counts["verified_allow"]
    failed = counts["verified_deny"]
    infra = counts["infrastructure_failure"]

    result = {
        "schema_version": "sable.execution_distribution.v1.2",
        "observation_count": n,
        "sample_quality": "rate_estimate" if n >= MIN_OBSERVATIONS_FOR_RATE else "observations_only",
        "minimum_observations_for_rate_estimate": MIN_OBSERVATIONS_FOR_RATE,
        "counts": dict(counts),
        "verified_task_success_rate": (verified / (verified + failed)) if (verified + failed) else None,
        "verified_failure_rate": (failed / (verified + failed)) if (verified + failed) else None,
        "infrastructure_failure_rate": (infra / n) if n else None,
        "all_replay_matches": all(r["replay_match"] is True for r in rows),
        "runtime_breakdown": {k: dict(v) for k, v in sorted(runtime_counts.items())},
        "records": rows,
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
