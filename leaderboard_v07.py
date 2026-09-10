#!/usr/bin/env python3
"""SABLE v0.7 comparable leaderboard builder.

Ranks real evaluation reports only when benchmark/task-set identity is held constant.
Provider/model failures remain visible and never become fake agent successes.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

SCHEMA = "sable.leaderboard.v0.7"

def load_report(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "tasks", "reliability_score", "operational_score_excluding_provider_failures", "pass_rate"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"{path}: missing {sorted(missing)}")
    if int(data["tasks"]) <= 0:
        raise ValueError(f"{path}: tasks must be > 0")
    return data

def compare_key(entry: dict) -> tuple:
    report = entry["report"]
    return (
        float(report["reliability_score"]),
        float(report["operational_score_excluding_provider_failures"]),
        float(report["pass_rate"]),
    )

def build(entries: list[dict], benchmark_id: str) -> dict:
    if not entries:
        return {"schema_version": SCHEMA, "benchmark_id": benchmark_id, "entries": [], "eligible_entries": 0}
    tasks = {int(e["report"]["tasks"]) for e in entries}
    if len(tasks) != 1:
        raise ValueError("all reports must use the same task count")
    ranked = sorted(entries, key=compare_key, reverse=True)
    for i, e in enumerate(ranked, 1):
        e["rank"] = i
    return {
        "schema_version": SCHEMA,
        "benchmark_id": benchmark_id,
        "task_count": tasks.pop(),
        "ranking_rule": ["reliability_score", "operational_score_excluding_provider_failures", "pass_rate"],
        "entries": ranked,
        "eligible_entries": len(ranked),
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="append", required=True, help="JSON report path; repeatable")
    ap.add_argument("--model", action="append", required=True, help="Model label matching each --report")
    ap.add_argument("--provider", action="append", required=True, help="Provider label matching each --report")
    ap.add_argument("--benchmark-id", default="SABLE-v0.5-140")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not (len(args.report) == len(args.model) == len(args.provider)):
        raise SystemExit("--report, --model, and --provider must have equal counts")
    entries=[]
    for p,m,prov in zip(args.report,args.model,args.provider):
        report=load_report(Path(p))
        entries.append({"model":m,"provider":prov,"report":report})
    out=build(entries,args.benchmark_id)
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__ == "__main__": main()
