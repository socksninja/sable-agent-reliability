# Reverse Demo: Pydantic AI #5536

> Public reverse-demo record derived from the issue's published Temporal durable-execution analysis. It is not an independent rerun.

## Target failure

Pydantic AI #5536 discusses approval state crossing a Temporal durable-execution boundary as ordinary serialized state. The thread also identifies a separate reliability boundary: an approved, side-effecting activity can be retried by Temporal after a timeout or worker restart, potentially repeating the external effect unless the tool has an idempotency mechanism.

## Observable claim to test

The bounded independent question is:

> After an approval-gated side effect has executed but the activity result is not durably observed by the caller, can Temporal retry cause the same logical tool action to execute again?

This deliberately separates ordinary retry correctness from the broader approval-tampering threat model.

## Reverse-demo procedure

1. Pin the reported pydantic-ai Temporal integration/version boundary.
2. Use a harmless external effect with a unique logical action ID.
3. Approve the tool call.
4. Force the activity to time out or simulate worker loss after the effect commits but before the caller observes completion.
5. Allow normal Temporal retry behavior.
6. Read the external effect from a fresh process and count occurrences.
7. Preserve runtime metadata, effect records, and hashes.
8. Classify:
   - VERIFIED
   - NOT VERIFIED
   - EVIDENCE GAP

## Evidence chain

```
approval
  -> Temporal activity
  -> external effect
  -> missing/late completion observation
  -> normal retry
  -> fresh external readback
  -> effect count/digest
  -> bounded verdict
```

The verifier must derive the effect count from external state, not from the activity's success/failure label.

## Fixed-scope verification offer

US$250 flat.

Deliverables:
- one bounded durable-retry experiment;
- fresh external effect readback;
- machine-readable evidence record;
- one-page findings;
- explicit VERIFIED / NOT VERIFIED / EVIDENCE GAP boundary.

No production credentials, framework patch, or SABLE adoption required.
