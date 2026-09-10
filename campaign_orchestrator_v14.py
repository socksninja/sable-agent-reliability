#!/usr/bin/env python3
"""SABLE v1.4 multi-task repeated external-model campaign."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def canon(o: object) -> bytes:
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run(cmd: list[str], env: dict[str, str]) -> None:
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def load_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def wrap(raw: dict, model: str, base_url: str, repetition: int) -> dict:
    trace = {
        "schema_version": "sable.submission.v0.9",
        "task_id": raw["task_id"],
        "goal": raw["goal"],
        "agent": {
            **raw["agent"],
            "framework": "SABLE native external-model runner",
            "framework_version": "v0.3",
            "model": model,
            "provider_base_url": base_url,
            "runtime_trace_id": f"external-model-{uuid.uuid4()}",
        },
        "steps": raw["steps"],
        "claimed_status": raw["claimed_status"],
        "final_report": raw["final_report"],
        "environment": raw["environment"],
        "integrity": raw["integrity"],
    }
    return {
        "protocol_version": "sable.submission.v0.9",
        "submission_id": f"sub-{uuid.uuid4()}",
        "source": {
            "agent_name": model,
            "agent_version": "1.0.0",
            "framework": "SABLE native external-model runner",
            "framework_version": "v0.3",
            "adapter": "real_agent_runner.py",
            "evidence_class": "external_model_execution",
        },
        "trace": trace,
        "provenance": {
            "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "collector": "SABLE external-model campaign v1.4 collector",
            "runtime_trace_id": trace["agent"]["runtime_trace_id"],
            "capture_method": "real_agent_runner.py",
            "campaign_repetition": repetition,
            "redaction_policy": "synthetic task data only; no secrets or unrelated personal data",
        },
        "integrity": {
            "source_trace_hash": hashlib.sha256(canon(trace)).hexdigest(),
            "hash_algorithm": "sha256",
            "canonicalization": "json-sort-keys-utf8",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--api-key", default=os.getenv("SABLE_API_KEY"))
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--max-turns", type=int, default=8)
    ap.add_argument("--thinking", choices=["disabled", "enabled"], default="disabled")
    ap.add_argument("--tasks", default="integrations/external_model/multi_task_v14.json")
    ap.add_argument("--out", default="results/external_model_campaign_v14.json")
    args = ap.parse_args()
    if not args.api_key:
        raise SystemExit("Missing SABLE_API_KEY")
    if args.repeats < 2:
        raise SystemExit("--repeats must be >= 2")

    campaign_id = f"campaign-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    campaign_dir = ROOT / "results" / "campaigns" / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"SABLE_API_KEY": args.api_key, "SABLE_BASE_URL": args.base_url, "SABLE_MODEL": args.model})
    records: list[dict] = []

    for repetition in range(1, args.repeats + 1):
        prefix = campaign_dir / f"rep_{repetition:02d}"
        raw = prefix.with_name(prefix.name + "_raw.jsonl")
        submission = prefix.with_name(prefix.name + "_submission.jsonl")
        normalized = prefix.with_name(prefix.name + "_sable.jsonl")
        evaluation = prefix.with_name(prefix.name + "_evaluation.json")
        evidence = prefix.with_name(prefix.name + "_evidence.jsonl")
        permission = prefix.with_name(prefix.name + "_permission.jsonl")

        run([sys.executable, "real_agent_runner.py", "--tasks", args.tasks, "--out", str(raw), "--base-url", args.base_url, "--model", args.model, "--max-turns", str(args.max_turns), "--thinking", args.thinking], env)
        raws = load_lines(raw)
        tasks = load_lines(Path(args.tasks)) if Path(args.tasks).suffix == ".jsonl" else json.loads(Path(args.tasks).read_text(encoding="utf-8"))
        if len(raws) != len(tasks):
            raise SystemExit(f"runner produced {len(raws)} traces for {len(tasks)} tasks")
        submissions = [wrap(item, args.model, args.base_url, repetition) for item in raws]
        submission.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in submissions), encoding="utf-8")

        run([sys.executable, "trace_submit_v09.py", "--input", str(submission), "--output", str(normalized)], env)
        run([sys.executable, "evaluator.py", "--tasks", args.tasks, "--traces", str(normalized), "--out", str(evaluation)], env)
        run([sys.executable, "evidence_v06.py", "--tasks", args.tasks, "--results", str(normalized), "--out", str(evidence)], env)
        run([sys.executable, "permission_v01.py", "--input", str(normalized), "--output", str(permission)], env)

        evidence_rows = load_lines(evidence)
        permission_rows = load_lines(permission)
        if len(evidence_rows) != len(permission_rows) or len(evidence_rows) != len(tasks):
            raise SystemExit("evidence/permission/task record counts diverged")
        for ev, pm in zip(evidence_rows, permission_rows):
            records.append({
                "repetition": repetition,
                "task_id": ev["task"]["task_id"],
                "family": ev["task"].get("family", "unknown"),
                "model": args.model,
                "provider": args.base_url,
                "runtime": ev["agent"].get("framework"),
                "framework_version": ev["agent"].get("framework_version"),
                "task_success": ev["outcome"]["task_success"],
                "replay_match": ev["replay"]["replay_match"],
                "permission": pm["decision"],
                "failure_labels": ev["outcome"].get("failure_labels", []),
                "infrastructure_error": ev.get("execution", {}).get("infrastructure_error"),
                "evidence_hash": ev.get("evidence_hash"),
            })

    n = len(records)
    allow = sum(r["permission"] == "ALLOW" and r["task_success"] for r in records)
    deny = sum(r["permission"] == "DENY" for r in records)
    infra = sum(bool(r["infrastructure_error"]) for r in records)
    result = {
        "schema_version": "sable.execution_campaign.v1.4",
        "campaign_id": campaign_id,
        "model": args.model,
        "provider": args.base_url,
        "task_set": args.tasks,
        "repetition_count": args.repeats,
        "observation_count": n,
        "sample_quality": "rate_estimate" if n >= 10 else "observations_only",
        "minimum_observations_for_rate_estimate": 10,
        "verified_task_success_rate": allow / (allow + deny) if allow + deny else None,
        "counts": {
            "verified_allow": allow,
            "verified_deny": deny,
            "infrastructure_failure": infra,
            "other": n - allow - deny,
        },
        "all_replay_matches": all(r["replay_match"] is True for r in records),
        "records": records,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
