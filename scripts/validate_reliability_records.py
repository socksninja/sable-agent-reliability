#!/usr/bin/env python3
"""Validate SABLE public Reliability Records without trusting model claims."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NON_RECORD_PREFIXES = ("RELIABILITY_MATRIX_", "FAILURE_TAXONOMY_", "ADVERSARIAL_FAMILY_COVERAGE_")


def fail(message: str) -> None:
    raise SystemExit(f"INVALID_RECORD: {message}")


def validate(path: Path) -> None:
    obj = json.loads(path.read_text(encoding="utf-8"))
    required = ["schema_version", "record_id", "generated_at", "benchmark", "model", "runtime", "n", "native_tool_call_rate", "task_success_rate", "task_successes", "model_errors", "environment_mutations", "provenance", "artifact"]
    for key in required:
        if key not in obj:
            fail(f"{path}: missing {key}")
    if obj["schema_version"] != "sable.reliability_record.v0.1":
        fail(f"{path}: unsupported schema_version")
    n = obj["n"]
    if not isinstance(n, int) or n < 1:
        fail(f"{path}: n must be positive integer")
    for key in ("native_tool_call_rate", "task_success_rate"):
        value = obj[key]
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            fail(f"{path}: {key} out of range")
    if obj["task_successes"] < 0 or obj["task_successes"] > n:
        fail(f"{path}: task_successes out of range")
    if abs(obj["task_success_rate"] - obj["task_successes"] / n) > 1e-9:
        fail(f"{path}: task_success_rate does not match task_successes/n")
    provenance = obj["provenance"]
    if provenance.get("source") != "GitHub Actions":
        fail(f"{path}: provenance source is not GitHub Actions")
    if not isinstance(provenance.get("run_id"), int) or provenance["run_id"] < 1:
        fail(f"{path}: invalid run_id")
    if not isinstance(provenance.get("job_id"), int) or provenance["job_id"] < 1:
        fail(f"{path}: invalid job_id")
    if not HEX40.fullmatch(provenance.get("commit", "")):
        fail(f"{path}: invalid provenance commit")
    artifact = obj["artifact"]
    if not isinstance(artifact.get("artifact_id"), int) or artifact["artifact_id"] < 1:
        fail(f"{path}: invalid artifact_id")
    if not HEX64.fullmatch(artifact.get("sha256", "")):
        fail(f"{path}: invalid artifact sha256")


def main() -> None:
    paths = sorted(
        p for p in RECORDS.glob("*.json") if not p.name.startswith(NON_RECORD_PREFIXES)
    )
    if not paths:
        fail("no records found")
    for path in paths:
        validate(path)
    print(f"VALID_RELIABILITY_RECORDS={len(paths)}")
    print("RECORD_IDS=" + json.dumps([json.loads(p.read_text(encoding="utf-8"))["record_id"] for p in paths]))


if __name__ == "__main__":
    main()
