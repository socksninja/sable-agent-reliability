# Reverse Demo: OpenClaw #136513

> Public reverse-demo record derived from the issue's published source audit and test-only reproduction. It is not an independent rerun.

## Target failure

OpenClaw #136513 reports that a duplicate subagent completion replay can receive a non-terminal `in_flight` response while the original completion is still pending, but the direct-delivery path can record that response as delivered before terminal evidence exists.

## Observable claim to test

The bounded independent question is:

> Can an in-flight completion be credited as delivered before a terminal result or visible delivery evidence exists?

This is narrower than judging the eventual fix.

## Reverse-demo procedure

1. Pin the reported OpenClaw source/revision.
2. Start one completion handoff and hold it pending.
3. Replay the same stable idempotency key with `expectFinal=true`.
4. Capture the exact replay response.
5. Verify whether delivery accounting changes before terminal evidence.
6. Settle the original completion with success and repeat with failure/abort.
7. Preserve the delivery ledger/test output and SHA-256 digest.
8. Classify only:
   - VERIFIED
   - NOT VERIFIED
   - EVIDENCE GAP

## Evidence chain

```
issue #136513
  -> pinned source
  -> pending completion
  -> duplicate replay
  -> in_flight response
  -> delivery-credit observation
  -> terminal result
  -> independent ledger/readback
  -> bounded verdict
```

The verifier should treat `in_flight` as non-terminal unless independently proven otherwise.

## Fixed-scope verification offer

US$250 flat.

Deliverables:
- one bounded reproduction;
- delivery-credit / terminal-evidence check;
- machine-readable evidence record;
- one-page findings;
- explicit VERIFIED / NOT VERIFIED / EVIDENCE GAP boundary.

No OpenClaw patch, production credentials, or SABLE adoption required.
