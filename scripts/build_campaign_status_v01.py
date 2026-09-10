#!/usr/bin/env python3
"""Build a non-secret, machine-readable Campaign Status v0.1 record."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagnostics", default="results/campaign_launch_diagnostics.json")
    ap.add_argument("--campaign", default="results/external_model_campaign_v14.json")
    ap.add_argument("--out", default="results/campaign_status_v01.json")
    args = ap.parse_args()

    diagnostics = load(Path(args.diagnostics)) or {}
    campaign = load(Path(args.campaign))

    status = "NOT_OBSERVED"
    reason = "No campaign diagnostics were produced."
    observations = 0
    replay_ok = None

    if diagnostics:
        enabled = diagnostics.get("enabled", False)
        key_present = diagnostics.get("api_key_present", False)
        exit_code = diagnostics.get("campaign_exit_code")
        if not enabled:
            status = "DISABLED"
            reason = "Campaign launch manifest is disabled."
        elif not diagnostics.get("model"):
            status = "CONFIG_ERROR"
            reason = "No model was resolved from dispatch input or repository configuration."
        elif not key_present:
            status = "SECRET_MISSING"
            reason = "SABLE_API_KEY was not present in the workflow environment."
        elif exit_code is None:
            status = "STARTED_NO_RESULT"
            reason = "Launch diagnostics exist but campaign exit status was not recorded."
        elif exit_code != 0:
            status = "EXECUTION_FAILED"
            reason = "Campaign runner exited non-zero; inspect campaign_launcher.log."
        elif campaign:
            observations = int(campaign.get("observation_count", 0))
            replay_ok = campaign.get("all_replay_matches")
            expected = 140 * int(campaign.get("repetition_count", 0))
            if observations != expected:
                status = "EVIDENCE_INCOMPLETE"
                reason = f"Observation count {observations} did not match expected {expected}."
            elif replay_ok is not True:
                status = "REPLAY_FAILED"
                reason = "At least one replay check failed."
            else:
                status = "SUCCESS"
                reason = "Campaign completed with expected observations and replay integrity."
        else:
            status = "EXECUTION_INCOMPLETE"
            reason = "Runner reported success but campaign result JSON is missing."

    result = {
        "schema_version": "sable.campaign_status.v0.1",
        "status": status,
        "reason": reason,
        "workflow": diagnostics.get("workflow"),
        "run_id": diagnostics.get("run_id"),
        "run_attempt": diagnostics.get("run_attempt"),
        "head_sha": diagnostics.get("head_sha"),
        "event": diagnostics.get("event"),
        "model": diagnostics.get("model"),
        "base_url": diagnostics.get("base_url"),
        "repetition_count": (campaign or {}).get("repetition_count", diagnostics.get("repeats")),
        "observation_count": observations,
        "all_replay_matches": replay_ok,
        "api_key_present": diagnostics.get("api_key_present"),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
