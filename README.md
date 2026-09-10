# SABLE — Silent Agent Reliability Benchmark

SABLE is a model-independent evaluation harness for tool-using AI agents. It measures whether an agent actually reaches the required environment state, rather than trusting the agent's final claim.

## Public Reliability Record loop

SABLE now supports a versioned public evidence loop for real pretrained models:

`public model → structured tool call → SABLE Sandbox → observed state → task checks → replay/evidence → versioned Reliability Record`

A Reliability Record is an auditable model/runtime snapshot, not a benchmark marketing score. It keeps successful executions, rejected/failed tool actions, environment outcomes, native tool-call transport, provenance, and the CI evidence reference together.

The first public record is `records/qwen_qwen2_5_0_5b_instruct_reliability_2026-09-10.json`, generated from GitHub Actions run `34513779679` and its uploaded corpus artifact. See `docs/RELIABILITY_RECORD_V0.1.md` for the record contract.

## External Reliability Record intake

SABLE now has a machine-validated path for third-party model/runtime submissions:

`external evaluation → GitHub Actions evidence → Reliability Record JSON → submission PR → CI validation → maintainer evidence review → public records/`

Submit a record under `submissions/*.json` using `schemas/reliability_record_submission_v01.schema.json`. The validator checks task-result cardinality, task-success arithmetic, native-tool-call arithmetic, provenance shape, and artifact digest format. See `docs/EXTERNAL_RELIABILITY_RECORD_SUBMISSION_V0.1.md` for the full admission and promotion policy.

A validated submission is not automatically considered evidence of general reliability or production safety; promotion requires inspection of the cited run, job, artifact, and task-level observations.

**External submitter quickstart:** `docs/EXTERNAL_SUBMISSION_QUICKSTART.md`

## v0.9 public trace submission layer

SABLE v0.9 adds a versioned public submission protocol for external agents and agent frameworks:

`external agent → v0.9 submission envelope → integrity/provenance validation → v0.5 trace → deterministic evaluation → evidence → reliability score → leaderboard`

The submission protocol is JSONL-based and keeps agent claims, observed execution, environment outcomes, and provenance/integrity distinct. See `docs/TRACE_SUBMISSION_PROTOCOL_V0.9.md`, `schemas/submission_v09.schema.json`, and `trace_submit_v09.py`.

A deterministic fixture is available at `examples/submissions/third_party_reference_v09.jsonl`. It is a protocol fixture, **not** evidence of real third-party execution.

The first runtime-level integration target is LangGraph; the acceptance criteria are documented in `docs/FIRST_THIRD_PARTY_INTEGRATION.md`. SABLE should not claim external validation until a live third-party trace has been captured and evaluated.

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
python3 selftest_ingest_v08.py
python3 selftest_submission_v09.py
```

These self-tests require no API key or external model.

## Running an external submission

Prepare a UTF-8 JSONL file containing one `sable.submission.v0.9` envelope per line, then validate and normalize it:

```bash
python3 trace_submit_v09.py \
  --input submission.jsonl \
  --output sable_traces_v05.jsonl
```

The normalized traces are compatible with the existing evaluator, evidence layer, score generator, and leaderboard.

For the public evidence and PR admission path, follow `docs/EXTERNAL_SUBMISSION_QUICKSTART.md`.

## Running a real model

Real-model evaluation is an optional second layer. Configure `SABLE_API_KEY`, `SABLE_BASE_URL`, and `SABLE_MODEL`, then use `run_sable.sh` or the GitHub Actions workflow's manual dispatch. A provider outage or quota limit is recorded separately and must not be confused with agent reliability.

See `schemas/trace.schema.json` for the v0.5 trace contract, `schemas/submission_v09.schema.json` for the v0.9 public submission contract, `sable_v05.py` for evaluation/replay, and `reliability_score.py` for scoring/report generation.
