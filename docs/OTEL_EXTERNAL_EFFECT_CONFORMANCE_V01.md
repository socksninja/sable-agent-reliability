# SABLE ↔ OTel GenAI External-Effect Conformance Fixture v0.1

## Purpose

A minimal, framework-agnostic fixture for testing whether durable agent execution evidence can be bound to a real external state transition without changing the runtime's own PASS/FAIL semantics.

This is an evidence-binding experiment, not a proposal to make SABLE part of the OTel conformance core.

## Minimal scenario

1. Run one durable / multi-step agent execution.
2. Assign one stable logical execution identity (`gen_ai.agent.execution.id` or an equivalent runtime identity).
3. Declare one mutating external effect before the effect occurs.
4. Perform the effect against a harmless test system.
5. Independently reread the authoritative external state after execution.
6. Compute a final-state SHA-256 over the independently observed state.
7. Emit a compact receipt containing:
   - execution identity
   - runtime / provenance identity
   - external-system reference
   - external-effect reference
   - final-state hash
   - underlying execution success marker

## Evidence distinction

The fixture deliberately distinguishes:

`execution happened`

from

`evidence written`

from

`evidence visible`

from

`evidence independently readable`

from

`external state verified`

An observability backend may report an execution successfully while an outside verifier still needs to establish whether the corresponding external state is actually readable and unchanged.

## Effect classification

The effect is explicitly classified before execution as either:

- `READ_ONLY`
- `MUTATING`

For a `MUTATING` effect, the fixture records the authoritative external reference and final state. Compensation / rollback, when applicable, should reference the original effect rather than relying on parent-child trace structure surviving retries or replay.

## Conformance boundary

The existing runtime remains authoritative for its own conformance PASS/FAIL result.

This fixture only asks whether the evidence around that execution is independently bindable and reproducible.

## Smallest concrete implementation

A GitHub Issue comment is sufficient as the harmless external system for the first fixture because another system can reread the resulting state without access to the observability backend.

Example evidence chain:

`durable agent execution -> trace -> external comment -> independent reread -> SHA-256 -> receipt`

## Success condition

An independent verifier can answer all of the following from the receipt plus public evidence:

- Which logical execution produced the effect?
- Which external system was mutated?
- What exact effect was observed?
- Can the final state be reread independently?
- Does the state hash match the receipt?
- Did the underlying runtime report successful completion?

## Non-goals

This fixture does not:

- redefine OTel semantic conventions;
- declare a platform consistency SLA;
- treat SABLE as the authority for runtime PASS/FAIL;
- require private prompts, model outputs, credentials, or customer data;
- assume parent-child trace relationships survive retries or replay.

## Current SABLE evidence

- First real Langfuse evidence receipt: `sable.reliability_record.v0.9`
- Real LangGraph execution: `34979126994`
- Real CrewAI execution: `34979126995`
- LangSmith readback experiment: `34988328698` observed exact-run readback at the 2s observation point after accepted write/update.

The LangSmith observation is treated only as a measurement of evidence visibility, not as evidence of a platform defect or SLA.
