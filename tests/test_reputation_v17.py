from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_reputation_is_observational_until_10_runs(tmp_path: Path) -> None:
    e = tmp_path / "evidence.jsonl"
    p = tmp_path / "permission.jsonl"
    out = tmp_path / "reputation.json"
    rows_e, rows_p = [], []
    for i in range(4):
        rows_e.append(json.dumps({
            "task": {"task_id": f"T{i}", "family": "inventory"},
            "agent": {"framework": "LangGraph", "model": "m", "provider_base_url": "test://p"},
            "outcome": {"task_success": True, "failure_labels": []},
            "execution": {"termination": "final"},
            "replay": {"replay_match": True},
            "evidence_hash": f"h{i}",
        }))
        rows_p.append(json.dumps({"decision": "ALLOW", "verified": True}))
    e.write_text("\n".join(rows_e) + "\n", encoding="utf-8")
    p.write_text("\n".join(rows_p) + "\n", encoding="utf-8")
    subprocess.run([
        sys.executable, str(ROOT / "reputation_v17.py"),
        "--evidence", str(e), "--permission", str(p), "--out", str(out)
    ], check=True)
    r = json.loads(out.read_text(encoding="utf-8"))
    profile = next(iter(r["profiles"].values()))
    assert profile["observations"] == 4
    assert profile["trust_score_observed"] == 100.0
    assert profile["reputation_state"] == "observational"
    assert r["scoring_contract"]["predictive_claim"] is False
    assert len(r["reputation_hash"]) == 64
