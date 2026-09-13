# SABLE Finding V01 — Streaming reliability failures are not one failure class

## Status
**Two dynamic SABLE reproductions are now verified against a pinned AgentScope-Java revision.**

This record combines the two cases without claiming production prevalence or cross-runtime generality.

## Finding

Streaming reliability can fail in at least two materially different ways at the stream/retry boundary:

1. **Silent completion / zero emission** — the stream completes without content-bearing responses, producing no error signal and therefore bypassing error-driven retry/fallback.
2. **Duplicate delivery after mid-stream retry** — a retryable error after chunks have already been delivered causes the upstream stream to be re-subscribed, replaying chunks that the consumer has already observed.

These are different failure modes, but both expose a limitation of treating streaming reliability as a simple request-level success/failure outcome.

## Evidence A — SABLE-001

Failure class: `silent_success_zero_chunk`

- Runtime: AgentScope-Java
- Pinned revision: `39cd304a7dc400eb3fb2a7daca750162e79bec05`
- Dynamic CI reproduction: verified
- Boundary: `ModelUtils.applyTimeoutAndRetry`
- Observed behavior: zero-emission stream completes normally; no error signal is produced, so `retryWhen` does not resubscribe.
- External anchor: AgentScope-Java issue #2962.

SABLE issue: https://github.com/socksninja/sable-agent-reliability/issues/45

## Evidence B — SABLE-002

Failure class: `mid_stream_retry_duplicate_delivery`

- Runtime: AgentScope-Java
- Pinned revision: `39cd304a7dc400eb3fb2a7daca750162e79bec05`
- Dynamic CI reproduction: verified
- Workflow run: `34762494234`
- Boundary: `ModelUtils.applyTimeoutAndRetry`
- Observed behavior:
  - `subscriptions=3`
  - `delivered=[Hello, world, Hello, world, Hello, world]`
- Receipt artifact: `sable-002-agentscope-stream-retry-receipt`
- Artifact SHA-256: `7bf64ac6e549ddacebf8de01e1ce0f63c078fec1486bbd347bd70b6d0b3aa5e4`
- External anchor: AgentScope-Java issue #2478.

SABLE issue: https://github.com/socksninja/sable-agent-reliability/issues/46

## Why this matters

A request-level pass rate can collapse both cases into a single outcome. The failure mechanics are different:

- zero emission can silently terminate without entering error-driven recovery;
- mid-stream retry can recover the transport while corrupting delivery semantics through replay.

For reliability engineering, the observable trajectory and delivery semantics therefore matter in addition to the terminal request outcome.

## Evidence boundary

This record establishes two dynamically reproduced behaviors in the pinned AgentScope-Java implementation under synthetic streams. It does **not** establish:

- production frequency;
- provider prevalence;
- severity distribution in deployed systems;
- cross-runtime prevalence;
- business impact.

Those claims require additional external evidence.

## SABLE's role

SABLE is using these cases as reliability records: external runtime problem → pinned implementation → deterministic reproduction → inspectable execution evidence.

The objective is to make concrete failure behavior easier for runtime, agent, and evaluation engineers to inspect, compare, and reproduce.
