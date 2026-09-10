from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_taxonomy_accepts_jsonl_and_classifies_success_and_failures(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.jsonl"
    permission = tmp_path / "permission.jsonl"
    out = tmp_path / "taxonomy.json"

    evidence.write_text(
        "\n".join(
            [
                json.dumps({"task": {"task_id": "T1", "family": "inventory"}, "agent": {"framework": "test", "framework_version": "1"}, "outcome": {"task_success": True, "failure_labels": []}, "replay": {"replay_match": True}, "evidence_hash": "h1"}),
                json.dumps({"task": {"task_id": "T2", "family": "file"}, "agent": {"framework": "test", "framework_version": "1"}, "outcome": {"task_success": False, "failure_labels": ["wrong_state"]}, "replay": {"replay_match": True}, "evidence_hash": "h2"}),
                json.dumps({"task": {"task_id": "T3", "family": "records"}, "agent": {"framework": "test", "framework_version": "1"}, "outcome": {"task_success": False, "failure_labels": []}, "execution": {"termination": "provider-rate-limit"}, "replay": {"replay_match": True}, "evidence_hash": "h3"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    permission.write_text("{\"decision\":\"ALLOW\"}\n{\"decision\":\"DENY\"}\n{\"decision\":\"DENY\"}\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(ROOT / "failure_taxonomy_v14.py"), "--evidence", str(evidence), "--permission", str(permission), "--out", str(out)],
        check=True,
    )
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["observation_count"] == 3
    assert result["verified_successes"] == 1
    assert result["verified_denials"] == 2
    assert result["all_replay_matches"] is True
    assert result["root_cause_counts"] == {"provider_rate_limit": 1, "state_incorrect": 1, "verified_success": 1}
