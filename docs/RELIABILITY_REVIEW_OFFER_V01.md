# SABLE Independent Reliability Verification

## A focused external test of whether an AI agent actually completes the task it claims to complete.

**Current fixed price:** US$250 one-time  
**Typical scope:** one focused verification cycle  
**Best fit:** AI agents, tool-using workflows, LangGraph/LangChain systems, automation agents, and LLM applications with a concrete reliability question.

### Start with one real incident

The lowest-friction starting point is a **public incident / existing trace / minimal reproducer**.

Send one line:

```
URL | reliability question | public/private boundary
```

The URL can be a GitHub issue/PR, trace, bug report, or minimal reproducer. We first map the observable evidence and identify the smallest useful verification.

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
- replay / checkpoint correctness

### What you receive

1. **Evidence boundary** — what the existing trace/runtime proves and what it cannot prove.
2. **Focused test matrix** — scenarios, expected state, observed state, verdict.
3. **Raw execution evidence** — tool calls, relevant state transitions, and reproducible run information.
4. **Failure report** — each finding classified by failure mode and evidence boundary.
5. **SHA-256 evidence digest** — integrity reference for the returned evidence bundle.
6. **Scoped verdict** — VERIFIED, NOT VERIFIED, or EVIDENCE GAP.
7. **One-page reliability summary** — what reproduced, what remained unknown, and the smallest engineering next step.

### The key difference

A final LLM answer is not treated as proof of task completion.

SABLE checks the observable execution state and separates:

**model/provider failure → tool/execution failure → state failure → genuine task completion**

Unknown evidence stays **UNKNOWN**. A missing receipt, trace gap, or ambiguous external outcome is not silently converted into PASS.

The goal is an engineering artifact another developer can reproduce and challenge.

### Minimal engagement

For a focused first test, provide:

- one concrete workflow or reduced reproducer,
- the reliability question,
- the expected final state,
- and the public/private boundary for any runtime evidence.

A public incident can be used for the initial evidence review; private execution is only needed when the missing proof cannot be established from public evidence.

### Public track record

SABLE is a provider-independent evaluation system with a reproducible 140-task benchmark covering recovery, authorization, state drift, duplicate actions, overclaiming, idempotency, and long-horizon execution.

Repository: https://github.com/socksninja/sable-agent-reliability

### Scope boundary

This is an evaluation/reliability verification service, not a promise to fix an entire production system. It does not provide production-wide reliability certification, security certification, or a guarantee that unrelated failure modes do not exist.

### Payment

**US$250 fixed, one-time fee.**

Payment is handled through PayPal. The active checkout link is supplied with the assignment/payment request.

For a smaller evidence-only first step, see [US$25 Evidence Snapshot](EVIDENCE_SNAPSHOT_USD25.md).

## Public service page

See [Independent Reliability Verification — US$250](INDEPENDENT_RELIABILITY_VERIFICATION_USD250.md).
