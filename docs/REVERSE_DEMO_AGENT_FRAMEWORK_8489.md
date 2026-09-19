# Reverse Demo: Microsoft Agent Framework #8489

> Public reverse-demo record derived from the issue's reproducible routing failure and automated triage. It is not an independent rerun.

## Target failure

Issue #8489 reports that a `SwitchCaseEdgeGroup` predicate exception is swallowed and the workflow silently routes to the default branch instead of surfacing the error.

## Observable claim to test

The bounded independent question is:

> Does a predicate failure produce an externally observable wrong-branch execution rather than an explicit workflow failure?

The important evidence boundary is not the warning log. It is whether the wrong target actually receives the message.

## Reverse-demo procedure

1. Pin agent-framework-core 1.18.0 and the reported source boundary.
2. Use the issue's deterministic switch-case reproducer.
3. Give the high-priority branch and default branch distinct harmless externally readable effects.
4. Trigger the predicate exception.
5. Record runtime completion/error state and branch execution.
6. Read both effect records from a fresh process and hash the retained evidence.
7. Compare observed routing with the expected fail-fast contract.
8. Classify:
   - VERIFIED
   - NOT VERIFIED
   - EVIDENCE GAP

## Evidence chain

```
predicate error
  -> switch selection
  -> runtime result
  -> branch effect
  -> fresh external readback
  -> digest
  -> bounded verdict
```

A warning log alone is not treated as proof of failure because the workflow can continue and produce a wrong downstream state.

## Fixed-scope verification offer

US$250 flat.

Deliverables:
- one bounded routing experiment;
- independent wrong-branch observation;
- machine-readable evidence record;
- one-page findings;
- explicit VERIFIED / NOT VERIFIED / EVIDENCE GAP boundary.

No framework patch, production credentials, or SABLE adoption required.
