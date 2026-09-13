# SABLE Evidence Layer

## The one-sentence purpose

> **SABLE measures whether an agent actually changed the world correctly, and preserves the evidence needed to prove what happened.**

The strategic objective is not to become another generic agent benchmark. It is to become a missing piece of the **external reality layer for Agent Reliability**.

## What SABLE currently knows

### Verified cross-runtime execution

SABLE has normalized inspectable executions from **LangGraph 1.2.11** and **CrewAI 1.15.20** against the same semantic task and the same terminal state. Both executions replay to the same final state and pass the same authorization/evidence contract.

See [`CROSS_RUNTIME_EVIDENCE_MATRIX_V10.md`](CROSS_RUNTIME_EVIDENCE_MATRIX_V10.md).

### Externally observed reliability boundaries

Public runtime incidents are being tracked as **external signals**, not converted into SABLE adoption claims. Current examples cover MCP initialization/cleanup failure, completion delivery mismatch, detached subagent liveness, and long-running subprocess degradation.

See [`EXTERNAL_REALITY_SCOREBOARD_V01.md`](EXTERNAL_REALITY_SCOREBOARD_V01.md).

### Evidence boundary

SABLE deliberately separates:

`public incident → attributable execution → SABLE reproduction → independent verification → repeated external use`

A weaker stage is never silently upgraded into a stronger claim.

## What the next external proof looks like

The highest-value next event is small:

```text
one real external runtime
        ↓
one concrete reliability boundary
        ↓
inspectable execution
        ↓
SABLE oracle + replay
        ↓
independent attribution
        ↓
public Reliability Record
```

The goal is not to ask a maintainer to "try a benchmark." The goal is to validate **one failure class against the runtime's own observable state**.

## Reality scoreboard

Current counters are maintained separately from the engineering surface. Until a new external event arrives, benchmark expansion and speculative architecture are intentionally paused.

See [`EXTERNAL_REALITY_SCOREBOARD_V01.md`](EXTERNAL_REALITY_SCOREBOARD_V01.md).

## Reality Map

See [`REALITY_MAP_V01.md`](REALITY_MAP_V01.md) for the current cross-runtime / failure-boundary coverage and explicit gaps.

## Failure Corpus

See [`FAILURE_CORPUS_V01.md`](FAILURE_CORPUS_V01.md) for the normalized contract used to turn observed reliability failures into reusable evidence without overstating provenance.

## Claim discipline

We will not claim that SABLE has external adoption, production safety, a data moat, or acquisition value merely because the repository contains fixtures, synthetic runs, self-tests, or public incident references.

The evidence has to come from reality.
