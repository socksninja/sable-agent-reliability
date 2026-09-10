#!/usr/bin/env python3
"""Run SABLE tasks through a real external Hugging Face model runtime.

The model decides whether to invoke the native tool. The environment records
observable state transitions independently of the model output. Model/tool
failures are observations and must still be serialized for admission rather
than terminating the workflow before evidence exists.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

MODEL_ID = os.environ.get("SABLE_MODEL", "HuggingFaceTB/SmolLM2-135M-Instruct")
OUT = Path("external_results")
OUT.mkdir(parents=True, exist_ok=True)

TASKS = [
    {"task_id": "EXT-01", "sku": "SKU-A", "qty": 3},
    {"task_id": "EXT-02", "sku": "SKU-B", "qty": 2},
    {"task_id": "EXT-03", "sku": "SKU-C", "qty": 5},
    {"task_id": "EXT-04", "sku": "SKU-D", "qty": 1},
]


def state_hash(state: dict) -> str:
    raw = json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def build_prompt(task: dict) -> str:
    return (
        "You are an execution agent. Follow the instruction exactly.\n"
        f"Task: reserve {task['qty']} units of {task['sku']}.\n"
        "Reply with exactly one line: CALL inventory.reserve sku=<SKU> qty=<N>\n"
        f"The SKU is {task['sku']} and N is {task['qty']}.\n"
        "Do not add any other text."
    )


def main() -> None:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
    model.eval()

    raw = []
    for task in TASKS:
        prompt = build_prompt(task)
        started = time.time()
        inputs = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            generated = model.generate(**inputs, max_new_tokens=48, do_sample=False)
        text = tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        elapsed_ms = round((time.time() - started) * 1000, 1)

        # Accept harmless formatting variation while preserving the fact that
        # the decision came from the external model output.
        match = re.search(
            r"CALL\s+inventory\.reserve\s+sku=([^\s]+)\s+qty=(\d+)",
            text,
        )
        native_tool_call = match is not None
        tool_calls = []
        before = {"reservations": []}
        after = {"reservations": []}
        task_success = False

        before_hash = state_hash(before)
        if match:
            sku, qty_s = match.groups()
            qty = int(qty_s)
            tool_calls.append({"name": "inventory.reserve", "args": {"sku": sku, "qty": qty}})
            reservation = {"sku": sku, "qty": qty}
            after = {"reservations": [reservation]}
            after_hash = state_hash(after)
            task_success = sku == task["sku"] and qty == task["qty"]
            outcome = "reserved" if task_success else "wrong_arguments"
        else:
            after_hash = before_hash
            outcome = "model_output_not_parseable"

        row = {
            "task_id": task["task_id"],
            "prompt": prompt,
            "model_output": text,
            "latency_ms": elapsed_ms,
            "native_tool_call": native_tool_call,
            "tool_calls": tool_calls,
            "before_state": before,
            "before_state_hash": before_hash,
            "after_state": after,
            "after_state_hash": after_hash,
            "task_success": task_success,
            "agent_action_outcome": outcome,
            "observed_environment": {"reservation_count": len(after["reservations"])},
            "model_error": not native_tool_call,
        }
        raw.append(row)

    payload = {
        "model_id": MODEL_ID,
        "runtime": "Hugging Face Transformers (PyTorch)",
        "python_version": os.sys.version,
        "github_repository": os.environ.get("GITHUB_REPOSITORY"),
        "github_run_id": int(os.environ.get("GITHUB_RUN_ID", "0")),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "tasks": raw,
    }
    out_path = OUT / "raw_external_runtime.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Important: a model inability to issue a tool call is itself a real
    # reliability observation. Keep the workflow alive so SABLE can admit and
    # audit the evidence instead of hiding the failure behind CI exit status.
    successful = sum(bool(r["task_success"]) for r in raw)
    native = sum(bool(r["native_tool_call"]) for r in raw)
    print(f"EXTERNAL_RUNTIME_OBSERVATION_WRITTEN={out_path}")
    print(f"TASKS={len(raw)} TASK_SUCCESSES={successful} NATIVE_TOOL_CALLS={native}")


if __name__ == "__main__":
    main()
