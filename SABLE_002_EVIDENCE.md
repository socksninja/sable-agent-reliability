# SABLE-002 — Mid-stream retry duplicates already-emitted chunks

## Evidence status
**Dynamically reproduced in GitHub Actions.**

## Pinned runtime
- Runtime: AgentScope-Java
- Revision: `39cd304a7dc400eb3fb2a7daca750162e79bec05`
- SABLE workflow run: `34762494234`
- Artifact: `sable-002-agentscope-stream-retry-receipt`
- Artifact SHA-256: `7bf64ac6e549ddacebf8de01e1ce0f63c078fec1486bbd347bd70b6d0b3aa5e4`

## Reproduction
A synthetic provider-independent `Flux` emits two chunks (`Hello`, ` world`) and then a retryable `IOException`. The configured retry policy uses `maxAttempts=3`.

The injected regression test observes both subscription count and delivered payloads.

## Observed result
The CI run completed successfully and the machine-readable receipt records:

```text
subscriptions=3
delivered=[Hello, world, Hello, world, Hello, world]
```

This means already-emitted chunks were delivered again after each retry subscription.

## Failure class
`mid_stream_retry_duplicate_delivery`

## Boundary
`ModelUtils.applyTimeoutAndRetry`

## Evidence boundary
This establishes the behavior of the pinned AgentScope implementation under the stated synthetic stream. It does **not** establish production frequency, provider prevalence, or impact distribution.

The SABLE objective is to turn runtime reliability failures that are otherwise discussed as isolated implementation bugs into deterministic, externally inspectable evidence that can be compared across runtimes.

## Upstream anchor
See AgentScope-Java issue #2478 for the upstream report describing the same retry/re-subscription failure shape.
