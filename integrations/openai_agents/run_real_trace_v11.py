#!/usr/bin/env python3
"""Run OpenAI Agents SDK against a local OpenAI-compatible model endpoint.

The third-party Agents SDK owns agent orchestration, function-tool dispatch,
and the run loop. SABLE owns the actual environment mutation and records
observed state and state hashes.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import http.server
import importlib.metadata
import json
import sys
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.decorators import function_tool

from sandbox import SABLEEnvironment, stable_hash, task_passes

TASK = json.loads((ROOT / "integrations/openai_agents/task.json").read_text(encoding="utf-8"))


class DeterministicHandler(http.server.BaseHTTPRequestHandler):
    calls = 0

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        length = int(self.headers.get("content-length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        messages = body.get("messages", [])
        tools = body.get("tools") or []
        DeterministicHandler.calls += 1

        wants_tool = bool(tools) and not any(m.get("role") == "tool" for m in messages)
        if wants_tool:
            tool_call = {
                "id": "call_sable_reserve_3",
                "type": "function",
                "function": {
                    "name": "inventory_reserve",
                    "arguments": json.dumps({"sku": "SKU-A", "qty": 3}, separators=(",", ":")),
                },
            }
            response = {
                "id": f"chatcmpl-sable-{DeterministicHandler.calls}",
                "object": "chat.completion",
                "created": 0,
                "model": body.get("model", "sable-local-reference"),
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "", "tool_calls": [tool_call]},
                    "finish_reason": "tool_calls",
                }],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        else:
            response = {
                "id": f"chatcmpl-sable-{DeterministicHandler.calls}",
                "object": "chat.completion",
                "created": 0,
                "model": body.get("model", "sable-local-reference"),
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Execution verified: reserved 3 units of SKU-A."},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        raw = json.dumps(response, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def start_server() -> tuple[http.server.ThreadingHTTPServer, int]:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), DeterministicHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_port


def canonical_json(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hash_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj)).hexdigest()


async def run() -> None:
    framework_version = importlib.metadata.version("openai-agents")
    server, port = start_server()
    try:
        set_tracing_disabled(disabled=True)
        client = AsyncOpenAI(api_key="sable-local", base_url=f"http://127.0.0.1:{port}/v1")
        model = OpenAIChatCompletionsModel(model="sable-local-reference", openai_client=client)
        env = SABLEEnvironment(TASK)
        runtime_trace_id = f"openai-agents-{uuid.uuid4()}"

        @function_tool
        def inventory_reserve(sku: str, qty: int) -> str:
            """Reserve inventory units inside the SABLE sandbox."""
            obs = env.execute("inventory.reserve", {"sku": sku, "qty": qty})
            return obs.message

        agent = Agent(
            name="SABLE-OpenAI-Agents-Reference-Agent",
            instructions="Use the inventory tool to satisfy the requested reservation. Report only what the tool result confirms.",
            model=model,
            tools=[inventory_reserve],
        )
        result = await Runner.run(agent, TASK["goal"])

        passed, checks = task_passes(TASK, env.state)
        trace = {
            "schema_version": "sable.submission.v0.9",
            "task_id": TASK["task_id"],
            "goal": TASK["goal"],
            "agent": {
                "name": "SABLE-OpenAI-Agents-Reference-Agent",
                "model": "sable-local-reference",
                "provider_base_url": f"http://127.0.0.1:{port}/v1",
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
        captured_at = dt.datetime.now(dt.timezone.utc).isoformat()
        submission = {
            "protocol_version": "sable.submission.v0.9",
            "submission_id": f"sub-{uuid.uuid4()}",
            "source": {
                "agent_name": trace["agent"]["name"],
                "agent_version": "0.1.0",
                "framework": "OpenAI Agents SDK",
                "framework_version": framework_version,
                "adapter": "integrations/openai_agents/run_real_trace_v11.py",
                "evidence_class": "third_party_framework_runtime",
            },
            "trace": trace,
            "provenance": {
                "captured_at": captured_at,
                "collector": "SABLE OpenAI Agents SDK v0.9 integration collector",
                "runtime_trace_id": runtime_trace_id,
                "capture_method": "Runner.run",
                "redaction_policy": "synthetic task data only; no secrets or unrelated personal data",
            },
            "integrity": {
                "source_trace_hash": hash_obj(trace),
                "hash_algorithm": "sha256",
                "canonicalization": "json-sort-keys-utf8",
            },
        }
        out_dir = ROOT / "results"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "third_party_openai_agents_raw_v09.jsonl").write_text(
            json.dumps({"runtime": {"name": "OpenAI Agents SDK", "version": framework_version, "runtime_trace_id": runtime_trace_id, "capture_method": "Runner.run", "captured_at": captured_at}, "trace": trace}, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out_dir / "third_party_openai_agents_submission_v09.jsonl").write_text(
            json.dumps(submission, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "runtime": "OpenAI Agents SDK",
            "framework_version": framework_version,
            "runtime_trace_id": runtime_trace_id,
            "task_success": passed,
            "checks": checks,
            "source_trace_hash": submission["integrity"]["source_trace_hash"],
            "final_output": str(result.final_output),
        }, indent=2))
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    asyncio.run(run())
