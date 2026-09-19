# Sample External Agent Reliability Audit

> Public sample only — this is **not a paid client engagement** and does not represent a customer result.

## Buyer question

**Did the agent actually complete the requested state transition, and can an independent observer prove it from runtime evidence?**

## Scope

- Runtime: LangGraph 1.2.11
- Run: `#65`
- One bounded agent task
- One terminal-state question
- No production credentials
- Independent environment checks

## Observed evidence

- Runtime trace ID: `langgraph-6bab3b22-a523-444e-8a48-674a0d4cffae`
- `task_success=true`
- Environment check A: `true`
- Environment check B: `true`
- Source-trace SHA-256: `fa1c8c964919cbdc11cf4d0f23fcf86a410002eca143e0eb4f13e98453ee9d1c`

## Finding

**VERIFIED for the bounded claim.**

The run produced a runtime trace tied to a concrete execution identity, and the independent environment checks agreed with the task-success claim for this specific execution.

This does **not** establish:

- production-wide reliability;
- reliability for other model/provider/runtime versions;
- absence of unrelated failure modes;
- long-horizon reliability;
- security certification.

## Evidence boundary

The useful result is not simply "the agent returned success."

The useful result is:

```
agent claim
  ↓
runtime execution identity
  ↓
observed environment state
  ↓
independent verification
  ↓
bounded verdict
```

## What the current US$250 verification adds

A paid verification applies the same evidence discipline to **your** workflow:

1. identify one reliability question;
2. pin the relevant runtime/workflow boundary;
3. run or reproduce one bounded case;
4. independently verify the claimed outcome;
5. return VERIFIED / NOT VERIFIED / EVIDENCE GAP with the evidence boundary and limitations;
6. return the raw evidence reference and SHA-256 digest.

**Current fixed price: US$250 one-time**

See [Independent Reliability Verification — US$250](INDEPENDENT_RELIABILITY_VERIFICATION_USD250.md).

> Historical note: this public sample was originally published during an earlier pilot period. Its old pilot price should not be used as the current service price.
