# SABLE Reliability Audit — Founder Pilot

## What it is

A small external audit for real tool-using AI agent executions.

The goal is not to benchmark a model in the abstract. The goal is to find cases where an agent appears to succeed but the observable environment says otherwise.

## Founder pilot

**Input:** 3–5 real agent tasks.

**Setup:** No SDK integration required for the initial pilot. Tasks can be supplied as structured prompts, traces, or a reproducible execution path.

**Output:**

- silent failure / overclaim evidence
- wrong-state outcomes
- tool-choice or tool-execution failures
- state drift across steps
- recovery failures
- duplicate / idempotency failures
- unauthorized tool-action attempts
- reproducible traces where available

## Workflow

```text
3–5 real tasks
    ↓
SABLE execution / capture
    ↓
observable environment state
    ↓
deterministic checks
    ↓
failure classification
    ↓
reproducible evidence
```

## What counts as a useful result

A useful result is an inspectable mismatch between the requested outcome, the agent's claimed outcome, and the observed environment state.

A fixture or self-generated benchmark row is not presented as evidence of customer-agent behavior.

## Commercial path

The first external pilot is intentionally small.

**Founder Pilot:** $49 for a larger follow-up audit after a useful issue is found in the initial sample.

**Reliability Audit:** $99 for a broader task set and structured failure report.

Larger recurring or integration work is scoped separately.

## Contact

GitHub: https://github.com/socksninja/sable-agent-reliability

SABLE is an independent, model- and provider-independent reliability/evidence layer.
