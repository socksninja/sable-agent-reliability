# SABLE Experiment — LangSmith Readback Gap v0.1

## Research question

After a LangSmith `create_run` and `update_run` are accepted, is the same run immediately retrievable through the LangSmith Run API?

## Initial observation

A real SABLE second-backend execution on 2026-09-15 successfully created and updated an explicitly addressed LangSmith run, but an immediate single-run GET returned HTTP 404 `Run not found`.

That observation is not sufficient to call this a consistency bug. It establishes only a **write/readback gap at the observation point**.

## Hypothesis

H1: LangSmith run writes may become readable only after a non-zero propagation delay.

H0: A successfully accepted LangSmith run should be immediately retrievable through the same run identifier.

## Protocol

1. Create a LangSmith run with a deterministic experiment name and explicit UUID.
2. Record the local timestamp immediately after `create_run` returns.
3. Update the same run and record the local timestamp after `update_run` returns.
4. Attempt `runs.retrieve(run_id)` at delays: `0s, 1s, 2s, 5s, 10s, 30s`.
5. Record status, exact observation timestamp, error type, and observed run ID.
6. Stop at the first successful readback.
7. Persist the result as `sable.experiment.langsmith_readback_gap.v0.1`.

## Independent variables

- Delay after write acknowledgement.
- LangSmith project/workspace.
- API client version.
- Region/base URL when applicable.

## Dependent variables

- Readback result (`READBACK_OK` vs `READBACK_404_OR_ERROR`).
- First successful readback delay.
- Exact HTTP/application error returned before readback.

## Pass conditions

**READBACK_EVENTUALLY_AVAILABLE:** at least one scheduled read returns the exact run ID.

**WRITE_ACCEPTED_WITHOUT_READBACK_WITHIN_SCHEDULE:** all scheduled reads fail while write/update operations were accepted.

Neither outcome alone proves a platform defect. Repetition is required to distinguish transient propagation from stable API behavior.

## Current implementation

- Experiment runner: `experiments/langsmith_readback_gap.py`
- Workflow: `.github/workflows/langsmith-readback-gap-experiment.yml`
- Result artifact: `artifacts/langsmith-readback-gap-experiment.json`

## SABLE significance

This experiment converts an ambiguous observability failure into a measurable reliability dimension: **evidence write visibility latency**. The same protocol can later be adapted to other observability backends to compare write acknowledgement, external visibility, and evidence-receipt reachability.
