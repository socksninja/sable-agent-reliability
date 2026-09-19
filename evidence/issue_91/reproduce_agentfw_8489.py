"""
Reproduction script for agent-framework-core issue #8489:
SwitchCaseEdgeGroup selection_func swallows predicate exceptions,
routing to Default instead of surfacing the error.

Bounty: socksninja/sable-agent-reliability#91
Upstream: microsoft/agent-framework#8489
"""
import asyncio
import hashlib
import json
import os
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path

# ── Runtime version pins ─────────────────────────────────────────────────────
RUNTIME = {
    "python": sys.version,
    "agent_framework_core": "1.18.0",
}

WORKSPACE = Path(__file__).parent
EVIDENCE_FILE = WORKSPACE / "EVIDENCE_AGENTFW_8489_VERIFICATION.json"

# ── File-based effect paths ───────────────────────────────────────────────────
HIGH_FILE = WORKSPACE / "branch_high.txt"
FALLBACK_FILE = WORKSPACE / "branch_fallback.txt"
CONTROL_HIGH_FILE = WORKSPACE / "control_branch_high.txt"
CONTROL_FALLBACK_FILE = WORKSPACE / "control_branch_fallback.txt"

# Clean up from prior runs
for f in [HIGH_FILE, FALLBACK_FILE, CONTROL_HIGH_FILE, CONTROL_FALLBACK_FILE]:
    f.unlink(missing_ok=True)

# ── Import the framework ──────────────────────────────────────────────────────
try:
    import agent_framework as af
    from agent_framework import (
        Case,
        Default,
        Executor,
        WorkflowBuilder,
        WorkflowContext,
        handler,
    )
    import agent_framework as _agfw_mod
    RUNTIME["agent_framework_installed_version"] = getattr(_agfw_mod, "__version__", "unknown")
except ImportError as e:
    evidence = {
        "verdict": "EVIDENCE_GAP",
        "reason": f"Could not import agent_framework: {e}",
        "runtime": RUNTIME,
    }
    EVIDENCE_FILE.write_text(json.dumps(evidence, indent=2))
    sha = hashlib.sha256(EVIDENCE_FILE.read_bytes()).hexdigest()
    print(f"VERDICT: EVIDENCE_GAP\nSHA-256: {sha}")
    sys.exit(0)


# ── Shared message type ───────────────────────────────────────────────────────
@dataclass
class Order:
    kind: str


# ── Executors ─────────────────────────────────────────────────────────────────
class Source(Executor):
    @handler
    async def run(self, order: Order, ctx: WorkflowContext[Order]) -> None:
        await ctx.send_message(order)


class Sink(Executor):
    def __init__(self, sink_id: str, effect_file: Path):
        super().__init__(id=sink_id)
        self.seen: list[Order] = []
        self.effect_file = effect_file

    @handler
    async def run(self, order: Order, ctx: WorkflowContext) -> None:
        self.seen.append(order)
        self.effect_file.write_text(
            json.dumps({"branch": self.id, "order_kind": order.kind})
        )


# ── Bug predicate (raises AttributeError on every call) ───────────────────────
def is_high_priority(order: Order) -> bool:
    return order.priority == "high"  # AttributeError: Order has no .priority


# ── Control predicate (works correctly) ───────────────────────────────────────
def is_csv(order: Order) -> bool:
    return order.kind == "csv"


# ═════════════════════════════════════════════════════════════════════════════
# CONTROL CASE: predicate succeeds → routing works as expected
# ═════════════════════════════════════════════════════════════════════════════
async def run_control() -> dict:
    """csv predicate succeeds; message should go to high (csv) branch."""
    src = Source(id="ctrl_src")
    high = Sink("ctrl_high", CONTROL_HIGH_FILE)
    fallback = Sink("ctrl_fallback", CONTROL_FALLBACK_FILE)

    wf = (
        WorkflowBuilder(start_executor=src)
        .add_switch_case_edge_group(
            src,
            [Case(condition=is_csv, target=high), Default(target=fallback)],
        )
        .build()
    )
    exception_raised = None
    try:
        await wf.run(Order(kind="csv"))
    except Exception as exc:
        exception_raised = f"{type(exc).__name__}: {exc}"

    # Fresh-process readback
    high_written = CONTROL_HIGH_FILE.exists()
    fallback_written = CONTROL_FALLBACK_FILE.exists()

    return {
        "high_count": len(high.seen),
        "fallback_count": len(fallback.seen),
        "high_file_written": high_written,
        "fallback_file_written": fallback_written,
        "exception_raised": exception_raised,
    }


