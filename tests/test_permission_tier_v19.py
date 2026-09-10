from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(tmp_path, profiles):
    src=tmp_path/'reputation.json'; out=tmp_path/'tier.json'
    src.write_text(json.dumps({'profiles':profiles}),encoding='utf-8')
    subprocess.run([sys.executable,str(ROOT/'permission_tier_v19.py'),'--input',str(src),'--out',str(out)],check=True)
    return json.loads(out.read_text())
def test_permission_tiers(tmp_path):
    r=run(tmp_path, {
      'u': {'observations':0,'trust_score_observed':0,'replay_clean':0,'verified_allow':0,'reputation_state':'observational'},
      'o': {'observations':5,'trust_score_observed':100,'replay_clean':5,'verified_allow':5,'reputation_state':'observational'},
      'l': {'observations':10,'trust_score_observed':80,'replay_clean':10,'verified_allow':8,'reputation_state':'stable'},
      't': {'observations':25,'trust_score_observed':95,'replay_clean':25,'verified_allow':25,'reputation_state':'stable'},
      'x': {'observations':25,'trust_score_observed':95,'replay_clean':24,'verified_allow':25,'reputation_state':'stable'},
    })
    p=r['profiles']
    assert p['u']['tier']=='UNKNOWN' and not p['u']['executable']
    assert p['o']['tier']=='OBSERVE' and not p['o']['executable']
    assert p['l']['tier']=='LIMITED' and p['l']['executable']
    assert p['t']['tier']=='TRUSTED' and p['t']['executable']
    assert p['x']['tier']=='OBSERVE' and not p['x']['executable']
    assert len(r['policy_hash'])==64
