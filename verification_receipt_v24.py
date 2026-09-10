#!/usr/bin/env python3
"""SABLE v2.4 portable verification receipt."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
VERSION = "sable.verification_receipt.v2.4"
def canon_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
def canon_hash(obj: object) -> str:
    return hashlib.sha256(canon_bytes(obj)).hexdigest()
def build_receipt(evidence: dict, permission: dict, *, capability_hash: str | None = None) -> dict:
    agent=evidence.get("agent",{}); state=evidence.get("state",{}); execution=evidence.get("execution",{}); outcome=evidence.get("outcome",{}); replay=evidence.get("replay",{})
    body={"schema_version":VERSION,
          "execution":{"task_id":evidence.get("task",{}).get("task_id") or evidence.get("task_id"),"runtime":agent.get("framework") or evidence.get("runtime"),"framework_version":agent.get("framework_version") or evidence.get("framework_version"),"model":agent.get("model") or evidence.get("model"),"provider":agent.get("provider_base_url") or evidence.get("provider"),"runtime_trace_id":agent.get("runtime_trace_id") or evidence.get("runtime_trace_id")},
          "authorization":{"permission":permission.get("decision"),"verified":permission.get("verified"),"reasons":permission.get("reasons",[]),"capability_token_hash":capability_hash},
          "evidence":{"evidence_hash":evidence.get("evidence_hash"),"task_success":outcome.get("task_success"),"replay_match":replay.get("replay_match"),"before_state_hash":state.get("initial_state_hash"),"after_state_hash":state.get("final_state_hash") or replay.get("final_state_hash"),"termination":execution.get("termination"),"tool_calls":execution.get("tool_calls"),"tools":execution.get("tools",[])}}
    return {**body,"receipt_hash":canon_hash(body)}
def verify_receipt(receipt: dict) -> tuple[bool,list[str]]:
    reasons=[]
    if receipt.get("schema_version")!=VERSION: reasons.append("schema_version_mismatch")
    body={k:receipt[k] for k in receipt if k!="receipt_hash"}
    if receipt.get("receipt_hash")!=canon_hash(body): reasons.append("receipt_integrity_mismatch")
    auth,ev=receipt.get("authorization",{}),receipt.get("evidence",{})
    if auth.get("permission")!="ALLOW": reasons.append("permission_not_allow")
    if auth.get("verified") is not True: reasons.append("permission_not_verified")
    if ev.get("task_success") is not True: reasons.append("task_not_successful")
    if ev.get("replay_match") is not True: reasons.append("replay_mismatch")
    if not ev.get("evidence_hash"): reasons.append("evidence_hash_missing")
    if not ev.get("before_state_hash"): reasons.append("before_state_hash_missing")
    if not ev.get("after_state_hash"): reasons.append("after_state_hash_missing")
    if ev.get("termination") not in {"final","completed"}: reasons.append("non_final_termination")
    return not reasons,reasons
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence",required=True); ap.add_argument("--permission",required=True); ap.add_argument("--capability-hash",default=None); ap.add_argument("--out",required=True); a=ap.parse_args()
    r=build_receipt(json.loads(Path(a.evidence).read_text()),json.loads(Path(a.permission).read_text()),capability_hash=a.capability_hash)
    ok,reasons=verify_receipt(r)
    if not ok: raise SystemExit("receipt_invalid:"+"|".join(reasons))
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema_version":VERSION,"status":"PASS","receipt_hash":r["receipt_hash"]},indent=2))
if __name__=="__main__": main()
