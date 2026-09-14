# External Reproduction — CrewAI #5802

## Status

**Independent external reproduction verified.**

This record documents an execution performed by `giskard09` against the real, unmocked CrewAI retry engine, using `crewai==1.15.21` from PyPI. It is external evidence, not a SABLE adoption or integration claim.

## Runtime boundary

The harness directly drives `crewai.tools.tool_usage.ToolUsage.use()` / `_use` with a hand-built `ToolCalling`, matching the executor's post-parsing entrypoint. No LLM call is made. The installed package is exercised directly rather than reimplemented or mocked.

The external receipt identifies two retry layers:

- outer `_run_attempts` / `_max_parsing_attempts`
- inner exception/retry fallback around `tool.invoke()`

## Failure observation

The fault is injected immediately after the side effect commits and before CrewAI registers the tool result.

### UNGUARDED_RETRY

- logical action: `unguarded-retry-001`
- CrewAI outer attempts: 4
- Python-level invocations: 6
- final runtime outcome: error
- independently observed effects: **6**
- effect IDs were read from a fresh SQLite connection after execution

The result demonstrates that the runtime's final error does not imply absence of committed effects.

### Same failure point with idempotency-ref-v1 guard

- same logical action
- same CrewAI retry engine
- two Python-level invocations
- independently observed effects: **1**
- guard observations include `PENDING_GUARD` and `RECONCILED_GUARD`

The only intended variable is the presence of the idempotency guard at the tool boundary.

## Why the 6-effect and 2-effect cases are not contradictory

A second external execution in the same CrewAI issue uses an end-to-end Agent/Crew fixture with an argument-free tool and injects the fault only on the first invocation. That case produces **2 effects** through the outer retry path.

The direct `ToolUsage.use()` reproduction uses non-empty arguments and a persistent post-effect exception, exercising both retry layers and producing **6 effects**.

These are adjacent failure cases under the same CrewAI 1.15.21 implementation, not competing measurements.

## Evidence properties

The external receipt states that:

- effect counts/IDs are independently read back from fresh SQLite connections;
- outcomes are not inferred from CrewAI's own reported status;
- the receipt was generated from live reruns, not replayed cached logs;
- the evidence is anchored on Base mainnet for proof-of-existence of the artifact.

Canonical external receipt:
`https://github.com/giskard09/argentum-core/blob/main/examples/conformance/crewai-unguarded-retry/receipt.json`

CrewAI issue:
`https://github.com/crewAIInc/crewAI/issues/5802`

## Evidence boundary

This record does **not** claim:

- CrewAI official adoption of SABLE;
- SABLE integration into CrewAI;
- a framework-level fix;
- production-wide reliability conclusions.

It establishes a narrower fact: a third party reproduced the failure against a real CrewAI retry engine and supplied independently observable side-effect evidence in a machine-readable receipt.

## SABLE classification

`independent_external_execution`
`real_runtime`
`side_effect_readback`
`retry_layer_composition`
`effect_amplification`
`runtime_outcome_vs_effect_truth`
`idempotency_guard_comparison`
