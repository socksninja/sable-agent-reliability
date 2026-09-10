#!/usr/bin/env python3
"""Validate the frozen 140-task SABLE benchmark coverage contract."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tasks" / "tasks.json"
EXPANDED = ROOT / "tasks" / "tasks_v0_4_140.json"

EXPECTED_FAMILIES = {
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
}


def fail(msg: str) -> None:
    raise SystemExit(f"INVALID_ADVERSARIAL_COVERAGE: {msg}")


def main() -> None:
    base = json.loads(BASE.read_text(encoding="utf-8"))
    expanded = json.loads(EXPANDED.read_text(encoding="utf-8"))
    if len(base) != 20:
        fail(f"baseline count={len(base)} expected=20")
    if len(expanded) != 140:
        fail(f"expanded count={len(expanded)} expected=140")

    base_ids = [t.get("task_id") for t in base]
    if len(base_ids) != len(set(base_ids)):
        fail("duplicate baseline task_id")

    adv = expanded[len(base):]
    adv_ids = [t.get("task_id") for t in adv]
    if adv_ids != [f"ADV-{i:03d}" for i in range(1, 121)]:
        fail("adversarial task ids are not exactly ADV-001..ADV-120")

    family_counts = Counter(t.get("adversarial_family") for t in adv)
    if set(family_counts) != EXPECTED_FAMILIES:
        fail(f"unexpected families={sorted(set(family_counts) - EXPECTED_FAMILIES)} missing={sorted(EXPECTED_FAMILIES - set(family_counts))}")
    for family in sorted(EXPECTED_FAMILIES):
        if family_counts[family] != 12:
            fail(f"family={family} count={family_counts[family]} expected=12")

    for task in adv:
        if task.get("difficulty") != "hard":
            fail(f"{task.get('task_id')}: difficulty is not hard")
        if task.get("family") != task.get("adversarial_family"):
            fail(f"{task.get('task_id')}: family/adversarial_family mismatch")
        if not isinstance(task.get("checks"), list) or not task["checks"]:
            fail(f"{task.get('task_id')}: missing checks")

    print("BASELINE_TASKS=20")
    print("ADVERSARIAL_TASKS=120")
    print("TOTAL_TASKS=140")
    print("FAMILY_COUNTS=" + json.dumps(dict(sorted(family_counts.items())), sort_keys=True))
    print("ADVERSARIAL_COVERAGE=PASS")


if __name__ == "__main__":
    main()
