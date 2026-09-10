from capability_token_v21 import issue, verify


def decision():
    return {
        "decision": "ALLOW", "executable": True,
        "permission_tier": "LIMITED", "trust_score_observed": 82.0,
        "tool": "inventory.reserve", "tool_class": "mutating",
    }


def subject():
    return {
        "agent_id": "agent-demo", "model": "demo-model", "provider": "demo-provider",
        "runtime": "crewai", "framework_version": "1.15.20", "task_id": "SABLE-T1",
        "task_semantic_key": "inventory:reserve", "policy_hash": "policy-hash",
        "reputation_hash": "rep-hash", "credential_hash": "cred-hash",
    }


def expected_subject():
    s = subject()
    return {"tool": "inventory.reserve", **s}


def test_issue_and_verify():
    token = issue(decision(), subject(), issued_at=1000, ttl_seconds=60, nonce="n1")
    ok, reasons = verify(token, now=1020, expected=expected_subject())
    assert ok and reasons == []


def test_expiry_and_replay():
    token = issue(decision(), subject(), issued_at=1000, ttl_seconds=60, nonce="n1")
    ok, reasons = verify(token, now=1060, expected={"tool": "inventory.reserve"})
    assert not ok and "token_expired" in reasons
    ok, reasons = verify(token, now=1020, expected={"tool": "inventory.reserve"}, used_nonces={"n1"})
    assert not ok and "token_replay" in reasons


def test_subject_binding_mismatch():
    token = issue(decision(), subject(), issued_at=1000, ttl_seconds=60, nonce="n2")
    ok, reasons = verify(token, now=1020, expected={"tool": "inventory.reserve", "runtime": "langgraph"})
    assert not ok and "binding_mismatch:runtime" in reasons


def test_tool_binding_mismatch():
    token = issue(decision(), subject(), issued_at=1000, ttl_seconds=60, nonce="n3")
    ok, reasons = verify(token, now=1020, expected={"tool": "inventory.ship"})
    assert not ok and "binding_mismatch:tool" in reasons


def test_deny_cannot_issue():
    bad = {**decision(), "decision": "DENY", "executable": False}
    try:
        issue(bad, subject(), issued_at=1000, ttl_seconds=60, nonce="n4")
        assert False
    except ValueError as exc:
        assert str(exc) == "capability_token_requires_gateway_allow"
