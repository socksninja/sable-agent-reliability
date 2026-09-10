#!/usr/bin/env python3
"""Run repeated SABLE external-model executions and build an auditable campaign manifest.

Each repetition is isolated into its own raw trace, v0.9 submission, normalized trace,
evidence pack, and permission decision. The campaign summary is only statistical once
it reaches the configured minimum observation count.
"""
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


def canon(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run(cmd: list[str], env: dict[str, str]) -> None:
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def load_jsonl_one(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def wrap_submission(raw: dict, model: str, provider_base_url: str, repetition: int) -> dict:
    trace = {
        "schema_version": "sable.submission.v0.9",
        "task_id": raw["task_id"],
        "goal": raw["goal"],
        "agent": {
            **raw["agent"],
            "framework": "SABLE native external-model runner",
            "framework_version": "v0.3",
            "model": model,
            "provider_base_url": provider_base_url,
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
            "collector": "SABLE external-model campaign v1.3 collector",
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
    ap.add_argument("--tasks", default="integrations/external_model/task.json")
    ap.add_argument("--out", default="results/external_model_campaign_v13.json")
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
        normalized = prefix.with_name(prefix.name + "_sable_v05.jsonl")
        evaluation = prefix.with_name(prefix.name + "_evaluation.json")
        evidence = prefix.with_name(prefix.name + "_evidence.json")
        permission = prefix.with_name(prefix.name + "_permission.json")

        run([sys.executable, "real_agent_runner.py", "--tasks", args.tasks, "--out", str(raw), "--base-url", args.base_url, "--model", args.model, "--max-turns", str(args.max_turns), "--thinking", args.thinking], env)
        raw_obj = load_jsonl_one(raw)
        sub = wrap_submission(raw_obj, args.model, args.base_url, repetition)
        submission.write_text(json.dumps(sub, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        run([sys.executable, "trace_submit_v09.py", "--input", str(submission), "--output", str(normalized)], env)
        run([sys.executable, "evaluator.py", "--tasks", args.tasks, "--traces", str(normalized), "--out", str(evaluation)], env)
        run([sys.executable, "evidence_v06.py", "--tasks", args.tasks, "--results", str(normalized), "--out", str(evidence)], env)
        run([sys.executable, "permission_v01.py", "--input", str(normalized), "--output", str(permission)], env)

        ev = json.loads(evidence.read_text(encoding="utf-8"))
        pm = json.loads(permission.read_text(encoding="utf-8"))
        records.append({
            "repetition": repetition,
            "task_id": ev["task"]["task_id"],
            "model": args.model,
            "provider": args.base_url,
            "runtime": ev["agent"]["framework"],
            "framework_version": ev["agent"]["framework_version"],
            "task_success": ev["outcome"]["task_success"],
            "replay_match": ev["replay"]["replay_match"],
            "permission": pm["decision"],
            "failure_labels": ev["outcome"].get("failure_labels", []),
            "infrastructure_error": ev.get("execution", {}).get("infrastructure_error") or ev.get("integrity", {}).get("infrastructure_error"),
            "evidence_hash": ev.get("evidence_hash"),
        })

    verified = [r for r in records if r["permission"] == "ALLOW" and r["task_success"] is True]
    denied = [r for r in records if r["permission"] == "DENY"]
    infra = [r for r in records if r["infrastructure_error"]]
    rates_allowed = len(records) >= 5
    result = {
        "schema_version": "sable.execution_campaign.v1.3",
        "campaign_id": campaign_id,
        "model": args.model,
        "provider": args.base_url,
        "repetition_count": len(records),
        "sample_quality": "rate_estimate" if rates_allowed else "observations_only",
        "minimum_observations_for_rate_estimate": 5,
        "counts": {
            "verified_allow": len(verified),
            "verified_deny": len(denied),
            "infrastructure_failure": len(infra),
            "other": len(records) - len(verified) - len(denied) - len(infra),
        },
        "verified_task_success_rate": (len(verified) / (len(verified) + len(denied))) if (verified or denied) else None,
        "infrastructure_failure_rate": (len(infra) / len(records)) if records else None,
        "all_replay_matches": all(r["replay_match"] is True for r in records),
        "records": records,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
