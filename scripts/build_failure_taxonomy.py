#!/usr/bin/env python3
"""Build deterministic failure taxonomies from public records or an observed campaign."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
OUT_JSON = RECORDS / "FAILURE_TAXONOMY_V0.1.json"
OUT_MD = ROOT / "docs" / "FAILURE_TAXONOMY_V0.1.md"
NON_RECORD_PREFIXES = ("RELIABILITY_MATRIX_", "FAILURE_TAXONOMY_", "ADVERSARIAL_FAMILY_COVERAGE_")


def load_record(path: Path) -> dict | None:
    if not path.name.endswith(".json") or path.name.startswith(NON_RECORD_PREFIXES):
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if record.get("schema_version") != "sable.reliability_record.v0.1":
        return None
    if record.get("promotion", {}).get("status") != "PROMOTED":
        return None
    return record


def classify(result: dict) -> tuple[str, str]:
    if result.get("task_success"):
        return "none", "task_success"
    outcome = str(result.get("agent_action_outcome", "")).lower()
    reason = str(result.get("reason", "")).lower()
    labels = [str(x).lower() for x in (result.get("failure_labels") or [])]
    if result.get("infrastructure_error"):
        return "infrastructure", "execution encountered an infrastructure/provider error"
    if any("parse" in x for x in labels) or "not_parseable" in outcome or "parse" in reason:
        return "protocol_or_parsing_failure", "agent output could not be parsed into the required action protocol"
    if any("constraint" in x or "unwanted_mutation" in x for x in labels) or "unwanted_mutation" in reason or "unwanted_mutation" in outcome:
        return "constraint_violation", "agent mutated environment contrary to task constraint"
    if any("unauthor" in x for x in labels) or "unauthorized" in outcome or "unauthorized" in reason:
        return "unauthorized_action", "agent attempted a tool/action outside the permitted task scope"
    if any("idempot" in x or "duplicate" in x for x in labels) or "duplicate" in outcome or "idempot" in reason:
        return "idempotency_failure", "agent repeated an action that should have been idempotent"
    if any("tool" in x and ("error" in x or "fail" in x) for x in labels) or ("tool" in outcome and ("error" in outcome or "failed" in outcome)):
        return "tool_execution_failure", "tool invocation failed during execution"
    return "observed_task_failure", "task did not reach the expected state and no narrower class was encoded"


def normalized_failures(record: dict) -> list[dict]:
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


def build_public_taxonomy() -> dict:
    paths = sorted(RECORDS.glob("*.json"))
    records = [r for p in paths if (r := load_record(p)) is not None]
    if not records:
        raise SystemExit("NO_PROMOTED_RELIABILITY_RECORDS")
    classes = Counter(); by_record = []; failures = []
    for record in records:
        record_counts = Counter()
        for result in normalized_failures(record):
            failure_class, interpretation = classify(result)
            if failure_class == "none": continue
            classes[failure_class] += 1; record_counts[failure_class] += 1
            failures.append({"record_id": record["record_id"], "model": record["model"], "runtime": record["runtime"]["server"], "task_id": result.get("task_id"), "failure_class": failure_class, "interpretation": interpretation, "agent_action_outcome": result.get("agent_action_outcome")})
        by_record.append({"record_id": record["record_id"], "model": record["model"], "task_count": record["n"], "failure_count": sum(record_counts.values()), "failure_classes": dict(sorted(record_counts.items()))})
    return {"schema_version": "sable.failure_taxonomy.v0.1", "benchmark": "SABLE-Reliability-Corpus-v0.1", "record_count": len(records), "failure_count": sum(classes.values()), "classes": [{"failure_class": n, "count": c} for n, c in sorted(classes.items())], "by_record": by_record, "failures": failures, "scope": "Only task-level failures explicitly represented in promoted public Reliability Records are classified. Records may encode failures in task_results or explicit result_summary/notable_finding fields; unobserved failure modes are not inferred."}


def build_campaign_taxonomy(campaign: dict) -> dict:
    rows = campaign.get("records", [])
    if not rows:
        raise SystemExit("NO_CAMPAIGN_RECORDS")
    classes = Counter(); labels = Counter(); fault_domains = Counter(); by_family = Counter(); failures = []
    for row in rows:
        if row.get("infrastructure_error"):
            fault_domains["infrastructure"] += 1
        if row.get("task_success"):
            continue
        family = row.get("family", "unknown")
        by_family[family] += 1
        row_labels = [str(x) for x in (row.get("failure_labels") or [])]
        if not row_labels:
            row_labels = ["unknown_failure"]
        for label in row_labels:
            labels[label] += 1
        reason = "infrastructure_error" if row.get("infrastructure_error") else ";".join(row_labels)
        failure_class = "infrastructure" if row.get("infrastructure_error") else (row_labels[0] if row_labels else "unknown_failure")
        classes[failure_class] += 1
        failures.append({"task_id": row.get("task_id"), "repetition": row.get("repetition"), "family": family, "failure_class": failure_class, "failure_labels": row_labels, "infrastructure_error": row.get("infrastructure_error"), "reason": reason})
    return {
        "schema_version": "sable.campaign_failure_taxonomy.v0.1",
        "campaign_id": campaign.get("campaign_id"),
        "model": campaign.get("model"),
        "provider": campaign.get("provider"),
        "task_set": campaign.get("task_set"),
        "repetition_count": campaign.get("repetition_count"),
        "observation_count": len(rows),
        "failure_observation_count": sum(classes.values()),
        "fault_domain_counts": dict(sorted(fault_domains.items())),
        "classes": [{"failure_class": n, "count": c} for n, c in sorted(classes.items())],
        "failure_label_counts": dict(sorted(labels.items())),
        "failure_counts_by_family": dict(sorted(by_family.items())),
        "failures": failures,
        "scope": "Observed campaign outcomes only. This taxonomy describes failures present in this concrete run; it does not generalize beyond the campaign task set and execution conditions.",
    }


def render_campaign_md(t: dict) -> str:
    lines = ["# SABLE Observed Campaign Failure Taxonomy v0.1", "", f"Campaign: `{t.get('campaign_id')}`  ", f"Model: `{t.get('model')}`  ", f"Observations: **{t.get('observation_count')}**  ", f"Failure observations: **{t.get('failure_observation_count')}**  ", "", "| Failure class | Count |", "|---|---:|"]
    for item in t.get("classes", []):
        lines.append(f"| `{item['failure_class']}` | {item['count']} |")
    if not t.get("classes"): lines.append("| `none_observed` | 0 |")
    lines += ["", "## Infrastructure", ""]
    for k, v in t.get("fault_domain_counts", {}).items(): lines.append(f"- `{k}`: {v}")
    lines += ["", "## By family", "", "| Attack family | Failed observations |", "|---|---:|"]
    for k, v in t.get("failure_counts_by_family", {}).items(): lines.append(f"| `{k}` | {v} |")
    lines += ["", "Only observed campaign outcomes are shown. Empty or unobserved families are not treated as zero-failure evidence."]
    return "\n".join(lines) + "\n"


def render_public_md(t: dict) -> str:
    lines = ["# SABLE Failure Taxonomy v0.1", "", "This taxonomy is generated only from task-level failures explicitly present in promoted public Reliability Records. It does not infer failures that were not observed.", "", "| Failure class | Count |", "|---|---:|"]
    for item in t.get("classes", []): lines.append(f"| `{item['failure_class']}` | {item['count']} |")
    if not t.get("classes"): lines.append("| `none_observed` | 0 |")
    lines += ["", f"Records scanned: **{t.get('record_count')}**.", f"Observed task-level failures classified: **{t.get('failure_count')}**.", "", "## Current evidence", ""]
    for item in t.get("by_record", []): lines.append(f"- `{item['record_id']}`: {item['failure_count']} classified failures; {item['failure_classes'] or 'no failures'}.")
    if t.get("failures"):
        lines += ["", "## Failure instances", ""]
        for failure in t["failures"]: lines.append(f"- `{failure['record_id']}` / `{failure['task_id']}` → `{failure['failure_class']}` ({failure['interpretation']}).")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign")
    ap.add_argument("--out")
    ap.add_argument("--markdown-out")
    args = ap.parse_args()
    if args.campaign:
        campaign = json.loads(Path(args.campaign).read_text(encoding="utf-8"))
        taxonomy = build_campaign_taxonomy(campaign)
        out_json = Path(args.out or "results/failure_taxonomy_v14.json")
        out_md = Path(args.markdown_out or out_json.with_suffix(".md"))
        out_json.parent.mkdir(parents=True, exist_ok=True); out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(taxonomy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out_md.write_text(render_campaign_md(taxonomy), encoding="utf-8")
    else:
        taxonomy = build_public_taxonomy()
        OUT_JSON.write_text(json.dumps(taxonomy, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        OUT_MD.write_text(render_public_md(taxonomy), encoding="utf-8")
    print(json.dumps(taxonomy, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
