#!/usr/bin/env python3
"""Run Qwen through the Hugging Face Transformers local OpenAI-compatible server.

This runner intentionally consumes structured `tool_calls` returned by the server.
It never parses model text such as <tool_call>...</tool_call> into a tool invocation.
The SABLE Sandbox remains the only executor.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sandbox import ALLOWED_TOOLS, SABLEEnvironment, task_passes

MODEL_DEFAULT = "Qwen/Qwen2.5-0.5B-Instruct"
BASE_URL_DEFAULT = "http://127.0.0.1:8000"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inventory.reserve",
            "description": "Reserve inventory quantity without changing total stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string"},
                    "qty": {"type": "integer", "minimum": 1},
                },
                "required": ["sku", "qty"],
            },
        },
    }
]


def post_json(url: str, payload: dict, timeout: int = 120) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def load_model(base_url: str, model: str, timeout: int = 300) -> None:
    data = json.dumps({"model": model}).encode("utf-8")
    req = Request(
        f"{base_url}/load_model",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    with urlopen(req, timeout=timeout) as resp:
        while True:
            line = resp.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").strip()
            if not text.startswith("data:"):
                continue
            event = json.loads(text[len("data:"):].strip())
            print("MODEL_LOAD=" + json.dumps(event, ensure_ascii=False))
            status = event.get("status")
            if status == "ready":
                return
            if status == "error":
                raise RuntimeError(event.get("message", "model load failed"))
            if time.time() - started > timeout:
                raise TimeoutError("model load timed out")
    raise RuntimeError("model load stream ended without ready")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="integrations/external_model/task.json")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--base-url", default=BASE_URL_DEFAULT)
    ap.add_argument("--out", default="results/public_model_qwen_native_trace.json")
    args = ap.parse_args()

    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    env = SABLEEnvironment(task)
    load_model(args.base_url, args.model)

    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "system",
                "content": "You are an agent evaluated by SABLE. Use the provided inventory.reserve function to perform the requested state change. Do not answer with prose when a function call is needed.",
            },
            {
                "role": "user",
                "content": json.dumps({
                    "task_id": task["task_id"],
                    "goal": task["goal"],
                    "initial_state": task["initial_state"],
                }, ensure_ascii=False),
            },
        ],
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0,
        "max_tokens": 160,
    }
    response = post_json(f"{args.base_url}/v1/chat/completions", payload, timeout=180)
    message = response["choices"][0]["message"]
    tool_calls = message.get("tool_calls") or []
    native = bool(tool_calls)
    steps = []
    termination = "model_error"
    final_report = message.get("content") or ""
    claimed = "uncertain"

    if tool_calls:
        call = tool_calls[0]
        fn = call.get("function", {})
        tool_name = fn.get("name")
        raw_args = fn.get("arguments", {})
        tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        if tool_name not in ALLOWED_TOOLS:
            observed = {"ok": False, "message": f"unknown_tool:{tool_name}"}
        else:
            before_state_hash = env.state_hash()
            obs = env.execute(tool_name, tool_args)
            observed = {
                "ok": obs.ok,
                "message": obs.message,
                "state": obs.state,
                "after_state_hash": obs.after_hash,
            }
            steps.append({
                "tool": tool_name,
                "args": tool_args,
                "observed_result": observed,
                "before_state_hash": before_state_hash,
                "after_state_hash": env.state_hash(),
                "state_after": env.snapshot(),
                "tool_call_id": call.get("id"),
                "transport": "structured_openai_compatible_tool_calls",
            })
        termination = "final"
        final_report = observed.get("message", "")
        claimed = "success" if observed.get("ok") else "failure"

    task_success, checks = task_passes(task, env.state)
    row = {
        "task_id": task["task_id"],
        "goal": task["goal"],
        "agent": {
            "name": "SABLE-Public-Qwen-Native-Serve-Agent",
            "framework": "Transformers Serve",
            "framework_version": "public-hf",
            "model": args.model,
            "provider_base_url": "https://huggingface.co",
        },
        "model_response": message,
        "steps": steps,
        "claimed_status": claimed,
        "final_report": final_report,
        "environment": {
            "task_success": task_success,
            "checks_passed": sum(checks),
            "checks_total": len(checks),
            "final_state": env.snapshot(),
            "final_state_hash": env.state_hash(),
        },
        "integrity": {
            "native_tool_calling": native,
            "tool_results_observed_by_sandbox": native and bool(steps),
            "agent_controlled_tool_result": False,
            "termination": termination,
            "infrastructure_error": None,
            "tool_call_transport": "structured_openai_compatible_tool_calls" if native else "none",
        },
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "model": args.model,
        "native_tool_calling": native,
        "task_success": task_success,
        "steps": len(steps),
        "tool_call_transport": row["integrity"]["tool_call_transport"],
    }, indent=2))
    if not native:
        raise SystemExit("PUBLIC_MODEL_DID_NOT_RETURN_STRUCTURED_TOOL_CALLS")
    if not task_success:
        raise SystemExit("PUBLIC_MODEL_TASK_FAILED")


if __name__ == "__main__":
    main()
