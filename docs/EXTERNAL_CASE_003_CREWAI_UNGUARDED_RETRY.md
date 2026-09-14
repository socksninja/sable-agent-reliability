# External Case 003 — CrewAI unguarded retry amplification

Canonical evidence record: [`EXTERNAL_REPRODUCTION_CREWAI_5802.md`](../EXTERNAL_REPRODUCTION_CREWAI_5802.md).

This case is an independent execution against the real CrewAI 1.15.21 retry engine. The strongest result is not the raw duplicate count; it is the separation of runtime-reported outcome from independently observed side effects.

- persistent post-effect exception, direct `ToolUsage.use()`: 6 effects;
- identical boundary with idempotency-ref-v1 guard: 1 effect;
- adjacent end-to-end Agent/Crew case: 2 effects through the outer retry path;
- effect counts/IDs read back independently from SQLite;
- machine-readable receipt published by the external executor;
- no SABLE adoption or integration claim.

Primary issue: https://github.com/crewAIInc/crewAI/issues/5802
External receipt: https://github.com/giskard09/argentum-core/blob/main/examples/conformance/crewai-unguarded-retry/receipt.json
