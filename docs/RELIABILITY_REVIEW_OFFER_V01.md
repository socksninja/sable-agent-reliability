# SABLE Agent Reliability Sprint

## A focused external test of whether an AI agent actually completes the task it claims to complete.

**Pilot price:** US$50 fixed scope  
**Typical turnaround:** one focused test cycle  
**Best fit:** AI agents, tool-using workflows, LangGraph/LangChain systems, automation agents, and LLM applications with a concrete reliability question.

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

1. **Test matrix** — scenarios, expected state, observed state, pass/fail.
2. **Raw execution evidence** — tool calls, relevant state transitions, and reproducible run information.
3. **Failure report** — each finding classified by failure mode and evidence boundary.
4. **One-page reliability summary** — what failed, what reproduced, and what should be fixed or monitored next.

### The key difference

A final LLM answer is not treated as proof of task completion.

SABLE checks the observable execution state and separates:

**model/provider failure → tool/execution failure → state failure → genuine task completion**

The goal is not a score that looks impressive. The goal is an engineering artifact another developer can reproduce and challenge.

### Minimal engagement

You do not need to expose your whole production stack for a focused first test.

For a minimal reproducer, send:

- the workflow or a reduced version,
- the failure you care about, and
- the expected final state.

We return the evidence package and a concise diagnosis.

### Public track record

SABLE is a provider-independent evaluation system with a reproducible 140-task benchmark covering recovery, authorization, state drift, duplicate actions, overclaiming, idempotency, and long-horizon execution.

Repository: https://github.com/socksninja/sable-agent-reliability

### Scope boundary

This pilot is an evaluation/reliability review, not a promise to fix an entire production system. If the first run identifies a concrete engineering defect, remediation can be scoped separately.
