#!/usr/bin/env python3
"""SABLE failure taxonomy v1.4: normalize observed failure causes into stable root domains."""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path

ROOT_PRIORITY = [
    ("provider_rate_limit", "infrastructure", "provider_rate_limit"),
    ("model_error", "infrastructure", "model_error"),
    ("unauthorized_tool", "agent", "authorization_violation"),
    ("tool_error", "agent", "tool_execution_error"),
    ("overclaim", "agent", "unsupported_success_claim"),
    ("duplicate_action", "agent", "idempotency_failure"),
    ("no_action", "agent", "no_observed_action"),
    ("max_turns", "agent", "termination_exhausted"),
    ("wrong_state", "agent", "state_incorrect"),
    ("incomplete", "agent", "task_incomplete"),
]


def load_many(path: str) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return obj if isinstance(obj, list) else [obj]


def labels_from_evidence(ev: dict) -> set[str]:
    labels = set(ev.get("outcome", {}).get("failure_labels", []))
    execution = ev.get("execution", {})
    if execution.get("termination") == "provider-rate-limit":
        labels.add("provider_rate_limit")
    if execution.get("termination") == "model_error":
        labels.add("model_error")
    return labels


def primary(labels: set[str], task_success: bool) -> tuple[str, str, str]:
    for label, domain, root in ROOT_PRIORITY:
        if label in labels:
            return label, domain, root
    if task_success:
        return "none", "verification", "verified_success"
    return "unknown", "unknown", "unknown"


def build(evidence_paths: list[str], permission_paths: list[str]) -> dict:
    if len(evidence_paths) != len(permission_paths):
        raise SystemExit("evidence/permission file counts must match")
    records = []
    root_counts = Counter()
    domain_counts = Counter()
    label_counts = Counter()
    by_task = defaultdict(Counter)
    for ep, pp in zip(evidence_paths, permission_paths):
        evs = load_many(ep)
        pms = load_many(pp)
        if len(evs) != len(pms):
            raise SystemExit(f"evidence/permission record counts must match for {ep} and {pp}")
        for ev, pm in zip(evs, pms):
            labels = labels_from_evidence(ev)
            task_success = bool(ev.get("outcome", {}).get("task_success"))
            label, domain, root = primary(labels, task_success)
            task = ev.get("task", {})
            row = {
                "task_id": task.get("task_id"),
                "family": task.get("family", "unknown"),
                "runtime": ev.get("agent", {}).get("framework"),
                "framework_version": ev.get("agent", {}).get("framework_version"),
                "model": ev.get("agent", {}).get("model"),
                "provider": ev.get("agent", {}).get("provider_base_url"),
                "permission": pm.get("decision"),
                "task_success": task_success,
                "replay_match": bool(ev.get("replay", {}).get("replay_match")),
                "observed_labels": sorted(labels),
                "primary_label": label,
                "fault_domain": domain,
                "root_cause": root,
                "evidence_hash": ev.get("evidence_hash"),
            }
            records.append(row)
            root_counts[root] += 1
            domain_counts[domain] += 1
            for x in labels or {"none" if task_success else "unknown"}:
                label_counts[x] += 1
            by_task[row["task_id"]][root] += 1
    n = len(records)
    safe = sum(r["permission"] == "ALLOW" and r["task_success"] for r in records)
    denied = sum(r["permission"] == "DENY" for r in records)
    return {
        "schema_version": "sable.failure_taxonomy.v1.4",
        "observation_count": n,
        "verified_successes": safe,
        "verified_denials": denied,
        "all_replay_matches": all(r["replay_match"] for r in records),
        "root_cause_counts": dict(sorted(root_counts.items())),
        "fault_domain_counts": dict(sorted(domain_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "task_breakdown": {k: dict(sorted(v.items())) for k, v in sorted(by_task.items())},
        "records": records,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", nargs="+", required=True)
    ap.add_argument("--permission", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = build(args.evidence, args.permission)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
