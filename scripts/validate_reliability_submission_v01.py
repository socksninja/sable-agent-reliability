#!/usr/bin/env python3
"""Validate an externally submitted SABLE Reliability Record."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = [
    "schema_version", "record_id", "generated_at", "benchmark", "model",
    "runtime", "n", "native_tool_call_rate", "task_success_rate",
    "task_successes", "model_errors", "environment_mutations", "task_results",
    "provenance", "artifact",
]


def fail(msg: str) -> None:
    raise SystemExit(f"INVALID_SUBMISSION: {msg}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_reliability_submission_v01.py PATH")
    path = Path(sys.argv[1])
    obj = json.loads(path.read_text(encoding="utf-8"))

    for key in REQUIRED:
        if key not in obj:
            fail(f"missing {key}")
    if obj["schema_version"] != "sable.reliability_record.v0.1":
        fail("unsupported schema_version")

    n = obj["n"]
    results = obj["task_results"]
    if not isinstance(n, int) or n < 1:
        fail("n must be a positive integer")
    if not isinstance(results, list) or len(results) != n:
        fail("task_results length must equal n")
    if not isinstance(obj["task_successes"], int) or not 0 <= obj["task_successes"] <= n:
        fail("task_successes out of range")
    expected_rate = obj["task_successes"] / n
    if abs(obj["task_success_rate"] - expected_rate) > 1e-9:
        fail("task_success_rate does not equal task_successes/n")
    if not isinstance(obj["model_errors"], int) or obj["model_errors"] < 0:
        fail("model_errors must be a non-negative integer")
    if not isinstance(obj["environment_mutations"], int) or obj["environment_mutations"] < 0:
        fail("environment_mutations must be a non-negative integer")
    for key in ("native_tool_call_rate", "task_success_rate"):
        if not isinstance(obj[key], (int, float)) or not 0 <= obj[key] <= 1:
            fail(f"{key} out of range")

    observed_successes = 0
    observed_native = 0
    for i, result in enumerate(results, 1):
        for key in ("task_id", "task_success", "tool_call_count", "native_tool_call", "observed_environment", "agent_action_outcome"):
            if key not in result:
                fail(f"task_results[{i}] missing {key}")
        if result["task_success"]:
            observed_successes += 1
        if result["native_tool_call"]:
            observed_native += 1
        if not isinstance(result["tool_call_count"], int) or result["tool_call_count"] < 0:
            fail(f"task_results[{i}] invalid tool_call_count")
        if not isinstance(result["observed_environment"], dict):
            fail(f"task_results[{i}] observed_environment must be an object")

    if observed_successes != obj["task_successes"]:
        fail("task_successes does not match task_results")
    if abs(obj["native_tool_call_rate"] - observed_native / n) > 1e-9:
        fail("native_tool_call_rate does not match task_results")

    provenance = obj["provenance"]
    if provenance.get("source") != "GitHub Actions":
        fail("provenance.source must be GitHub Actions")
    if not isinstance(provenance.get("run_id"), int) or provenance["run_id"] < 1:
        fail("invalid provenance.run_id")
    if not isinstance(provenance.get("job_id"), int) or provenance["job_id"] < 1:
        fail("invalid provenance.job_id")
    if not HEX40.fullmatch(provenance.get("commit", "")):
        fail("invalid provenance.commit")

    artifact = obj["artifact"]
    if not isinstance(artifact.get("artifact_id"), int) or artifact["artifact_id"] < 1:
        fail("invalid artifact.artifact_id")
    if not HEX64.fullmatch(artifact.get("sha256", "")):
        fail("invalid artifact.sha256")

    print(f"VALID_EXTERNAL_SUBMISSION={path}")
    print(f"MODEL={obj['model']}")
    print(f"N={n}")
    print(f"TASK_SUCCESS_RATE={obj['task_success_rate']}")
    print(f"NATIVE_TOOL_CALL_RATE={obj['native_tool_call_rate']}")


if __name__ == "__main__":
    main()
