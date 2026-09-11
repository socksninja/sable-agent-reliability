#!/usr/bin/env python3
"""Verify a public RNCP execution receipt by URL.

This checks only cryptographic/internal consistency. It does not establish
that an external action actually happened beyond the claims encoded in the
receipt.
"""
import argparse
import hashlib
import json
import urllib.request


def canonical(value):
    if value is None or not isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(canonical(v) for v in value) + "]"
    return "{" + ",".join(
        json.dumps(k, separators=(",", ":"), ensure_ascii=False) + ":" + canonical(value[k])
        for k in sorted(value)
    ) + "}"


def sha256(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sable-public-receipt-verifier/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def verify_provider(name, provider):
    required = {
        "protocol_version", "commitment_id", "commitment_hash", "execution_id",
        "executor_id", "executor_revision", "observed", "receipt_hash",
    }
    missing = sorted(required - provider.keys())
    if missing:
        raise AssertionError(f"{name}: missing fields: {missing}")
    envelope = {
        "protocol_version": provider["protocol_version"],
        "commitment_id": provider["commitment_id"],
        "action": provider["observed"].get("action"),
        "payload": provider["observed"].get("payload"),
    }
    unsigned = dict(provider)
    unsigned.pop("receipt_hash")
    assert provider["commitment_hash"] == sha256(envelope), f"{name}: commitment hash mismatch"
    assert provider["receipt_hash"] == sha256(unsigned), f"{name}: receipt hash mismatch"
    assert provider["observed"].get("status") == "EXECUTED", f"{name}: not executed"


def verify(receipt):
    assert receipt.get("schema") == "RNCP-EXECUTION-RECEIPT-v1", "unexpected schema"
    assert receipt.get("verdict") == "PASS", "receipt verdict is not PASS"
    providers = receipt.get("providers", {})
    assert len(providers) >= 2, "expected at least two provider receipts"
    for name, provider in providers.items():
        verify_provider(name, provider)
    hashes = {p["commitment_hash"] for p in providers.values()}
    assert len(hashes) == 1, "providers do not share one commitment hash"
    identities = [p["executor_id"] for p in providers.values()]
    assert len(set(identities)) == len(identities), "provider identities are not distinct"
    unsigned = dict(receipt)
    unsigned.pop("content_address", None)
    assert receipt.get("content_address") == sha256(unsigned), "content address mismatch"
    return {
        "status": "PASS",
        "schema": receipt["schema"],
        "providers": identities,
        "commitment_hash": next(iter(hashes)),
        "content_address": receipt["content_address"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="HTTPS URL returning a JSON RNCP execution receipt")
    args = parser.parse_args()
    result = verify(fetch_json(args.source))
    print(json.dumps({**result, "source": args.source}, indent=2))


if __name__ == "__main__":
    main()
