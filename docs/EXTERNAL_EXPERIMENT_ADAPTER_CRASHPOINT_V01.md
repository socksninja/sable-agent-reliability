# External Experiment Adapter — Crashpoint CrewAI Retry v0.1

## Purpose

This document records how SABLE can independently verify a third-party reliability experiment whose native receipt schema is not RNCP-EXECUTION-RECEIPT-v1.

The first target is `mstevens843/crashpoint`, experiment `crewai_retry`.

## Source evidence

- Repository: `https://github.com/mstevens843/crashpoint`
- Evidence file: `evidence/crewai_retry.json`
- Evidence blob SHA-1: `13f35572ebd0d0f56f57e893c62e38132793f4b1`
- Runtime: CrewAI 1.15.21
- Experiment receipt id: `cp1_a7376a114c8eeb06eb7042039a8557b00630fde0cf946788d8be9a2cdd22541d`

## Observed result

The published receipt reports:

- clean: 30/30 `EXACTLY_ONCE`
- pre-effect: 30/30 `EXACTLY_ONCE`
- post-effect: 30/30 `DUPLICATED`
- post-effect expected effect count: 2

The receipt explicitly limits the claim to same-process synchronous CrewAI tool retry. It does not claim fresh-process crash recovery, real LLM/provider behavior, or idempotency protection.

## SABLE treatment

This is **external experiment evidence**, not an RNCP receipt and must not be promoted as one.

Admission should preserve the native schema and provenance, then independently recompute/verifiy at minimum:

1. public source reachability;
2. native receipt parseability;
3. native receipt internal consistency (`all_agree`, case counts, hashes/receipt id);
4. pinned CrewAI source commit and version;
5. experiment repository commit provenance;
6. explicit limitations and scope.

The SABLE record should classify the result as an independently observed runtime reliability finding, not as a general reliability verdict.

## Current status

`SOURCE_REACHABLE` — yes.

`NATIVE_RECEIPT_REACHABLE` — yes.

`SABLE_NATIVE_RNCP_COMPATIBLE` — no; the native receipt has a different schema.

`INDEPENDENT_RUNTIME_OWNER_SUBMISSION` — pending; this adapter does not imply endorsement by CrewAI or the experiment author.

## Next verification action

Run a SABLE-side adapter/verifier against the public JSON, producing a deterministic verification record that references the exact source commit/file and does not rewrite the source experiment's claims.
