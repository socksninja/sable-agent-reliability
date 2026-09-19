# Reverse Demo: LangGraph #8834

> Public reverse-demo record. This is an evidence-design artifact derived from the maintainer's published reproduction and source analysis. It is **not** an independent rerun.

## Target failure

LangGraph #8834 reports that when a conditional-router function raises after a node has produced a state update, a later resume can return normally with no pending work while the downstream node never runs.

## Observable claim to test

We are not testing whether the initial router exception exists; the issue already provides that reproduction.

The narrow independent question is:

> After the router failure and resume, can an external observer distinguish a genuinely completed downstream transition from a runtime response that merely returned normally?

## Control boundary

The issue's published controls report:

- node failure: resume retries the node and reaches the sink;
- router failure: resume returns the intermediate state;
- router call count remains 1;
- sink call count remains 0;
- no pending tasks remain.

Those observations define the exact boundary for an independent check.

## Reverse-demo procedure

1. Pin the reported LangGraph/package versions and the issue's reproduction commit.
2. Run the router-failure case from a fresh process.
3. Record runtime return value, router invocation count, sink invocation count, and checkpoint/pending-task state.
4. Independently observe a durable external effect that only the sink can create.
5. Read that effect from a fresh observer process and hash the retained bytes.
6. Classify only the bounded claim:
   - VERIFIED
   - NOT VERIFIED
   - EVIDENCE GAP

## Evidence chain

```
issue #8834 reproduction
  -> pinned runtime/version
  -> controlled router failure
  -> resume
  -> runtime-return observation
  -> fresh external readback
  -> digest
  -> bounded verdict
```

The important separation is between the runtime's returned state and the independently observed downstream effect.

## Fixed-scope verification offer

US$250 flat.

Deliverables:
- one bounded execution experiment;
- one controlled failure/recovery boundary;
- fresh-process external readback;
- machine-readable evidence record;
- one-page findings report;
- explicit VERIFIED / NOT VERIFIED / EVIDENCE GAP boundary.

No framework patch, production credentials, or SABLE adoption is required for the pilot.
