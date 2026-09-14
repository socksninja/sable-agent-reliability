# External Case — Effect Convergence / Replay Classification

## Status

**E0/E1 external case material only. Not a SABLE reproduction or adoption claim.**

This case is extracted from a public Chase Sets reliability/repair lane and normalized into a runtime-agnostic SABLE failure pattern.

## Source provenance

- Repository: `chase-sets/chase-sets`
- Issue context: #6732
- PR: #7836 — `Payments: add SetupIntent cancellation convergence (#6732)`
- Observed repair head: `e6fc1adb0cc2e1e159d3fb656a1efb73f9613f1f`
- Base: `6107022715ee9460b6e1fc460d5a5704bc7fd090`
- Public cadence/source comment: `https://github.com/chase-sets/chase-sets/issues/4388#issuecomment-5671455865`
- PR public record: `https://github.com/chase-sets/chase-sets/pull/7836`

At the observed point the PR remained **draft/open/unmerged** and explicitly required hosted-green validation plus a separately guarded provider-authority window. Therefore this source is evidence of a concrete reliability-control pattern, not evidence that the repair was production-adopted.

## Runtime-agnostic failure pattern

### Pattern ID

`SABLE-FP-EFFECT-CONVERGENCE-001`

### Name

**Concurrent destructive/reversal requests converge incorrectly when completion order is mistaken for effect truth.**

### Core shape

```text
logical operation
  -> concurrent/repeated attempts
  -> external side effect may partially commit
  -> one or more requests return non-2xx / ambiguous outcome
  -> runtime must reconcile against observable external state
  -> terminal classification must derive from effect state, not call completion order
```

The key reliability boundary is:

**request outcome != effect outcome**

and:

**completion order != authority over the final resource state**

## Concrete external signal

The Chase Sets repair defines a classifier for two concurrent/repeated cancellation responses. The control cases include:

- `[200,200]` → successful replay/converged cancellation
- `[409,200]` → `rejected-then-reconciled`
- `[200,409]` → `rejected-then-reconciled`
- 2xx boundary cases
- reversed call-array order
- unchanged raw transcripts
- multiple reconciliation defects in both mixed orders

The important invariant is that a non-2xx response does **not** automatically mean the desired state was not reached, while two 2xx responses do **not** by themselves justify inventing a different terminal class.

The repaired classifier explicitly requires successful post-write reconciliation after the rejected call and avoids inferring the winner from completion order.

## SABLE failure taxonomy

Primary:

- `idempotency_failure`
- `terminal_truth_mismatch`
- `state_drift`
- `completion_delivery_mismatch`

Secondary control-plane dimensions:

- `effect_convergence`
- `reconciliation_required`
- `completion_order_not_authoritative`
- `provider_authority_required`

## Minimal reproducer schema

A cross-runtime SABLE harness can model the pattern without using Stripe or Chase-specific APIs:

```json
{
  "logical_action_id": "cancel-001",
  "initial_state": {"resource_state": "active"},
  "concurrent_calls": [
    {"attempt": 1, "response": {"status": 409}},
    {"attempt": 2, "response": {"status": 200}}
  ],
  "external_state_after_calls": {"resource_state": "canceled"},
  "required_reconciliation": true,
  "completion_order_authoritative": false,
  "expected_terminal": "rejected-then-reconciled"
}
```

A valid implementation must derive the terminal result from an environment-observed state transition or authoritative reconciliation oracle.

## Cross-runtime prediction

This pattern should be portable across:

- payment / transaction APIs;
- email/message send/cancel flows;
- job cancellation APIs;
- cloud resource create/delete operations;
- browser agents performing irreversible actions;
- file/object mutation with retry wrappers;
- agent tool calls where the provider commits an effect before the runtime records the result.

The implementation-specific HTTP status code is incidental. The reliability problem is the **effect ledger vs. execution ledger divergence**.

## Falsifiers / forcing tests

A runtime should fail the conformance test if any of the following occur:

1. It classifies `409 + 200` differently from `200 + 409` solely because call order differs.
2. It reports failure without checking whether the external resource already reached the requested terminal state.
3. It retries an ambiguous external effect without an idempotency key or authoritative reconciliation path.
4. It treats provider/runtime completion metadata as stronger evidence than the external state oracle.
5. It cannot distinguish:
   - no effect committed;
   - effect committed but result registration failed;
   - effect committed and desired state reached;
   - effect state unknown because the reconciliation oracle is unavailable.

## Evidence boundary

This case is intentionally **not** promoted to an SABLE benchmark claim merely because the source is public.

Promotion requires SABLE-controlled reproduction or an independently inspectable external execution record containing:

`request trace + external state readback + exact response sequence + terminal classification + immutable receipt`

## Strategic value

This is a useful third-party reality pattern because it exposes a class of failures that ordinary "did the API call return 200?" metrics cannot measure.

The acquisition-grade SABLE question is therefore not:

> "Which runtime handles cancellation correctly?"

It is:

> **"Can an agent/runtime prove that the external effect converged to the requested state, even when request outcomes are conflicting or ambiguous?"**

That is directly testable across runtimes and providers.
