# SABLE — External Validation Packet

## Question under validation

Should streaming-agent reliability be evaluated beyond terminal request-level pass/fail?

SABLE currently has two dynamic reproductions against the same pinned AgentScope-Java revision (`39cd304a7dc400eb3fb2a7daca750162e79bec05`):

1. **Silent completion / zero emission** — a stream can complete without content-bearing responses or an error signal, so error-driven retry/fallback is not triggered.
2. **Mid-stream retry replay** — after chunks have already been delivered, a retryable error can re-subscribe upstream and replay those chunks.

## Primary evidence

- SABLE-001: https://github.com/socksninja/sable-agent-reliability/issues/45
- SABLE-002: https://github.com/socksninja/sable-agent-reliability/issues/46
- Combined finding: https://github.com/socksninja/sable-agent-reliability/blob/main/STREAMING_RELIABILITY_FINDING_V01.md

## What we are asking external reviewers to do

We are **not** asking for endorsement.

A useful response can be any of the following:

- a counterexample showing these should be modeled differently;
- a better taxonomy or metric;
- evidence from another runtime/provider;
- evidence from a real workload;
- a reference to prior work that already captures these semantics.

## Current evidence boundary

The claims above are limited to dynamic code-level reproduction in the pinned implementation under synthetic streams. SABLE does **not** currently claim production prevalence, provider-wide prevalence, severity distribution, or business impact from these two cases alone.

## Public validation thread

https://github.com/socksninja/sable-agent-reliability/issues/47

The goal is to falsify the framing before expanding the benchmark.
