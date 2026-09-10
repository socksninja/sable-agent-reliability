from verification_receipt_v24 import build_receipt, verify_receipt


def evidence():
    return {
        "task_id":"SABLE-T1","runtime":"CrewAI","framework_version":"1.15.20",
        "model":"deterministic-crewai-stub","provider":"local",
        "runtime_trace_id":"crewai-test",
        "evidence_hash":"e"*64,
        "outcome":{"task_success":True},
        "replay":{"replay_match":True},
        "execution":{"initial_state_hash":"a"*64,"final_state_hash":"b"*64,"termination":"final","steps":[{"tool":"inventory.reserve"}]},
    }


def permission():
    return {"decision":"ALLOW","verified":True,"reasons":[]}


def test_roundtrip():
    r=build_receipt(evidence(),permission(),capability_hash="c"*64)
    ok,reasons=verify_receipt(r)
    assert ok and reasons==[] and r["receipt_hash"]


def test_tamper_is_denied():
    r=build_receipt(evidence(),permission())
    r["evidence"]["after_state_hash"]="x"*64
    ok,reasons=verify_receipt(r)
    assert not ok and "receipt_integrity_mismatch" in reasons


def test_bad_replay_is_denied():
    e=evidence(); e["replay"]["replay_match"]=False
    r=build_receipt(e,permission())
    ok,reasons=verify_receipt(r)
    assert not ok and "replay_mismatch" in reasons


def test_denied_permission_is_denied():
    r=build_receipt(evidence(),{"decision":"DENY","verified":False,"reasons":["token_replay"]})
    ok,reasons=verify_receipt(r)
    assert not ok and "permission_not_allow" in reasons
