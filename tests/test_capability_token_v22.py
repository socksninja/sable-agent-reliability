from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from capability_token_v22 import issue_signed, verify_signed, public_key_b64
from capability_gate_v22 import authorized_execute


def decision():
    return {"decision":"ALLOW","executable":True,"permission_tier":"LIMITED","trust_score_observed":82.0,"tool":"inventory.reserve","tool_class":"mutating"}

def subject():
    return {"agent_id":"agent-demo","model":"demo-model","provider":"demo-provider","runtime":"crewai","framework_version":"1.15.20","task_id":"SABLE-T1","task_semantic_key":"inventory:reserve","policy_hash":"policy-hash","reputation_hash":"rep-hash","credential_hash":"cred-hash"}

def expected(): return {**subject(),"tool":"inventory.reserve"}

def test_signed_token_roundtrip():
    private=Ed25519PrivateKey.generate(); token=issue_signed(decision(),subject(),private,issued_at=1000,ttl_seconds=60,nonce="n1")
    ok,reasons=verify_signed(token,private.public_key(),now=1020,expected=expected())
    assert ok and reasons==[] and token['signing']['alg']=='Ed25519'
    assert public_key_b64(private.public_key())

def test_signature_tamper_is_denied():
    private=Ed25519PrivateKey.generate(); token=issue_signed(decision(),subject(),private,issued_at=1000,ttl_seconds=60,nonce="n2")
    token['authorization']['tool']='order.ship'
    ok,reasons=verify_signed(token,private.public_key(),now=1020,expected=expected())
    assert not ok and 'token_integrity_mismatch' in reasons and 'signature_invalid' in reasons

def test_context_mismatch_and_replay_are_denied():
    private=Ed25519PrivateKey.generate(); token=issue_signed(decision(),subject(),private,issued_at=1000,ttl_seconds=60,nonce="n3")
    ok,reasons=verify_signed(token,private.public_key(),now=1020,expected={**expected(),"runtime":"langgraph"})
    assert not ok and 'binding_mismatch:runtime' in reasons
    ok,reasons=verify_signed(token,private.public_key(),now=1020,expected=expected(),used_nonces={'n3'})
    assert not ok and 'token_replay' in reasons

def test_hard_gate_blocks_tool_and_preserves_state():
    from sandbox import SABLEEnvironment
    task={"task_id":"SABLE-T1","initial_state":{"inventory":{"SKU-A":{"stock":10,"reserved":1}}},"allowed_tools":["inventory.reserve"],"checks":[]}
    env=SABLEEnvironment(task); private=Ed25519PrivateKey.generate(); used=set()
    denied=authorized_execute(env,'inventory.reserve',{'sku':'SKU-A','qty':3},token={},public_key=private.public_key(),expected=expected(),now=1020,used_nonces=used)
    assert not denied.ok and env.state['inventory']['SKU-A']['reserved']==1 and len(env.observations)==1
    token=issue_signed(decision(),subject(),private,issued_at=1000,ttl_seconds=60,nonce='n4')
    allowed=authorized_execute(env,'inventory.reserve',{'sku':'SKU-A','qty':3},token=token,public_key=private.public_key(),expected=expected(),now=1020,used_nonces=used)
    assert allowed.ok and env.state['inventory']['SKU-A']['reserved']==4
