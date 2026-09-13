# SABLE Failure Corpus v0.1

## Purpose

Capture **real agent reliability failures** as reusable evidence, not anecdotes.

The corpus is a strategic asset only when each record preserves enough provenance and environment truth for another party to inspect or reproduce the claim.

## Record contract

Each failure record should contain:

| Field | Requirement |
|---|---|
| `failure_id` | Stable identifier, e.g. `SABLE-F-0001` |
| `observed_at` | UTC timestamp |
| `runtime` | Agent/runtime/framework name and version |
| `source_type` | `external_execution`, `public_incident`, `internal_reproduction`, or `synthetic` |
| `provenance` | URL, issue/PR, trace ID, or other attributable source |
| `task` | Concrete user/agent objective |
| `requested_contract` | What the system was asked to do |
| `actions` | Relevant tool calls / execution sequence |
| `expected_state` | Machine-checkable terminal expectation |
| `observed_state` | Machine-checkable result |
| `claimed_status` | What the agent/runtime reported |
| `failure_class` | Normalized SABLE taxonomy class |
| `silent` | Whether the failure could pass as success to a caller |
| `recoverable` | Whether the runtime recovered correctly |
| `evidence` | Artifact(s), hash(es), logs, or replay output |
| `verification_status` | `unverified`, `reproduced`, `independently_verified`, `admitted` |
| `notes` | Limits, ambiguity, redactions |

## Failure taxonomy v0.1

- `wrong_state`
- `silent_failure`
- `false_success`
- `unauthorized_action`
- `tool_failure`
- `partial_completion`
- `idempotency_failure`
- `state_drift`
- `terminal_truth_mismatch`
- `completion_delivery_mismatch`
- `detached_liveness_mismatch`
- `stale_evidence`
- `provider_failure`

## Evidence levels

**E0 — Signal:** public report, comment, screenshot, or unverified claim.

**E1 — Attributable execution:** source runtime and execution are attributable, but machine-verifiable terminal evidence is incomplete.

**E2 — Reproduced:** SABLE independently reproduces the failure with an inspectable oracle.

**E3 — Independently verified:** an external maintainer/actor can inspect the execution and evidence and confirms the result.

**E4 — Repeated external use:** the same or another independent runtime uses the SABLE evidence path again and obtains inspectable results.

Only E2+ belongs in benchmark/evidence claims. E0/E1 may guide targeting but must never be presented as adoption.

## Example skeleton

```json
{
  "failure_id": "SABLE-F-0001",
  "observed_at": "2026-09-13T00:00:00Z",
  "runtime": {
    "name": "example-runtime",
    "version": "x.y.z"
  },
  "source_type": "external_execution",
  "provenance": {
    "url": "",
    "trace_id": ""
  },
  "task": "",
  "requested_contract": "",
  "actions": [],
  "expected_state": {},
  "observed_state": {},
  "claimed_status": "success",
  "failure_class": "terminal_truth_mismatch",
  "silent": true,
  "recoverable": false,
  "evidence": [],
  "verification_status": "unverified",
  "notes": ""
}
```

## Non-negotiable rule

A public incident can tell us **what to investigate**. It cannot by itself tell us **what SABLE proved**.
