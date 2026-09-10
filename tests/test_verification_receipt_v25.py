from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from verification_receipt_v25 import sign_receipt, verify_signed_receipt, public_key_b64


def receipt():
    return {
        "schema_version": "sable.verification_receipt.v2.4",
        "execution": {"task_id":"T1","runtime":"CrewAI","framework_version":"1.15.20","model":"m","provider":"local","runtime_trace_id":"trace-1"},
        "authorization": {"permission":"ALLOW","verified":True,"reasons":[],"capability_token_hash":"cap-hash"},
        "evidence": {"evidence_hash":"ev-hash","task_success":True,"replay_match":True,"before_state_hash":"before","after_state_hash":"after","termination":"final","tool_calls":1,"tools":["inventory.reserve"]},
        "receipt_hash":"placeholder",
    }


def test_sign_and_verify():
    p=Ed25519PrivateKey.generate(); signed=sign_receipt(receipt(),p)
    ok,reasons=verify_signed_receipt(signed,p.public_key())
    assert ok and reasons==[]
    assert signed["signing"]["alg"]=="Ed25519"
    assert public_key_b64(p.public_key()) == signed["public_key"]


def test_tamper_is_denied():
    p=Ed25519PrivateKey.generate(); signed=sign_receipt(receipt(),p)
    signed["evidence"]["after_state_hash"]="tampered"
    ok,reasons=verify_signed_receipt(signed,p.public_key())
    assert not ok and "receipt_integrity_mismatch" in reasons and "signature_invalid" in reasons


def test_public_key_swap_is_denied():
    p=Ed25519PrivateKey.generate(); other=Ed25519PrivateKey.generate(); signed=sign_receipt(receipt(),p)
    signed["public_key"]=public_key_b64(other.public_key())
    ok,reasons=verify_signed_receipt(signed,p.public_key())
    assert not ok and "public_key_mismatch" in reasons


def test_unsigned_is_denied():
    p=Ed25519PrivateKey.generate(); r=receipt(); r["receipt_hash"]="bad"; r["signature"]="bad"; r["signing"]={"alg":"Ed25519","key_id":"x"}; r["public_key"]=public_key_b64(p.public_key())
    ok,reasons=verify_signed_receipt(r,p.public_key())
    assert not ok and "signature_invalid" in reasons
