#!/usr/bin/env python3
"""SABLE v2.1 deterministic capability-token issuer/verifier.

A gateway ALLOW becomes a short-lived authorization artifact bound to the
agent/model/provider/runtime/task/tool/policy and reputation context.
Tokens are integrity-protected by a deterministic SHA-256 hash and rejected
on expiry, mismatch, or replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

VERSION = "sable.capability_token.v2.1"


def canon_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _body(*, decision: dict, subject: dict, issued_at: int, expires_at: int, nonce: str) -> dict:
    return {
        "schema_version": VERSION,
        "subject": subject,
        "authorization": {
            "tool": decision["tool"],
            "tool_class": decision["tool_class"],
            "decision": decision["decision"],
            "permission_tier": decision["permission_tier"],
            "trust_score_observed": decision["trust_score_observed"],
        },
        "bindings": {
            "task_id": subject.get("task_id"),
            "task_semantic_key": subject.get("task_semantic_key"),
            "policy_hash": subject.get("policy_hash"),
            "reputation_hash": subject.get("reputation_hash"),
            "credential_hash": subject.get("credential_hash"),
        },
        "issued_at": int(issued_at),
        "expires_at": int(expires_at),
        "nonce": nonce,
    }


def issue(decision: dict, subject: dict, *, issued_at: int, ttl_seconds: int, nonce: str) -> dict:
    if decision.get("decision") != "ALLOW" or not decision.get("executable"):
        raise ValueError("capability_token_requires_gateway_allow")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds_must_be_positive")
    expires_at = issued_at + ttl_seconds
    body = _body(decision=decision, subject=subject, issued_at=issued_at, expires_at=expires_at, nonce=nonce)
    return {**body, "token_hash": canon_hash(body)}


def verify(token: dict, *, now: int, expected: dict, used_nonces: set[str] | None = None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    body = {k: token[k] for k in token if k != "token_hash"}
    if token.get("schema_version") != VERSION:
        reasons.append("schema_version_mismatch")
    if token.get("token_hash") != canon_hash(body):
        reasons.append("token_integrity_mismatch")
    if int(now) < int(token.get("issued_at", 0)):
        reasons.append("token_not_yet_valid")
    if int(now) >= int(token.get("expires_at", 0)):
        reasons.append("token_expired")
    auth = token.get("authorization", {})
    bindings = token.get("bindings", {})
    if auth.get("decision") != "ALLOW":
        reasons.append("token_not_allow")
    for key in ("tool", "task_id", "task_semantic_key", "policy_hash", "reputation_hash", "credential_hash"):
        actual = auth.get(key) if key == "tool" else bindings.get(key)
        expected_value = expected.get(key)
        if expected_value is not None and actual != expected_value:
            reasons.append(f"binding_mismatch:{key}")
    nonce = str(token.get("nonce", ""))
    if used_nonces is not None and nonce in used_nonces:
        reasons.append("token_replay")
    return not reasons, reasons


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decision", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--issued-at", type=int, default=None)
    ap.add_argument("--ttl", type=int, default=60)
    ap.add_argument("--nonce", required=True)
    args = ap.parse_args()
    decision = json.loads(Path(args.decision).read_text(encoding="utf-8"))
    subject = json.loads(Path(args.subject).read_text(encoding="utf-8"))
    issued_at = int(time.time()) if args.issued_at is None else args.issued_at
    token = issue(decision, subject, issued_at=issued_at, ttl_seconds=args.ttl, nonce=args.nonce)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(token, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(token, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