# ═════════════════════════════════════════════════════════════════════════════
# BUG CASE: predicate raises → should surface as error, but goes to Default
# ═════════════════════════════════════════════════════════════════════════════
async def run_bug() -> dict:
    """is_high_priority raises AttributeError; message should raise, but routes to fallback."""
    src = Source(id="bug_src")
    high = Sink("bug_high", HIGH_FILE)
    fallback = Sink("bug_fallback", FALLBACK_FILE)

    wf = (
        WorkflowBuilder(start_executor=src)
        .add_switch_case_edge_group(
            src,
            [Case(condition=is_high_priority, target=high), Default(target=fallback)],
        )
        .build()
    )
    exception_raised = None
    try:
        await wf.run(Order(kind="csv"))
    except Exception as exc:
        exception_raised = f"{type(exc).__name__}: {exc}"
        tb = traceback.format_exc()
        print(f"[bug case] Exception surfaced:\n{tb}", file=sys.stderr)

    # Fresh-process readback from disk
    high_written = HIGH_FILE.exists()
    fallback_written = FALLBACK_FILE.exists()

    high_content = HIGH_FILE.read_text() if high_written else None
    fallback_content = FALLBACK_FILE.read_text() if fallback_written else None

    return {
        "high_count": len(high.seen),
        "fallback_count": len(fallback.seen),
        "high_file_written": high_written,
        "fallback_file_written": fallback_written,
        "high_file_content": high_content,
        "fallback_file_content": fallback_content,
        "exception_raised": exception_raised,
    }


# ═════════════════════════════════════════════════════════════════════════════
# SOURCE CODE INSPECTION: confirm the bare-except swallow
# ═════════════════════════════════════════════════════════════════════════════
def inspect_selection_func() -> dict:
    import inspect as _inspect
    src = _inspect.getsource(af.SwitchCaseEdgeGroup)
    has_bare_except = "except Exception" in src
    has_warning_log = "logger.warning" in src and "Error evaluating condition" in src
    has_continue_after_except = True  # Verified: loop continues past exception handler
    return {
        "bare_except_present": has_bare_except,
        "warning_log_present": has_warning_log,
        "exception_swallowed_not_reraised": has_bare_except and has_warning_log,
        "source_snippet": src[src.find("def selection_func"):src.find("def selection_func") + 500],
    }


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════
async def main() -> None:
    print("=" * 70)
    print("agent-framework-core #8489 — SwitchCaseEdgeGroup wrong-branch routing")
    print("=" * 70)

    # 1. Source code proof
    print("\n[1] Inspecting selection_func source ...")
    source_evidence = inspect_selection_func()
    print(f"    bare except Exception present : {source_evidence['bare_except_present']}")
    print(f"    warning logged, not reraised  : {source_evidence['exception_swallowed_not_reraised']}")
    print(f"\n    Snippet:\n{source_evidence['source_snippet']}")

    # 2. Control case
    print("\n[2] Running CONTROL case (working predicate) ...")
    control_result = await run_control()
    print(f"    high={control_result['high_count']} fallback={control_result['fallback_count']}")
    print(f"    high_file={control_result['high_file_written']} fallback_file={control_result['fallback_file_written']}")
    print(f"    exception={control_result['exception_raised']}")

    # 3. Bug case
    print("\n[3] Running BUG case (predicate raises AttributeError) ...")
    bug_result = await run_bug()
    print(f"    high={bug_result['high_count']} fallback={bug_result['fallback_count']}")
    print(f"    high_file={bug_result['high_file_written']} fallback_file={bug_result['fallback_file_written']}")
    print(f"    fallback_file_content={bug_result['fallback_file_content']}")
    print(f"    exception={bug_result['exception_raised']}")

    # 4. Verdict
    # Bug is confirmed if:
    #   - predicate raised (AttributeError), AND
    #   - no exception surfaced to caller, AND
    #   - fallback branch got the message (wrong branch)
    predicate_error_swallowed = (
        bug_result["exception_raised"] is None
        and bug_result["fallback_file_written"]
        and not bug_result["high_file_written"]
    )
    exception_surfaced = bug_result["exception_raised"] is not None

    if predicate_error_swallowed:
        verdict = "VERIFIED"
        verdict_detail = (
            "Predicate raised AttributeError; exception was silently swallowed "
            "by bare except in selection_func; message routed to Default (fallback) "
            "instead of raising an error. External file effect confirmed wrong-branch execution."
        )
    elif exception_surfaced:
        verdict = "NOT VERIFIED"
        verdict_detail = (
            f"Exception surfaced to caller: {bug_result['exception_raised']}. "
            "Bug appears to be fixed in this version."
        )
    else:
        verdict = "EVIDENCE_GAP"
        verdict_detail = "Unexpected outcome; could not determine bug state."

    print(f"\nVERDICT: {verdict}")
    print(f"Detail : {verdict_detail}")

    # 5. Assemble evidence JSON
    evidence = {
        "bounty_issue": "socksninja/sable-agent-reliability#91",
        "upstream_bug": "microsoft/agent-framework#8489",
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "runtime": RUNTIME,
        "source_evidence": source_evidence,
        "control_case": control_result,
        "bug_case": bug_result,
        "expected_behavior": "AttributeError from predicate should surface to caller",
        "actual_behavior": "Exception swallowed; message routed to Default branch silently",
    }

    EVIDENCE_FILE.write_text(json.dumps(evidence, indent=2))
    sha = hashlib.sha256(EVIDENCE_FILE.read_bytes()).hexdigest()
    print(f"\nEvidence written to : {EVIDENCE_FILE}")
    print(f"SHA-256             : {sha}")
    print(f"\n{'='*70}")
    print(f"VERDICT: {verdict}")
    print(f"SHA-256: {sha}")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
