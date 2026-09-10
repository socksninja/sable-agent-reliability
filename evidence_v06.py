#!/usr/bin/env python3
"""SABLE v0.6 Evidence Pack generator.

Turns a run's trace rows into compact, deterministic, auditable evidence records.
No model/API is required beyond the input JSONL trace.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from sable_v05 import classify, replay_task


def canonical_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def state_diff(task: dict, row: dict) -> dict:
    before = task.get("initial_state", {})
    after = row.get("environment", {}).get("final_state", {})
    before_hash = canonical_hash(before)
    after_hash = row.get("environment", {}).get("final_state_hash") or canonical_hash(after)
    return {"initial_state_hash": before_hash, "final_state_hash": after_hash, "changed": before != after}


def build_evidence(task: dict, row: dict) -> dict:
    labels = sorted(classify(row))
    checks_total = int(row.get("environment", {}).get("checks_total", 0))
    checks_passed = int(row.get("environment", {}).get("checks_passed", 0))
    replay = replay_task(task, row)
    trace = row.get("steps", [])
    evidence = {
        "schema_version": "sable.evidence.v0.6",
        "task": {"task_id": task["task_id"], "family": task.get("family", "unknown"), "goal": task.get("goal", "")},
        "agent": row.get("agent", {}),
        "outcome": {
            "task_success": bool(row.get("environment", {}).get("task_success")),
            "claimed_status": row.get("claimed_status", "uncertain"),
            "checks_passed": checks_passed,
            "checks_total": checks_total,
            "failure_labels": labels,
        },
        "execution": {
            "tool_calls": len(trace),
            "tools": [s.get("tool") for s in trace],
            "termination": row.get("integrity", {}).get("termination"),
            "infrastructure_error": row.get("integrity", {}).get("infrastructure_error"),
        },
        "state": state_diff(task, row),
        "replay": replay,
        "evidence_hash": None,
    }
    evidence["evidence_hash"] = canonical_hash({k: v for k, v in evidence.items() if k != "evidence_hash"})
    return evidence


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    tasks = {t["task_id"]: t for t in json.loads(Path(args.tasks).read_text(encoding="utf-8"))}
    rows = [json.loads(x) for x in Path(args.results).read_text(encoding="utf-8").splitlines() if x.strip()]
    evidence = [build_evidence(tasks[r["task_id"]], r) for r in rows if r.get("task_id") in tasks]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in evidence) + ("\n" if evidence else ""), encoding="utf-8")
    print(f"generated {len(evidence)} evidence packs")


if __name__ == "__main__":
    main()
