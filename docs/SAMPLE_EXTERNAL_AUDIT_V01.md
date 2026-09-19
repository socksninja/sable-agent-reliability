# Sample External Agent Reliability Audit

> Public sample only — this is **not** a paid client engagement and does not represent a customer result.

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

## What a paid audit adds

A paid audit applies the same discipline to **your** workflow:

1. identify one reliability question;
2. pin the relevant runtime/workflow boundary;
3. run or reproduce one bounded case;
4. independently verify the claimed outcome;
5. return PASS / FAIL / UNKNOWN with the evidence boundary and limitations.

**Fixed pilot price: US$99**

Payment: https://www.paypal.com/ncp/payment/2URELJ9NE4ZBN
