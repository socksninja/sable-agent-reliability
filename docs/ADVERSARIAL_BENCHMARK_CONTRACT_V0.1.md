# SABLE Adversarial Benchmark Contract v0.1

The public SABLE benchmark is a frozen execution contract, not merely a task count.

## Coverage

- 20 baseline tasks
- 120 adversarial tasks
- 140 total tasks
- 10 adversarial families
- 12 tasks per adversarial family
- adversarial IDs are exactly `ADV-001` through `ADV-120`

## Attack families

`authorization`, `constraint_confusion`, `cross_step_memory`, `error_recovery`, `idempotency`, `long_horizon`, `overclaim`, `partial_success`, `state_drift`, `tool_selection`.

## Integrity rules

The coverage gate rejects duplicate baseline IDs, missing or unexpected adversarial families, uneven family counts, non-hard adversarial tasks, family metadata mismatches, missing checks, and gaps in the `ADV-001..ADV-120` ID sequence.

## Evidence semantics

Benchmark coverage says which failure surfaces SABLE can test. It does not say that a model has failed on a surface. Observed failures enter the public Failure Taxonomy only when a promoted Reliability Record contains explicit task-level evidence.

## CI position

The benchmark contract is checked before Reliability Matrix and Failure Taxonomy generation. This prevents accidental benchmark shrinkage or structural drift from silently changing later measurements.
