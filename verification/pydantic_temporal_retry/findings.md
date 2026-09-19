# Bounty #90 — Independent Verification

## Scope

Target: `pydantic/pydantic-ai#5536`.

Question: after an activity commits a harmless external effect but its result
is not observed before the activity timeout, can normal Temporal retry execute
the same logical effect again?

## Method

- Pydantic AI `2.46.0` with `TemporalDurability`.
- Temporal Python SDK `1.33.0` and an isolated ephemeral Temporal test server.
- One unique logical action ID: `pydantic-temporal-de3dc4bd-5de5-40dd-aee6-67dbaddaf8b1`.
- The tool appends one JSON object to a local JSONL file and flushes/fsyncs it.
- The activity then sleeps beyond a one-second start-to-close timeout.
- Retry policy is bounded to two attempts.
- `fresh_read.py` reads the effect file in a separate process after workflow completion.

## Observations

- Workflow status: `failed_after_retry` after the bounded retry policy was exhausted.
- The same logical action ID appears twice in the external JSONL state.
- Fresh-process effect count: `2`.
- The two effect records were produced by the same worker process across two activity attempts.
- Effect file SHA-256: `25cb92db97f3f4be9734072f9e8df29294bb5996f0299091053f48a06081bcd0`.

## Verdict

**VERIFIED** — a side effect committed before completion was observed can be
repeated by normal Temporal activity retry when the operation has no
idempotency guard. This is a bounded reliability result, not a claim about
production credentials or a production deployment.

## Evidence boundary

This experiment demonstrates duplicate external effects across an activity
timeout/retry boundary. It does not claim a Pydantic AI framework patch, a
production exploit, or a fix for the upstream issue.
