# SABLE External Case 001 — OpenClaw terminal-truth failure boundary

**Status:** EXTERNAL OBSERVATION / NOT BENCHMARK-ADMITTED

**Purpose:** convert real public runtime failure reports into narrowly defined, independently reproducible SABLE validation targets without claiming adoption or reproduction before evidence exists.

## External sources

- Runtime: OpenClaw
- Primary incident: `openclaw/openclaw#144911`
- Collector/status incident: `openclaw/openclaw#141474`
- Runtime degradation incident: `openclaw/openclaw#97616`
- Related external incidents: `#143334`, `#101656`

These are public reports from an independently maintained runtime. Their existence is external evidence of reliability problem classes, **not** evidence that SABLE has reproduced them.

## Case A — MCP child timeout → parent runtime terminal truth

For `#144911`, the externally reported sequence is:

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

The reported failure is instead:

```text
initialize timeout
→ cleanup-path exception
→ main process exit(1)
```

### SABLE question

Can an external observer independently establish the runtime's **terminal state transition** after an MCP initialization timeout, without relying on the agent's final text or the incident author's interpretation?

> **Does a failed child operation produce the correct parent/runtime terminal state, and is that state observable and attributable?**

## Case B — collector completion / status disagreement

OpenClaw `#141474` reports a collector child that calls `sessions_yield` and leaves no collector completion record while different status surfaces disagree: `recent` reports `done`, `tasks` reports `running`, and the parent wait can remain pending. The repository's automated review says current source supports the orphaned yielded-collector shape, while noting that a fresh runtime reproduction has not been executed on the reviewed source. 

### SABLE question

Can one fresh collector execution produce a machine-checkable chain:

```text
collector run
→ yield / terminal event
→ completion-record state
→ recent projection
→ tasks projection
→ agents_wait result
```

The result must be one of:

- **reproduced** — the lifecycle/projection disagreement is observed;
- **not reproduced** — terminal/completion surfaces converge; or
- **taxonomy correction** — the observed behavior belongs to a different lifecycle boundary.

This is a particularly strong SABLE target because the evidence gap is explicitly about **runtime truth versus status claims** rather than model quality.

## Case C — zombie/resource degradation after partial repairs

OpenClaw `#97616` remains an explicit cross-owner zombie/reaping umbrella. The September 13 automated review says there is still no high-confidence current-main reproduction and specifically requests one redacted `v2026.9.4`/current-main trace connecting a spawning owner, PID identity, exit observation, and independent post-exit state to a remaining defect.

### SABLE question

Can a current runtime run establish:

```text
tool/hook owner
→ child PID identity
→ child exit
→ post-exit process state
→ runtime health
→ eventual terminal/degraded state
```

The acceptance result is **not** "the old issue is still true". It is whether a fresh execution closes the owner-to-observable-state evidence chain after the partial repairs.

## Proposed minimal validation

1. Run an independently maintained OpenClaw version/configuration that can exercise the selected path.
2. Trigger one controlled failure condition.
3. Capture the relevant runtime lifecycle events and exact timestamps.
4. Capture observable state outside the agent's narrative channel.
5. Verify the oracle against runtime state.
6. Preserve the external run as inspectable evidence before any SABLE admission decision.

## Admission gate

A case becomes benchmark-admitted only if an external runtime independently provides a machine-checkable receipt or reproducible run that closes:

```text
independent runtime
→ actual execution
→ observable terminal state
→ inspectable evidence
→ attribution/context
→ SABLE oracle
```

Until then, these documents remain external-case hypotheses and targeting artifacts.

## Evidence discipline

Do not count:

- the public issue alone as SABLE reproduction;
- comments mentioning SABLE as adoption;
- synthetic local reproduction as third-party evidence;
- inferred OpenClaw usage as a run;
- a benchmark fixture as a real-runtime receipt.

The current SABLE external scoreboard remains unchanged until the evidence chain is independently closed.

## Strategic value

A successful external validation would establish something more valuable than another benchmark task: a public, inspectable example where **runtime terminal truth differs from an agent/task-level claim or expected containment contract**.

That is the evidence layer SABLE is designed to measure.
