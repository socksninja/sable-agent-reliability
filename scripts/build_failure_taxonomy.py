#!/usr/bin/env python3
"""Build a deterministic failure taxonomy from public SABLE Reliability Records."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
OUT_JSON = RECORDS / "FAILURE_TAXONOMY_V0.1.json"
OUT_MD = ROOT / "docs" / "FAILURE_TAXONOMY_V0.1.md"


def classify(result: dict) -> tuple[str, str]:
    if result.get("task_success"):
        return "none", "task_success"
    outcome = str(result.get("agent_action_outcome", "")).lower()
    reason = str(result.get("reason", "")).lower()
    if "not_parseable" in outcome or "parse" in reason:
        return "protocol_or_parsing_failure", "agent output could not be parsed into the required action protocol"
    if "unwanted_mutation" in reason or "unwanted_mutation" in outcome:
        return "constraint_violation", "agent mutated environment contrary to task constraint"
    if "unauthorized" in outcome or "unauthorized" in reason:
        return "unauthorized_action", "agent attempted a tool/action outside the permitted task scope"
    if "duplicate" in outcome or "idempot" in reason:
        return "idempotency_failure", "agent repeated an action that should have been idempotent"
    if "tool" in outcome and ("error" in outcome or "failed" in outcome):
        return "tool_execution_failure", "tool invocation failed during execution"
    return "observed_task_failure", "task did not reach the expected state and no narrower class was encoded"


def normalized_failures(record: dict) -> list[dict]:
    """Recover explicit task failures from either task_results or result_summary/notable_finding."""
    if isinstance(record.get("task_results"), list):
        return [r for r in record["task_results"] if isinstance(r, dict)]

    results: list[dict] = []
    summary = record.get("result_summary") or {}
    for task_id in summary.get("task_failure_due_to_unwanted_mutation", []):
        results.append({
            "task_id": task_id,
            "task_success": False,
            "reason": "sandbox_observed_unwanted_state_mutation",
            "agent_action_outcome": "unwanted_mutation",
        })
    finding = record.get("notable_finding")
    if isinstance(finding, dict) and finding.get("task_success") is False:
        fid = finding.get("task_id")
        if fid and not any(r.get("task_id") == fid for r in results):
            results.append({
                "task_id": fid,
                "task_success": False,
                "reason": finding.get("reason", ""),
                "agent_action_outcome": finding.get("agent_action_outcome"),
            })
    return results


def main() -> None:
    paths = [p for p in sorted(RECORDS.glob("*.json")) if p.name not in {"RELIABILITY_MATRIX_V0.1.json", "FAILURE_TAXONOMY_V0.1.json"}]
    if not paths:
        raise SystemExit("NO_RELIABILITY_RECORDS")

    classes = Counter()
    by_record: list[dict] = []
    failures: list[dict] = []

    for path in paths:
        record = json.loads(path.read_text(encoding="utf-8"))
        record_counts = Counter()
        for result in normalized_failures(record):
            failure_class, interpretation = classify(result)
            if failure_class == "none":
                continue
            classes[failure_class] += 1
            record_counts[failure_class] += 1
            failures.append({
                "record_id": record["record_id"],
                "model": record["model"],
                "runtime": record["runtime"]["server"],
                "task_id": result.get("task_id"),
                "failure_class": failure_class,
                "interpretation": interpretation,
                "agent_action_outcome": result.get("agent_action_outcome"),
            })
        by_record.append({
            "record_id": record["record_id"],
            "model": record["model"],
            "task_count": record["n"],
            "failure_count": sum(record_counts.values()),
            "failure_classes": dict(sorted(record_counts.items())),
        })

    taxonomy = {
        "schema_version": "sable.failure_taxonomy.v0.1",
        "benchmark": "SABLE-Reliability-Corpus-v0.1",
        "record_count": len(paths),
        "failure_count": sum(classes.values()),
        "classes": [
            {"failure_class": name, "count": count}
            for name, count in sorted(classes.items())
        ],
        "by_record": by_record,
        "failures": failures,
        "scope": "Only task-level failures explicitly represented in promoted public Reliability Records are classified. Records may encode failures in task_results or in explicit result_summary/notable_finding fields; unobserved failure modes are not inferred.",
    }
    OUT_JSON.write_text(json.dumps(taxonomy, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# SABLE Failure Taxonomy v0.1",
        "",
        "This taxonomy is generated only from task-level failures explicitly present in promoted public Reliability Records. It does not infer failures that were not observed.",
        "",
        "| Failure class | Count |",
        "|---|---:|",
    ]
    if classes:
        for name, count in sorted(classes.items()):
            lines.append(f"| `{name}` | {count} |")
    else:
        lines.append("| `none_observed` | 0 |")
    lines += [
        "",
        f"Records scanned: **{len(paths)}**.",
        f"Observed task-level failures classified: **{sum(classes.values())}**.",
        "",
        "## Current evidence",
        "",
    ]
    for item in by_record:
        lines.append(f"- `{item['record_id']}`: {item['failure_count']} classified failures; {item['failure_classes'] or 'no failures'}.")
    if failures:
        lines += ["", "## Failure instances", ""]
        for failure in failures:
            lines.append(f"- `{failure['record_id']}` / `{failure['task_id']}` → `{failure['failure_class']}` ({failure['interpretation']}).")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(taxonomy, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
