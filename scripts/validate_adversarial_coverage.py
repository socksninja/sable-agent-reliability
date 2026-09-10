#!/usr/bin/env python3
"""Validate the published SABLE adversarial-family coverage manifest."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "records" / "ADVERSARIAL_FAMILY_COVERAGE_V0.1.json"

EXPECTED_FAMILY_COUNT = 10
EXPECTED_TASKS_PER_FAMILY = 12
EXPECTED_ADVERSARIAL_TASKS = 120
EXPECTED_TOTAL_TASKS = 140


def main() -> None:
    obj = json.loads(MANIFEST.read_text(encoding="utf-8"))
    families = obj.get("families")
    if obj.get("schema_version") != "sable.adversarial_family_coverage.v0.1":
        raise SystemExit("INVALID_COVERAGE_SCHEMA")
    if not isinstance(families, list) or len(families) != EXPECTED_FAMILY_COUNT:
        raise SystemExit("INVALID_FAMILY_COUNT")
    names = [item.get("family") for item in families]
    if len(set(names)) != EXPECTED_FAMILY_COUNT or any(not name for name in names):
        raise SystemExit("INVALID_FAMILY_NAMES")
    counts = [item.get("task_count") for item in families]
    if any(count != EXPECTED_TASKS_PER_FAMILY for count in counts):
        raise SystemExit("INVALID_TASK_DISTRIBUTION")
    if obj.get("adversarial_task_count") != EXPECTED_ADVERSARIAL_TASKS:
        raise SystemExit("INVALID_ADVERSARIAL_TASK_COUNT")
    if obj.get("total_task_count") != EXPECTED_TOTAL_TASKS:
        raise SystemExit("INVALID_TOTAL_TASK_COUNT")
    if sum(counts) != EXPECTED_ADVERSARIAL_TASKS:
        raise SystemExit("INVALID_FAMILY_SUM")
    print("ADVERSARIAL_COVERAGE=PASS")
    print(f"FAMILIES={len(families)}")
    print(f"ADVERSARIAL_TASKS={sum(counts)}")
    print(f"TOTAL_TASKS={obj.get('total_task_count')}")


if __name__ == "__main__":
    main()
