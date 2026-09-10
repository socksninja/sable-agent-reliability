from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cross_agent_profile_shared_task_comparison(tmp_path: Path) -> None:
    e1 = tmp_path / "langgraph_evidence.jsonl"
    p1 = tmp_path / "langgraph_permission.jsonl"
    e2 = tmp_path / "crewai_evidence.jsonl"
    p2 = tmp_path / "crewai_permission.jsonl"
    out = tmp_path / "profile.json"

    ev = lambda runtime, task, success=True: json.dumps({
        "task": {"task_id": task, "family": "inventory"},
        "agent": {"framework": runtime, "framework_version": "1", "model": "test", "provider_base_url": "test://provider"},
        "outcome": {"task_success": success, "failure_labels": [] if success else ["wrong_state"]},
        "replay": {"replay_match": True},
        "evidence_hash": runtime + task,
    })
    e1.write_text(ev("LangGraph", "T1") + "\n" + ev("LangGraph", "T2") + "\n", encoding="utf-8")
    e2.write_text(ev("CrewAI", "T1") + "\n" + ev("CrewAI", "T2", False) + "\n", encoding="utf-8")
    p1.write_text('{"decision":"ALLOW","verified":true}\n{"decision":"ALLOW","verified":true}\n', encoding="utf-8")
    p2.write_text('{"decision":"ALLOW","verified":true}\n{"decision":"DENY","verified":false,"reasons":["environment_state_not_verified"]}\n', encoding="utf-8")

    subprocess.run([
        sys.executable, str(ROOT / "cross_agent_permission_profile_v16.py"),
        "--evidence", str(e1), str(e2), "--permission", str(p1), str(p2), "--out", str(out)
    ], check=True)
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["observation_count"] == 4
    assert r["runtime_count"] == 2
    assert r["shared_task_count"] == 2
    assert r["runtime_profiles"]["LangGraph"]["eligibility"] == "eligible"
    assert r["runtime_profiles"]["CrewAI"]["observed_allow_rate"] == 0.5
    assert all(x["shared_replay_clean"] for x in r["shared_task_comparisons"])
    assert len(r["profile_hash"]) == 64
