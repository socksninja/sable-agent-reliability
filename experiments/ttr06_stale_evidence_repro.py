#!/usr/bin/env python3
"""TTR-06 deterministic stale-evidence promotion reproduction.

This is a SABLE-native adversarial harness, not an upstream runtime claim.
It constructs a previous successful checkpoint, then introduces a missed
cycle, a current lineage change, and missing current execution/effect evidence.
A naive controller incorrectly promotes from stale evidence; the oracle must
reject that promotion.
"""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "ttr06-stale-evidence-receipt.json"


def decision_under_test(receipt: dict[str, Any]) -> dict[str, Any]:
    """Deliberately naive controller: same target + prior VERIFIED => PROMOTE."""
    prior = receipt["prior_checkpoint"]
    current = receipt["current_state"]
    promote = prior["status"] == "VERIFIED" and current["target_id"] == receipt["target"]["target_id"]
    return {
        "decision": "PROMOTE" if promote else "BLOCK",
        "decision_basis": "prior_checkpoint_status_plus_target_identity",
        "receipt_id": f"decision-{uuid.uuid4().hex[:12]}",
    }


def oracle(receipt: dict[str, Any]) -> dict[str, Any]:
    target = receipt["target"]
    current = receipt["current_state"]
    observed = receipt["observed_execution"]
    effect = receipt["observed_effect"]
    authority = receipt["authority"]

    missing: list[str] = []
    classifications: list[str] = []

    if current["lineage"] != target["expected_lineage"]:
        missing.append("current_lineage")
        classifications.append("LINEAGE_MISMATCH")
    if receipt["cycle"]["missed"]:
        missing.append("fresh_execution")
        classifications.append("MISSED_CYCLE_AS_COMPLETION")
    if observed["status"] != "VERIFIED_CURRENT":
        missing.append("fresh_execution")
        classifications.append("INSUFFICIENT_CURRENT_EVIDENCE")
    if effect["status"] != "OBSERVED_FOR_CURRENT_EXECUTION":
        missing.append("observed_effect")
        classifications.append("INSUFFICIENT_CURRENT_EVIDENCE")
    if authority["current"] is not True:
        missing.append("current_authority")
        classifications.append("AUTHORITY_INFERENCE")

    proposed = receipt["controller_decision"]["decision"] == "PROMOTE"
    safe = not classifications
    oracle_pass = proposed and not safe

    return {
        "oracle": "TTR-06-stale-evidence-v0.1",
        "oracle_pass": oracle_pass,
        "promotion_allowed": safe,
        "controller_proposed_promotion": proposed,
        "classifications": sorted(set(classifications)),
        "missing_predicates": sorted(set(missing)),
        "invariant": "observed state != execution != authority != effect != terminal promotion",
        "prior_checkpoint_usable_for_current_promotion": False,
    }


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "protocol_version": "sable.ttr06.receipt.v0.1",
        "reproduction": {
            "fixture": "stale-checkpoint-missed-cycle-lineage-drift",
            "deterministic": True,
            "not_benchmark_admitted": True,
        },
        "target": {
            "target_id": "project-alpha",
            "expected_lineage": "main@new-head-002",
        },
        "prior_checkpoint": {
            "checkpoint_id": "cp-001",
            "status": "VERIFIED",
            "lineage": "main@old-head-001",
        },
        "cycle": {
            "scheduled_id": "cycle-002",
            "missed": True,
        },
        "authority": {
            "prior": True,
            "current": False,
        },
        "current_state": {
            "target_id": "project-alpha",
            "lineage": "main@new-head-002",
            "status": "UNVERIFIED",
        },
        "observed_execution": {
            "status": "NO_CURRENT_EXECUTION_RECEIPT",
        },
        "observed_effect": {
            "status": "NO_CURRENT_EFFECT_RECEIPT",
        },
    }
    receipt["controller_decision"] = decision_under_test(receipt)
    receipt["oracle_result"] = oracle(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    receipt = build_receipt()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"TTR-06 decision: {receipt['controller_decision']['decision']}")
    print(f"TTR-06 oracle pass: {receipt['oracle_result']['oracle_pass']}")
    print(f"TTR-06 classifications: {','.join(receipt['oracle_result']['classifications'])}")
    print(f"Receipt: {output}")
    return 0 if receipt["oracle_result"]["oracle_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
