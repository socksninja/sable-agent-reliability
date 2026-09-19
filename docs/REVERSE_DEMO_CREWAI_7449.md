# Reverse Demo: CrewAI #7449

> Public reverse-demo record. This is an evidence-design artifact derived from the issue's published reproduction. It is not an independent rerun.

## Target failure

CrewAI #7449 reports two retry layers around a tool call: the outer retry loop and an inner exception fallback. When the first invocation raises, the inner fallback invokes the same tool again inside the same outer attempt. With the reported configuration, the tool function can be invoked 6 times rather than the expected 3.

## Observable claim to test

The narrow external question is:

> Does one logical tool action produce more than one externally observable side effect under the reported retry boundary?

The important distinction is between **tool invocation count** and **external effect count**.

## Reverse-demo procedure

1. Pin crewAI 1.15.21 and the reported reproduction.
2. Replace the in-process list-only observation with one harmless externally readable effect carrying a unique logical action ID.
3. Trigger the same failing tool/retry path.
4. Observe runtime invocation count.
5. Read the external effect from a fresh process.
6. Count and hash the retained effect records.
7. Classify only the bounded claim:
   - VERIFIED
   - NOT VERIFIED
   - EVIDENCE GAP

## Evidence chain

```
issue #7449 reproduction
  -> pinned runtime/version
  -> retry/fallback execution
  -> runtime invocation observation
  -> fresh external effect readback
  -> digest
  -> bounded verdict
```

The independent observer must derive the effect count from the retained external state, not from CrewAI's retry counters.

## Fixed-scope verification offer

US$250 flat.

Deliverables:
- one bounded execution experiment;
- one controlled retry/failure boundary;
- fresh-process effect readback;
- machine-readable evidence record;
- one-page findings;
- explicit VERIFIED / NOT VERIFIED / EVIDENCE GAP boundary.

No CrewAI patch, production credentials, or SABLE adoption is required.
