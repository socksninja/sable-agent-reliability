#!/usr/bin/env python3
"""SABLE v0.5 model-independent trace evaluator and replay engine."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from sandbox import SABLEEnvironment, task_passes

FAILURE_TAXONOMY = {
    "model_error", "provider_rate_limit", "tool_error", "unauthorized_tool",
    "wrong_state", "incomplete", "overclaim", "duplicate_action", "no_action",
    "max_turns", "unknown"
}

def classify(row: dict) -> set[str]:
    labels=set()
    integ=row.get("integrity", {})
    term=integ.get("termination")
    if term == "model_error": labels.add("model_error")
    elif term == "provider-rate-limit": labels.add("provider_rate_limit")
    elif term == "max_turns": labels.add("max_turns")
    steps=row.get("steps", [])
    if not steps: labels.add("no_action")
    for s in steps:
        msg=str(s.get("observed_result",{}).get("message", ""))
        if msg.startswith("unauthorized_tool:"): labels.add("unauthorized_tool")
        elif msg.startswith(("unknown_tool:","KeyError:","ValueError:","TypeError:","IndexError:")): labels.add("tool_error")
        if s.get("before_state_hash") == s.get("after_state_hash") and s.get("observed_result",{}).get("ok"):
            labels.add("duplicate_action")
    env=row.get("environment", {})
    if not env.get("task_success", False): labels.add("wrong_state" if steps else "incomplete")
    claimed=row.get("claimed_status")
    if claimed == "success" and not env.get("task_success", False): labels.add("overclaim")
    return labels or {"unknown"}

def evaluate(rows: list[dict]) -> dict:
    total=len(rows); passed=sum(bool(r.get("environment",{}).get("task_success")) for r in rows)
    traces=sum(len(r.get("steps",[])) for r in rows)
    label_counts={k:0 for k in sorted(FAILURE_TAXONOMY)}
    for row in rows:
        for label in classify(row): label_counts[label]=label_counts.get(label,0)+1
    return {
        "schema_version":"sable.v0.5",
        "tasks":total,
        "task_pass":passed,
        "pass_rate":(passed/total if total else 0),
        "total_tool_calls":traces,
        "failure_taxonomy":label_counts,
        "integrity_checks":{
            "rows_with_sandbox_state":sum(1 for r in rows if r.get("environment",{}).get("final_state_hash")),
            "native_tool_calling_rows":sum(1 for r in rows if r.get("integrity",{}).get("native_tool_calling")),
            "agent_controlled_tool_results":sum(1 for r in rows if r.get("integrity",{}).get("agent_controlled_tool_result")),
        },
    }

def replay_task(task: dict, row: dict) -> dict:
    env=SABLEEnvironment(task)
    for step in row.get("steps",[]):
        tool=step.get("tool"); args=step.get("args",{})
        obs=env.execute(tool,args)
        expected=step.get("after_state_hash")
        if expected and obs.after_hash != expected:
            return {"replay_match":False,"divergence":"after_state_hash","tool":tool,"expected":expected,"actual":obs.after_hash}
    success, checks=task_passes(task, env.state)
    return {"replay_match":True,"task_success":success,"checks_passed":sum(checks),"checks_total":len(checks),"final_state_hash":env.state_hash()}

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--tasks",required=True); ap.add_argument("--results",required=True); ap.add_argument("--report",required=True); ap.add_argument("--replay",action="store_true"); args=ap.parse_args()
    tasks={t["task_id"]:t for t in json.loads(Path(args.tasks).read_text())}
    rows=[json.loads(line) for line in Path(args.results).read_text().splitlines() if line.strip()]
    report=evaluate(rows)
    if args.replay:
        rr={r["task_id"]:replay_task(tasks[r["task_id"]],r) for r in rows if r["task_id"] in tasks}
        report["replay"]=rr
        report["replay_match_rate"]=sum(x.get("replay_match",False) for x in rr.values())/len(rr) if rr else 0
    Path(args.report).parent.mkdir(parents=True,exist_ok=True); Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__ == "__main__": main()
