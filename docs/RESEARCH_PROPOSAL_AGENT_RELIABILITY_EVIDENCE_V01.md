# SABLE Research Proposal v0.1

## Title

**Verifiable Agent Reliability Evidence: A Cross-Runtime Evidence Layer for Real-World Agent Execution**

## Research gap

AI agents are increasingly evaluated not only on whether they generate a correct answer, but on whether they can reliably execute actions in changing environments.

A critical gap remains between **an agent claiming that a task succeeded** and **independent evidence that the intended state transition actually occurred**.

Existing evaluations often operate at the model-response or benchmark level. For real agent systems, the harder question is:

> **When is an automated system justified in saying DONE?**

The research problem is to make that claim independently checkable across runtimes, model providers, and execution environments.

## Core hypothesis

A useful reliability layer can be built around a verifiable evidence chain:

```text
agent decision
→ structured tool call
→ observed environment state
→ deterministic verification
→ execution trace
→ integrity / provenance checks
→ Reliability Record
```

The key hypothesis is that **reliability claims should be treated as evidence claims, not merely model-output claims**.

## What has already been built

SABLE is a model- and provider-independent evaluation system for tool-using agents. The repository currently documents and implements:

- a reproducible 140-task benchmark;
- deterministic sandbox state and per-task authorization;
- structured execution traces and failure taxonomy;
- deterministic verification and replay;
- public Reliability Record / evidence-loop concepts;
- external verification and submission workflows;
- explicit separation of provider/runtime failure from agent behavior;
- runtime reliability findings with reproducibility and evidence boundaries;
- a proposed external design-partner / paid reliability-review path.

These are documented publicly in the repository README and linked evidence documents.

## Research programme: first 90 days

### Workstream 1 — Cross-runtime evidence admission

Validate whether traces from independent runtimes can be normalized into a common Reliability Record without hiding runtime-specific semantics.

Initial targets should be chosen from real, independently observable runtimes rather than synthetic adapters alone.

### Workstream 2 — Completion-truth boundary

Define and test the minimum evidence chain required for increasingly strong completion claims:

```text
code candidate
→ test execution
→ artifact
→ published artifact identity
→ installed artifact
→ target environment
→ runtime execution
→ terminal state
→ qualification result
```

The goal is not to make verification unnecessarily expensive; it is to identify which evidence boundary is authoritative for each claim.

### Workstream 3 — Failure corpus

Collect externally reproducible failures that expose mismatches between:

- claimed success vs actual state;
- hosted-green vs deployed behavior;
- successful tool invocation vs intended state change;
- retry behavior vs duplicate side effects;
- partial completion vs authoritative completion;
- provider/runtime error vs agent error.

Each case should preserve explicit evidence boundaries and remain falsifiable.

### Workstream 4 — Independent admission

Measure whether a third party can take a submitted trace/evidence packet and independently determine:

1. what the agent attempted;
2. what the environment actually did;
3. which evidence supports the outcome claim;
4. which claims remain unproven;
5. whether the record is reproducible.

## Falsifiable outcomes

The project succeeds only if external evidence shows that the proposed layer is useful.

Useful negative results are explicitly acceptable. We will publish when:

- a trace cannot be normalized reliably;
- a proposed evidence field is insufficient;
- an admission rule produces false confidence;
- runtime-specific semantics break comparability;
- a lower-cost evidence boundary proves equally authoritative.

## Deliverables

Within an initial 90-day research cycle:

1. **Cross-runtime Reliability Record specification** — versioned schema and admission rules.
2. **Public failure corpus** — independently reproducible reliability failures with evidence boundaries.
3. **External runtime studies** — real traces from multiple runtimes where access is available.
4. **Verification toolkit** — minimal tooling for third parties to inspect and validate evidence packets.
5. **Research report** — what can and cannot be established from execution traces.
6. **Open benchmark updates** — new tasks derived from externally observed failure modes rather than invented failure categories.

## Funding request

### Initial research sponsorship target

**US$5,000–10,000** for a focused evidence-building phase.

The requested support is intended primarily for direct research bottlenecks such as:

- compute / API usage required for reproducible runtime studies;
- hosting and evidence infrastructure;
- access to research resources / datasets;
- travel or collaboration costs directly tied to obtaining independent runtime evidence;
- targeted external testing and reproduction work.

The project should not be presented as guaranteed commercial success. The purpose of the first sponsorship is to increase the amount and quality of independently verifiable evidence.

## Why this matters

As agents move from generating text to taking actions, the cost of false completion can move from a bad answer to a bad state transition, a failed deployment, a duplicated transaction, an unauthorized action, or a silent operational failure.

A trustworthy agent ecosystem therefore needs a way to distinguish:

**“the model said it succeeded”**

from

**“the execution produced independently verifiable evidence of success.”**

SABLE investigates the missing layer between those two claims.

## Funding fit

This proposal is intentionally compatible with multiple funding routes:

- **Open research sponsorship:** support a focused 90-day evidence programme.
- **Public-interest grants:** fund specific research bottlenecks and outputs.
- **Strategic partnerships:** provide real runtime traces, failure cases, or reproduction opportunities.
- **Larger R&D programmes:** scale the evidence layer after initial independent validation.

This document does not imply eligibility for any particular programme. Each funder should be evaluated against its current eligibility, geography, legal, and thematic requirements.

## Reality standard

SABLE will not count any of the following as evidence of market or research impact by themselves:

- GitHub activity;
- repository size;
- architecture diagrams;
- self-authored benchmarks without external confirmation;
- social engagement without substantive use;
- unverified claims of adoption.

Priority evidence is:

**external trace → independent reproduction → repeated use → research collaboration → funding → paid reliability work → strategic adoption.**

## Contact / collaboration

The project is open to maintainers, runtime teams, evaluators, researchers, reliability engineers, and funders who can contribute real execution traces, failure cases, reproduction capacity, or research support.
