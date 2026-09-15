from integrations.otel_conformance.evidence_receipt import RECEIPT_SCHEMA, validate_receipt


def valid_receipt():
    return {
        "schema": RECEIPT_SCHEMA,
        "repository": "socksninja/sable-agent-reliability",
        "commit_sha": "abc123",
        "github_actions_run_id": "34971496689",
        "trace_id": "fad2a88e996225507b7a21d61962fe94",
        "trace_url": "https://cloud.langfuse.com/project/example/traces/fad2a88e996225507b7a21d61962fe94",
        "task_success": True,
        "external_effect": {
            "system": "GitHub Issues",
            "operation": "create_issue_comment",
            "effect_id": "5681069014",
            "effect_url": "https://github.com/socksninja/sable-agent-reliability/issues/63#issuecomment-5681069014",
            "final_state_sha256": "042b4ff60584f4c263c3bd644ae14c2ba63edd528e9ac0b9845c04c5a6791ad0",
        },
    }


def test_valid_receipt_passes():
    result = validate_receipt(valid_receipt())
    assert result.valid is True
    assert result.errors == ()


def test_receipt_does_not_pass_without_external_effect_hash():
    receipt = valid_receipt()
    del receipt["external_effect"]["final_state_sha256"]
    result = validate_receipt(receipt)
    assert result.valid is False
    assert "external_effect.final_state_sha256 is required" in result.errors


def test_receipt_cannot_override_conformance_semantics():
    receipt = valid_receipt()
    receipt["task_success"] = False
    result = validate_receipt(receipt)
    assert result.valid is False
    assert "task_success must be true" in result.errors
