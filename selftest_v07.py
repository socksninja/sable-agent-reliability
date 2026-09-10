#!/usr/bin/env python3
"""SABLE v0.7 leaderboard self-test; no model or API required."""
from __future__ import annotations
import json
from pathlib import Path
from leaderboard_v07 import build


def report(score: float, op: float, passed: float) -> dict:
    return {
        "schema_version": "sable.v0.5",
        "tasks": 140,
        "reliability_score": score,
        "operational_score_excluding_provider_failures": op,
        "pass_rate": passed,
    }


def main() -> None:
    entries = [
        {"model":"synthetic-good","provider":"synthetic","report":report(97.0,96.0,0.96)},
        {"model":"synthetic-mid","provider":"synthetic","report":report(91.0,90.0,0.90)},
    ]
    out = build(entries, "SABLE-v0.5-140")
    assert out["schema_version"] == "sable.leaderboard.v0.7"
    assert out["task_count"] == 140
    assert out["eligible_entries"] == 2
    assert [x["model"] for x in out["entries"]] == ["synthetic-good", "synthetic-mid"]
    assert [x["rank"] for x in out["entries"]] == [1, 2]

    try:
        build(entries[:1] + [{"model":"bad","provider":"synthetic","report":report(99,98,0.98) | {"tasks": 139}}], "SABLE-v0.5-140")
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched task counts must be rejected")

    Path("results").mkdir(exist_ok=True)
    result = {"schema_version":"sable.v0.7","status":"PASS","task_count":140,"entries":2}
    Path("results/selftest_v07.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
