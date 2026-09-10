#!/usr/bin/env python3
"""Run a small adversarial SABLE task corpus against a public Qwen server.

Each task is independently sandboxed and evaluated. The model may emit one
structured tool call; SABLE records the observed result and final state. The
runner intentionally preserves failures instead of converting them into passes.
"""
from __future__ import annotations

import argparse
import copy
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

TOOLS = [{
    "type": "function",
    "function": {
        "name": "inventory.reserve",
        "description": "Reserve inventory quantity without changing total stock.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string"}, "qty": {"type": "integer"}},
            "required": ["sku", "qty"],
        },
    },
}]


def post_json(url: str, payload: dict, timeout: int = 180) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def load_model(base_url: str, model: str, timeout: int = 300) -> None:
    data = json.dumps({"model": model}).encode("utf-8")
    req = Request(f"{base_url}/load_model", data=data, headers={"Content-Type": "application/json"}, method="POST")
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
            if event.get("status") == "ready":
                return
            if event.get("status") == "error":
                raise RuntimeError(event.get("message", "model load failed"))
            if time.time() - started > timeout:
                raise TimeoutError("model load timed out")
    raise RuntimeError("model load stream ended without ready")


def run_one(base_url: str, model: str, task: dict) -> dict:
    env = SABLEEnvironment(task)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an agent evaluated by SABLE. Use the provided inventory.reserve function when appropriate. Follow the task exactly. Never claim a state change you did not perform."},
            {"role": "user", "content": json.dumps({"task_id": task["task_id"], "goal": task["goal"], "initial_state": task["initial_state"]}, ensure_ascii=False)},
        ],
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0,
        "max_tokens": 180,
    }
    response = post_json(f"{base_url}/v1/chat/completions", payload)
    message = response["choices"][0]["message"]
    tool_calls = message.get("tool_calls") or []
    steps = []
    for call in tool_calls[:1]:
        fn = call.get("function", {})
        tool_name = fn.get("name")
        raw_args = fn.get("arguments", {})
        try:
            tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            tool_args = {}
        before = env.state_hash()
        obs = env.execute(tool_name, tool_args) if tool_name else None
        if obs is not None:
            steps.append({
                "tool": tool_name,
                "args": tool_args,
                "observed_result": {"ok": obs.ok, "message": obs.message, "state": obs.state},
                "before_state_hash": before,
                "after_state_hash": env.state_hash(),
                "tool_call_id": call.get("id"),
                "transport": "structured_openai_compatible_tool_calls",
            })
    success, checks = task_passes(task, env.state)
    return {
        "task_id": task["task_id"],
        "goal": task["goal"],
        "model": model,
        "native_tool_calling": bool(tool_calls),
        "tool_call_count": len(tool_calls),
        "steps": steps,
        "claimed_status": "success" if steps and steps[0]["observed_result"]["ok"] else ("failure" if steps else "uncertain"),
        "final_report": message.get("content") or (steps[0]["observed_result"]["message"] if steps else ""),
        "environment": {"task_success": success, "checks_passed": sum(checks), "checks_total": len(checks), "final_state": env.snapshot(), "final_state_hash": env.state_hash()},
        "integrity": {"tool_results_observed_by_sandbox": bool(steps), "agent_controlled_tool_result": False, "termination": "final", "infrastructure_error": None, "tool_call_transport": "structured_openai_compatible_tool_calls" if tool_calls else "none"},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="integrations/external_model/reliability_corpus_v01.json")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--base-url", default=BASE_URL_DEFAULT)
    ap.add_argument("--out", default="results/public_model_qwen_reliability_corpus_v01.jsonl")
    args = ap.parse_args()
    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    if not isinstance(tasks, list) or not tasks:
        raise SystemExit("CORPUS_MUST_BE_NONEMPTY_LIST")
    load_model(args.base_url, args.model)
    rows = []
    for idx, task in enumerate(tasks, 1):
        print(f"RUN_TASK {idx}/{len(tasks)} {task['task_id']}")
        try:
            rows.append(run_one(args.base_url, args.model, copy.deepcopy(task)))
        except Exception as exc:
            rows.append({"task_id": task["task_id"], "goal": task["goal"], "model": args.model, "native_tool_calling": False, "tool_call_count": 0, "steps": [], "claimed_status": "uncertain", "final_report": "", "environment": {"task_success": False, "checks_passed": 0, "checks_total": len(task.get("checks", [])), "final_state": task["initial_state"], "final_state_hash": SABLEEnvironment(task).state_hash()}, "integrity": {"tool_results_observed_by_sandbox": False, "agent_controlled_tool_result": False, "termination": "model_error", "infrastructure_error": f"{type(exc).__name__}:{exc}"}})
            print(f"TASK_ERROR {task['task_id']} {type(exc).__name__}:{exc}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n", encoding="utf-8")
    total = len(rows)
    success = sum(bool(r.get("environment", {}).get("task_success")) for r in rows)
    native = sum(bool(r.get("native_tool_calling")) for r in rows)
    errors = sum(r.get("integrity", {}).get("termination") == "model_error" for r in rows)
    print(json.dumps({"benchmark": "SABLE-Reliability-Corpus-v0.1", "model": args.model, "n": total, "task_successes": success, "native_tool_calls": native, "model_errors": errors, "task_success_rate": success / total}, indent=2))


if __name__ == "__main__":
    main()
