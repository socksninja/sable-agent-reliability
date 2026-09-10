#!/usr/bin/env python3
"""Model-independent self-test for the SABLE v0.9 submission protocol."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from trace_submit_v09 import canonical_hash, normalize_envelope


def build_trace():
    return {
        "task_id": "v09-selftest-001",
        "goal": "Ship order O-100.",
        "agent": {"model": "selftest-agent", "provider_base_url": "https://example.invalid"},
        "steps": [{
            "tool": "order.ship",
            "args": {"order_id": "O-100"},
            "observed_result": {"ok": True, "message": "shipped"},
            "before_state_hash": "before",
            "after_state_hash": "after",
            "state_after": {"order": "shipped"},
        }],
        "claimed_status": "success",
        "final_report": "Order shipped.",
        "environment": {"task_success": True, "checks_passed": 1, "checks_total": 1, "final_state_hash": "after"},
        "integrity": {
            "native_tool_calling": True,
            "tool_results_observed_by_sandbox": True,
            "agent_controlled_tool_result": False,
            "termination": "final",
        },
    }


def build_envelope(trace):
    return {
        "protocol_version": "sable.submission.v0.9",
        "submission_id": "selftest-submission-001",
        "source": {
            "agent_name": "SABLE v0.9 selftest agent",
            "agent_version": "0.1",
            "framework": "synthetic",
            "framework_version": "0.1",
            "adapter": "manual-jsonl",
        },
        "trace": trace,
        "provenance": {
            "captured_at": "2026-01-01T00:00:00Z",
            "collector": "selftest",
            "redaction_policy": "none-needed",
        },
        "integrity": {
            "source_trace_hash": canonical_hash(trace),
            "hash_algorithm": "sha256",
            "canonicalization": "json-sort-keys-utf8",
        },
    }


if __name__ == "__main__":
    trace = build_trace()
    envelope = build_envelope(trace)
    normalized = normalize_envelope(envelope)
    assert normalized["schema_version"] == "sable.v0.5"
    assert normalized["submission"]["schema_version"] == "sable.submission.v0.9"
    assert normalized["submission"]["source_trace_hash"] == canonical_hash(trace)

    bad = json.loads(json.dumps(envelope))
    bad["integrity"]["source_trace_hash"] = "0" * 64
    try:
        normalize_envelope(bad)
    except ValueError as exc:
        assert "source_trace_hash" in str(exc)
    else:
        raise AssertionError("tampered source trace hash was accepted")

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "submission.jsonl"
        p.write_text(json.dumps(envelope) + "\n", encoding="utf-8")
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        assert len(digest) == 64
    print("SABLE v0.9 submission self-test: PASS")
