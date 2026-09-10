#!/usr/bin/env python3
"""Run a public Hugging Face Qwen model on one SABLE task with no API key.

The model must emit a tool call in its chat response. The SABLE Sandbox remains the
only executor. A text answer without a tool call is rejected as non-native control.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from sandbox import ALLOWED_TOOLS, SABLEEnvironment, task_passes

MODEL_DEFAULT = "Qwen/Qwen2.5-0.5B-Instruct"

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "inventory_reserve",
            "description": "Reserve inventory quantity without changing total stock.",
            "parameters": {
                "type": "object",
                "properties": {"sku": {"type": "string"}, "qty": {"type": "integer", "minimum": 1}},
                "required": ["sku", "qty"],
            },
        },
    }
]

SYSTEM = """You are an agent evaluated by SABLE. You must act on the environment using a tool.
For the requested state change, output exactly one tool call using this format:
<tool_call>{\"name\":\"inventory_reserve\",\"arguments\":{\"sku\":\"SKU-A\",\"qty\":3}}</tool_call>
Do not output prose before the tool call. After the tool result is supplied, output a brief final report.
"""


def parse_tool_call(text: str) -> tuple[str, dict] | None:
    m = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, flags=re.S)
    if not m:
        return None
    obj = json.loads(m.group(1))
    return obj["name"], obj.get("arguments", {})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="integrations/external_model/task.json")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--out", default="results/public_model_qwen_trace.json")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    env = SABLEEnvironment(task)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float32)
    model.eval()

    prompt = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps({
            "task_id": task["task_id"],
            "goal": task["goal"],
            "initial_state": task["initial_state"],
        }, ensure_ascii=False)},
    ]
    rendered = tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(rendered, return_tensors="pt")
    with torch.no_grad():
        generated = model.generate(**inputs, max_new_tokens=160, do_sample=False)
    text = tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)

    tool = parse_tool_call(text)
    native = tool is not None
    steps = []
    termination = "model_error"
    final_report = ""
    claimed = "uncertain"

    if tool:
        tool_name, tool_args = tool
        if tool_name not in ALLOWED_TOOLS:
            observed = {"ok": False, "message": f"unknown_tool:{tool_name}"}
        else:
            obs = env.execute(tool_name.replace("_", ".") if tool_name == "inventory_reserve" else tool_name, tool_args)
            observed = {"ok": obs.ok, "message": obs.message, "state": obs.state, "after_state_hash": obs.after_hash}
            steps.append({"tool": "inventory.reserve", "args": tool_args, "observed_result": observed, "before_state_hash": env.replay_states[-2] if len(env.replay_states) >= 2 else None, "after_state_hash": env.state_hash(), "state_after": env.snapshot()})
        if observed.get("ok"):
            termination = "final"
            final_report = observed.get("message", "")
            claimed = "success"
        else:
            termination = "final"
            final_report = observed.get("message", "")
            claimed = "failure"
    else:
        final_report = text

    task_success, checks = task_passes(task, env.state)
    row = {
        "task_id": task["task_id"],
        "goal": task["goal"],
        "agent": {
            "name": "SABLE-Public-Qwen-Agent",
            "framework": "Transformers",
            "framework_version": "public-hf",
            "model": args.model,
            "provider_base_url": "https://huggingface.co",
        },
        "model_response": text,
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
        },
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"model": args.model, "native_tool_calling": native, "task_success": task_success, "steps": len(steps)}, indent=2))
    if not native:
        raise SystemExit("PUBLIC_MODEL_DID_NOT_EMIT_TOOL_CALL")
    if not task_success:
        raise SystemExit("PUBLIC_MODEL_TASK_FAILED")


if __name__ == "__main__":
    main()
# Trigger the path-scoped public-model E2E workflow without changing behavior.
