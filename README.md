# SABLE — Silent Agent Reliability Benchmark

> **Can an AI agent actually complete a task — and can we prove that it did?**

SABLE is a model- and provider-independent evaluation system for tool-using AI agents. Instead of trusting the agent's final answer, SABLE verifies the **observable environment state** and records the execution evidence needed to explain success, failure, and silent failure.

[GitHub](https://github.com/socksninja/sable-agent-reliability) · [Evidence layer](EVIDENCE_LAYER.md) · [Streaming reliability finding](STREAMING_RELIABILITY_FINDING_V01.md) · [Reality Map](REALITY_MAP_V01.md) · [Failure Corpus](FAILURE_CORPUS_V01.md) · [External verification guide](docs/10_MIN_EXTERNAL_VERIFICATION.md) · [Submission quickstart](docs/EXTERNAL_SUBMISSION_QUICKSTART.md) · [Strategy alignment](STRATEGY_ALIGNMENT_V01.md)

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

## SABLE's core distinction

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

## External verification: use SABLE against your runtime

SABLE is designed to be independently checked rather than trusted by default.

- **10-minute verification:** run an existing agent with a small adapter and submit a machine-readable evidence packet. See [docs/10_MIN_EXTERNAL_VERIFICATION.md](docs/10_MIN_EXTERNAL_VERIFICATION.md).
- **Third-party submission:** publish a real runtime trace, tool calls, before/after state hashes, outcome claim, timestamp, collector identity, and integrity digest. See [docs/EXTERNAL_SUBMISSION_QUICKSTART.md](docs/EXTERNAL_SUBMISSION_QUICKSTART.md).
- **Public reproduction challenge:** [SABLE-002 independent reproduction](https://github.com/socksninja/sable-agent-reliability/issues/48) asks for a concrete reproduce / not-reproduce / taxonomy-correction result.
- **OpenClaw external cases:** [terminal-truth validation targets](docs/EXTERNAL_CASE_001_OPENCLAW_TERMINAL_TRUTH.md) cover OpenClaw incidents `#141474`, `#97616`, and `#144911`, with explicit evidence gaps and no adoption/reproduction claims.

The goal is not to make a SABLE claim harder to question. The goal is to make it easier for someone else to disprove, reproduce, or strengthen it.

## Reliability reviews for real agent systems

Teams with a concrete runtime failure, reliability incident, or uncertain execution claim can bring the real trace or minimal reproducer to SABLE.

A focused review can produce:

1. a minimal reproduction or non-reproduction result,
2. a failure classification with explicit evidence boundaries, and
3. a machine-readable evidence receipt suitable for engineering review.

This can be done as an external design-partner engagement or paid reliability review. No access to proprietary data is required for a minimal reproduction when the failure can be reduced to a synthetic trace.

## Published runtime reliability finding

SABLE now publishes dynamically reproduced runtime failures as evidence records. The first combined finding covers two distinct streaming failure modes: silent zero-chunk completion and duplicate delivery after mid-stream retry.

See [STREAMING_RELIABILITY_FINDING_V01.md](STREAMING_RELIABILITY_FINDING_V01.md) for the evidence, pinned runtime revision, external anchors, reproduction results, and explicit evidence boundaries.
