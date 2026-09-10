# SABLE Agent Trace Submission Protocol v0.9

## Purpose

SABLE v0.9 defines the public interchange contract for submitting execution traces from an external agent, framework, or runtime into SABLE.

The protocol separates four things that must not be conflated:

1. **Agent claim** — what the agent says happened.
2. **Observed execution** — tool calls and results captured by the external collector.
3. **Environment outcome** — independently recorded state/check results.
4. **Provenance/integrity** — who produced the trace, when it was captured, and whether the submitted trace was modified.

SABLE does not treat a final success message as proof of task success.

## Transport

The canonical submission format is **UTF-8 JSONL**. Each line is one complete `sable.submission.v0.9` envelope.

A submission may contain one or many lines. Lines are independently hashable and independently ingestible.

Validate and normalize with:

```bash
python3 trace_submit_v09.py \
  --input submission.jsonl \
  --output sable_traces_v05.jsonl
```

The output is the existing SABLE v0.5 trace contract, augmented with a `submission` provenance block. This preserves compatibility with the existing evaluator, evidence packer, score generator, and leaderboard.

## Required envelope

```json
{
  "protocol_version": "sable.submission.v0.9",
  "submission_id": "unique-submission-id",
  "source": {
    "agent_name": "External Agent",
    "agent_version": "1.0.0",
    "framework": "agent-framework",
    "framework_version": "1.2.3",
    "adapter": "adapter-name"
  },
  "trace": { "...": "SABLE-compatible external trace" },
  "provenance": {
    "captured_at": "2026-09-10T00:00:00Z",
    "collector": "collector-name@version",
    "redaction_policy": "describe any redactions"
  },
  "integrity": {
    "source_trace_hash": "64-hex-sha256-of-trace",
    "hash_algorithm": "sha256",
    "canonicalization": "json-sort-keys-utf8"
  }
}
```

## Trace requirements

The `trace` object must contain the existing SABLE v0.5 minimum fields:

- `task_id`
- `goal`
- `agent`
- `steps`
- `claimed_status`
- `environment`
- `integrity`

Every step must preserve the execution boundary:

- `tool`
- `args`
- `observed_result`
- `before_state_hash`
- `after_state_hash`

`state_after` may be included where the collector can safely expose the resulting state.

## Integrity rule

`source_trace_hash` is computed from the exact JSON value stored in `trace`, using UTF-8 JSON with sorted keys and compact separators. Do not hash the outer submission envelope.

A verifier rejects a submission when the supplied hash does not equal the canonical hash of the embedded trace.

This is an integrity check, not a cryptographic proof of the original runtime. SABLE therefore keeps provenance metadata separate from evaluation claims.

## Security and privacy

Submitters must remove API keys, cookies, bearer tokens, passwords, payment data, private keys, and unrelated personal data before submission. The `redaction_policy` field must describe what was removed or transformed.

A redacted trace remains valid only when the redaction does not destroy the fields required for execution reconstruction and state/outcome verification.

## Scoring boundary

SABLE v0.9 does **not** redefine the reliability score. After ingestion, the trace enters the existing SABLE pipeline:

`external agent → v0.9 submission → v0.9 validation → v0.5 trace → evaluator → evidence → reliability score → leaderboard`

Provider outages and unavailable-model conditions remain separate from agent failures under the existing scoring convention.

## First third-party integration target

The first external integration should come from a real agent runtime rather than a hand-authored benchmark row. The integration package should contain:

1. the runtime-specific collector/adapter;
2. one captured raw trace with its original source identifier;
3. the v0.9 envelope containing the source trace hash;
4. the normalized SABLE trace;
5. a replay/evaluation result;
6. a short provenance note explaining runtime version and capture method.

The repository may include deterministic fixtures for protocol CI, but fixtures must never be presented as real third-party execution evidence.

## Acceptance criteria for a third-party submission

A trace is considered **ingested** when the v0.9 validator accepts it and produces a v0.5 trace.

A trace is considered **evaluated** when SABLE's deterministic evaluator produces an outcome from the normalized trace.

A trace is considered **externally evidenced** only when the runtime-specific source, capture provenance, and original trace identifier are retained.

These labels are intentionally distinct so SABLE's public results do not overclaim what a submission proves.
