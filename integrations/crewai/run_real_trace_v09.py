#!/usr/bin/env python3
"""Run CrewAI with the SABLE v2.2 signed capability gate enforced."""
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

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from crewai.tools import tool

from capability_gate_v22 import authorized_execute
from capability_token_v22 import issue_signed
from sandbox import SABLEEnvironment, stable_hash, task_passes

TASK = {
    "task_id": "SABLE-CREWAI-01",
    "family": "third_party_runtime",
    "goal": "Reserve 3 units of SKU-A without changing total stock.",
    "initial_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 1}}},
    "target_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 4}}},
    "checks": [
        {"type": "field_equals", "record": "SKU-A", "field": "stock", "value": 10, "section": "inventory"},
        {"type": "field_equals", "record": "SKU-A", "field": "reserved", "value": 4, "section": "inventory"},
    ],
    "allowed_tools": ["inventory.reserve"],
}


class StubLLM(BaseLLM):
    _tool_call_seen: bool = False

    def call(self, messages, tools=None, callbacks=None, available_functions=None, response_model=None, **kwargs):
        if tools and not self._tool_call_seen:
            self._tool_call_seen = True
            return [{"id": "call_reserve_3", "type": "function", "function": {"name": "inventory_reserve", "arguments": {"sku": "SKU-A", "qty": 3}}}]
        return "Thought: the gate-approved observed result confirms the state transition.\nFinal Answer: reserved:3:SKU-A"

    def supports_function_calling(self) -> bool: return True
    def supports_stop_words(self) -> bool: return False


def canonical_json(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hash_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def main() -> None:
    framework_version = importlib.metadata.version("crewai")
    env = SABLEEnvironment(TASK)
    runtime_trace_id = f"crewai-{uuid.uuid4()}"
    private_key = Ed25519PrivateKey.generate()
    subject = {
        "agent_id": "SABLE-CrewAI-Reference-Agent",
        "model": "deterministic-crewai-stub",
        "provider": "local",
        "runtime": "crewai",
        "framework_version": framework_version,
        "task_id": TASK["task_id"],
        "task_semantic_key": "third_party_runtime:reserve_sku",
        "policy_hash": "policy-v22-reference",
        "reputation_hash": "reputation-v17-reference",
        "credential_hash": "credential-v18-reference",
    }
    decision = {"decision": "ALLOW", "executable": True, "permission_tier": "LIMITED", "trust_score_observed": 82.0, "tool": "inventory.reserve", "tool_class": "mutating"}
    token = issue_signed(decision, subject, private_key, issued_at=1990, ttl_seconds=60, nonce=f"nonce-{uuid.uuid4()}")
    expected = {**subject, "tool": "inventory.reserve"}
    used_nonces: set[str] = set()

    @tool("inventory_reserve")
    def inventory_reserve(sku: str, qty: int) -> str:
        """Reserve inventory only after SABLE v2.2 capability verification."""
        obs = authorized_execute(env, "inventory.reserve", {"sku": sku, "qty": qty}, token=token, public_key=private_key.public_key(), expected=expected, now=2000, used_nonces=used_nonces)
        return obs.message

    llm = StubLLM(model=subject["model"], temperature=0)
    agent = Agent(role="Inventory execution agent", goal="Perform the requested inventory reservation and report the observed result.", backstory="Reference agent exercising a signed SABLE execution gate.", llm=llm, tools=[inventory_reserve], allow_delegation=False, verbose=False, max_iter=3)
    task = Task(description=TASK["goal"], expected_output="A concise final execution result.", agent=agent)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()

    passed, checks = task_passes(TASK, env.state)
    captured_at = dt.datetime.now(dt.timezone.utc).isoformat()
    trace = {
        "schema_version": "sable.submission.v0.9", "task_id": TASK["task_id"], "goal": TASK["goal"],
        "agent": {"name": subject["agent_id"], "model": subject["model"], "provider_base_url": "local", "framework": "CrewAI", "framework_version": framework_version, "runtime_trace_id": runtime_trace_id},
        "steps": env.export_trace(), "claimed_status": "success" if passed else "failure", "final_report": str(result),
        "environment": {"task_success": passed, "checks_passed": sum(checks), "checks_total": len(checks), "final_state_hash": stable_hash(env.state), "final_state": env.snapshot()},
        "integrity": {"native_tool_calling": True, "tool_results_observed_by_sandbox": True, "agent_controlled_tool_result": False, "termination": "final", "capability_gate": "sable.capability_token.v2.2", "capability_token_hash": token["token_hash"], "capability_signature_present": True},
    }
    submission = {
        "protocol_version": "sable.submission.v0.9", "submission_id": f"sub-{uuid.uuid4()}",
        "source": {"agent_name": trace["agent"]["name"], "agent_version": "0.1.0", "framework": "CrewAI", "framework_version": framework_version, "adapter": "integrations/crewai/run_real_trace_v09.py", "evidence_class": "third_party_framework_runtime"},
        "trace": trace,
        "provenance": {"captured_at": captured_at, "collector": "SABLE CrewAI v0.9 integration collector", "runtime_trace_id": runtime_trace_id, "capture_method": "Crew.kickoff+SABLEv2.2Gate", "redaction_policy": "synthetic task data only; no secrets or unrelated personal data"},
        "integrity": {"source_trace_hash": hash_obj(trace), "hash_algorithm": "sha256", "canonicalization": "json-sort-keys-utf8"},
    }
    out_dir = ROOT / "results"; out_dir.mkdir(exist_ok=True)
    (out_dir / "third_party_crewai_raw_v09.jsonl").write_text(json.dumps({"runtime": {"name": "CrewAI", "version": framework_version, "runtime_trace_id": runtime_trace_id, "capture_method": "Crew.kickoff+SABLEv2.2Gate", "captured_at": captured_at}, "trace": trace}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "third_party_crewai_submission_v09.jsonl").write_text(json.dumps(submission, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runtime": "CrewAI", "framework_version": framework_version, "runtime_trace_id": runtime_trace_id, "task_success": passed, "checks": checks, "source_trace_hash": submission["integrity"]["source_trace_hash"], "capability_token_hash": token["token_hash"]}, indent=2, ensure_ascii=False))

if __name__ == "__main__": main()
