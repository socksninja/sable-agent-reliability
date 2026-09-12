# SABLE — Silent Agent Reliability Benchmark

> **Can an AI agent actually complete a task — and can we prove that it did?**

SABLE is a model- and provider-independent evaluation system for tool-using AI agents. Instead of trusting the agent’s final answer, SABLE verifies the **observable environment state** and records the execution evidence needed to explain success, failure, and silent failure.

[GitHub](https://github.com/socksninja/sable-agent-reliability) · [External verification guide](docs/10_MIN_EXTERNAL_VERIFICATION.md) · [Submission quickstart](docs/EXTERNAL_SUBMISSION_QUICKSTART.md)

## Why SABLE exists

Agent systems are moving from generating answers to taking actions: calling tools, changing state, recovering from errors, and completing long-horizon tasks.

That creates a reliability question that a final text response cannot answer:

**Did the agent really do what it claimed to do?**

SABLE treats the environment as the judge.

```text
agent decision
      ↓
structured tool call
      ↓
SABLE Sandbox
      ↓
observed environment state
      ↓
deterministic verification
      ↓
trajectory + failure taxonomy + evidence
```

## What SABLE measures

- **Wrong state** — the claimed outcome does not match the environment.
- **Silent failure / overclaim** — the agent reports success when execution did not succeed.
- **Unauthorized actions** — the agent attempts tools outside task authorization.
- **Tool failures** — rejected calls, failed mutations, and execution errors.
- **Idempotency** — unsafe or incorrect behavior on repeated operations.
- **State drift** — losing critical state across multiple steps.
- **Long-horizon execution** — reliability across multi-step tasks.
- **Replay integrity** — evidence that can be checked against recorded state hashes.
- **Provider failures** — model/runtime/infrastructure failures are separated from agent behavior.

## SABLE’s core distinction

Most evaluations ask whether the model produced a good answer.

SABLE asks whether the **system changed the world correctly**.

That makes the benchmark useful for studying the gap between:

`model capability → execution capability → reliable autonomy`

## Current benchmark

SABLE v0.5 contains a reproducible **140-task benchmark**:

- 20 baseline tasks
- 120 adversarial tasks
- deterministic Sandbox
- per-task tool authorization
- structured execution traces
- deterministic verification and replay
- failure taxonomy and reliability scoring

The benchmark targets failure modes such as recovery, authorization, state drift, duplicate actions, overclaiming, and long-horizon execution.

## Public evidence layer

SABLE supports a versioned public evidence loop for real model runs:

```text
public model
→ structured tool call
→ SABLE Sandbox
→ observed state
→ task checks
→ replay/evidence
→ versioned Reliability Record
```

A **Reliability Record** is an auditable model/runtime snapshot rather than a marketing score. It keeps successful executions, rejected or failed tool actions, environment outcomes, native tool-call transport, provenance, and CI evidence together.

An example public record is:

`records/qwen_qwen2_5_0_5b_instruct_reliability_2026-09-10.json`

with evidence generated from GitHub Actions run `34513779679`.

## External verification

SABLE also provides a machine-validated path for independently run agents and runtimes:

```text
external agent/runtime
→ capture
→ GitHub Actions evidence
→ Reliability Record / trace
→ validation
→ maintainer evidence review
→ public record
```

The **10-minute external verification path** is intentionally small: wrap one real tool call, capture the execution, and let the reusable workflow validate and upload the resulting evidence artifact.

Start here:

```text
sable_capture_v09.py
examples/external_agent_10min.py
.github/workflows/external-verification-reusable.yml
docs/10_MIN_EXTERNAL_VERIFICATION.md
```

A fixture or structurally valid submission is **not** presented as evidence of real third-party adoption. SABLE only treats an external run as external evidence when the agent/runtime is independently maintained and the execution can be inspected.

## Terminal-truth admission cases

SABLE now maintains three minimal external-runtime case specifications covering a recurring reliability boundary:

```text
requested contract
      ↓
callable surface
      ↓
actual invocation
      ↓
observed state transition
      ↓
terminal outcome
      ↓
parent-visible result
```

`tasks/external_runtime_terminal_truth_v01.md` defines TTR-01 (child failure must not become parent success), TTR-02 (parent success requires terminal ownership of child work), and TTR-03 (requested tool contract must match observed invocation).

These cases are **SPEC / NOT YET BENCHMARK-ADMITTED**. Upstream reports are external references only until SABLE independently reproduces them or obtains an inspectable machine-verifiable receipt. This prevents public case studies from being silently promoted into benchmark truth.

## Running the model-independent core

No model API key is required for the core self-tests:

```bash
python3 tasks/generate_adversarial.py
python3 selftest_v05.py
python3 selftest_ingest_v08.py
python3 selftest_submission_v09.py
```

## Running a real model

Real-model evaluation is an optional second layer. Configure:

```bash
SABLE_API_KEY=...
SABLE_BASE_URL=...
SABLE_MODEL=...
```

then run `run_sable.sh` or the GitHub Actions workflow’s manual dispatch.

Provider outages, quota failures, and model infrastructure errors are recorded separately from agent reliability so that the benchmark does not mistake an unavailable model for an unreliable agent.

## External submissions

For the public v0.9 submission path, submit a UTF-8 JSONL file containing `sable.submission.v0.9` envelopes:

```bash
python3 trace_submit_v09.py \
  --input submission.jsonl \
  --output sable_traces_v05.jsonl
```

See:

- `docs/EXTERNAL_SUBMISSION_QUICKSTART.md`
- `docs/EXTERNAL_RELIABILITY_RECORD_SUBMISSION_V0.1.md`
- `schemas/submission_v09.schema.json`
- `schemas/reliability_record_submission_v01.schema.json`

## Measurement

SABLE reports:

- **Reliability Score** — a 0–100 critical-failure score across wrong-state, overclaim, unauthorized-tool, incomplete, model, and provider-limit failures.
- **Operational Score** — task pass rate after unavailable-model/provider rows are excluded.
- **Failure rates** — explicit rates for unsafe actions, overclaims, wrong state, duplicate actions, tool errors, and provider limits.
- **Family breakdown** — performance across recovery, idempotency, authorization, state drift, long-horizon, and other adversarial families.

See `RELIABILITY_SCORE.md` for the exact measurement convention.

## Status

SABLE is an **open, experimental reliability-evaluation project**. The repository provides reproducible evaluation infrastructure and public evidence formats, but it does not claim that fixture data or a self-test proves general agent reliability.

The next meaningful milestone is **independent external execution with terminal-truth evidence**: at least one TTR case is independently reproduced by a real agent/runtime, captured with inspectable child/parent provenance, and admitted only after the machine-verifiable oracle passes.

## Repository map

```text
sable_v05.py                         evaluator / replay
reliability_score.py                 score + report generation
sable_capture_v09.py                 external execution collector
tasks/                               baseline + adversarial tasks
schemas/                             trace + submission contracts
records/                             public Reliability Records
docs/                                protocols, admission, integration guides
.github/workflows/                   reproducible evidence pipelines
```

**Principle:** AI can propose the action. **Reality must determine whether the action actually worked.**