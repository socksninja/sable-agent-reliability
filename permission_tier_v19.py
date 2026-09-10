#!/usr/bin/env python3
"""SABLE v1.9: convert portable reputation into executable permission tiers."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

VERSION = "sable.permission_tier.v1.9"

def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def decide(profile: dict) -> dict:
    score = float(profile.get("trust_score_observed", 0.0))
    n = int(profile.get("observations", 0))
    replay = int(profile.get("replay_clean", 0))
    allow = int(profile.get("verified_allow", 0))
    state = profile.get("reputation_state")
    reasons = []
    if n == 0:
        return {"tier":"UNKNOWN","reason_codes":["no_observations"],"executable":False}
    if replay < n:
        reasons.append("replay_integrity_not_clean")
    if allow == 0:
        reasons.append("no_verified_allow")
    if state != "stable":
        reasons.append("reputation_not_stable")
    if replay < n or allow == 0:
        tier = "OBSERVE"
    elif n < 10:
        tier = "OBSERVE"
    elif score < 70:
        tier = "OBSERVE"
    elif score < 90:
        tier = "LIMITED"
    elif n < 25:
        tier = "LIMITED"
        reasons.append("trusted_threshold_requires_25_observations")
    else:
        tier = "TRUSTED"
    return {"tier":tier,"reason_codes":reasons,"executable":tier in {"LIMITED","TRUSTED"}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--out",required=True); args=ap.parse_args()
    source=load(args.input); out={"schema_version":VERSION,"policy_contract":{"tiers":["UNKNOWN","OBSERVE","LIMITED","TRUSTED"],"stable_observations":10,"trusted_observations":25,"score_floor_limited":70.0,"score_floor_trusted":90.0,"replay_must_be_clean":True},"profiles":{}}
    for identity, p in sorted(source.get("profiles",{}).items()):
        d=decide(p); out["profiles"][identity]={"identity":identity,"observations":p.get("observations",0),"trust_score_observed":p.get("trust_score_observed",0.0),**d}
    body={k:v for k,v in out.items() if k!="policy_hash"}
    out["policy_hash"]=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"profiles":len(out["profiles"]),"policy_hash":out["policy_hash"]},indent=2))
if __name__=="__main__": main()
