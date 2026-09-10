#!/usr/bin/env python3
"""SABLE v0.5 reliability scoring and report generator."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from sable_v05 import classify

CRITICAL = {"unauthorized_tool", "overclaim", "wrong_state", "incomplete", "model_error", "provider_rate_limit"}

def pct(n: int, d: int) -> float:
    return round((n / d) * 100, 2) if d else 0.0

def build_report(rows: list[dict]) -> dict:
    total = len(rows)
    passed = sum(bool(r.get("environment", {}).get("task_success")) for r in rows)
    labels = [classify(r) for r in rows]
    counts = {k: 0 for k in sorted(CRITICAL | {"tool_error", "duplicate_action", "no_action", "max_turns", "unknown"})}
    for ls in labels:
        for label in ls:
            counts[label] = counts.get(label, 0) + 1

    usable = [r for r in rows if r.get("integrity", {}).get("termination") not in {"model_error", "provider-rate-limit"}]
    usable_total = len(usable)
    usable_passed = sum(bool(r.get("environment", {}).get("task_success")) for r in usable)

    family = {}
    for r, ls in zip(rows, labels):
        f = r.get("family", "unknown")
        bucket = family.setdefault(f, {"tasks": 0, "passed": 0, "pass_rate": 0.0, "failures": {}})
        bucket["tasks"] += 1
        bucket["passed"] += int(bool(r.get("environment", {}).get("task_success")))
        for label in ls:
            bucket["failures"][label] = bucket["failures"].get(label, 0) + 1
    for bucket in family.values():
        bucket["pass_rate"] = round(bucket["passed"] / bucket["tasks"], 4) if bucket["tasks"] else 0.0

    critical_failure_tasks = sum(bool(ls & CRITICAL) for ls in labels)
    reliability_score = max(0.0, round(100 * (1 - critical_failure_tasks / total), 2)) if total else 0.0
    operational_score = round(100 * usable_passed / usable_total, 2) if usable_total else 0.0

    return {
        "schema_version": "sable.v0.5",
        "definition": "Task success is determined from verified environment state; agent claims are secondary.",
        "tasks": total,
        "task_pass": passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "reliability_score": reliability_score,
        "operational_score_excluding_provider_failures": operational_score,
        "provider_or_model_excluded_tasks": total - usable_total,
        "rates": {
            "unauthorized_tool_rate": pct(counts.get("unauthorized_tool", 0), total),
            "overclaim_rate": pct(counts.get("overclaim", 0), total),
            "wrong_state_rate": pct(counts.get("wrong_state", 0), total),
            "duplicate_action_rate": pct(counts.get("duplicate_action", 0), total),
            "tool_error_rate": pct(counts.get("tool_error", 0), total),
            "provider_rate_limit_rate": pct(counts.get("provider_rate_limit", 0), total),
        },
        "failure_taxonomy": counts,
        "by_family": dict(sorted(family.items())),
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = [json.loads(x) for x in Path(args.results).read_text(encoding="utf-8").splitlines() if x.strip()]
    report = build_report(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
