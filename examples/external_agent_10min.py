#!/usr/bin/env python3
"""A complete capture example that can be copied around an existing agent.

Run: python examples/external_agent_10min.py
Produces: artifacts/submission-v09.jsonl and artifacts/sable-trace-v05.jsonl
This demo uses a tiny local stateful tool so the example is deterministic and
network-free; a real integration replaces `tool()` and `snapshot()` with the
existing agent/runtime calls.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from sable_capture_v09 import SableCapture, write_envelope

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
STATE = {"counter": 0}


def snapshot() -> dict[str, int]:
    return dict(STATE)


def tool(name: str, amount: int) -> dict[str, int]:
    if name != "increment_counter":
        raise ValueError(f"unknown tool: {name}")
    STATE["counter"] += amount
    return snapshot()


def main() -> int:
    OUT.mkdir(exist_ok=True)
    capture = SableCapture(
        agent_name="sable-quickstart-agent",
        agent_version="0.1.0",
        framework="custom-demo-runtime",
        framework_version="0.1.0",
        adapter="sable_capture_v09/0.1",
    )

    before = snapshot()
    observed = tool("increment_counter", 1)
    after = snapshot()
    capture.call("increment_counter", {"amount": 1}, observed, before, after)

    envelope = capture.envelope(
        task_id="quickstart-counter-01",
        goal="Increase the counter from 0 to 1.",
        claimed_status="success",
        final_report="Counter reached 1.",
        environment={"counter": STATE["counter"]},
    )
    raw = OUT / "submission-v09.jsonl"
    write_envelope(raw, envelope)

    normalized = OUT / "sable-trace-v05.jsonl"
    subprocess.run([
        sys.executable, str(ROOT / "trace_submit_v09.py"),
        "--input", str(raw),
        "--output", str(normalized),
    ], check=True)
    print(f"SABLE external verification complete: {raw}")
    print(f"Normalized trace: {normalized}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
