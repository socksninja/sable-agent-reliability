# SABLE Failure Taxonomy v0.1

This taxonomy is generated only from task-level failures explicitly present in promoted public Reliability Records. It does not infer failures that were not observed.

| Failure class | Count |
|---|---:|
| `constraint_violation` | 1 |
| `protocol_or_parsing_failure` | 4 |

Records scanned: **3**.

Observed task-level failures classified: **5**.

## Current evidence

- `SABLE-CREWAI-REF-34522362667`: 0 classified failures.
- `SABLE-EXT-SMOLLM-34518509976`: 4 classified failures; `protocol_or_parsing_failure: 4`.
- `qwen-qwen2.5-0.5b-instruct-2026-09-10-run-34513779679`: 1 classified failure; `constraint_violation: 1`.

## Failure instances

- `SABLE-EXT-SMOLLM-34518509976` / `EXT-01` → `protocol_or_parsing_failure` (agent output could not be parsed into the required action protocol).
- `SABLE-EXT-SMOLLM-34518509976` / `EXT-02` → `protocol_or_parsing_failure` (agent output could not be parsed into the required action protocol).
- `SABLE-EXT-SMOLLM-34518509976` / `EXT-03` → `protocol_or_parsing_failure` (agent output could not be parsed into the required action protocol).
- `SABLE-EXT-SMOLLM-34518509976` / `EXT-04` → `protocol_or_parsing_failure` (agent output could not be parsed into the required action protocol).
- `qwen-qwen2.5-0.5b-instruct-2026-09-10-run-34513779679` / `SABLE-RC-08` → `constraint_violation` (agent mutated environment contrary to task constraint).
