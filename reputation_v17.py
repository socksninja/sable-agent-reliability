#!/usr/bin/env python3
"""SABLE v1.7: derive auditable trust reputation from verified execution history."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

VERSION = "sable.reputation.v1.7"
MIN_OBSERVATIONS_STABLE = 10


def load_many(path: str) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, list) else [obj]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def canon_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def reputation(records: list[dict]) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        identity = "|".join([str(r.get("model") or "unknown"), str(r.get("provider") or "unknown"), str(r.get("runtime") or "unknown")])
        groups[identity].append(r)

    profiles = {}
    for identity, rows in sorted(groups.items()):
        n = len(rows)
        verified_allow = sum(r.get("permission") == "ALLOW" and r.get("verified") is True and r.get("task_success") is True for r in rows)
        verified_deny = sum(r.get("permission") == "DENY" for r in rows)
        replay_clean = sum(r.get("replay_match") is True for r in rows)
        infra = sum(r.get("termination") in {"provider-rate-limit", "model_error"} for r in rows)
        failures = defaultdict(int)
        for r in rows:
            for label in r.get("failure_labels", []):
                failures[label] += 1

        # Reputation is descriptive, not predictive. The score is bounded [0,100]
        # and only becomes a stable reputation after enough observations.
        observed_success_rate = verified_allow / n if n else 0.0
        integrity_rate = replay_clean / n if n else 0.0
        score = round(100.0 * (0.7 * observed_success_rate + 0.3 * integrity_rate), 2)
        state = "stable" if n >= MIN_OBSERVATIONS_STABLE else "observational"
        eligibility = "eligible" if replay_clean == n and verified_allow > 0 else "restricted"
        profiles[identity] = {
            "observations": n,
            "verified_allow": verified_allow,
            "verified_deny": verified_deny,
            "replay_clean": replay_clean,
            "infrastructure_events": infra,
            "observed_verified_success_rate": observed_success_rate,
            "replay_integrity_rate": integrity_rate,
            "trust_score_observed": score,
            "reputation_state": state,
            "permission_eligibility": eligibility,
            "failure_labels": dict(sorted(failures.items())),
        }

    result = {
        "schema_version": VERSION,
        "observation_count": len(records),
        "minimum_observations_for_stable_reputation": MIN_OBSERVATIONS_STABLE,
        "scoring_contract": {
            "verified_success_weight": 0.7,
            "replay_integrity_weight": 0.3,
            "score_range": [0, 100],
            "predictive_claim": False,
        },
        "profiles": profiles,
        "records": records,
    }
    result["reputation_hash"] = canon_hash(result)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", nargs="+", required=True)
    ap.add_argument("--permission", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if len(args.evidence) != len(args.permission):
        raise SystemExit("evidence/permission file counts must match")
    records: list[dict] = []
    for ep, pp in zip(args.evidence, args.permission):
        evs, pms = load_many(ep), load_many(pp)
        if len(evs) != len(pms):
            raise SystemExit(f"record counts must match: {ep} vs {pp}")
        for ev, pm in zip(evs, pms):
            task, agent, outcome, execution = ev.get("task", {}), ev.get("agent", {}), ev.get("outcome", {}), ev.get("execution", {})
            records.append({
                "task_id": task.get("task_id"),
                "runtime": agent.get("framework", "unknown"),
                "model": agent.get("model"),
                "provider": agent.get("provider_base_url"),
                "permission": pm.get("decision"),
                "verified": pm.get("verified") is True,
                "task_success": outcome.get("task_success") is True,
                "replay_match": ev.get("replay", {}).get("replay_match") is True,
                "termination": execution.get("termination"),
                "failure_labels": sorted(outcome.get("failure_labels", [])),
                "evidence_hash": ev.get("evidence_hash"),
            })
    result = reputation(records)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"observations": result["observation_count"], "profiles": len(result["profiles"]), "reputation_hash": result["reputation_hash"]}, indent=2))


if __name__ == "__main__":
    main()
