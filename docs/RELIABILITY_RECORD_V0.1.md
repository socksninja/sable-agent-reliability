# SABLE Reliability Record v0.1

A Reliability Record is a versioned, auditable snapshot of an agent/runtime evaluation. It is evidence metadata, not a claim that a model is generally reliable.

## Required fields

- `schema_version`: `sable.reliability_record.v0.1`
- `record_id`
- `generated_at`
- `benchmark`
- `model`
- `runtime`
- `n`
- `native_tool_call_rate`
- `task_success_rate`
- `task_successes`
- `model_errors`
- `environment_mutations`
- `task_results[]`
- `provenance`
- `artifact`

## Task result semantics

Each task result records the goal, model claim, tool-call count, native transport, observed sandbox outcome, final environment state/hash, and whether the deterministic task checks passed.

A task is successful only when the environment reaches the task's expected state. A model's textual claim does not override the observed state. A failed tool action may still be a successful *safety behavior* when the task explicitly requires the state to remain unchanged; consumers must distinguish `agent_action_outcome` from `task_success`.

## Public evidence rule

Records must identify the GitHub Actions run and artifact digest that generated the observation. Consumers should treat repository fixtures as non-evidence unless they point to an actual external execution artifact.
