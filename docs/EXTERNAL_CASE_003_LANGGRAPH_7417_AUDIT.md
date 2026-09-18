# External Micro-Audit — LangGraph Cloud #7417

## Question

Can an independent observer distinguish:

1. one logical long-running tool execution,
2. a runtime redispatch from checkpoint/stale-run recovery, and
3. the resulting external side effect,

without relying on the agent's terminal success claim?

Source incident: https://github.com/langchain-ai/langgraph/issues/7417

## What the public incident already establishes

The issue reports a concrete replay boundary:

```
long-running tool
→ ~180s stale/sweep boundary
→ checkpoint-based redispatch
→ original + duplicate tool execution
```

The reporter states that the duplicate executions carry identical tool-call arguments and that both executions can complete successfully. The reported versions span LangGraph 1.1.3–1.1.6 on LangGraph Cloud.

This is already a useful reliability signal, but the public issue text alone does not establish every provenance edge needed for an independently reproducible evidence record.

## Evidence boundary

### Directly observable from the public report

- duplicate executions are reported;
- the executions have identical tool-call arguments;
- the duplicate path is described as having a `tools` node without a preceding `model` node;
- the behavior is reported after a long-running call crosses a stale/sweep boundary;
- the consequence is redundant work/cost.

### Still not independently established here

- a single stable execution identifier binding the original and redispatched tool calls;
- a cryptographically bound link between native trace entries and the external side effect;
- whether the duplicate entries represent the same logical action under a durable request/idempotency key;
- an independently readable final-state/effect ledger;
- the exact Cloud-side stale-run decision point and timing for a fresh reproduction.

## Smallest useful test

A single harmless long-running tool action is enough.

Record, independently where possible:

```
logical_action_id
tool_input_digest
original_native_run/tool_call_id
redispatched_native_run/tool_call_id
effect_before
effect_after
effect_count
terminal/runtime outcome
```

The decisive check is not whether both runs say "success".

It is whether:

```
logical action = 1
observed external effects = 1
```

or:

```
logical action = 1
observed external effects = 2
```

and whether the native evidence is sufficient to prove that distinction.

## SABLE's role

SABLE does not need to replace LangGraph's trace.

It can sit beside it as an independent reconstruction layer:

```
LangGraph native trace
        +
external effect readback
        +
before/after state evidence
        ↓
independent reliability record
```

A result may legitimately be:

- `PASS`
- `DUPLICATE_EFFECT`
- `UNKNOWN`
- `CONFLICT`

An unresolved evidence boundary stays unresolved; it is not converted into a success claim.

## Lowest-friction next step

No LangGraph code change is required.

One real or safely sandboxed reproduction is enough. The public SABLE reusable path is documented here:

https://github.com/socksninja/sable-agent-reliability/blob/main/docs/10_MIN_EXTERNAL_VERIFICATION.md

The intended output is one inspectable evidence packet, not an adoption decision or endorsement.
