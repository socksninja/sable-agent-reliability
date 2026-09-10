#!/usr/bin/env python3
"""SABLE v0.8 external agent trace ingestion and normalization.

Accepts JSONL traces from arbitrary agents and normalizes them into the
SABLE v0.5 trace contract without requiring a live model provider.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

SCHEMA = "sable.ingest.v0.8"

REQUIRED = {"task_id", "goal", "agent", "steps", "claimed_status", "environment", "integrity"}
STEP_REQUIRED = {"tool", "args", "observed_result", "before_state_hash", "after_state_hash"}


def canonical_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_step(step: dict) -> dict:
    out = {
        "tool": str(step.get("tool", "")),
        "args": step.get("args") or {},
        "observed_result": step.get("observed_result") or {"ok": False, "message": "missing_observed_result"},
        "before_state_hash": str(step.get("before_state_hash", "")),
        "after_state_hash": str(step.get("after_state_hash", "")),
    }
    if "state_after" in step:
        out["state_after"] = step["state_after"]
    return out


def normalize(row: dict) -> dict:
    missing = REQUIRED - set(row)
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    steps = [normalize_step(s) for s in row["steps"]]
    for i, s in enumerate(steps):
        sm = STEP_REQUIRED - set(s)
        if sm:
            raise ValueError(f"step {i}: missing {sorted(sm)}")
    claimed = row.get("claimed_status", "uncertain")
    if claimed not in {"success", "failure", "uncertain"}:
        raise ValueError("claimed_status must be success|failure|uncertain")
    environment = dict(row.get("environment") or {})
    integrity = dict(row.get("integrity") or {})
    normalized = {
        "schema_version": "sable.v0.5",
        "task_id": str(row["task_id"]),
        "goal": str(row["goal"]),
        "agent": dict(row.get("agent") or {}),
        "steps": steps,
        "claimed_status": claimed,
        "final_report": str(row.get("final_report", "")),
        "environment": environment,
        "integrity": integrity,
        "ingestion": {
            "schema_version": SCHEMA,
            "source_schema": str(row.get("schema_version", "unknown")),
            "trace_hash": canonical_hash({k: v for k, v in row.items() if k != "ingestion"}),
        },
    }
    return normalized


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    rows = [json.loads(x) for x in Path(args.input).read_text(encoding="utf-8").splitlines() if x.strip()]
    normalized = [normalize(r) for r in rows]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in normalized) + ("\n" if normalized else ""), encoding="utf-8")
    print(f"ingested {len(normalized)} traces")

if __name__ == "__main__":
    main()
