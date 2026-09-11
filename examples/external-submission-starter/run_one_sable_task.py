#!/usr/bin/env python3
"""Replace run_real_agent_task() with one real task from your Agent runtime.

The script writes artifacts/submission-v09.jsonl for the reusable SABLE workflow.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path.cwd()
SABLE_ROOT = ROOT / ".sable"
sys.path.insert(0, str(SABLE_ROOT))

from sable_capture_v09 import SableCapture, write_envelope  # type: ignore

OUT = ROOT / "artifacts"


def run_real_agent_task(capture: SableCapture) -> tuple[dict, str, str]:
    """Replace this with your actual agent/runtime call.

    The values returned here must come from the real runtime/environment.
    Return (final_environment_state, claimed_status, final_report).
    """
    raise NotImplementedError("Connect this function to your real Agent runtime")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    capture = SableCapture(
        agent_name="replace-me",
        agent_version="replace-me",
        framework="replace-me",
        framework_version="replace-me",
        adapter="sable-external-starter/0.1",
    )

    final_state, claimed_status, final_report = run_real_agent_task(capture)
    envelope = capture.envelope(
        task_id="replace-me",
        goal="replace-me with the original task goal",
        claimed_status=claimed_status,
        final_report=final_report,
        environment=final_state,
    )
    write_envelope(OUT / "submission-v09.jsonl", envelope)
    print("Wrote artifacts/submission-v09.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
