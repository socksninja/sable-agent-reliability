#!/usr/bin/env python3
"""Run a real CrewAI runtime against a deliberately failing SABLE task.

The CrewAI agent executes a real tool call through the third-party framework.
The SABLE sandbox observes the rejected mutation, preserving evidence that a
failed external runtime execution results in DENY rather than ALLOW.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from crewai.tools import tool

from sandbox import SABLEEnvironment, stable_hash

TASK = {
    "task_id": "SABLE-CREWAI-NEG-01",
    "family": "third_party_runtime_negative",
    "goal": "Reserve 100 units of SKU-A without changing total stock.",
    "initial_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 1}}},
    "target_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 101}}},
    "checks": [
        {"type": "field_equals", "record": "SKU-A", "field": "stock", "value": 10, "section": "inventory"},
        {"type": "field_equals", "record": "SKU-A", "field": "reserved", "value": 101, "section": "inventory"},
    ],
    "allowed_tools": ["inventory.reserve"],
}

class StubLLM(BaseLLM):
    _tool_call_seen: bool = False

    def call(self, messages, tools=None, callbacks=None, available_functions=None, response_model=None, **kwargs):
        if tools and not self._tool_call_seen:
            self._tool_call_seen = True
            return [{
                "id": "call_reserve_100",
                "type": "function",
                "function": {
                    "name": "inventory_reserve",
                    "arguments": {"sku": "SKU-A", "qty": 100},
                },
            }]
        return "Thought: The tool rejected the reservation because available stock was insufficient.\nFinal Answer: reservation failed"

    def supports_function_calling(self) -> bool:
        return True

    def supports_stop_words(self) -> bool:
        return False


def canonical_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    framework_version = importlib.metadata.version("crewai")
    env = SABLEEnvironment(TASK)
    runtime_trace_id = f"crewai-negative-{uuid.uuid4()}"

    @tool("inventory_reserve")
    def inventory_reserve(sku: str, qty: int) -> str:
        """Attempt an inventory reservation inside the SABLE sandbox."""
        obs = env.execute("inventory.reserve", {"sku": sku, "qty": qty})
        return obs.message

    agent = Agent(
        role="Inventory execution agent",
        goal="Attempt the requested inventory reservation and report the observed result.",
        backstory="Deterministic negative reference agent used to verify DENY behavior.",
        llm=StubLLM(model="sable-crewai-negative-stub", temperature=0),
        tools=[inventory_reserve],
        allow_delegation=False,
        verbose=False,
        max_iter=3,
    )
    task = Task(description=TASK["goal"], expected_output="A concise final execution result.", agent=agent)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()

    passed = env.state == TASK["target_state"]
    checks = [
        env.state.get("inventory", {}).get("SKU-A", {}).get("stock") == 10,
        env.state.get("inventory", {}).get("SKU-A", {}).get("reserved") == 101,
    ]

    trace = {
        "schema_version": "sable.submission.v0.9",
        "task_id": TASK["task_id"],
        "goal": TASK["goal"],
        "agent": {
            "name": "SABLE-CrewAI-Negative-Reference-Agent",
            "model": "deterministic-crewai-negative-stub",
            "provider_base_url": "local",
            "framework": "CrewAI",
            "framework_version": framework_version,
            "runtime_trace_id": runtime_trace_id,
        },
        "steps": env.export_trace(),
        "claimed_status": "failure" if not passed else "success",
        "final_report": str(result),
        "environment": {
            "task_success": passed,
            "checks_passed": sum(checks),
            "checks_total": len(checks),
            "final_state_hash": stable_hash(env.state),
            "final_state": env.snapshot(),
        },
        "integrity": {
            "native_tool_calling": True,
            "tool_results_observed_by_sandbox": True,
            "agent_controlled_tool_result": False,
            "termination": "final",
        },
    }
    captured_at = dt.datetime.now(dt.timezone.utc).isoformat()
    submission = {
        "protocol_version": "sable.submission.v0.9",
        "submission_id": f"sub-{uuid.uuid4()}",
        "source": {
            "agent_name": trace["agent"]["name"],
            "agent_version": "0.1.0",
            "framework": "CrewAI",
            "framework_version": framework_version,
            "adapter": "integrations/crewai/run_negative_trace_v09.py",
            "evidence_class": "third_party_framework_runtime_negative",
        },
        "trace": trace,
        "provenance": {
            "captured_at": captured_at,
            "collector": "SABLE CrewAI v0.9 negative integration collector",
            "runtime_trace_id": runtime_trace_id,
            "capture_method": "Crew.kickoff",
            "redaction_policy": "synthetic task data only; no secrets or unrelated personal data",
        },
        "integrity": {
            "source_trace_hash": canonical_hash(trace),
            "hash_algorithm": "sha256",
            "canonicalization": "json-sort-keys-utf8",
        },
    }
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "third_party_crewai_negative_raw_v09.jsonl").write_text(json.dumps({"runtime": {"name": "CrewAI", "version": framework_version, "runtime_trace_id": runtime_trace_id, "capture_method": "Crew.kickoff", "captured_at": captured_at}, "trace": trace}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "third_party_crewai_negative_submission_v09.jsonl").write_text(json.dumps(submission, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runtime": "CrewAI", "framework_version": framework_version, "runtime_trace_id": runtime_trace_id, "task_success": passed, "checks": checks, "source_trace_hash": submission["integrity"]["source_trace_hash"]}, indent=2))

if __name__ == "__main__":
    main()
