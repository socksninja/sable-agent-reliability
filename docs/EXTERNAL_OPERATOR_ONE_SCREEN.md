# SABLE — External Operator One-Screen Run

**Goal:** produce one independently verifiable SABLE-native execution. No SABLE adoption or endorsement is required.

## What the operator does

1. Copy `examples/external-submission-starter/run_one_sable_task.py` and `.github/workflows/sable-external.yml` into your own agent repository.
2. Replace only `run_real_agent_task()` with one real task from your runtime/framework.
3. Push to GitHub.
4. GitHub Actions validates `sable.submission.v0.9` and uploads the execution artifact plus SHA-256 evidence manifest.
5. Send back the public run URL, job ID, artifact ID, commit SHA, and artifact digest.

## What must be real

- The agent/runtime must actually execute.
- Claimed status must come from the runtime.
- Final environment state must come from the environment, not be hand-authored.
- Provenance must point to the actual GitHub run/commit/artifact.

## Recommended first task

Choose one harmless task with an observable environment effect, for example:

`write marker file -> agent reports success -> independently read file -> compare before/after state hash`

This is deliberately small because the first objective is **external provenance**, not benchmark coverage.

## Result classes

SABLE may classify the run as `PASS`, `FAIL`, or `UNKNOWN`. A negative result is useful evidence.

## Links

Starter: `examples/external-submission-starter/`

Submission protocol: `docs/EXTERNAL_RELIABILITY_RECORD_SUBMISSION_V0.1.md`

Open call: `issues/63`
