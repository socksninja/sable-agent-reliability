#!/usr/bin/env python3
"""SABLE v2.6 portable signed receipt with self-contained verification."""
from __future__ import annotations
import base64, hashlib, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

VERSION = "sable.verification_receipt.v2.6"
V24 = "sable.verification_receipt.v2.4"

def canon_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def canon_hash(obj: object) -> str:
    return hashlib.sha256(canon_bytes(obj)).hexdigest()

def public_key_b64(key: Ed25519PublicKey) -> str:
    return base64.b64encode(key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode("ascii")

def load_public_key(value: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(value))

def sign_receipt(receipt: dict, private_key: Ed25519PrivateKey, key_id: str = "sable-receipt-dev") -> dict:
    if receipt.get("schema_version") != V24:
        raise ValueError("expected_v24_receipt")
    body = {k: receipt[k] for k in receipt if k != "receipt_hash"}
    body.pop("signing", None); body.pop("signature", None); body.pop("public_key", None)
    body["schema_version"] = VERSION
    receipt_hash = canon_hash(body)
    signing = {"alg": "Ed25519", "key_id": key_id}
    public_key = public_key_b64(private_key.public_key())
    payload = {**body, "receipt_hash": receipt_hash, "signing": signing, "public_key": public_key}
    signature = base64.b64encode(private_key.sign(canon_bytes(payload))).decode("ascii")
    return {**payload, "signature": signature}

def verify_self_contained(receipt: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if receipt.get("schema_version") != VERSION:
        reasons.append("schema_version_mismatch")
    signing = receipt.get("signing", {})
    if signing.get("alg") != "Ed25519": reasons.append("signing_algorithm_mismatch")
    body = {k: receipt[k] for k in receipt if k not in {"receipt_hash", "signature", "signing", "public_key"}}
    if receipt.get("receipt_hash") != canon_hash(body): reasons.append("receipt_integrity_mismatch")
    try:
        key = load_public_key(receipt["public_key"])
        payload = {k: receipt[k] for k in receipt if k != "signature"}
        key.verify(base64.b64decode(receipt["signature"]), canon_bytes(payload))
    except Exception:
        reasons.append("signature_invalid")
    auth = receipt.get("authorization", {}); ev = receipt.get("evidence", {})
    if auth.get("permission") != "ALLOW" or auth.get("verified") is not True: reasons.append("authorization_not_verified_allow")
    if ev.get("task_success") is not True or ev.get("replay_match") is not True: reasons.append("execution_not_verified")
    for field in ("evidence_hash", "before_state_hash", "after_state_hash"):
        if not ev.get(field): reasons.append(f"{field}_missing")
    return not reasons, reasons
