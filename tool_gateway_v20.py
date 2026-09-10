#!/usr/bin/env python3
"""SABLE v2.0 deterministic pre-execution tool gateway.

Authorization is decided before a tool is executed. The gateway intentionally
makes no network calls and does not execute the tool itself; it returns a
machine-readable decision that a runtime adapter can enforce.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

VERSION = "sable.tool_gateway.v2.0"
TIERS = {"UNKNOWN": 0, "OBSERVE": 1, "LIMITED": 2, "TRUSTED": 3}

# Conservative defaults: read/inspect tools require OBSERVE; state mutation
# requires LIMITED; destructive tools are never granted by reputation alone.
READ_PREFIXES = ("read", "get", "list", "inspect", "search", "status")
MUTATING_PREFIXES = ("create", "update", "write", "reserve", "schedule", "ship", "rename", "move", "copy", "send")
DESTRUCTIVE_PREFIXES = ("delete", "destroy", "drop", "purge")


def canon_hash(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def classify_tool(tool: str) -> str:
    name = tool.strip().lower().split(".")[-1].replace("-", "_")
    if any(name.startswith(p) for p in DESTRUCTIVE_PREFIXES):
        return "destructive"
    if any(name.startswith(p) for p in MUTATING_PREFIXES):
        return "mutating"
    if any(name.startswith(p) for p in READ_PREFIXES):
        return "read"
    return "unknown"


def decide(profile: dict, tool: str) -> dict:
    tier = str(profile.get("permission_tier", "UNKNOWN")).upper()
    if tier not in TIERS:
        tier = "UNKNOWN"
    score = float(profile.get("trust_score_observed", 0.0) or 0.0)
    tool_class = classify_tool(tool)
    reasons: list[str] = []

    if tool_class == "destructive":
        reasons.append("destructive_tool_requires_explicit_policy")
    elif tier == "UNKNOWN":
        reasons.append("unknown_permission_tier")
    elif tier == "OBSERVE" and tool_class != "read":
        reasons.append("observe_tier_cannot_mutate")
    elif tier == "LIMITED" and tool_class == "unknown":
        reasons.append("limited_tier_requires_known_tool_class")
    elif tier == "TRUSTED" and score < 90.0:
        reasons.append("trusted_tier_score_below_floor")

    allowed = not reasons
    return {
        "schema_version": VERSION,
        "decision": "ALLOW" if allowed else "DENY",
        "executable": allowed,
        "permission_tier": tier,
        "trust_score_observed": score,
        "tool": tool,
        "tool_class": tool_class,
        "reasons": reasons,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--tool", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    result = decide(profile, args.tool)
    result["decision_hash"] = canon_hash(result)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
