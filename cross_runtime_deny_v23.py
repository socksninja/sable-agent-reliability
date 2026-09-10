#!/usr/bin/env python3
"""SABLE v2.3 cross-runtime negative-control harness.

Proves the same signed capability gate semantics across two runtime adapters:
without a valid capability, the underlying sandbox state must not change.
With a valid capability, the same tool call may execute exactly once.
"""
from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from capability_token_v22 import issue_signed
from capability_gate_v22 import authorized_execute
from sandbox import SABLEEnvironment


def task(runtime: str) -> dict:
    return {
        "task_id": f"SABLE-V23-{runtime.upper()}",
        "initial_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 1}}},
        "allowed_tools": ["inventory.reserve"],
        "checks": [],
    }


def subject(runtime: str, task_id: str) -> dict:
    return {
        "agent_id": "sable-v23-reference-agent",
        "model": "deterministic-reference-policy",
        "provider": "local",
        "runtime": runtime,
        "framework_version": "v2.3-test",
        "task_id": task_id,
        "task_semantic_key": "inventory:reserve",
        "policy_hash": "v23-policy",
        "reputation_hash": "v23-reputation",
        "credential_hash": "v23-credential",
    }


def decision():
    return {
        "decision": "ALLOW",
        "executable": True,
        "permission_tier": "LIMITED",
        "trust_score_observed": 82.0,
        "tool": "inventory.reserve",
        "tool_class": "mutating",
    }


def exercise(runtime: str) -> dict:
    t = task(runtime)
    s = subject(runtime, t["task_id"])
    private = Ed25519PrivateKey.generate()
    used: set[str] = set()
    env = SABLEEnvironment(t)
    before = env.state_hash()

    denied = authorized_execute(
        env,
        "inventory.reserve",
        {"sku": "SKU-A", "qty": 3},
        token={},
        public_key=private.public_key(),
        expected={**s, "tool": "inventory.reserve"},
        now=1020,
        used_nonces=used,
    )
    denied_hash = env.state_hash()

    token = issue_signed(decision(), s, private, issued_at=1000, ttl_seconds=60, nonce=f"{runtime}-n1")
    allowed = authorized_execute(
        env,
        "inventory.reserve",
        {"sku": "SKU-A", "qty": 3},
        token=token,
        public_key=private.public_key(),
        expected={**s, "tool": "inventory.reserve"},
        now=1020,
        used_nonces=used,
    )

    replay = authorized_execute(
        env,
        "inventory.reserve",
        {"sku": "SKU-A", "qty": 3},
        token=token,
        public_key=private.public_key(),
        expected={**s, "tool": "inventory.reserve"},
        now=1020,
        used_nonces=used,
    )
    final_hash = env.state_hash()

    return {
        "runtime": runtime,
        "task_id": t["task_id"],
        "before_state_hash": before,
        "deny_without_token": {"ok": denied.ok, "message": denied.message, "state_hash_unchanged": denied_hash == before},
        "allow_with_signed_token": {"ok": allowed.ok, "message": allowed.message},
        "replay_denied": {"ok": replay.ok, "message": replay.message, "state_hash": env.state_hash()},
        "final_state_hash": final_hash,
        "reserved": env.state["inventory"]["SKU-A"]["reserved"],
        "observations": len(env.observations),
    }


def main() -> None:
    rows = [exercise("langgraph"), exercise("crewai")]
    assert all(r["deny_without_token"]["state_hash_unchanged"] for r in rows)
    assert all(r["allow_with_signed_token"]["ok"] for r in rows)
    assert all(not r["replay_denied"]["ok"] for r in rows)
    assert all(r["reserved"] == 4 for r in rows)
    print({"schema_version": "sable.cross_runtime_deny.v2.3", "runtimes": rows, "status": "PASS"})


if __name__ == "__main__":
    main()
