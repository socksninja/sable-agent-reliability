from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_credential_is_hash_linked_and_portable(tmp_path: Path) -> None:
    src = tmp_path / 'reputation.json'
    out = tmp_path / 'credential.json'
    src.write_text(json.dumps({
        'schema_version': 'sable.reputation.v1.7',
        'observation_count': 10,
        'reputation_hash': 'a' * 64,
        'profiles': {
            'model|provider|runtime': {
                'reputation_state': 'stable',
                'permission_eligibility': 'eligible',
                'trust_score_observed': 93.5,
                'observations': 10,
                'verified_allow': 9,
                'verified_deny': 1,
                'replay_clean': 10,
                'infrastructure_events': 0,
                'failure_labels': {}
            }
        }
    }), encoding='utf-8')
    subprocess.run([sys.executable, str(ROOT / 'reputation_credential_v18.py'), '--input', str(src), '--out', str(out)], check=True)
    r = json.loads(out.read_text(encoding='utf-8'))
    assert r['schema_version'] == 'sable.reputation_credential.v1.8'
    assert r['source_reputation_hash'] == 'a' * 64
    assert r['observation_count'] == 10
    assert len(r['credentials']) == 1
    assert r['credentials'][0]['trust_score_observed'] == 93.5
    assert len(r['credential_hash']) == 64
    assert r['verification_contract']['portable_without_prediction_claim'] is True
