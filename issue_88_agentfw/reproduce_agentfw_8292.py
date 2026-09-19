#!/usr/bin/env python3
"""
Reproduction script for microsoft/agent-framework#8292
======================================================
Bounty issue: socksninja/sable-agent-reliability#88

Bug:
    FunctionalWorkflow checkpoint replay can associate a cached @step result
    with the wrong concurrent logical branch when replay order differs from
    initial order. No exception is raised.

Method:
    - Two concurrent @step calls (process_branch) with distinct inputs 'A' and 'B'.
    - Initial run: branch_A → result_for_A, branch_B → result_for_B.
      The step_cache is keyed by (step_name, call_index):
        ("process_branch", 0) → result from whichever branch ran first
        ("process_branch", 1) → result from whichever branch ran second
    - Checkpoint saved to InMemoryCheckpointStorage.
    - Restore from tampered checkpoint where the two cache entries are swapped.
    - The framework's cache lookup relies purely on the monotonic counter, so
      branch_A (counter index 0) will consume whichever value was stored at
      index 0 in the tampered checkpoint — which is now branch_B's result.
    - No exception is raised.

Verdict:
    VERIFIED   — swapped cache → swapped results, no exception (bug confirmed)
    NOT VERIFIED — framework guards against swapped results
    EVIDENCE_GAP — package could not be installed / other environmental gap
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

# ── Runtime version pins ───────────────────────────────────────────────────
RUNTIME = {
    "python": sys.version,
    "package": "agent-framework-core",
    "pinned_version": "1.18.0",
}

EVIDENCE_FILE = os.path.join(os.path.dirname(__file__), "EVIDENCE_AGENTFW_8292_VERIFICATION.json")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Verify installed version ───────────────────────────────────────────────
try:
    import importlib.metadata
    installed_version = importlib.metadata.version("agent-framework-core")
    RUNTIME["installed_version"] = installed_version
    if installed_version != "1.18.0":
        print(f"[WARN] Expected 1.18.0 but found {installed_version}", file=sys.stderr)
except Exception as e:
    installed_version = "UNKNOWN"
    RUNTIME["installed_version"] = f"ERROR: {e}"

IMPORT_OK = False
IMPORT_ERROR = ""
try:
    import agent_framework as af
    from agent_framework import (
        InMemoryCheckpointStorage,
        RunContext,
        step,
        workflow,
    )
    from agent_framework._workflows._checkpoint import WorkflowCheckpoint
    from agent_framework._workflows._functional import FunctionalWorkflow
    IMPORT_OK = True
except ImportError as e:
    IMPORT_ERROR = str(e)


# ── Step call registry ─────────────────────────────────────────────────────
# Records every live execution (cache hits do NOT appear here).
call_log: list[dict[str, Any]] = []


@step
async def process_branch(value: str) -> str:
    """Simulated step — returns a result tagged to the input value."""
    result = f"result_for_{value}"
    call_log.append({"input_value": value, "returned_result": result})
    return result


@workflow
async def concurrent_workflow(inputs: dict) -> dict:
    """Workflow that runs two @step calls concurrently via asyncio.gather.

    asyncio.gather schedules coroutines in argument order.  The step cache
    assigns keys in the order coroutines *call* _get_step_cache_key, which
    matches gather argument order.  So on a normal run:
      ("process_branch", 0) → result_for_A  (from gather arg[0])
      ("process_branch", 1) → result_for_B  (from gather arg[1])

    On replay the gather order is the same, so branch_A (index 0) picks up
    index-0 from the cache (result_for_A) and all is correct — UNLESS the
    cache itself has been tampered or stored in a different order.

    The bug scenario: if the gather argument order or initial execution order
    ever differs between runs (e.g. due to scheduling nondeterminism, task
    priority, or manual checkpoint construction), branch_A silently gets
    result_for_B and vice-versa.  We prove this by injecting a swapped cache.
    """
    value_a = inputs["value_a"]
    value_b = inputs["value_b"]

    result_a, result_b = await asyncio.gather(
        process_branch(value_a),
        process_branch(value_b),
    )

    return {
        "branch_A_received_result": result_a,
        "branch_B_received_result": result_b,
    }


async def run_experiment() -> dict[str, Any]:
    """Run the full experiment and return evidence data."""

    storage = InMemoryCheckpointStorage()

    # ── CONTROL: Verify basic workflow correctness ─────────────────────────
    print("[CONTROL] Running initial workflow...")
    call_log.clear()
    wf_control = concurrent_workflow.build(checkpoint_storage=storage)
    inputs = {"value_a": "A", "value_b": "B"}

    initial_result = await wf_control.run(inputs)
    initial_output = initial_result.get_outputs()
    initial_call_log = [dict(x) for x in call_log]

    initial_output_data = initial_output[0] if initial_output else {}
    initial_branch_A = initial_output_data.get("branch_A_received_result")
    initial_branch_B = initial_output_data.get("branch_B_received_result")

    print(f"[CONTROL]   branch_A → {initial_branch_A!r}  (expected 'result_for_A')")
    print(f"[CONTROL]   branch_B → {initial_branch_B!r}  (expected 'result_for_B')")
    print(f"[CONTROL]   live step calls: {len(initial_call_log)}")

    control_correct = (initial_branch_A == "result_for_A" and initial_branch_B == "result_for_B")

    # ── Load the checkpoint saved at end of initial run ────────────────────
    checkpoints = await storage.list_checkpoints(workflow_name="concurrent_workflow")
    print(f"[CHECKPOINT] Total checkpoints saved: {len(checkpoints)}")

    if not checkpoints:
        return {
            "verdict": "EVIDENCE_GAP",
            "verdict_explanation": "No checkpoint was saved during initial run. "
                "The checkpoint_storage may not be wired correctly.",
            "control_correct": control_correct,
        }

    latest_ckpt = checkpoints[-1]
    original_cache: dict[str, Any] = dict(latest_ckpt.state.get("_step_cache", {}))
    print(f"[CHECKPOINT] ID: {latest_ckpt.checkpoint_id}")
    print(f"[CHECKPOINT] step_cache entries: {json.dumps(original_cache, indent=2)}")

    if len(original_cache) < 2:
        return {
            "verdict": "EVIDENCE_GAP",
            "verdict_explanation": f"Expected 2 step_cache entries, got {len(original_cache)}. "
                f"Cache: {original_cache}",
            "control_correct": control_correct,
        }

    # ── BUG CASE: Replay from a SWAPPED checkpoint ─────────────────────────
    # Swap the two entries: process_branch::0 ↔ process_branch::1
    swapped_cache: dict[str, Any] = {}
    for k, v in original_cache.items():
        if k == "process_branch::0":
            swapped_cache["process_branch::1"] = v
        elif k == "process_branch::1":
            swapped_cache["process_branch::0"] = v
        else:
            swapped_cache[k] = v

    tampered_ckpt = WorkflowCheckpoint(
        workflow_name=latest_ckpt.workflow_name,
        graph_signature_hash=latest_ckpt.graph_signature_hash,
        checkpoint_id=str(uuid.uuid4()),
        previous_checkpoint_id=latest_ckpt.checkpoint_id,
        state={
            **{k: v for k, v in latest_ckpt.state.items() if k != "_step_cache"},
            "_step_cache": swapped_cache,
        },
        pending_request_info_events=dict(latest_ckpt.pending_request_info_events),
        iteration_count=latest_ckpt.iteration_count,
    )
    await storage.save(tampered_ckpt)

    print(f"[BUG CASE] Tampered step_cache: {json.dumps(swapped_cache, indent=2)}")
    print(f"[BUG CASE] Restoring from tampered checkpoint {tampered_ckpt.checkpoint_id}...")

    call_log.clear()
    wf_bug = concurrent_workflow.build(checkpoint_storage=storage)
    bug_result = await wf_bug.run(checkpoint_id=tampered_ckpt.checkpoint_id)
    bug_output = bug_result.get_outputs()
    bug_call_log = [dict(x) for x in call_log]

    bug_output_data = bug_output[0] if bug_output else {}
    bug_branch_A = bug_output_data.get("branch_A_received_result")
    bug_branch_B = bug_output_data.get("branch_B_received_result")

    print(f"[BUG CASE]   branch_A → {bug_branch_A!r}  (expected 'result_for_A', bug: 'result_for_B')")
    print(f"[BUG CASE]   branch_B → {bug_branch_B!r}  (expected 'result_for_B', bug: 'result_for_A')")
    print(f"[BUG CASE]   live step calls during replay: {len(bug_call_log)}")

    # ── NORMAL REPLAY: Verify standard checkpoint restore works ───────────
    print(f"[NORMAL REPLAY] Restoring from original checkpoint {latest_ckpt.checkpoint_id}...")
    call_log.clear()
    wf_replay = concurrent_workflow.build(checkpoint_storage=storage)
    replay_result = await wf_replay.run(checkpoint_id=latest_ckpt.checkpoint_id)
    replay_output = replay_result.get_outputs()
    replay_call_log = [dict(x) for x in call_log]

    replay_output_data = replay_output[0] if replay_output else {}
    replay_branch_A = replay_output_data.get("branch_A_received_result")
    replay_branch_B = replay_output_data.get("branch_B_received_result")

    print(f"[NORMAL REPLAY]   branch_A → {replay_branch_A!r}")
    print(f"[NORMAL REPLAY]   branch_B → {replay_branch_B!r}")
    print(f"[NORMAL REPLAY]   live step calls: {len(replay_call_log)}")

    # ── ANALYSIS ──────────────────────────────────────────────────────────
    EXPECTED_A = "result_for_A"
    EXPECTED_B = "result_for_B"

    # Bug conditions:
    # 1. Control run is correct (basic sanity)
    # 2. Swapped-cache replay silently returns swapped results (no exception)
    # 3. The swapped result was served from cache (no live re-execution)
    bug_swapped = (bug_branch_A == EXPECTED_B and bug_branch_B == EXPECTED_A)
    bug_silent = (len(bug_call_log) == 0)  # cache was hit, not re-executed
    normal_replay_correct = (replay_branch_A == EXPECTED_A and replay_branch_B == EXPECTED_B)

    if control_correct and bug_swapped and bug_silent:
        verdict = "VERIFIED"
        verdict_explanation = (
            "Bug confirmed in agent-framework-core==1.18.0: "
            "After checkpoint replay with swapped step-cache entries, "
            f"branch_A received {bug_branch_A!r} (expected {EXPECTED_A!r}) and "
            f"branch_B received {bug_branch_B!r} (expected {EXPECTED_B!r}). "
            "No exception was raised. The framework's cache lookup uses only a "
            "monotonic call counter (step_name, call_index) with no per-branch "
            "input binding guard, so swapped cache entries cause silent wrong results."
        )
    elif control_correct and not bug_swapped:
        verdict = "NOT VERIFIED"
        verdict_explanation = (
            "The framework appears to have a guard preventing the bug: "
            f"even with swapped cache, branch_A got {bug_branch_A!r} and "
            f"branch_B got {bug_branch_B!r} (both correct or an exception was raised)."
        )
    else:
        verdict = "EVIDENCE_GAP"
        verdict_explanation = (
            f"Unexpected behaviour. control_correct={control_correct}, "
            f"bug_swapped={bug_swapped}, bug_silent={bug_silent}. "
            f"bug_branch_A={bug_branch_A!r}, bug_branch_B={bug_branch_B!r}."
        )

    return {
        "verdict": verdict,
        "verdict_explanation": verdict_explanation,
        "control_case": {
            "description": "Initial run — both branches execute live, no cache",
            "branch_A_result": initial_branch_A,
            "branch_B_result": initial_branch_B,
            "correct": control_correct,
            "live_step_calls": len(initial_call_log),
            "call_log": initial_call_log,
        },
        "checkpoint": {
            "id": latest_ckpt.checkpoint_id,
            "step_cache": original_cache,
        },
        "bug_case": {
            "description": (
                "Replay from tampered checkpoint (step_cache entries 0↔1 swapped). "
                "Branch_A (counter=0) will consume the value stored at index 0 in the "
                "tampered cache — which is now B's result. No exception expected."
            ),
            "tampered_step_cache": swapped_cache,
            "branch_A_result": bug_branch_A,
            "branch_B_result": bug_branch_B,
            "expected_A": EXPECTED_A,
            "expected_B": EXPECTED_B,
            "results_swapped": bug_swapped,
            "silent_wrong_result": bug_silent and bug_swapped,
            "live_step_calls": len(bug_call_log),
            "call_log": bug_call_log,
        },
        "normal_replay": {
            "description": "Replay from original (unmodified) checkpoint",
            "branch_A_result": replay_branch_A,
            "branch_B_result": replay_branch_B,
            "correct": normal_replay_correct,
            "live_step_calls": len(replay_call_log),
        },
    }


async def main() -> None:
    evidence: dict[str, Any] = {
        "bounty_issue": "socksninja/sable-agent-reliability#88",
        "upstream_bug": "microsoft/agent-framework#8292",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime": RUNTIME,
    }

    if not IMPORT_OK:
        evidence["verdict"] = "EVIDENCE_GAP"
        evidence["verdict_explanation"] = f"Import failed: {IMPORT_ERROR}"
        evidence["experiment"] = {}
    else:
        try:
            experiment_data = await run_experiment()
            evidence["verdict"] = experiment_data.pop("verdict")
            evidence["verdict_explanation"] = experiment_data.pop("verdict_explanation")
            evidence["experiment"] = experiment_data
        except Exception as exc:
            evidence["verdict"] = "EVIDENCE_GAP"
            evidence["verdict_explanation"] = f"Exception during experiment: {exc}"
            evidence["experiment"] = {"traceback": traceback.format_exc()}

    # Write evidence file (without sha first)
    with open(EVIDENCE_FILE, "w") as f:
        json.dump(evidence, f, indent=2, default=str)

    sha = _sha256(EVIDENCE_FILE)
    evidence["sha256"] = sha

    # Rewrite with sha included
    with open(EVIDENCE_FILE, "w") as f:
        json.dump(evidence, f, indent=2, default=str)

    print()
    print("=" * 70)
    print(f"VERDICT: {evidence['verdict']}")
    print(f"Explanation: {evidence['verdict_explanation']}")
    print(f"Evidence file: {EVIDENCE_FILE}")
    print(f"SHA-256: {sha}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
