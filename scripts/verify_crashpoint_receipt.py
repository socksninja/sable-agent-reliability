#!/usr/bin/env python3
"""Verify the native Crashpoint CrewAI retry experiment without converting it to RNCP."""
import argparse
import hashlib
import json
import urllib.request


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sable-crashpoint-verifier/0.1"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    args = parser.parse_args()
    receipt = fetch_json(args.source)

    assert receipt["runtime"] == "crewai"
    assert receipt["name"] == "crewai_retry"
    assert receipt["prediction_registered_before_execution"] is True
    assert receipt["k_per_case"] == 30
    assert receipt["all_agree"] is True

    cases = receipt["cases"]
    expected = {
        "clean": ("EXACTLY_ONCE", 1),
        "pre_effect": ("EXACTLY_ONCE", 1),
        "post_effect": ("DUPLICATED", 2),
    }
    verified = {}
    for name, (classification, effect_count) in expected.items():
        case = cases[name]
        assert case["k"] == 30
        assert case["pass_rate"] == 1.0
        assert case["classifications"] == {classification: 30}
        assert case["expected_classification"] == classification
        assert case["expected_effect_count"] == effect_count
        verified[name] = {
            "k": case["k"],
            "classification": classification,
            "effect_count": effect_count,
        }

    payload = canonical(receipt).encode("utf-8")
    print(json.dumps({
        "status": "PASS",
        "runtime": receipt["runtime"],
        "experiment": receipt["name"],
        "receipt_id": receipt["receipt"],
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "cases": verified,
        "limitations_preserved": "limitation" in receipt,
    }, indent=2))


if __name__ == "__main__":
    main()
