# External Case — LangGraph #8764 Non-Crash Positive Control

## Status

**External evidence received and mapped; SABLE protocol admission pending.**

This case records the public non-crash positive control published by `mstevens843` in response to [langchain-ai/langgraph#8764](https://github.com/langchain-ai/langgraph/issues/8764). It is evidence from an independent external runtime execution, but it is **not** counted as a SABLE-admitted third-party submission yet.

The reason for keeping that distinction is deliberate: the external receipt has a strong independent observation chain, but the recorded control is not itself a `sable.submission.v0.9` envelope and does not expose every field required by the current SABLE v0.9 normalization surface (for example, task-step tool-call fields and per-step before/after state hashes).

## Source

- External repository: `mstevens843/crashpoint`
- Source branch: `experiment/langgraph-noncrash-control`
- Publication commit: `2d8b05535a53ce4695935efa2d8908c767d64588`
- LangGraph issue: [#8764](https://github.com/langchain-ai/langgraph/issues/8764)
- External report: [results/12-langgraph-noncrash-control.md](https://github.com/mstevens843/crashpoint/blob/2d8b05535a53ce4695935efa2d8908c767d64588/results/12-langgraph-noncrash-control.md)
- External receipt: [evidence/langgraph_noncrash_control_v4/receipt.json](https://github.com/mstevens843/crashpoint/blob/2d8b05535a53ce4695935efa2d8908c767d64588/evidence/langgraph_noncrash_control_v4/receipt.json)
- External manifest: [evidence/langgraph_noncrash_control_v4/manifest.json](https://github.com/mstevens843/crashpoint/blob/2d8b05535a53ce4695935efa2d8908c767d64588/evidence/langgraph_noncrash_control_v4/manifest.json)
- Retained ledger readback: [ledger-readback.jsonl](https://github.com/mstevens843/crashpoint/blob/2d8b05535a53ce4695935efa2d8908c767d64588/evidence/langgraph_noncrash_control_v4/ledger-readback.jsonl)
- Observer report: [observer-report.json](https://github.com/mstevens843/crashpoint/blob/2d8b05535a53ce4695935efa2d8908c767d64588/evidence/langgraph_noncrash_control_v4/observer-report.json)

## What was actually observed

One real, non-crashed LangGraph execution was recorded.

| Field | Observed value |
|---|---|
| LangGraph | `1.2.11` |
| langgraph-checkpoint | `4.2.0` |
| langgraph-checkpoint-sqlite | `3.1.1` |
| durability | `sync` |
| invoke count | `1` |
| worker exit | `0` |
| runtime completion | `success` |
| terminal state | `{"done": true}` |
| admission before invoke | `true` |
| post-run admission events | `accepted -> completed` |
| checkpoint count | `3` |
| observer status | `OBSERVED` |
| observer exit | `0` |
| ledger chain | valid |
| independently observed effect count | `1` |
| oracle classification | `EXACTLY_ONCE` |
| native receipt `passed` | `true` |
| receipt schema | `crashpoint.langgraph_control.receipt.v3` |
| receipt ID | `cp1_f644c93d28cebc7ab00eae2b8f24cb9df6de009f5004687d3eebbaa2773248a9` |

The effect observation is specifically derived by a newly spawned observer process reading the on-disk ledger bytes. The external receipt states that the archived readback bytes match the original readback and gives the ledger SHA-256 as:

`5757811ea521504d0065dfb0db60c703da9c5b57f4615cd2dc6a3943502f5523`

The observed effect is bound to the same identity used for admission and LangGraph `thread_id`:

`lgnc-32fe56ed89764a879922fb58d429670f`

The single ledger record contains:

- `attempt_id = lgnc-32fe56ed89764a879922fb58d429670f:attempt-1`
- `intent_id = lgnc-32fe56ed89764a879922fb58d429670f`
- `op = execute`
- `deduped = false`
- `payload_digest = 8468d8677fb6e2676785fab68f344e7d37e727c3f9f76de998a24d0e91f51077`

## Evidence chain

The external control's strongest property is separation of claims:

```
caller-owned admission
        |
        v
LangGraph thread identity
        |
        v
real worker invocation
        |
        +--> runtime completion claim
        |
        +--> checkpoints
        |
        v
fresh observer process
        |
        v
on-disk ledger readback
        |
        v
effect count / digest / reference
        |
        v
native classification
```

The observer does not derive effect truth from the worker's return value or from a count computed by the worker. The external verifier independently parses the retained ledger bytes, recomputes effect facts, and separately queries the retained SQLite databases.

## SABLE mapping

This case maps naturally onto the SABLE reliability question:

> Can a runtime distinguish its own completion claim from independently observable execution state?

### Directly mappable evidence

| SABLE concept | External evidence |
|---|---|
| external run identity | caller-owned `admission_id` |
| runtime identity | LangGraph `thread_id` |
| runtime result | worker exit + returned terminal state |
| external effect | ledger record for the same `intent_id` |
| independent observation | fresh observer process |
| observed state integrity | ledger chain + retained bytes + SHA-256 |
| expected vs measured | pre-declared contract + measured receipt |
| terminal classification | `EXACTLY_ONCE` |
| evidence limitations | explicitly recorded in receipt |

### Not yet directly admissible under v0.9

The current `sable.submission.v0.9` validator expects:

- a `trace.steps[]` sequence;
- each step to contain `tool`, `args`, `observed_result`, `before_state_hash`, and `after_state_hash`;
- source/runtime metadata in the v0.9 envelope;
- a canonical `source_trace_hash`;
- a trace-level structure designed around task/tool execution.

The LangGraph positive control is an application-level evidence control, not a normal agent-tool benchmark run. We therefore **must not manufacture missing v0.9 fields** merely to make it pass the schema.

## Smallest protocol bridge

The lowest-risk bridge is an adapter/reporting layer, not a core protocol expansion.

Conceptually:

```
external receipt.v3
    |
    +--> preserve native receipt unchanged
    |
    +--> normalize independent observation facts
    |
    +--> bind admission_id == thread_id == intent_id
    |
    +--> retain runtime claim separately
    |
    +--> derive SABLE-facing PASS / FAIL / UNKNOWN mapping
```

A future formal submission can add a small, runtime-neutral evidence adapter only if another external case demonstrates that the same fields are repeatedly required.

## Current classification

`INDEPENDENT_EXTERNAL_EXECUTION`

`REAL_RUNTIME`

`FRESH_PROCESS_READBACK`

`EFFECT_STATE_EVIDENCE`

`RUNTIME_OUTCOME_VS_EXTERNAL_STATE`

`SABLE_MAPPING_READY`

`NOT_YET_SABLE_ADMITTED`

## What this proves

This case provides inspectable evidence that:

1. an external actor ran a real LangGraph 1.2.11 execution;
2. admission identity was committed before the runtime invocation;
3. the runtime completed normally;
4. an independently spawned observer read the external ledger;
5. the observed effect count was one;
6. the native classification agreed with the observed evidence;
7. the evidence bundle contains retained artifacts and hashes that can be checked offline.

## What this does not prove

It does not establish:

- a LangGraph framework fix;
- a general exactly-once guarantee;
- production-wide reliability;
- SABLE certification;
- SABLE adoption by LangGraph;
- statistical reliability rates;
- an independently re-executed copy of the experiment;
- authenticated proof of a real network/provider side effect.

The source itself explicitly scopes this as a one-run positive control.

## Next action

The next useful step is **not** benchmark expansion.

It is one of:

1. obtain the external actor's confirmation that the SABLE mapping is technically correct;
2. produce a minimal adapter/record without changing SABLE's core semantics;
3. use the same evidence boundary against one second runtime, then compare whether the adapter fields remain stable.

The strategic objective is to test whether SABLE can become a reusable **evidence layer across runtimes**, not to inflate the benchmark with synthetic cases.
