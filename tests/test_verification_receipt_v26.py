from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from verification_receipt_v24 import build_receipt
from verification_receipt_v26 import sign_receipt, verify_self_contained, load_public_key


def receipt():
    evidence={
        'task': {'task_id':'SABLE-LIVE-T1'},
        'agent': {'framework':'CrewAI','framework_version':'1.15.20','model':'deterministic-crewai-stub','provider_base_url':'local','runtime_trace_id':'trace-live'},
        'state': {'initial_state_hash':'before','final_state_hash':'after'},
        'outcome': {'task_success':True},
        'replay': {'replay_match':True},
        'execution': {'termination':'final','tool_calls':1,'tools':['inventory.reserve']},
        'evidence_hash':'evidence-live',
    }
    permission={'decision':'ALLOW','verified':True,'reasons':[]}
    return build_receipt(evidence, permission, capability_hash='cap-live')


def test_self_contained_roundtrip():
    p=Ed25519PrivateKey.generate(); signed=sign_receipt(receipt(),p)
    ok,reasons=verify_self_contained(signed)
    assert ok and reasons==[]
    assert load_public_key(signed['public_key']).public_bytes_raw()


def test_tamper_any_field_is_denied():
    p=Ed25519PrivateKey.generate(); signed=sign_receipt(receipt(),p)
    signed['evidence']['after_state_hash']='tampered'
    ok,reasons=verify_self_contained(signed)
    assert not ok and 'receipt_integrity_mismatch' in reasons and 'signature_invalid' in reasons


def test_key_swap_is_denied():
    p=Ed25519PrivateKey.generate(); q=Ed25519PrivateKey.generate(); signed=sign_receipt(receipt(),p)
    signed['public_key']=signed['public_key']
    signed['signature']=__import__('base64').b64encode(q.sign(__import__('json').dumps({k:signed[k] for k in signed if k!='signature'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())).decode()
    signed['public_key']=__import__('base64').b64encode(q.public_key().public_bytes(__import__('cryptography').hazmat.primitives.serialization.Encoding.Raw,__import__('cryptography').hazmat.primitives.serialization.PublicFormat.Raw)).decode()
    ok,reasons=verify_self_contained(signed)
    assert not ok
