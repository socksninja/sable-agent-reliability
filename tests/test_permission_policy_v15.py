from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_policy_profile_blocks_replay_mismatch_and_hashes_contract(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.jsonl"
    permission = tmp_path / "permission.jsonl"
    out = tmp_path / "policy.json"

    evidence.write_text(
        "\n".join([
            json.dumps({"task":{"task_id":"T1","family":"inventory"},"agent":{"framework":"CrewAI","framework_version":"1","model":"m"},"outcome":{"task_success":True,"failure_labels":[]},"execution":{"termination":"final"},"replay":{"replay_match":True},"evidence_hash":"h1"}),
            json.dumps({"task":{"task_id":"T2","family":"file"},"agent":{"framework":"CrewAI","framework_version":"1","model":"m"},"outcome":{"task_success":False,"failure_labels":["wrong_state"]},"execution":{"termination":"final"},"replay":{"replay_match":False},"evidence_hash":"h2"}),
        ]) + "\n", encoding="utf-8")
    permission.write_text(
        "\n".join([
            json.dumps({"decision":"ALLOW","verified":True,"reasons":[]}),
            json.dumps({"decision":"DENY","verified":False,"reasons":["environment_state_not_verified"]}),
        ]) + "\n", encoding="utf-8")

    subprocess.run([
        sys.executable, str(ROOT / "permission_policy_v15.py"),
        "--evidence", str(evidence),
        "--permission", str(permission),
        "--out", str(out),
    ], check=True)
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["schema_version"] == "sable.permission_policy.v1.5"
    assert result["observation_count"] == 2
    profile = result["runtime_profiles"]["CrewAI"]
    assert profile["allow"] == 1
    assert profile["deny"] == 1
    assert profile["replay_mismatch"] == 1
    assert profile["policy_state"] == "blocked"
    assert len(result["policy_hash"]) == 64
