from __future__ import annotations

import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(tmp_path: Path, profile: dict, tool: str) -> dict:
    p = tmp_path / "profile.json"
    o = tmp_path / "decision.json"
    p.write_text(json.dumps(profile), encoding="utf-8")
    subprocess.run([
        sys.executable, str(ROOT / "tool_gateway_v20.py"),
        "--profile", str(p), "--tool", tool, "--out", str(o)
    ], check=True, capture_output=True, text=True)
    return json.loads(o.read_text(encoding="utf-8"))


def test_gateway_tiers_and_tool_classes(tmp_path: Path) -> None:
    observe = run(tmp_path, {"permission_tier":"OBSERVE","trust_score_observed":100}, "inventory.read")
    assert observe["decision"] == "ALLOW"
    assert observe["tool_class"] == "read"

    observe_mutation = run(tmp_path, {"permission_tier":"OBSERVE","trust_score_observed":100}, "inventory.reserve")
    assert observe_mutation["decision"] == "DENY"
    assert "observe_tier_cannot_mutate" in observe_mutation["reasons"]

    limited = run(tmp_path, {"permission_tier":"LIMITED","trust_score_observed":80}, "inventory.reserve")
    assert limited["decision"] == "ALLOW"
    assert limited["tool_class"] == "mutating"

    trusted = run(tmp_path, {"permission_tier":"TRUSTED","trust_score_observed":95}, "inventory.reserve")
    assert trusted["decision"] == "ALLOW"

    destructive = run(tmp_path, {"permission_tier":"TRUSTED","trust_score_observed":99}, "inventory.delete")
    assert destructive["decision"] == "DENY"
    assert "destructive_tool_requires_explicit_policy" in destructive["reasons"]

    unknown = run(tmp_path, {"permission_tier":"UNKNOWN","trust_score_observed":0}, "inventory.read")
    assert unknown["decision"] == "DENY"
    assert len(unknown["decision_hash"]) == 64
