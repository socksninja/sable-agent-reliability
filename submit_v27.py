#!/usr/bin/env python3
"""SABLE v2.7 public trace verifier.

Accepts a v0.9 trace/submission, validates the portable structure, evaluates
state claims from observed hashes, and emits a deterministic verification
response. This is a local/public protocol surface: no secrets or network calls.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

VERSION = "sable.submission_verifier.v2.7"

def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha(obj):
    return hashlib.sha256(canon(obj)).hexdigest()

def verify_submission(submission: dict) -> dict:
    reasons=[]
    if submission.get("protocol_version") != "sable.submission.v0.9":
        reasons.append("protocol_version_mismatch")
    trace=submission.get("trace",{})
    integ=submission.get("integrity",{})
    if not isinstance(trace,dict): reasons.append("trace_missing")
    if not isinstance(integ,dict): reasons.append("integrity_missing")
    expected=sha(trace) if isinstance(trace,dict) else None
    if expected and integ.get("source_trace_hash") != expected:
        reasons.append("source_trace_hash_mismatch")
    if isinstance(trace,dict):
        agent=trace.get("agent",{}); env=trace.get("environment",{}); integrity=trace.get("integrity",{})
        if not trace.get("task_id"): reasons.append("task_id_missing")
        if not trace.get("goal"): reasons.append("goal_missing")
        if not agent.get("framework"): reasons.append("framework_missing")
        if not agent.get("framework_version"): reasons.append("framework_version_missing")
        if not trace.get("steps"): reasons.append("steps_missing")
        if env.get("task_success") is not True: reasons.append("environment_task_not_successful")
        if not integrity.get("native_tool_calling"): reasons.append("native_tool_calling_not_attested")
        if integrity.get("tool_results_observed_by_sandbox") is not True: reasons.append("sandbox_observation_not_attested")
        if integrity.get("agent_controlled_tool_result") is not False: reasons.append("agent_controlled_result_not_excluded")
        if integrity.get("termination") != "final": reasons.append("non_final_termination")
    return {
        "schema_version": VERSION,
        "verified": not reasons,
        "decision": "VERIFIED" if not reasons else "REJECTED",
        "reasons": reasons,
        "submission_id": submission.get("submission_id"),
        "source_trace_hash": integ.get("source_trace_hash"),
        "task_id": trace.get("task_id") if isinstance(trace,dict) else None,
        "runtime": trace.get("agent",{}).get("framework") if isinstance(trace,dict) else None,
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); sub=json.loads(Path(a.input).read_text(encoding="utf-8")); result=verify_submission(sub)
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2)); raise SystemExit(0 if result["verified"] else 1)
if __name__=="__main__": main()
