# Reverse Demo: Microsoft Agent Framework #8292

> Public reverse-demo record. This is derived from the issue's deterministic reproduction and published triage notes. It is not an independent rerun.

## Target failure

Issue #8292 reports that Functional Workflow checkpoint replay can associate a cached result with the wrong concurrent logical branch when the same @step is reached in a different order during replay.

The reported example has:
- initial output: result:A / result:B
- replayed output: result:B / result:A
- no exception

## Observable claim to test

The bounded question is:

> After checkpoint replay, does each logical branch receive the result for its own input, and can an independent observer verify that branch/result binding?

This is intentionally narrower than evaluating the proposed fix.

## Reverse-demo procedure

1. Pin agent-framework-core 1.18.0 and the published reproduction commit.
2. Run the deterministic parallel workflow.
3. Capture the initial branch/input/result mapping.
4. Restore from the produced checkpoint.
5. Capture the replayed branch/input/result mapping.
6. Preserve both outputs and hash the evidence bundle.
7. Recompute the expected mapping from the branch inputs independently of the runtime's success/completion signal.
8. Classify:
   - VERIFIED
   - NOT VERIFIED
   - EVIDENCE GAP

## Evidence chain

```
issue #8292 reproduction
  -> pinned runtime/version
  -> concurrent step execution
  -> checkpoint restore
  -> replay mapping
  -> independent branch/result reconstruction
  -> digest
  -> bounded verdict
```

No claim is made about the best framework fix. The purpose is to independently establish the observed replay/evidence boundary.

## Fixed-scope verification offer

US$250 flat.

Deliverables:
- one bounded checkpoint/replay experiment;
- one machine-readable evidence record;
- independent branch/result mapping check;
- one-page findings;
- explicit VERIFIED / NOT VERIFIED / EVIDENCE GAP boundary.

No framework patch, production credentials, or SABLE adoption is required.
