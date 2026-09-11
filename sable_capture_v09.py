#!/usr/bin/env python3
"""Tiny dependency-free collector for real third-party agent executions.

The caller owns the agent and environment. SABLE only records observed tool
calls, state hashes, provenance and the final claim, then emits a valid
`sable.submission.v0.9` envelope. No model provider is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


@dataclass
class SableCapture:
    agent_name: str
    agent_version: str
    framework: str
    framework_version: str
    adapter: str
    collector: str = "sable_capture_v09/0.1"
    redaction_policy: str = "caller-controlled; no secrets"
    steps: list[dict[str, Any]] = field(default_factory=list)

    def call(
        self,
        tool: str,
        args: dict[str, Any],
        observed_result: Any,
        state_before: Any,
        state_after: Any,
    ) -> Any:
        """Record one real tool call and return the observed result unchanged.

        Put this immediately around the *real* tool invocation in an agent:

            before = snapshot()
            result = real_tool(**args)
            after = snapshot()
            result = capture.call("tool", args, result, before, after)
        """
        self.steps.append({
            "tool": str(tool),
            "args": args or {},
            "observed_result": observed_result,
            "before_state_hash": sha256(state_before),
            "after_state_hash": sha256(state_after),
            "state_after": state_after,
        })
        return observed_result

    def envelope(
        self,
        *,
        task_id: str,
        goal: str,
        agent_metadata: dict[str, Any] | None = None,
        claimed_status: str = "success",
        final_report: str = "",
        environment: dict[str, Any] | None = None,
        submission_id: str | None = None,
    ) -> dict[str, Any]:
        if claimed_status not in {"success", "failure", "uncertain"}:
            raise ValueError("claimed_status must be success|failure|uncertain")
        trace = {
            "task_id": task_id,
            "goal": goal,
            "agent": agent_metadata or {"name": self.agent_name, "version": self.agent_version},
            "steps": self.steps,
            "claimed_status": claimed_status,
            "final_report": final_report,
            "environment": environment or {},
            "integrity": {"state_hash_algorithm": "sha256"},
        }
        return {
            "protocol_version": "sable.submission.v0.9",
            "submission_id": submission_id or f"sable-ext-{uuid.uuid4().hex[:12]}",
            "source": {
                "agent_name": self.agent_name,
                "agent_version": self.agent_version,
                "framework": self.framework,
                "framework_version": self.framework_version,
                "adapter": self.adapter,
            },
            "trace": trace,
            "provenance": {
                "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "collector": self.collector,
                "redaction_policy": self.redaction_policy,
            },
            "integrity": {
                "source_trace_hash": sha256(trace),
                "hash_algorithm": "sha256",
                "canonicalization": "json-sort-keys-utf8",
            },
        }


def write_envelope(path: str | Path, envelope: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _cli() -> None:
    ap = argparse.ArgumentParser(description="Emit one SABLE v0.9 envelope from a capture JSON object")
    ap.add_argument("--input", required=True, help="JSON file containing an already-captured envelope object")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    row = json.loads(Path(args.input).read_text(encoding="utf-8"))
    # Recompute integrity at the final serialization boundary.
    row["integrity"]["source_trace_hash"] = sha256(row["trace"])
    write_envelope(args.output, row)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    _cli()
