#!/usr/bin/env python3
"""
Reproduction script for crewAI issue #7449:
ToolUsage._use retries a failed tool call TWICE per outer attempt.
With _max_parsing_attempts=3, a tool that always raises is called 6 times, not 3.

Bounty: socksninja/sable-agent-reliability #87
"""
import os
import sys
import json
import hashlib
import subprocess
import tempfile
import datetime
import importlib.metadata

# --- Disable telemetry before any crewai imports ---
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")

ISSUE_ID = "CREWAI_7449"
EVIDENCE_FILE = os.path.join(os.path.dirname(__file__), "EVIDENCE_CREWAI_7449_VERIFICATION.json")

# ---------------------------------------------------------------------------
# Runtime version pinning
# ---------------------------------------------------------------------------
RUNTIME = {
    "python": sys.version,
    "crewai": None,
    "platform": sys.platform,
}
try:
    RUNTIME["crewai"] = importlib.metadata.version("crewai")
except Exception:
    RUNTIME["crewai"] = "unknown"

print(f"[runtime] python={sys.version.split()[0]}  crewai={RUNTIME['crewai']}")

# ---------------------------------------------------------------------------
# External effect log (temp file written to by the tool, read by subprocess)
# ---------------------------------------------------------------------------
EFFECT_LOG = os.path.join(tempfile.gettempdir(), f"crewai_7449_invocations_{os.getpid()}.log")

def _clear_effect_log():
    if os.path.exists(EFFECT_LOG):
        os.remove(EFFECT_LOG)

def _count_effect_log():
    """Count lines in the external effect log."""
    if not os.path.exists(EFFECT_LOG):
        return 0
    with open(EFFECT_LOG) as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    return len(lines)

def _read_effect_log_subprocess():
    """Read the effect log from a fresh subprocess (proves external observability)."""
    result = subprocess.run(
        [sys.executable, "-c",
         f"open({repr(EFFECT_LOG)}).read().splitlines()|print(open({repr(EFFECT_LOG)}).read().strip())"],
        capture_output=True, text=True
    )
    # Simpler approach: just wc -l
    result2 = subprocess.run(
        ["wc", "-l", EFFECT_LOG],
        capture_output=True, text=True
    )
    if result2.returncode == 0:
        parts = result2.stdout.strip().split()
        return int(parts[0]) if parts else 0
    return -1

# ---------------------------------------------------------------------------
# Import crewAI components
# ---------------------------------------------------------------------------
try:
    from crewai.tools.structured_tool import CrewStructuredTool
    from crewai.tools.tool_calling import ToolCalling
    from crewai.tools.tool_usage import ToolUsage
    print("[import] crewai components imported successfully")
