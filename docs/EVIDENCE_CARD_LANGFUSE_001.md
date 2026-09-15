# SABLE Evidence Card — LANGFUSE-001

## Claim
A real agent-style execution can be recorded by an observability stack while a separately readable external world-state proves that the claimed tool effect actually occurred.

## Verified execution
- Runtime: Langfuse Python SDK v4 observation runtime
- Telemetry: OpenTelemetry-backed Langfuse SDK
- GitHub Actions run: https://github.com/socksninja/sable-agent-reliability/actions/runs/34971496689
- Trace ID: `fad2a88e996225507b7a21d61962fe94`
- External system: GitHub Issues
- Effect: https://github.com/socksninja/sable-agent-reliability/issues/63#issuecomment-5681069014
- Effect ID: `5681069014`
- Final-state SHA-256: `042b4ff60584f4c263c3bd644ae14c2ba63edd528e9ac0b9845c04c5a6791ad0`
- Receipt schema: `sable.reliability_record.v0.9`
- Receipt status: `EVIDENCE_REACHABLE`

## What is independently verifiable
1. The GitHub comment exists outside Langfuse.
2. Its body and authoritative identifiers can be reread independently.
3. The receipt binds the effect ID and final-state hash to the execution provenance.
4. The conformance result is not delegated to SABLE.

## Boundary being tested
`runtime execution -> telemetry -> external effect -> independent reread -> evidence receipt`

## Why it matters
Observability answers what a system reported. The receipt adds a separately verifiable statement about what remained true in the external world after the run.

## Smallest next experiment
Repeat the same harmless effect with a second agent runtime and a second observability stack, then compare whether both can produce receipts that bind to the same evidence contract without exposing proprietary data.

## Design-partner CTA
Bring one harmless production-like agent/tool action that your team currently trusts from telemetry alone. SABLE will attempt to produce a compact receipt that an outside verifier can check without access to private traces or credentials.
