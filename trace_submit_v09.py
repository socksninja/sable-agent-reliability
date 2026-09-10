#!/usr/bin/env python3
"""Validate and normalize SABLE v0.9 external trace submissions.

Input: JSONL, one sable.submission.v0.9 envelope per line.
Output: JSONL of sable.v0.5 traces, preserving submission provenance.
No model provider or network access is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PROTOCOL = "sable.submission.v0.9"
STEP_REQUIRED = {"tool", "args", "observed_result", "before_state_hash", "after_state_hash"}
CLAIMED = {"success", "failure", "uncertain"}


def canonical_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_envelope(row: dict) -> None:
    required = {"protocol_version", "submission_id", "source", "trace", "provenance", "integrity"}
    missing = required - set(row)
    if missing:
        raise ValueError(f"missing required envelope fields: {sorted(missing)}")
    if row["protocol_version"] != PROTOCOL:
        raise ValueError(f"protocol_version must be {PROTOCOL}")
    source = row["source"]
    for key in ("agent_name", "agent_version", "framework", "framework_version", "adapter"):
        if not isinstance(source.get(key), str) or not source[key]:
            raise ValueError(f"source.{key} must be a non-empty string")
    provenance = row["provenance"]
    for key in ("captured_at", "collector", "redaction_policy"):
        if not isinstance(provenance.get(key), str) or not provenance[key]:
            raise ValueError(f"provenance.{key} must be a non-empty string")
    integrity = row["integrity"]
    if integrity.get("hash_algorithm") != "sha256":
        raise ValueError("integrity.hash_algorithm must be sha256")
    if integrity.get("canonicalization") != "json-sort-keys-utf8":
        raise ValueError("integrity.canonicalization must be json-sort-keys-utf8")
    expected = canonical_hash(row["trace"])
    if integrity.get("source_trace_hash") != expected:
        raise ValueError("integrity.source_trace_hash does not match trace")


def normalize_envelope(row: dict) -> dict:
    validate_envelope(row)
    trace = row["trace"]
    for key in ("task_id", "goal", "agent", "steps", "claimed_status", "environment", "integrity"):
        if key not in trace:
            raise ValueError(f"trace missing required field: {key}")
    if trace["claimed_status"] not in CLAIMED:
        raise ValueError("trace.claimed_status must be success|failure|uncertain")

    steps = []
    for i, step in enumerate(trace["steps"]):
        missing = STEP_REQUIRED - set(step)
        if missing:
            raise ValueError(f"trace step {i}: missing {sorted(missing)}")
        steps.append({
            "tool": str(step["tool"]),
            "args": step.get("args") or {},
            "observed_result": step.get("observed_result") or {"ok": False, "message": "missing_observed_result"},
            "before_state_hash": str(step["before_state_hash"]),
            "after_state_hash": str(step["after_state_hash"]),
            **({"state_after": step["state_after"]} if "state_after" in step else {}),
        })

    normalized = {
        "schema_version": "sable.v0.5",
        "task_id": str(trace["task_id"]),
        "goal": str(trace["goal"]),
        "agent": dict(trace["agent"] or {}),
        "steps": steps,
        "claimed_status": trace["claimed_status"],
        "final_report": str(trace.get("final_report", "")),
        "environment": dict(trace["environment"] or {}),
        "integrity": dict(trace["integrity"] or {}),
        "submission": {
            "schema_version": PROTOCOL,
            "submission_id": str(row["submission_id"]),
            "source": dict(row["source"]),
            "provenance": dict(row["provenance"]),
            "source_trace_hash": row["integrity"]["source_trace_hash"],
        },
    }
    return normalized


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate and normalize SABLE v0.9 trace submissions")
    ap.add_argument("--input", required=True, help="Input JSONL of v0.9 submission envelopes")
    ap.add_argument("--output", required=True, help="Output JSONL of SABLE v0.5 traces")
    args = ap.parse_args()

    rows = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    normalized = [normalize_envelope(row) for row in rows]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in normalized)
        + ("\n" if normalized else ""),
        encoding="utf-8",
    )
    print(f"accepted {len(normalized)} SABLE v0.9 submissions")


if __name__ == "__main__":
    main()
