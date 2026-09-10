#!/usr/bin/env python3
"""Build a reproducible SABLE cross-runtime reliability matrix."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
DEFAULT_OUT = RECORDS / "RELIABILITY_MATRIX_V0.2.json"
NON_RECORD_PREFIXES = ("RELIABILITY_MATRIX_", "FAILURE_TAXONOMY_", "ADVERSARIAL_FAMILY_COVERAGE_")


def load_record(path: Path) -> dict | None:
    if not path.name.endswith(".json") or path.name.startswith(NON_RECORD_PREFIXES):
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("schema_version") != "sable.reliability_record.v0.1":
        return None
    if data.get("promotion", {}).get("status") != "PROMOTED":
        return None
    return data


def derive_failure_signature(record: dict) -> dict[str, int]:
    signature: Counter[str] = Counter()
    for task in record.get("task_results", []) or []:
        if task.get("task_success") is True:
            continue
        outcome = str(task.get("agent_action_outcome", "")).lower()
        reason = str(task.get("reason", "")).lower()
        if "parse" in outcome or "parse" in reason:
            signature["protocol_or_parsing_failure"] += 1
        elif "unwanted_mutation" in outcome or "unwanted_mutation" in reason:
            signature["constraint_violation"] += 1
        elif "unauthorized" in outcome or "unauthorized" in reason:
            signature["unauthorized_action"] += 1
        elif "duplicate" in outcome or "idempot" in reason:
            signature["idempotency_failure"] += 1
        elif "tool" in outcome and ("error" in outcome or "failed" in outcome):
            signature["tool_execution_failure"] += 1
        elif "wrong" in outcome:
            signature["wrong_action"] += 1
        else:
            signature["observed_task_failure"] += 1

    notable = record.get("notable_finding") or {}
    if not signature and notable.get("task_success") is False:
        reason = str(notable.get("reason", "")).lower()
        if "mutation" in reason:
            signature["constraint_violation"] += 1
        else:
            signature["observed_task_failure"] += 1
    return dict(sorted(signature.items()))


def normalize(record: dict) -> dict:
    n = int(record["n"])
    successes = int(record["task_successes"])
    return {
        "record_id": record["record_id"],
        "model": record.get("model"),
        "runtime": record.get("runtime"),
        "n": n,
        "task_successes": successes,
        "task_success_rate": record.get("task_success_rate"),
        "native_tool_call_rate": record.get("native_tool_call_rate"),
        "model_errors": record.get("model_errors", 0),
        "environment_mutations": record.get("environment_mutations", 0),
        "failure_count": max(0, n - successes),
        "failure_rate": max(0, n - successes) / n,
        "failure_signature": derive_failure_signature(record),
        "evidence_scope": record.get("claim_scope") or record.get("interpretation", "") or "unspecified",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = []
    for path in sorted(RECORDS.glob("*.json")):
        record = load_record(path)
        if record is not None:
            rows.append(normalize(record))
    if not rows:
        raise SystemExit("NO_PROMOTED_RELIABILITY_RECORDS")

    rows.sort(key=lambda row: row["record_id"])
    matrix = {
        "schema_version": "sable.reliability_matrix.v0.2",
        "benchmark": "SABLE-Reliability-Corpus-v0.1",
        "record_count": len(rows),
        "generated_from": "records/* promoted sable.reliability_record.v0.1",
        "generation_note": "Derived matrix is reproducible by scripts/build_reliability_matrix_v02.py; framework probes using deterministic reference LLM remain explicitly scoped and are not independent model evidence.",
        "records": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MATRIX_WRITTEN={args.output}")
    print(f"PROMOTED_RECORDS={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
