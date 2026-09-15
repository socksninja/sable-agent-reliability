"""Validate an optional execution-evidence receipt without changing conformance semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

RECEIPT_SCHEMA = "sable.reliability_record.v0.9"


@dataclass(frozen=True)
class EvidenceReceiptResult:
    valid: bool
    errors: tuple[str, ...] = ()


def validate_receipt(receipt: Mapping[str, Any]) -> EvidenceReceiptResult:
    """Validate the minimum post-run evidence receipt contract.

    This deliberately does not decide whether an OTel conformance scenario
    passed. Conformance PASS/FAIL remains owned by the existing runner.
    """
    errors: list[str] = []
    required = (
        "repository",
        "commit_sha",
        "github_actions_run_id",
        "trace_id",
        "trace_url",
    )

    if receipt.get("schema") != RECEIPT_SCHEMA:
        errors.append(f"schema must be {RECEIPT_SCHEMA}")
    for field in required:
        if not receipt.get(field):
            errors.append(f"{field} is required")

    effect = receipt.get("external_effect")
    if not isinstance(effect, Mapping):
        errors.append("external_effect must be an object")
    else:
        for field in (
            "system",
            "operation",
            "effect_id",
            "effect_url",
            "final_state_sha256",
        ):
            if not effect.get(field):
                errors.append(f"external_effect.{field} is required")

    if receipt.get("task_success") is not True:
        errors.append("task_success must be true")

    return EvidenceReceiptResult(valid=not errors, errors=tuple(errors))


if __name__ == "__main__":  # pragma: no cover
    import json
    import sys

    result = validate_receipt(json.load(sys.stdin))
    print(json.dumps({"valid": result.valid, "errors": list(result.errors)}))
    raise SystemExit(0 if result.valid else 1)
