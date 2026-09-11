#!/usr/bin/env python3
"""Build a 10-family reliability heatmap from a SABLE campaign result."""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED_FAMILIES = [
    "authorization",
    "constraint_confusion",
    "cross_step_memory",
    "error_recovery",
    "idempotency",
    "long_horizon",
    "overclaim",
    "partial_success",
    "state_drift",
    "tool_selection",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    campaign = json.loads(Path(args.campaign).read_text(encoding="utf-8"))
    rows = campaign.get("records", [])
    if not rows:
        raise SystemExit("NO_CAMPAIGN_RECORDS")

    totals = Counter()
    failures = Counter()
    labels = defaultdict(Counter)
    for row in rows:
        family = row.get("family", "unknown")
        totals[family] += 1
        if not row.get("task_success", False):
            failures[family] += 1
            for label in row.get("failure_labels", []) or ["unknown_failure"]:
                labels[family][label] += 1

    families = []
    for family in EXPECTED_FAMILIES + sorted(set(totals) - set(EXPECTED_FAMILIES)):
        n = totals[family]
        f = failures[family]
        families.append({
            "family": family,
            "observations": n,
            "failures": f,
            "failure_rate": (f / n) if n else None,
            "failure_labels": dict(sorted(labels[family].items())),
        })

    heatmap = {
        "schema_version": "sable.campaign_family_heatmap.v0.1",
        "campaign_id": campaign.get("campaign_id"),
        "model": campaign.get("model"),
        "provider": campaign.get("provider"),
        "task_set": campaign.get("task_set"),
        "repetition_count": campaign.get("repetition_count"),
        "observation_count": len(rows),
        "families": families,
        "scope": "Observed campaign outcomes only. Failure rates are descriptive for this campaign and task set; they are not general model reliability claims.",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(heatmap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# SABLE Campaign Family Heatmap v0.1",
        "",
        f"Campaign: `{heatmap['campaign_id']}`  ",
        f"Model: `{heatmap['model']}`  ",
        f"Observations: **{heatmap['observation_count']}**  ",
        "",
        "| Attack family | Observations | Failures | Failure rate | Failure labels |",
        "|---|---:|---:|---:|---|",
    ]
    for item in families:
        rate = "—" if item["failure_rate"] is None else f"{item['failure_rate']:.3f}"
        label_text = ", ".join(f"`{k}`×{v}" for k, v in item["failure_labels"].items()) or "—"
        md.append(f"| `{item['family']}` | {item['observations']} | {item['failures']} | {rate} | {label_text} |")
    md += [
        "",
        "Only observed campaign outcomes are shown. Empty or unobserved families are not treated as zero-failure evidence.",
    ]
    md_path = Path(args.markdown_out) if args.markdown_out else Path(args.out).with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(heatmap, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
