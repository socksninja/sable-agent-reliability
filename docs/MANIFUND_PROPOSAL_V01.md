# Manifund Proposal Draft v0.1

## Working title
**Verifiable Agent Reliability Evidence: Proving What an AI Agent Actually Did**

## Funding target
- Minimum viable stage: **$5,000**
- Preferred stage: **$10,000**
- Initial research period: **90 days**

## The problem
AI agents are moving from generating text to taking actions: calling tools, modifying state, recovering from errors, deploying software, and performing multi-step workflows.

But a persistent reliability gap remains:

> **An agent can claim that it succeeded even when the real environment disagrees.**

This is more serious than ordinary answer-quality evaluation. A false completion can mean an incorrect database state, a duplicated side effect, an unauthorized action, an incomplete deployment, or a silent operational failure.

The ecosystem needs a way to distinguish:

**agent-reported success**

from

**independently verifiable execution success.**

## What I am building

SABLE is an open-source, provider-independent reliability evidence layer for tool-using AI agents.

Instead of trusting the final answer, SABLE verifies observable environment state and preserves evidence about what happened.

The core evidence chain is:

```text
agent decision
→ structured tool call
→ observed environment state
→ deterministic verification
→ execution trace
→ provenance / integrity checks
→ Reliability Record
```

The long-term research question is whether this evidence model can become portable across agent runtimes and model providers.

## Existing work

The project is already underway rather than being a proposal-only idea.

Current public work includes:

- a reproducible 140-task benchmark;
- deterministic sandbox and environment-state checks;
- tool authorization and failure taxonomy;
- structured execution traces;
- replay and integrity evidence;
- external trace-submission and admission workflows;
- runtime reliability findings with explicit evidence boundaries;
- external case studies covering completion truth and deployment truth;
- a public 10-minute external-verification path.

The repository is public and the research programme is explicitly designed to allow third parties to reproduce, challenge, or strengthen the claims.

## 90-day research plan

### 1. Cross-runtime evidence admission

Test whether real execution traces from different agent runtimes can be converted into a common Reliability Record without erasing important runtime-specific information.

### 2. Completion-truth boundary

Identify the minimum evidence required before an automated system is justified in claiming DONE, from source/test state through artifact, installation, target environment, runtime execution, and terminal state.

### 3. External failure corpus

Collect and reproduce real failure cases involving silent failure, wrong state, unauthorized actions, duplicate side effects, state drift, partial completion, and runtime/provider failure.

### 4. Independent verification

Measure whether a third party can independently determine what happened from the evidence packet, including what remains unproven.

## What will be published

1. A versioned Reliability Record specification.
2. A public corpus of externally reproducible agent reliability failures.
3. Cross-runtime evidence studies.
4. Lightweight verification tools.
5. A technical report describing the limits of execution evidence.
6. Benchmark tasks derived from externally observed failure modes.

## What makes this different

This is **not** primarily another model benchmark.

The central unit of study is a **verifiable execution claim**.

SABLE asks:

> What evidence is sufficient to establish that an agent actually achieved the intended state change?

The intended result is a reusable evidence layer that can sit between agent runtimes and downstream evaluation, reliability, governance, or operational systems.

## Falsifiability

The project will publish negative findings.

A useful result includes discovering that:

- a proposed field is insufficient;
- different runtimes cannot be reliably normalized;
- an admission rule creates false confidence;
- a cheaper evidence boundary is equally authoritative;
- or the evidence model does not predict real-world reliability.

The objective is to discover the truth about the evidence problem, not to prove that SABLE is correct.

## Budget logic

Funding will be used for concrete research bottlenecks rather than generic development:

- model/API and compute costs for reproducible experiments;
- hosting and evidence infrastructure;
- research resources and datasets;
- targeted reproduction work;
- collaboration and fieldwork needed to obtain independent runtime evidence.

## Milestones

### First 30 days
At least 3 external runtime/evidence interactions, first independently submitted records, and a revised cross-runtime schema based on failures.

### Days 31–60
At least 2 reproducible external reliability cases and an initial comparison across runtime/provider boundaries.

### Days 61–90
Public evidence corpus, verification tooling, research report, and a decision on whether the cross-runtime evidence hypothesis survives contact with external data.

## Why now

Agent systems are increasingly being used for actions rather than only text generation. The reliability question therefore moves from “was the answer good?” to “did the system change the world correctly?”

SABLE targets that transition directly.

## Links

Repository: https://github.com/socksninja/sable-agent-reliability

Research proposal: `docs/RESEARCH_PROPOSAL_AGENT_RELIABILITY_EVIDENCE_V01.md`
