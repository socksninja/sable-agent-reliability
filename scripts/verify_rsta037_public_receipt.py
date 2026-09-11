#!/usr/bin/env python3
import hashlib
import json
import sys
import urllib.request

SOURCE = "https://raw.githubusercontent.com/socksninja/-/main/rsta-evidence/rsta037/34630865469-rsta037-execution-receipt.json"
EXPECTED_CONTENT_ADDRESS = "0943787de4f906a578cc7ddb8cca1a8964fbb110d21e50d9e48fbb4f465f8960"
EXPECTED_COMMITMENT_HASH = "ffa4b838925b47acb027446d65bfa7240c9e8735721c601ed735fc0ae0cd4e38"


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


def fetch_json():
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "sable-rsta037-independent-verifier/1.0"})
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


def main():
    receipt = fetch_json()
    assert receipt["schema"] == "RNCP-EXECUTION-RECEIPT-v1"
    assert receipt["rsta"] == "RSTA-037"
    assert receipt["verdict"] == "PASS"
    assert receipt["commitment"]["commitment_id"] == "RSTA-037-34630865469"
    assert receipt["providers"]["github"]["commitment_hash"] == EXPECTED_COMMITMENT_HASH
    verify_provider("github", receipt["providers"]["github"])
    verify_provider("vercel", receipt["providers"]["vercel"])
    assert receipt["providers"]["github"]["commitment_hash"] == receipt["providers"]["vercel"]["commitment_hash"]
    assert receipt["providers"]["github"]["executor_id"] != receipt["providers"]["vercel"]["executor_id"]
    unsigned_receipt = dict(receipt)
    unsigned_receipt.pop("content_address")
    assert sha256(unsigned_receipt) == receipt["content_address"] == EXPECTED_CONTENT_ADDRESS
    print(json.dumps({
        "status": "PASS",
        "source": SOURCE,
        "content_address": receipt["content_address"],
        "commitment_hash": receipt["commitment"]["commitment_id"],
        "github_receipt_hash": receipt["providers"]["github"]["receipt_hash"],
        "vercel_receipt_hash": receipt["providers"]["vercel"]["receipt_hash"],
        "providers": [receipt["providers"]["github"]["executor_id"], receipt["providers"]["vercel"]["executor_id"]],
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"INDEPENDENT_VERIFICATION_FAILED: {exc}", file=sys.stderr)
        raise
