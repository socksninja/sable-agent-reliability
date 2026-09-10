#!/usr/bin/env python3
"""Model-independent SABLE v0.5 structural and security self-test."""
from __future__ import annotations
import json
from pathlib import Path
from sandbox import SABLEEnvironment, task_passes, ALLOWED_TOOLS, stable_hash

REQUIRED_TASK_KEYS={"task_id","family","goal","initial_state","checks"}

def assert_task_schema(tasks: list[dict]) -> None:
    assert len(tasks)==140, f"expected 140 tasks, got {len(tasks)}"
    ids=[t["task_id"] for t in tasks]
    assert len(ids)==len(set(ids)), "duplicate task ids"
    for t in tasks:
        missing=REQUIRED_TASK_KEYS-set(t)
        assert not missing, f"{t.get('task_id')}: missing {sorted(missing)}"
        assert isinstance(t["checks"],list) and t["checks"], f"{t['task_id']}: empty checks"
        if "allowed_tools" in t:
            assert set(t["allowed_tools"]).issubset(ALLOWED_TOOLS), f"{t['task_id']}: invalid allowed_tools"

def security_tests() -> list[dict]:
    results=[]
    task={"task_id":"SELF-AUTH","initial_state":{"files":["secret.txt"]},"allowed_tools":["file.copy"]}
    env=SABLEEnvironment(task)
    before=env.state_hash(); obs=env.execute("file.delete",{"path":"secret.txt"})
    results.append({"name":"authorization_denies_delete","pass":(not obs.ok and obs.message.startswith("unauthorized_tool:") and env.state_hash()==before)})

    task={"task_id":"SELF-IDEMP","initial_state":{"files":["a.txt"]}}
    env=SABLEEnvironment(task)
    env.execute("file.copy",{"source":"a.txt","destination":"b.txt"})
    second=env.execute("file.copy",{"source":"a.txt","destination":"b.txt"})
    results.append({"name":"duplicate_copy_is_not_silent","pass":(not second.ok and env.state["files"]==["a.txt","b.txt"])})

    task={"task_id":"SELF-ROLL","initial_state":{"inventory":{"S":{"stock":5,"reserved":4}}}}
    env=SABLEEnvironment(task); before=env.state_hash(); obs=env.execute("inventory.reserve",{"sku":"S","qty":2})
    results.append({"name":"failed_reservation_does_not_mutate","pass":(not obs.ok and env.state_hash()==before)})

    task={"task_id":"SELF-HASH","initial_state":{"records":{"A":{"status":"lead"}}}}
    env=SABLEEnvironment(task); h0=stable_hash(env.state); obs=env.execute("record.set",{"section":"records","record":"A","field":"status","value":"qualified"}); h1=env.state_hash()
    results.append({"name":"state_hash_changes_on_mutation","pass":(obs.ok and h0!=h1 and obs.before_hash==h0 and obs.after_hash==h1)})
    return results

def main() -> None:
    tasks=json.loads(Path("tasks/tasks_v0_4_140.json").read_text(encoding="utf-8"))
    assert_task_schema(tasks)
    security=security_tests()
    assert all(x["pass"] for x in security), security
    report={"schema_version":"sable.v0.5","task_count":len(tasks),"security_self_tests":security,"status":"PASS"}
    Path("results").mkdir(exist_ok=True)
    Path("results/selftest_v05.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
