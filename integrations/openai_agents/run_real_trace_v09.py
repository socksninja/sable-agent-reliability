#!/usr/bin/env python3
"""Run a real OpenAI Agents SDK runtime and emit a SABLE v0.9 submission."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled, trace
from sandbox import SABLEEnvironment, stable_hash, task_passes

TASK = json.loads((Path(__file__).with_name("task.json")).read_text(encoding="utf-8"))
RAW = ROOT / "results" / "third_party_openai_agents_raw_v09.jsonl"
SUBMISSION = ROOT / "results" / "third_party_openai_agents_submission_v09.jsonl"


def canonical_json(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hash_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def main() -> None:
    framework_version = importlib.metadata.version("openai-agents")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for the live runtime test")

    model_name = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
    env = SABLEEnvironment(TASK)
    set_tracing_disabled(True)

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://github.com/socksninja/sable-agent-reliability"},
    )
    model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)

    @function_tool
    def reserve_inventory(sku: str, qty: int) -> str:
        """Reserve inventory for a SKU. Returns an observed sandbox result."""
        obs = env.execute("inventory.reserve", {"sku": sku, "qty": qty})
        return json.dumps({"ok": obs.ok, "message": obs.message}, ensure_ascii=False, sort_keys=True)

    agent = Agent(
        name="SABLE-OpenAI-Agents-Reference-Agent",
        instructions=(
            "Complete the user's inventory task. You MUST use the reserve_inventory tool "
            "with the exact requested SKU and quantity before reporting success. "
            "Do not invent tool results."
        ),
        model=model,
        tools=[reserve_inventory],
    )

    workflow_trace_id = f"trace_{uuid.uuid4().hex}"
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()

    with trace(
        "SABLE third-party runtime integration",
        trace_id=workflow_trace_id,
        metadata={"sable_task_id": TASK["task_id"], "integration": "openai-agents-sdk"},
        disabled=True,
    ) as runtime_trace:
        result = Runner.run_sync(agent, TASK["goal"])
        runtime_trace_id = runtime_trace.trace_id

    passed, checks = task_passes(TASK, env.state)
    if not env.observations:
        raise RuntimeError("OpenAI Agents SDK completed without executing the required SABLE tool")

    trace_payload = {
        "schema_version": "sable.submission.v0.9",
        "task_id": TASK["task_id"],
        "goal": TASK["goal"],
        "agent": {
            "name": "SABLE-OpenAI-Agents-Reference-Agent",
            "model": model_name,
            "provider_base_url": "https://openrouter.ai/api/v1",
            "framework": "OpenAI Agents SDK",
            "framework_version": framework_version,
            "runtime_trace_id": runtime_trace_id,
        },
        "steps": env.export_trace(),
        "claimed_status": "success" if passed else "failure",
        "final_report": str(result.final_output),
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

    raw = {
        "runtime": {
            "name": "OpenAI Agents SDK",
            "version": framework_version,
            "runtime_trace_id": runtime_trace_id,
            "capture_method": "trace(disabled=true)+Runner.run_sync",
            "captured_at": started_at,
        },
        "trace": trace_payload,
    }
    source_hash = hash_obj(trace_payload)
    submission = {
        "protocol_version": "sable.submission.v0.9",
        "submission_id": f"sub-{uuid.uuid4()}",
        "source": {
            "agent_name": trace_payload["agent"]["name"],
            "agent_version": "0.1.0",
            "framework": "OpenAI Agents SDK",
            "framework_version": framework_version,
            "adapter": "integrations/openai_agents/run_real_trace_v09.py",
            "evidence_class": "third_party_framework_runtime",
        },
        "trace": trace_payload,
        "provenance": {
            "captured_at": started_at,
            "collector": "SABLE OpenAI Agents SDK v0.9 integration collector",
            "runtime_trace_id": runtime_trace_id,
            "capture_method": "trace(disabled=true)+Runner.run_sync",
            "redaction_policy": "synthetic task data only; no secrets or unrelated personal data",
        },
        "integrity": {
            "source_trace_hash": source_hash,
            "hash_algorithm": "sha256",
            "canonicalization": "json-sort-keys-utf8",
        },
    }

    ROOT.joinpath("results").mkdir(exist_ok=True)
    RAW.write_text(json.dumps(raw, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    SUBMISSION.write_text(json.dumps(submission, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "runtime": "OpenAI Agents SDK",
        "framework_version": framework_version,
        "runtime_trace_id": runtime_trace_id,
        "model": model_name,
        "task_success": passed,
        "checks": checks,
        "tool_calls": len(env.observations),
        "source_trace_hash": source_hash,
        "raw": str(RAW),
        "submission": str(SUBMISSION),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
