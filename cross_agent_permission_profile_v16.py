#!/usr/bin/env python3
"""SABLE v1.6: compare permission/reliability profiles across runtimes on shared tasks."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

VERSION = "sable.cross_agent_permission_profile.v1.6"


def load_many(path: str) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, list) else [obj]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def canon_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def semantic_task_key(task: dict) -> str:
    family = str(task.get("family", "unknown")).strip().lower()
    goal = " ".join(str(task.get("goal", "")).split()).strip().lower()
    return f"{family}:{canon_hash({'family': family, 'goal': goal})[:16]}"


def collect(evidence_paths: list[str], permission_paths: list[str]) -> list[dict]:
    if len(evidence_paths) != len(permission_paths):
        raise SystemExit("evidence/permission file counts must match")
    rows: list[dict] = []
    for ep, pp in zip(evidence_paths, permission_paths):
        evs, pms = load_many(ep), load_many(pp)
        if len(evs) != len(pms):
            raise SystemExit(f"record counts must match: {ep} vs {pp}")
        for ev, pm in zip(evs, pms):
            task = ev.get("task", {})
            agent = ev.get("agent", {})
            outcome = ev.get("outcome", {})
            rows.append({
                "task_id": task.get("task_id"),
                "semantic_task_key": semantic_task_key(task),
                "goal": task.get("goal"),
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
                "deny_reasons": sorted(pm.get("reasons", [])),
                "evidence_hash": ev.get("evidence_hash"),
            })
    return rows


def profile(rows: list[dict]) -> dict:
    by_rt: dict[str, list[dict]] = defaultdict(list)
    by_task: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_rt[r["runtime"]].append(r)
        by_task[r["semantic_task_key"]].append(r)

    runtime_profiles = {}
    for runtime, rs in sorted(by_rt.items()):
        n = len(rs)
        allow = sum(r["permission"] == "ALLOW" for r in rs)
        success = sum(r["task_success"] for r in rs)
        replay_ok = sum(r["replay_match"] for r in rs)
        runtime_profiles[runtime] = {
            "observations": n,
            "allow": allow,
            "deny": n - allow,
            "task_success": success,
            "replay_matches": replay_ok,
            "observed_allow_rate": allow / n if n else None,
            "observed_task_success_rate": success / n if n else None,
            "replay_match_rate": replay_ok / n if n else None,
            "eligibility": "blocked" if any(not r["replay_match"] for r in rs) else ("eligible" if n else "unknown"),
        }

    comparisons = []
    for task_key, rs in sorted(by_task.items()):
        runtimes = sorted({r["runtime"] for r in rs})
        if len(runtimes) < 2:
            continue
        per_runtime = {}
        for runtime in runtimes:
            sub = [r for r in rs if r["runtime"] == runtime]
            per_runtime[runtime] = {
                "observations": len(sub),
                "allow": sum(r["permission"] == "ALLOW" for r in sub),
                "success": sum(r["task_success"] for r in sub),
                "replay_matches": sum(r["replay_match"] for r in sub),
                "allow_rate_observed": sum(r["permission"] == "ALLOW" for r in sub) / len(sub),
            }
        comparisons.append({
            "semantic_task_key": task_key,
            "task_ids": sorted({r["task_id"] for r in rs}),
            "family": rs[0]["family"],
            "goal": rs[0]["goal"],
            "runtimes": runtimes,
            "per_runtime": per_runtime,
            "shared_replay_clean": all(v["replay_matches"] == v["observations"] for v in per_runtime.values()),
        })

    result = {
        "schema_version": VERSION,
        "observation_count": len(rows),
        "runtime_count": len(runtime_profiles),
        "shared_task_count": len(comparisons),
        "runtime_profiles": runtime_profiles,
        "shared_task_comparisons": comparisons,
        "observations": rows,
    }
    result["profile_hash"] = canon_hash(result)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", nargs="+", required=True)
    ap.add_argument("--permission", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = profile(args.evidence, args.permission)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"observations": result["observation_count"], "runtimes": result["runtime_count"], "shared_tasks": result["shared_task_count"], "profile_hash": result["profile_hash"]}, indent=2))


if __name__ == "__main__":
    main()
