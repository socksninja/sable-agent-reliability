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

BAD = {
    **GOOD,
    "task_id": "permission-bad",
    "environment": {"task_success": False},
}

assert decide(GOOD)["decision"] == "ALLOW"
assert decide(BAD)["decision"] == "DENY"
assert "environment_state_not_verified" in decide(BAD)["reasons"]
print("permission_v0.1 self-test: PASS")
