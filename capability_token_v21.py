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
SUBJECT_KEYS = ("agent_id", "model", "provider", "runtime", "framework_version")
BINDING_KEYS = ("task_id", "task_semantic_key", "policy_hash", "reputation_hash", "credential_hash")


def canon_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _body(*, decision: dict, subject: dict, issued_at: int, expires_at: int, nonce: str) -> dict:
    return {
        "schema_version": VERSION,
        "subject": {k: subject.get(k) for k in SUBJECT_KEYS},
        "authorization": {
            "tool": decision["tool"],
            "tool_class": decision["tool_class"],
            "decision": decision["decision"],
            "permission_tier": decision["permission_tier"],
            "trust_score_observed": decision["trust_score_observed"],
        },
        "bindings": {k: subject.get(k) for k in BINDING_KEYS},
        "issued_at": int(issued_at),
        "expires_at": int(expires_at),
        "nonce": nonce,
    }


def issue(decision: dict, subject: dict, *, issued_at: int, ttl_seconds: int, nonce: str) -> dict:
    if decision.get("decision") != "ALLOW" or not decision.get("executable"):
        raise ValueError("capability_token_requires_gateway_allow")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds_must_be_positive")
    if not nonce:
        raise ValueError("nonce_required")
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
    try:
        issued_at = int(token["issued_at"])
        expires_at = int(token["expires_at"])
    except (KeyError, TypeError, ValueError):
        reasons.append("invalid_token_times")
        issued_at, expires_at = 0, 0
    if int(now) < issued_at:
        reasons.append("token_not_yet_valid")
    if int(now) >= expires_at:
        reasons.append("token_expired")
    auth = token.get("authorization", {})
    subject = token.get("subject", {})
    bindings = token.get("bindings", {})
    if auth.get("decision") != "ALLOW":
        reasons.append("token_not_allow")
    if not isinstance(subject, dict) or not isinstance(bindings, dict):
        reasons.append("token_subject_or_bindings_invalid")
        subject, bindings = {}, {}
    expected_map = dict(expected)
    for key in SUBJECT_KEYS:
        expected_value = expected_map.get(key)
        if expected_value is not None and subject.get(key) != expected_value:
            reasons.append(f"binding_mismatch:{key}")
    for key in BINDING_KEYS:
        actual = bindings.get(key)
        expected_value = expected_map.get(key)
        if expected_value is not None and actual != expected_value:
            reasons.append(f"binding_mismatch:{key}")
    expected_tool = expected_map.get("tool")
    if expected_tool is not None and auth.get("tool") != expected_tool:
        reasons.append("binding_mismatch:tool")
    nonce = str(token.get("nonce", ""))
    if not nonce:
        reasons.append("nonce_missing")
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
