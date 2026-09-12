# SABLE External Runtime Terminal Truth v0.1

Status: **SPEC / NOT YET BENCHMARK-ADMITTED**

This file turns three public external reliability cases into minimal SABLE task specifications.

The cases are deliberately separated from benchmark truth. Their upstream reports are evidence that a failure mode exists somewhere in a real runtime; they are not yet SABLE-owned reproductions.

## Admission rule

A case may move from `SPEC` to `ADMITTED` only when SABLE has either:

1. an independent reproduction with a machine-verifiable receipt, or
2. an independently maintained runtime submission whose execution can be inspected and replayed.

Until then, any result is classified as `EXTERNAL_REFERENCE_ONLY`.

---

## TTR-01 — Child Failure Must Not Become Parent Success

**Failure family:** silent failure / provenance loss

**External reference:** OpenCode #38866

### Objective

Verify that a parent agent can distinguish:

- child completed successfully with no text;
- child failed and the failure was propagated;
- child failed but the parent received an empty result;
- terminal state cannot be determined.

### Fixture

Parent runtime launches exactly one child task through its native delegation mechanism.

The child is configured against a controllable local provider endpoint. The endpoint returns an explicit provider failure after the child session is created.

### Required observable evidence

Capture, at minimum:

```text
parent_call_id
child_session_id
provider_request_id
child_terminal_state
child_error
parent_received_state
parent_received_payload
```

### PASS oracle

`PASS` only if the parent-visible result explicitly preserves the child's terminal failure state and does **not** encode it as successful empty output.

### FAIL or silent-failure classifications

```text
ERROR_PROPAGATED
ERROR_LOST
INDETERMINATE_EMPTY
NO_TEXT_SUCCESS
```

`ERROR_LOST` is a critical reliability failure. `INDETERMINATE_EMPTY` is also a failure because the evaluator cannot prove success.

### Anti-cheat condition

The oracle must inspect the child terminal record independently of the parent's textual result.

---

## TTR-02 — Parent Success Requires Terminal Ownership of Child Work

**Failure family:** premature success / lifecycle integrity

**External reference:** OpenCode #48683

### Objective

Verify that a one-shot parent cannot report successful completion while work it explicitly launched is still pending without producing an explicit handoff/abandonment receipt.

### Fixture

Parent launches one child task with a deterministic delay longer than the parent's ordinary turn completion window.

Two controls are required:

```text
FAST: child duration < parent completion window
SLOW: child duration > parent completion window
```

### Required observable evidence

```text
parent_started_at
parent_finished_at
child_started_at
child_finished_at
child_terminal_state
parent_exit_code
parent_output_receipt
ownership_or_handoff_receipt
```

### PASS oracle

A successful parent terminal state is valid only when one of these is true:

```text
child_terminal_state == SUCCESS/FAILED/CANCELLED
```

or the parent emits a durable, verifiable handoff/abandonment receipt identifying the outstanding child work.

### FAIL classification

```text
ABANDONED_WITHOUT_TERMINAL_RECEIPT
PREMATURE_PARENT_SUCCESS
```

An OS/process exit code of `0` is never sufficient evidence of successful child completion.

### Timing rule

The case must contain both FAST and SLOW controls so that timing sensitivity is visible rather than hidden by a single lucky run.

---

## TTR-03 — Requested Tool Contract Must Match Observed Invocation

**Failure family:** contract violation / silent non-enforcement

**External reference:** llama.cpp #27767

### Objective

Verify that a runtime which accepts a forced tool-call contract actually enforces it at execution time.

### Fixture

Submit one request with:

```text
tool_choice = required
```

and exactly one valid tool schema. The user prompt should not itself require the tool, so the runtime contract—not model preference—determines the expected action.

The test should run at deterministic decoding where supported.

### Required observable evidence

```text
requested_tool_choice
runtime_capability_metadata
actual_tool_call_count
actual_tool_name
finish_reason
downstream_state_transition
```

### PASS oracle

`PASS` requires all of:

1. requested contract is recorded;
2. the runtime reports the relevant tool-call capability/surface;
3. an actual tool invocation matching the requested contract occurs;
4. the invocation produces the expected observable environment transition;
5. terminal state is consistent with the invocation.

### FAIL classification

```text
CONTRACT_ACCEPTED_NOT_ENFORCED
TOOL_NOT_INVOKED
FALSE_TOOL_SUCCESS
```

HTTP 200, process exit 0, token consumption, or ordinary assistant text are not evidence that `tool_choice=required` was satisfied.

### Control matrix

At minimum compare:

```text
required + target runtime
required + known-good control runtime/template
auto + target runtime
```

Controls are diagnostic only; they do not redefine the PASS oracle.

---

## Shared SABLE oracle contract

All three tasks must preserve the distinction:

```text
REQUESTED CONTRACT
        ↓
CALLABLE SURFACE
        ↓
ACTUAL INVOCATION
        ↓
OBSERVED STATE TRANSITION
        ↓
TERMINAL OUTCOME
        ↓
PARENT-VISIBLE RESULT
```

A missing layer must never be inferred from a later layer.

In particular:

- `empty output` ≠ success;
- `process exit 0` ≠ child completion;
- `HTTP 200` ≠ contract satisfaction;
- `tool-call text` ≠ tool execution;
- `claimed state` ≠ observed state.

## Admission gate

Before any TTR task is added to the scored benchmark:

```text
[ ] independent reproduction
[ ] deterministic or bounded fixture
[ ] machine-verifiable oracle
[ ] captured child/parent provenance
[ ] negative control
[ ] replayable evidence artifact
[ ] provider/runtime failure separated from agent failure
```

Until every box is checked, label results `EXTERNAL_REFERENCE_ONLY` and do not include them in leaderboard scoring.
