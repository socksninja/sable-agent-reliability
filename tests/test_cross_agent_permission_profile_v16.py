from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cross_agent_profile_shared_semantic_task(tmp_path: Path) -> None:
    e1 = tmp_path / "langgraph_evidence.jsonl"
    p1 = tmp_path / "langgraph_permission.jsonl"
    e2 = tmp_path / "crewai_evidence.jsonl"
    p2 = tmp_path / "crewai_permission.jsonl"
    out = tmp_path / "profile.json"

    goal = "Reserve 3 units of SKU-A without changing total stock."
    def evidence(runtime: str, task_id: str, success: bool = True) -> str:
        return json.dumps({
            "task": {"task_id": task_id, "family": "inventory", "goal": goal},
            "agent": {"framework": runtime, "framework_version": "1", "model": "test", "provider_base_url": "test://provider"},
            "outcome": {"task_success": success, "failure_labels": [] if success else ["wrong_state"]},
            "replay": {"replay_match": True},
            "evidence_hash": runtime + task_id,
        })
    e1.write_text(evidence("LangGraph", "SABLE-LG-01") + "\n", encoding="utf-8")
    e2.write_text(evidence("CrewAI", "SABLE-CREW-01") + "\n", encoding="utf-8")
    p1.write_text('{"decision":"ALLOW","verified":true}\n', encoding="utf-8")
    p2.write_text('{"decision":"DENY","verified":false,"reasons":["environment_state_not_verified"]}\n', encoding="utf-8")

    subprocess.run([
        sys.executable, str(ROOT / "cross_agent_permission_profile_v16.py"),
        "--evidence", str(e1), str(e2), "--permission", str(p1), str(p2), "--out", str(out)
    ], check=True)
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["observation_count"] == 2
    assert r["runtime_count"] == 2
    assert r["shared_task_count"] == 1
    assert r["shared_task_comparisons"][0]["task_ids"] == ["SABLE-CREW-01", "SABLE-LG-01"]
    assert r["shared_task_comparisons"][0]["runtimes"] == ["CrewAI", "LangGraph"]
    assert len(r["profile_hash"]) == 64
