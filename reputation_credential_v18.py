#!/usr/bin/env python3
"""SABLE v1.8: package reputation as an auditable, portable credential."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

VERSION = "sable.reputation_credential.v1.8"

def canon(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha(obj: object) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()

def build(reputation: dict) -> dict:
    profiles = reputation.get("profiles", {})
    credentials = []
    for identity, profile in sorted(profiles.items()):
        credentials.append({
            "subject": identity,
            "reputation_state": profile.get("reputation_state"),
            "permission_eligibility": profile.get("permission_eligibility"),
            "trust_score_observed": profile.get("trust_score_observed"),
            "observations": profile.get("observations", 0),
            "verified_allow": profile.get("verified_allow", 0),
            "verified_deny": profile.get("verified_deny", 0),
            "replay_clean": profile.get("replay_clean", 0),
            "infrastructure_events": profile.get("infrastructure_events", 0),
            "failure_labels": profile.get("failure_labels", {}),
        })
    unsigned = {
        "schema_version": VERSION,
        "source_reputation_schema": reputation.get("schema_version"),
        "source_reputation_hash": reputation.get("reputation_hash"),
        "observation_count": reputation.get("observation_count", 0),
        "credentials": credentials,
        "verification_contract": {
            "source_hash_required": True,
            "portable_without_prediction_claim": True,
            "score_is_observed_history": True,
        },
    }
    result = dict(unsigned)
    result["credential_hash"] = sha(unsigned)
    return result

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    reputation = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = build(reputation)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"credentials": len(result["credentials"]), "credential_hash": result["credential_hash"]}, indent=2))

if __name__ == "__main__":
    main()
