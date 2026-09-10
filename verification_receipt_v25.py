#!/usr/bin/env python3
"""SABLE v2.5 independently verifiable signed execution receipt."""
from __future__ import annotations
import base64, hashlib, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

VERSION = "sable.verification_receipt.v2.5"

def canon_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def canon_hash(obj: object) -> str:
    return hashlib.sha256(canon_bytes(obj)).hexdigest()

def public_key_b64(key: Ed25519PublicKey) -> str:
    return base64.b64encode(key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()

def sign_receipt(receipt: dict, private_key: Ed25519PrivateKey, key_id: str = "sable-receipt-dev") -> dict:
    if receipt.get("schema_version") != "sable.verification_receipt.v2.4":
        raise ValueError("expected_v24_receipt")
    body = {k: receipt[k] for k in receipt if k not in {"receipt_hash", "signature", "signing"}}
    signed = {**body, "receipt_hash": canon_hash(body), "signing": {"alg": "Ed25519", "key_id": key_id}}
    payload = {k: signed[k] for k in signed if k not in {"signature"}}
    signed["signature"] = base64.b64encode(private_key.sign(canon_bytes(payload))).decode()
    return signed

def verify_signed_receipt(receipt: dict, public_key: Ed25519PublicKey) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if receipt.get("schema_version") != VERSION:
        reasons.append("schema_version_mismatch")
    signing = receipt.get("signing", {})
    if signing.get("alg") != "Ed25519":
        reasons.append("signing_algorithm_mismatch")
    body = {k: receipt[k] for k in receipt if k not in {"receipt_hash", "signature", "signing"}}
    if receipt.get("receipt_hash") != canon_hash(body):
        reasons.append("receipt_integrity_mismatch")
    payload = {k: receipt[k] for k in receipt if k != "signature"}
    try:
        public_key.verify(base64.b64decode(receipt["signature"]), canon_bytes(payload))
    except Exception:
        reasons.append("signature_invalid")
    auth = receipt.get("authorization", {})
    evidence = receipt.get("evidence", {})
    if auth.get("permission") != "ALLOW" or auth.get("verified") is not True:
        reasons.append("authorization_not_verified_allow")
    if evidence.get("task_success") is not True or evidence.get("replay_match") is not True:
        reasons.append("execution_not_verified")
    if not evidence.get("evidence_hash") or not evidence.get("before_state_hash") or not evidence.get("after_state_hash"):
        reasons.append("evidence_binding_incomplete")
    return not reasons, reasons

def main() -> None:
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--receipt", required=True); ap.add_argument("--out", required=True)
    args=ap.parse_args(); receipt=json.loads(open(args.receipt, encoding="utf-8").read())
    private=Ed25519PrivateKey.generate(); signed=sign_receipt(receipt, private); ok,reasons=verify_signed_receipt(signed, private.public_key())
    if not ok: raise SystemExit("receipt_signature_invalid:"+"|".join(reasons))
    signed["public_key"] = public_key_b64(private.public_key())
    open(args.out,"w",encoding="utf-8").write(json.dumps(signed,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema_version":VERSION,"status":"PASS","receipt_hash":signed["receipt_hash"],"public_key":signed["public_key"]},indent=2))

if __name__ == "__main__": main()
