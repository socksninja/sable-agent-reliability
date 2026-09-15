# SABLE — External Reality Scoreboard v0.2

**Purpose:** keep external-world evidence ahead of internal engineering.

**Operating rule:** No External Reality → no new core complexity.

## Current external queue

| Target | Current state | Next valid signal | Action on signal |
|---|---|---|---|
| CrewAI #5802 | VERIFIED EXTERNAL REPRODUCTION | independent follow-up, runtime maintainer response, or repeat use | preserve receipt; pursue one bounded follow-up, no benchmark expansion |
| Langfuse #17377 | OUTREACH / RESPONSE PENDING | maintainer reply or real execution receipt | offer one concrete cross-runtime evidence test |
| #97616 / ClawSweeper review | WAITING | maintainer/reviewer result, receipt, runtime evidence | verify → archive → update public record |
| #144911 / MCP init-timeout crash | RECEIPT REQUESTED | receipt / machine-readable evidence / maintainer confirmation | verify → archive → update public record |
| #137332 | EXTERNAL DATA RECEIVED / VERIFY | complete receipt, reproducible runtime result, maintainer confirmation | verify/cross-check → archive → update public record |
| #143334 / subagent completion-delivery mismatch | NEW TARGET | maintainer response or reproducible runtime evidence | request 1–3-case terminal-truth validation; then verify |
| #101656 / detached subagent liveness + terminal-state mismatch | NEW TARGET | maintainer response or reproducible runtime evidence | request 1–3-case liveness/terminal-state validation; then verify |
| Chase Sets #6732 / PR #7836 | EXTERNAL CASE / VERIFY | reproducible runtime execution with effect-state readback | reproduce one ambiguous concurrent cancellation case; compare terminal classification vs external state |
| Gemini CLI #19069 | EXTERNAL INCIDENT / VERIFY | maintainer/user response or reproducible filesystem mismatch evidence | request one bounded post-operation verification case; compare tool success vs filesystem state |

## Latest external observations

| UTC date | Actor / project | Event | Evidence | Signal type | Verification | Next action |
|---|---|---|---|---|---|---|
| 2026-09-15 | Gemini CLI #19069 | Public incident reports `replace` returning success while the target file remains unchanged; issue explicitly calls for mandatory post-operation verification | public issue #19069, CLI 0.28.2, Windows win32 v25.6.1, session `ca4ece6a-ac3f-4f42-8e6c-abe513378307` | external incident / false-success case | E0/E1; concrete public report, not SABLE reproduction | obtain reproducible before/after filesystem state with immutable trace |
| 2026-09-15 | Chase Sets / #6732 / PR #7836 | Public repair case for concurrent cancellation convergence; classifier distinguishes `[409,200]` / `[200,409]` from `[200,200]` and requires post-write reconciliation rather than completion-order inference | `EXTERNAL_CASE_CHASE_7836_EFFECT_CONVERGENCE_V01.md` + public PR #7836 | public incident / repair case | E0/E1; public control evidence, not SABLE reproduction | reproduce one bounded effect-convergence case with independent external-state readback |
| 2026-09-14 | giskard09 / crewAI #5802 | Real crewAI 1.15.21 retry engine executed externally; persistent post-effect exception produced 6 independently read effects; same boundary with idempotency-ref-v1 guard produced 1 | `EXTERNAL_REPRODUCTION_CREWAI_5802.md` + external `receipt.json` | independent external execution | machine-readable receipt; fresh SQLite readback; live rerun; artifact anchored on Base | preserve evidence; seek maintainer-level response or repeat execution, not benchmark expansion |
| 2026-09-13 | OpenClaw public incident reports | Multiple public runtime incidents expose terminal-truth boundaries around child cleanup, subagent completion delivery, detached-task liveness, and long-running process degradation | `docs/EXTERNAL_CASE_001_OPENCLAW_TERMINAL_TRUTH.md` + public issues #144911/#143334/#101656/#97616 | externally observed problem class | not independently reproduced by SABLE | obtain one inspectable external runtime execution; do not count incident reports as SABLE adoption |

## External Runtime Target List — v1

The following are **prospects, not adoption**. Their existence in this table never increments a reality counter.

| Project / issue | Why it matters to SABLE | Best validation wedge | Status |
|---|---|---|---|
| CrewAI #5802 | real retry-layer composition can amplify committed side effects before result registration | rerun one bounded real-runtime case and compare independent effect readback | evidence obtained; maintainer-level response pending |
| Langfuse #17377 | existing trace/eval infrastructure creates a natural telemetry→evidence interoperability boundary | one real non-sensitive run + compact public receipt | outreach sent; response pending |
| OpenClaw #144911 | MCP initialization timeout causes cleanup failure and Gateway crash; explicit observable terminal boundary | reproduce timeout → verify expected contained state vs crash state | outreach target |
| OpenClaw #143334 | task registry can say `succeeded` while completion delivery is pending/failed and requester is effectively deadlocked | compare authoritative task outcome, delivery state, requester state | outreach target |
| OpenClaw #101656 | detached child can be running, waiting, failed, or dead while user-facing channel sees only silence; reported trajectory/state mismatch | verify liveness + terminal outcome from runtime state, not model report | outreach target |
| OpenClaw #97616 | long-running tool/hook subprocess leak degrades runtime despite nominal health for a period | execute bounded workload → verify process/runtime state over time | outreach target |
| Gemini CLI #19069 | tool-layer success claim can diverge from actual filesystem mutation; direct terminal-truth mismatch with public runtime/version/session context | reproduce one file mutation with independent before/after hash and compare claimed success vs observed state | newly added; external incident, not independently reproduced |
| Chase Sets #6732 / PR #7836 | concurrent external-effect calls can return conflicting statuses while desired state still converges; completion order is not authoritative | reproduce `[409,200]` and `[200,409]` with an external-state oracle; require identical convergence semantics | newly added external case; not independently reproduced |

### Targeting rule

Prioritize targets where:

1. the failure is already public and concrete;
2. the runtime state is observable without privileged production access;
3. the claimed outcome can be independently checked;
4. the result would demonstrate a reliability boundary SABLE already knows how to measure;
5. the smallest useful experiment is ≤10–20 minutes.

Do **not** ask for a generic "try my benchmark". Ask for one concrete failure-class validation against the runtime's own observable state.

## Reality counters

| Metric | Current | Rule |
|---|---:|---|
| External Runtime Users | 1 confirmed | count only external actors who executed a real runtime under the evidence path |
| Third-party Runs | 1 formally admitted | count only inspectable executions |
| Verified Receipts | 1 formally admitted | receipt must be independently attributable and checkable |
| Maintainer Confirmations | 0 formally admitted | confirmation must come from the external project owner/maintainer |
| Machine-readable Evidence | 1 formally admitted | artifact must be inspectable and linked to the run |
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

_Last updated: 2026-09-15._
