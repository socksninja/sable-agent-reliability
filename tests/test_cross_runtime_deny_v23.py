from cross_runtime_deny_v23 import exercise


def test_langgraph_deny_allow_replay():
    r = exercise("langgraph")
    assert r["deny_without_token"]["ok"] is False
    assert r["deny_without_token"]["state_hash_unchanged"] is True
    assert r["allow_with_signed_token"]["ok"] is True
    assert r["replay_denied"]["ok"] is False
    assert r["reserved"] == 4


def test_crewai_deny_allow_replay():
    r = exercise("crewai")
    assert r["deny_without_token"]["ok"] is False
    assert r["deny_without_token"]["state_hash_unchanged"] is True
    assert r["allow_with_signed_token"]["ok"] is True
    assert r["replay_denied"]["ok"] is False
    assert r["reserved"] == 4
