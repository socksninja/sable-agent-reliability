# SABLE — External Reality Scoreboard v0.1

**Purpose:** keep external-world evidence ahead of internal engineering.

**Operating rule:** No External Reality → no new core complexity.

## Current external queue

| Target | Current state | Next valid signal | Action on signal |
|---|---|---|---|
| #97616 / ClawSweeper review | WAITING | maintainer/reviewer result, receipt, runtime evidence | verify → archive → update public record |
| #144911 | RECEIPT REQUESTED | receipt / machine-readable evidence / maintainer confirmation | verify → archive → update public record |
| #137332 | EXTERNAL DATA RECEIVED / VERIFY | complete receipt, reproducible runtime result, maintainer confirmation | verify/cross-check → archive → update public record |

## Reality counters

| Metric | Current | Rule |
|---|---:|---|
| External Runtime Users | 0 confirmed in this scoreboard | count only independently maintained external runtimes |
| Third-party Runs | 0 formally admitted here | count only inspectable executions |
| Verified Receipts | 0 formally admitted here | receipt must be independently attributable and checkable |
| Maintainer Confirmations | 0 formally admitted here | confirmation must come from the external project owner/maintainer |
| Machine-readable Evidence | 0 formally admitted here | artifact must be inspectable and linked to the run |
| Repeat Usage | 0 confirmed | same external actor/runtime uses SABLE evidence path again |
| Inbound Requests | 0 confirmed | unsolicited request for evaluation, evidence, integration, or collaboration |
| Revenue | 0 | cash actually received |

## Evidence admission rule

An item is **not** counted merely because:

- a comment mentions SABLE;
- a fixture or synthetic run exists;
- a structurally valid submission was produced;
- we inferred adoption from repository activity.

Count only evidence that closes the chain:

```text
independent actor/runtime
→ actual execution
→ observable result
→ inspectable evidence
→ attribution/context
→ record
```

## Event-driven operating rules

### Receipt
Verify provenance and contents. Record it. Do not automatically expand the benchmark.

### Runtime result
Cross-check the reported result against the available evidence. Record only what can be established.

### Maintainer confirmation
Capture the exact confirmation and, where appropriate, obtain permission to quote it publicly.

### Machine-readable evidence
Check whether the artifact is independently inspectable and whether its fields support the claimed result.

### Usage / collaboration
Move immediately to the smallest concrete next step: repeat run, integration test, design-partner discussion, or paid evaluation.

### Rejection / limitation
Record the objection as evidence about product-market/evidence fit. Do not argue with the signal.

### Silence
**No action.** Do not chase merely to manufacture activity.

## Stop line

Until a new external event arrives:

- do not expand the core benchmark;
- do not add new failure families;
- do not add speculative architecture;
- do not manufacture adoption claims;
- do not count internal GitHub activity as external progress.

The next meaningful engineering change should be justified by a concrete external observation.

## Update protocol

When a new event arrives, append one row with:

`UTC time | actor | project | event | evidence link/ID | signal type | verification status | next action`

Then update the counters above **only after verification**.

_Last updated: 2026-09-13._
