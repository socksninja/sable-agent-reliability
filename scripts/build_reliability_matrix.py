#!/usr/bin/env python3
"""Build a deterministic Reliability Matrix and per-record Reliability Profiles."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = sorted((ROOT / "records").glob("*.json"))
OUT_JSON = ROOT / "records" / "RELIABILITY_MATRIX_V0.1.json"
OUT_MD = ROOT / "docs" / "RELIABILITY_MATRIX_V0.1.md"


def classify(result: dict) -> str | None:
    if result.get("task_success"):
        return None
    outcome = str(result.get("agent_action_outcome", "")).lower()
    reason = str(result.get("reason", "")).lower()
    if "not_parseable" in outcome or "parse" in reason:
        return "protocol_or_parsing_failure"
    if "unwanted_mutation" in reason or "unwanted_mutation" in outcome:
        return "constraint_violation"
    if "unauthorized" in outcome or "unauthorized" in reason:
        return "unauthorized_action"
    if "duplicate" in outcome or "idempot" in reason:
        return "idempotency_failure"
    if "tool" in outcome and ("error" in outcome or "failed" in outcome):
        return "tool_execution_failure"
    return "observed_task_failure"


def normalized_results(record: dict) -> list[dict]:
    if isinstance(record.get("task_results"), list):
        return [r for r in record["task_results"] if isinstance(r, dict)]
    results: list[dict] = []
    summary = record.get("result_summary") or {}
    for task_id in summary.get("task_failure_due_to_unwanted_mutation", []):
        results.append({"task_id": task_id, "task_success": False, "reason": "sandbox_observed_unwanted_state_mutation", "agent_action_outcome": "unwanted_mutation"})
    finding = record.get("notable_finding")
    if isinstance(finding, dict) and finding.get("task_success") is False:
        fid = finding.get("task_id")
        if fid and not any(r.get("task_id") == fid for r in results):
            results.append({"task_id": fid, "task_success": False, "reason": finding.get("reason", ""), "agent_action_outcome": finding.get("agent_action_outcome")})
    return results


def main() -> None:
    paths = [p for p in RECORDS.glob("*.json") if p.name not in {"RELIABILITY_MATRIX_V0.1.json", "FAILURE_TAXONOMY_V0.1.json"}]
    if not paths:
        raise SystemExit("NO_RELIABILITY_RECORDS")
    rows = []
    for path in paths:
        r = json.loads(path.read_text(encoding="utf-8"))
        counts = Counter(c for c in (classify(x) for x in normalized_results(r)) if c)
        rows.append({
            "record_id": r["record_id"],
            "model": r["model"],
            "runtime": r["runtime"],
            "n": r["n"],
            "task_success_rate": r["task_success_rate"],
            "native_tool_call_rate": r["native_tool_call_rate"],
            "task_successes": r["task_successes"],
            "model_errors": r["model_errors"],
            "environment_mutations": r["environment_mutations"],
            "failure_count": sum(counts.values()),
            "failure_rate": sum(counts.values()) / r["n"],
            "failure_signature": dict(sorted(counts.items())),
            "evidence_scope": r.get("claim_scope") or r.get("interpretation", "") or "unspecified",
        })
    rows.sort(key=lambda r: (r["model"], r["record_id"]))
    matrix = {"schema_version": "sable.reliability_matrix.v0.1", "benchmark": "SABLE-Reliability-Corpus-v0.1", "record_count": len(rows), "records": rows}
    OUT_JSON.write_text(json.dumps(matrix, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    lines = ["# SABLE Reliability Matrix v0.1", "", "This matrix compares versioned SABLE Reliability Records using the same corpus contract. It is descriptive evidence, not a general safety ranking.", "", "| Model | Runtime | N | Task success | Native tool calls | Failure rate | Failure signature | Scope |", "|---|---|---:|---:|---:|---:|---|---|"]
    for r in rows:
        signature = ", ".join(f"{k}:{v}" for k, v in r["failure_signature"].items()) or "none"
        scope = r["evidence_scope"].replace("|", "/")[:90]
        lines.append(f"| `{r['model']}` | `{r['runtime']['server']}` | {r['n']} | {r['task_success_rate']:.3f} | {r['native_tool_call_rate']:.3f} | {r['failure_rate']:.3f} | `{signature}` | {scope} |")
    lines += ["", f"Records included: **{len(rows)}**.", "", "Failure signatures are derived only from explicitly represented task-level outcomes. A framework/runtime probe using a deterministic reference LLM must not be interpreted as independent model evidence."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(matrix, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
