# SABLE — Silent Agent Reliability Benchmark

SABLE is a model-independent evaluation harness for tool-using AI agents. It measures whether an agent actually reaches the required environment state, rather than trusting the agent's final claim.

## v0.5 core

The evaluation layer is independent of any model provider:

`task → agent trace → Sandbox → observed tool result → state hash → deterministic verifier → failure taxonomy → reliability score`

The repository contains a reproducible 140-task benchmark (20 baseline + 120 adversarial), a deterministic Sandbox with per-task tool authorization, a trace schema, a model-independent structural/security self-test, and a replayable evaluator.

### What SABLE measures

- deterministic task success from environment state
- unauthorized tool attempts
- tool execution errors and failed mutations
- overclaiming (agent says success while the state is wrong)
- idempotency and duplicate-action behavior
- long-horizon / cross-step state preservation
- replay integrity via state hashes
- provider/infrastructure failures separated from agent failures

### Reliability Score

SABLE v0.5 reports:

- **Reliability Score** — a 0–100 critical-failure score that penalizes wrong-state, overclaim, unauthorized-tool, incomplete, model, and provider-rate-limit failures.
- **Operational Score** — task pass rate after excluding unavailable-model/provider rows.
- **Failure rates** — explicit rates for unsafe actions, overclaims, wrong state, duplicate actions, tool errors, and provider limits.
- **Family breakdown** — performance across recovery, idempotency, authorization, state drift, long-horizon, and other adversarial families.

See `RELIABILITY_SCORE.md` for the exact measurement convention.

## Running the model-independent core

```bash
python3 tasks/generate_adversarial.py
python3 selftest_v05.py
```

The self-test requires no API key or external model.

## Running a real model

Real-model evaluation is an optional second layer. Configure `SABLE_API_KEY`, `SABLE_BASE_URL`, and `SABLE_MODEL`, then use `run_sable.sh` or the GitHub Actions workflow's manual dispatch. A provider outage or quota limit is recorded separately and must not be confused with agent reliability.

See `schemas/trace.schema.json` for the v0.5 trace contract, `sable_v05.py` for evaluation/replay, and `reliability_score.py` for scoring/report generation.
