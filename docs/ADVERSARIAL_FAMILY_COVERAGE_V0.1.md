# SABLE Adversarial Family Coverage v0.1

SABLE's reproducible benchmark contains 20 baseline tasks plus 120 adversarial tasks across 10 attack families.

This artifact is **task coverage metadata**, not a measurement of model failure. Observed failures are recorded separately in `FAILURE_TAXONOMY_V0.1`.

| Attack family | Tasks |
|---|---:|
| `authorization` | 12 |
| `constraint_confusion` | 12 |
| `cross_step_memory` | 12 |
| `error_recovery` | 12 |
| `idempotency` | 12 |
| `long_horizon` | 12 |
| `overclaim` | 12 |
| `partial_success` | 12 |
| `state_drift` | 12 |
| `tool_selection` | 12 |

**Coverage:** 10 families / 120 adversarial tasks / 140 total tasks.

The benchmark separates intended attack coverage from observed model behavior. A family is not treated as an observed failure mode until an execution record contains evidence for it.
