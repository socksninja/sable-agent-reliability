# SABLE Agent Reliability Sprint

## A focused external test of whether an AI agent actually completes the task it claims to complete.

**Pilot price:** US$50 fixed scope  
**Typical turnaround:** one focused test cycle  
**Best fit:** AI agents, tool-using workflows, LangGraph/LangChain systems, automation agents, and LLM applications with a concrete reliability question.

### Start with almost no integration work

The lowest-friction entry is a **public incident / existing trace**.

Send one line:

```
URL | reliability question | public/private boundary
```

The URL can be a GitHub issue/PR, trace, bug report, or minimal reproducer. We first map the observable evidence and identify the smallest missing proof. No benchmark migration, adoption decision, or production credentials are required.

When a real execution is needed, the fixed-scope pilot starts from that same evidence boundary rather than from a generic integration project.

### What we test

We take one concrete workflow and deliberately exercise failure-prone paths such as:

- wrong or malformed tool arguments
- duplicate or repeated actions
- state drift across steps
- silent tool failure
- unauthorized actions
- false success / premature completion
- partial success
- recovery after an execution error

### What you receive

1. **Evidence boundary** — what the existing trace/runtime proves and what it cannot prove.
2. **Focused test matrix** — scenarios, expected state, observed state, verdict.
3. **Raw execution evidence** — tool calls, relevant state transitions, and reproducible run information.
4. **Failure report** — each finding classified by failure mode and evidence boundary.
5. **One-page reliability summary** — what reproduced, what remained unknown, and the smallest engineering next step.

### The key difference

A final LLM answer is not treated as proof of task completion.

SABLE checks the observable execution state and separates:

**model/provider failure → tool/execution failure → state failure → genuine task completion**

Unknown evidence stays **UNKNOWN**. A missing receipt, trace gap, or ambiguous external outcome is not silently converted into PASS.

The goal is not a score that looks impressive. The goal is an engineering artifact another developer can reproduce and challenge.

### Minimal engagement

You do not need to expose your whole production stack for a focused first test.

For a minimal engagement, provide:

- one concrete workflow or reduced reproducer,
- the reliability question,
- the expected final state,
- and the public/private boundary for any runtime evidence.

A public incident can be used for the initial evidence review; private execution is only needed when the missing proof cannot be established from public evidence.

### Public track record

SABLE is a provider-independent evaluation system with a reproducible 140-task benchmark covering recovery, authorization, state drift, duplicate actions, overclaiming, idempotency, and long-horizon execution.

Repository: https://github.com/socksninja/sable-agent-reliability

### Scope boundary

This pilot is an evaluation/reliability review, not a promise to fix an entire production system. If the first run identifies a concrete engineering defect, remediation can be scoped separately.

### Reply format

For the fastest start, reply with:

```
URL | reliability question | public/private boundary
```

One real incident is enough to begin.