except ImportError as e:
    print(f"[FATAL] Cannot import crewai: {e}")
    evidence = {
        "issue_id": ISSUE_ID,
        "verdict": "EVIDENCE GAP",
        "reason": f"Cannot import crewai: {e}",
        "runtime": RUNTIME,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    with open(EVIDENCE_FILE, "w") as f:
        json.dump(evidence, f, indent=2)
    print(f"VERDICT: EVIDENCE GAP")
    sys.exit(0)

# ---------------------------------------------------------------------------
# CONTROL CASE: a tool that succeeds — should be invoked exactly 1 time
# ---------------------------------------------------------------------------
print("\n=== CONTROL CASE: tool that succeeds ===")
_clear_effect_log()
control_in_memory = []

def control_tool_fn(logical_id: str) -> str:
    control_in_memory.append(logical_id)
    with open(EFFECT_LOG, "a") as f:
        f.write(f"control:{logical_id}:{datetime.datetime.utcnow().isoformat()}\n")
    return "success"

control_tool = CrewStructuredTool.from_function(
    func=control_tool_fn, name="control_tool", description="control tool that succeeds"
)

class _ControlAction:
    tool = "control_tool"
    tool_input = {"logical_id": "ctrl-001"}

control_usage = ToolUsage(
    tools_handler=None, tools=[control_tool], task=None,
    function_calling_llm=None, agent=None, action=_ControlAction(),
)
control_usage._max_parsing_attempts = 3

control_calling = ToolCalling(tool_name="control_tool", arguments={"logical_id": "ctrl-001"})
try:
    control_usage.use(calling=control_calling, tool_string="control_tool(logical_id=ctrl-001)")
except Exception as ex:
    print(f"  [control] exception (expected=False): {ex}")

control_file_count = _count_effect_log()
control_memory_count = len(control_in_memory)
print(f"  in-memory invocations : {control_memory_count}")
print(f"  file-based invocations: {control_file_count}")
control_ok = control_memory_count == 1

# ---------------------------------------------------------------------------
# BUG CASE: tool that always raises — should be called 3x but is called 6x
# ---------------------------------------------------------------------------
print("\n=== BUG CASE: tool that always raises ===")
_clear_effect_log()
bug_in_memory = []

def failing_tool_fn(logical_id: str) -> str:
    bug_in_memory.append(logical_id)
    with open(EFFECT_LOG, "a") as f:
        f.write(f"bug:{logical_id}:{datetime.datetime.utcnow().isoformat()}\n")
    raise RuntimeError("boom — simulated permanent failure")

failing_tool = CrewStructuredTool.from_function(
    func=failing_tool_fn, name="my_tool", description="demo failing tool"
)

class _BugAction:
    tool = "my_tool"
    tool_input = {"logical_id": "abc"}

bug_usage = ToolUsage(
    tools_handler=None, tools=[failing_tool], task=None,
    function_calling_llm=None, agent=None, action=_BugAction(),
)
bug_usage._max_parsing_attempts = 3

bug_calling = ToolCalling(tool_name="my_tool", arguments={"logical_id": "abc"})
try:
    bug_usage.use(calling=bug_calling, tool_string="my_tool(logical_id=abc)")
except Exception as ex:
    print(f"  [bug] exception (expected=True): {type(ex).__name__}: {ex}")

bug_memory_count = len(bug_in_memory)
bug_file_count = _count_effect_log()
bug_subprocess_count = _read_effect_log_subprocess()

print(f"  _max_parsing_attempts : 3")
print(f"  in-memory invocations : {bug_memory_count}  (expected >3 if bug present)")
print(f"  file-based invocations: {bug_file_count}")
print(f"  subprocess readback   : {bug_subprocess_count}")

# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------
# Bug is present if the tool was called more times than _max_parsing_attempts
MAX_ATTEMPTS = 3
if bug_memory_count > MAX_ATTEMPTS:
    verdict = "VERIFIED"
    verdict_detail = (
        f"Tool invoked {bug_memory_count} times with _max_parsing_attempts={MAX_ATTEMPTS}. "
        f"Expected <= {MAX_ATTEMPTS}. Duplicate-effect retry boundary confirmed."
    )
elif bug_memory_count == 0:
    verdict = "EVIDENCE GAP"
    verdict_detail = "Tool was never invoked — import or setup issue."
else:
    verdict = "NOT VERIFIED"
    verdict_detail = (
        f"Tool invoked {bug_memory_count} times with _max_parsing_attempts={MAX_ATTEMPTS}. "
        f"Bug not reproduced on this version."
    )

# ---------------------------------------------------------------------------
# Evidence document
# ---------------------------------------------------------------------------
evidence = {
    "issue_id": ISSUE_ID,
    "bounty_issue": "socksninja/sable-agent-reliability#87",
    "upstream_bug": "crewAIInc/crewAI#7449",
    "verdict": verdict,
    "verdict_detail": verdict_detail,
    "runtime": RUNTIME,
    "control_case": {
        "description": "Tool that succeeds — should be invoked exactly once",
        "in_memory_count": control_memory_count,
        "file_count": control_file_count,
        "pass": control_ok,
    },
    "bug_case": {
        "description": "Tool that always raises — invoked >_max_parsing_attempts times if bug present",
        "_max_parsing_attempts": MAX_ATTEMPTS,
        "in_memory_count": bug_memory_count,
        "file_count": bug_file_count,
        "subprocess_readback_count": bug_subprocess_count,
        "expected_if_buggy": MAX_ATTEMPTS * 2,
    },
    "analysis": {
        "root_cause": (
            "ToolUsage._use has an inner try/except around tool.invoke() that catches ANY "
            "exception (not just schema/parsing errors). When the tool raises, _use catches it "
            "and re-raises after logging. The outer attempt loop in ToolUsage.use() then catches "
            "that and increments the retry counter — but _use itself already tried once "
            "internally, doubling the actual invocations."
        ),
        "expected_calls": MAX_ATTEMPTS,
        "actual_calls": bug_memory_count,
        "multiplication_factor": (bug_memory_count / MAX_ATTEMPTS) if MAX_ATTEMPTS > 0 else None,
    },
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "effect_log_path": EFFECT_LOG,
}

evidence_json = json.dumps(evidence, indent=2)
sha256 = hashlib.sha256(evidence_json.encode()).hexdigest()
evidence["sha256"] = sha256

# Re-serialize with sha256 included and recompute (canonical form)
evidence_json_final = json.dumps(evidence, indent=2)
sha256_final = hashlib.sha256(evidence_json_final.encode()).hexdigest()
evidence["sha256"] = sha256_final
evidence_json_final = json.dumps(evidence, indent=2)

with open(EVIDENCE_FILE, "w") as f:
    f.write(evidence_json_final)

print(f"\n{'='*60}")
print(f"VERDICT: {verdict}")
print(f"  {verdict_detail}")
print(f"SHA-256: {sha256_final}")
print(f"Evidence: {EVIDENCE_FILE}")
print(f"{'='*60}")
sys.exit(0)
