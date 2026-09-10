#!/usr/bin/env python3
from permission_v01 import decide

GOOD = {
    "task_id": "permission-good",
    "environment": {"task_success": True},
    "steps": [{"observed_result": {"ok": True}, "after_state_hash": "abc"}],
    "integrity": {
        "termination": "final",
        "native_tool_calling": True,
        "tool_results_observed_by_sandbox": True,
        "agent_controlled_tool_result": False,
    },
}
REPORT_GOOD = {"pass_rate": 1.0, "replay_match_rate": 1.0}
REPORT_BAD = {"pass_rate": 1.0, "replay_match_rate": 0.0}
BAD = {**GOOD, "task_id": "permission-bad", "environment": {"task_success": False}}

assert decide(GOOD, REPORT_GOOD)["decision"] == "ALLOW"
assert decide(BAD, REPORT_GOOD)["decision"] == "DENY"
assert "environment_state_not_verified" in decide(BAD, REPORT_GOOD)["reasons"]
assert decide(GOOD, REPORT_BAD)["decision"] == "DENY"
assert "replay_not_fully_verified" in decide(GOOD, REPORT_BAD)["reasons"]
print("permission_v0.1 self-test: PASS")
