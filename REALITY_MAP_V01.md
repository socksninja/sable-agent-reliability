# SABLE Reality Map v0.1

> **North star:** make SABLE a missing piece of the external reality layer for Agent Reliability.
>
> If a strategic buyer ignored SABLE, what part of the real-world reliability picture would they no longer see?

This page is deliberately evidence-first. A prospect, framework, model provider, or runtime maintainer should be able to distinguish **observed reality**, **SABLE reproduction**, and **open hypotheses** without reading the whole repository.

## Current evidence layers

| Layer | What SABLE can currently show | Status |
|---|---|---|
| Deterministic sandbox | Environment-state verification, replay, authorization checks | VERIFIED internally |
| Cross-runtime normalization | LangGraph and CrewAI executions normalized to the same SABLE evidence model | VERIFIED external-runtime executions |
| Terminal-truth cases | TTR-01 through TTR-03 are explicit reliability boundaries | Benchmark-admitted/spec boundary maintained |
| Public incident mapping | OpenClaw issues expose concrete terminal-truth failure classes relevant to SABLE | EXTERNALLY OBSERVED, not SABLE adoption |
| Independent adoption | Third-party runtime uses SABLE and produces inspectable evidence | 0 formally admitted |
| Repeat external usage | Same external actor/runtime uses SABLE more than once | 0 formally admitted |
| Commercial pull | Paid evaluation / design-partner workflow | 0 |

## Reality coverage matrix

Legend: **V** = independently verified execution; **O** = externally observed problem; **S** = SABLE specification only; **—** = not yet evidenced.

| Reliability boundary | LangGraph | CrewAI | OpenClaw public reports | SABLE status |
|---|---:|---:|---:|---|
| Environment-state correctness | V | V | — | Verified on cross-runtime cases |
| Tool contract / actual invocation | V | V | O | TTR-03 + external targets |
| Child/parent terminal truth | — | — | O | TTR-01 / external validation pending |
| Completion delivery vs task status | — | — | O | External validation pending |
| Detached-task liveness | — | — | O | External validation pending |
| Stale evidence promotion | — | — | O | TTR-06 spec; not benchmark-admitted |
| Silent failure / false success | — | — | O | Core SABLE target |
| Repeated-operation safety | — | — | — | Benchmark target |
| State drift | — | — | — | Benchmark target |

## How a new reality becomes SABLE evidence

```text
external runtime/problem
        ↓
inspectable execution
        ↓
minimal terminal-truth reproduction
        ↓
SABLE capture + deterministic oracle
        ↓
replay + provenance + evidence hash
        ↓
public Reliability Record
        ↓
independent repeat usage
```

## Admission rule

Public reports, screenshots, comments, synthetic fixtures, or claims by an agent are **signals**, not SABLE evidence. A case becomes admitted only when an independently attributable runtime execution produces inspectable machine-verifiable evidence.

## What matters most next

1. One independently maintained runtime reproduces one terminal-truth boundary through SABLE.
2. A second external runtime or repeated run confirms the same evidence contract is useful beyond one integration.
3. An external maintainer asks to run, integrate, or reuse SABLE without being prompted to manufacture activity.
4. A concrete design-partner or paid reliability workflow appears.

The map should change only when reality changes.
