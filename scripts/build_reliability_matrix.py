#!/usr/bin/env python3
"""Build a deterministic cross-record Reliability Matrix from public Records."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = sorted((ROOT / "records").glob("*.json"))
OUT_JSON = ROOT / "records" / "RELIABILITY_MATRIX_V0.1.json"
OUT_MD = ROOT / "docs" / "RELIABILITY_MATRIX_V0.1.md"


def main() -> None:
    if not RECORDS:
        raise SystemExit("NO_RELIABILITY_RECORDS")
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in RECORDS]
    rows.sort(key=lambda r: (r["model"], r["record_id"]))
    matrix = {
        "schema_version": "sable.reliability_matrix.v0.1",
        "benchmark": "SABLE-Reliability-Corpus-v0.1",
        "record_count": len(rows),
        "records": [
            {
                "record_id": r["record_id"],
                "model": r["model"],
                "runtime": r["runtime"],
                "n": r["n"],
                "task_success_rate": r["task_success_rate"],
                "native_tool_call_rate": r["native_tool_call_rate"],
                "task_successes": r["task_successes"],
                "model_errors": r["model_errors"],
                "environment_mutations": r["environment_mutations"],
            }
            for r in rows
        ],
    }
    OUT_JSON.write_text(json.dumps(matrix, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# SABLE Reliability Matrix v0.1",
        "",
        "This matrix compares only versioned SABLE Reliability Records using the same benchmark contract. It is descriptive evidence, not a general safety ranking.",
        "",
        "| Model | Runtime | N | Task success | Native tool calls | Model errors | Environment mutations |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['model']}` | `{r['runtime']['server']}` | {r['n']} | {r['task_success_rate']:.3f} | {r['native_tool_call_rate']:.3f} | {r['model_errors']} | {r['environment_mutations']} |"
        )
    lines += [
        "",
        f"Records included: **{len(rows)}**.",
        "",
        "The matrix becomes more informative as independently executed model/runtime records accumulate under the same corpus and schema.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(matrix, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
