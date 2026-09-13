# SABLE External Case 001 — OpenClaw terminal-truth failure boundary

**Status:** EXTERNAL OBSERVATION / NOT BENCHMARK-ADMITTED

**Purpose:** convert a real public runtime failure report into a narrowly defined, independently reproducible SABLE validation target without claiming adoption or reproduction before evidence exists.

## External source

- Runtime: OpenClaw
- Primary incident: `openclaw/openclaw#144911`
- Related external incidents: `#143334`, `#101656`, `#97616`

These are public reports from an independently maintained runtime. Their existence is external evidence of a reliability problem class, **not** evidence that SABLE has reproduced it.

## Case hypothesis

For #144911, the externally reported sequence is:

```text
MCP child initialization
→ initialize timeout
→ child cleanup / abort path
→ unhandled rejection
→ Gateway exits
```

The expected terminal truth is containment:

```text
MCP server unavailable / timed out
→ bounded failure state
→ Gateway remains alive
```

The observed external report instead describes a process-level failure:

```text
initialize timeout
→ cleanup-path exception
→ main process exit(1)
```

## SABLE question

Can an external observer independently establish the runtime's **terminal state transition** after an MCP initialization timeout, without relying on the agent's final text or the incident author's interpretation?

The validation target is therefore not "does OpenClaw have a bug?" but:

> **Does a failed child operation produce the correct parent/runtime terminal state, and is that state observable and attributable?**

## Proposed minimal validation

1. Run an independently maintained OpenClaw version/configuration that can exercise the MCP child initialization path.
2. Cause one bounded initialization timeout using a controlled MCP test server.
3. Capture:
   - child start;
   - timeout event;
   - cleanup attempt;
   - parent/Gateway process state;
   - terminal exit/recovery state;
   - exact timestamps and run identity.
4. Verify the oracle against runtime state rather than the model's or operator's textual claim.
5. Record either:
   - **contained failure** — timeout is surfaced while parent runtime remains operational; or
   - **propagated runtime failure** — timeout causes parent runtime termination/degraded state.
6. Preserve the external run as inspectable evidence before any SABLE admission decision.

## Admission gate

This case becomes benchmark-admitted only if an external runtime independently provides a machine-checkable receipt or reproducible run that closes:

```text
independent runtime
→ actual execution
→ observable terminal state
→ inspectable evidence
→ attribution/context
→ SABLE oracle
```

Until then, this document remains an external-case hypothesis and targeting artifact.

## Adjacent SABLE terminal-truth mappings

The same runtime family exposes additional validation wedges:

### #143334 — parent/task/delivery disagreement

Check that:

```text
task registry outcome
↔ child terminal outcome
↔ completion delivery state
↔ requester-visible terminal state
```

A `succeeded` task must not become user-visible success when completion delivery is failed or the requester remains blocked.

### #101656 — silent detached work

Check that:

```text
runtime liveness
↔ child terminal state
↔ user-visible terminal notification
```

Silence must not be interpreted as success, failure, or continued progress without authoritative runtime evidence.

### #97616 — long-run runtime degradation

Check that:

```text
tool/hook execution
→ resource/process state
→ runtime health
→ eventual terminal/degraded state
```

Nominal health must not mask accumulating process/resource failure when objective runtime state shows degradation.

## Evidence discipline

Do not count:

- the public issue alone as SABLE reproduction;
- comments mentioning SABLE as adoption;
- synthetic local reproduction as third-party evidence;
- inferred OpenClaw usage as a run;
- a benchmark fixture as a real-runtime receipt.

The current SABLE external scoreboard must remain at zero until the evidence chain is independently closed.

## Strategic value

A successful external validation would establish something more valuable than another benchmark task: a public, inspectable example where **runtime terminal truth differs from an agent/task-level claim or expected containment contract**.

That is the evidence layer SABLE is designed to measure.
