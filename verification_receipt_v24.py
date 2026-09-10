#!/usr/bin/env python3
"""SABLE v2.4 portable verification receipt.

A receipt compresses authorization, execution evidence, observed state, replay,
and final permission into one independently verifiable object.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

VERSION = "sable.verification_receipt.v2.4"


def canon_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canon_hash(obj: object) -> str:
    return hashlib.sha256(canon_bytes(obj)).hexdigest()


def build_receipt(evidence: dict, permission: dict, *, capability_hash: str | None = None) -> dict:
    body = {
        "schema_version": VERSION,
        "execution": {
            "task_id": evidence.get("task_id"),
            "runtime": evidence.get("runtime"),
            "framework_version": evidence.get("framework_version"),
            "model": evidence.get("model"),
            "provider": evidence.get("provider"),
            "runtime_trace_id": evidence.get("runtime_trace_id"),
        },
        "authorization": {
            "permission": permission.get("decision"),
            "verified": permission.get("verified"),
            "reasons": permission.get("reasons", []),
            "capability_token_hash": capability_hash,
        },
        "evidence": {
            "evidence_hash": evidence.get("evidence_hash"),
            "task_success": evidence.get("outcome", {}).get("task_success"),
            "replay_match": evidence.get("replay", {}).get("replay_match"),
            "before_state_hash": evidence.get("execution", {}).get("initial_state_hash"),
            "after_state_hash": evidence.get("execution", {}).get("final_state_hash"),
            "termination": evidence.get("execution", {}).get("termination"),
            "steps": evidence.get("execution", {}).get("steps"),
        },
    }
    return {**body, "receipt_hash": canon_hash(body)}


def verify_receipt(receipt: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if receipt.get("schema_version") != VERSION:
        reasons.append("schema_version_mismatch")
    body = {k: receipt[k] for k in receipt if k != "receipt_hash"}
    if receipt.get("receipt_hash") != canon_hash(body):
        reasons.append("receipt_integrity_mismatch")
    auth = receipt.get("authorization", {})
    ev = receipt.get("evidence", {})
    if auth.get("permission") != "ALLOW":
        reasons.append("permission_not_allow")
    if auth.get("verified") is not True:
        reasons.append("permission_not_verified")
    if ev.get("task_success") is not True:
        reasons.append("task_not_successful")
    if ev.get("replay_match") is not True:
        reasons.append("replay_mismatch")
    if not ev.get("evidence_hash"):
        reasons.append("evidence_hash_missing")
    if not ev.get("after_state_hash"):
        reasons.append("after_state_hash_missing")
    if ev.get("termination") not in {"final", "completed"}:
        reasons.append("non_final_termination")
    return not reasons, reasons


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--permission", required=True)
    ap.add_argument("--capability-hash", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    permission = json.loads(Path(args.permission).read_text(encoding="utf-8"))
    receipt = build_receipt(evidence, permission, capability_hash=args.capability_hash)
    ok, reasons = verify_receipt(receipt)
    if not ok:
        raise SystemExit("receipt_invalid:" + "|".join(reasons))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema_version": VERSION, "status": "PASS", "receipt_hash": receipt["receipt_hash"]}, indent=2))


if __name__ == "__main__":
    main()
