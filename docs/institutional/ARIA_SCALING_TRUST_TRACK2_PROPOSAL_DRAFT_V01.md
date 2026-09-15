# ARIA Scaling Trust — Track 2 Proposal Draft v0.1

## Working title

**Verifiable Execution Evidence for AI Agents in Untrusted Environments**

## Applicant

Tang Yuanlong (唐袁隆) — Independent Researcher / Independent AI Builder

## Track

Track 2 — Tooling

## Core proposition

AI agents increasingly act across tools, runtimes, APIs, filesystems, browsers, and other external environments. Existing agent traces can show that a runtime emitted an action or reported success, but they do not necessarily establish that the intended external state transition actually occurred.

SABLE proposes an open-source, runtime-agnostic evidence layer that binds an agent execution identity to independently observable effects and provenance. The core output is a machine-readable reliability record that distinguishes:

1. what the agent/runtime claimed;
2. what execution evidence exists;
3. what external state can be independently observed;
4. whether the claimed effect is supported, contradicted, or unobservable.

The project is not a replacement for agent runtimes, observability vendors, or evaluation benchmarks. It is a reusable verification primitive intended to make evidence portable across them.

## Why this matters to Scaling Trust

Scaling Trust seeks open-source coordination infrastructure and verification capabilities for agents operating in untrusted environments. A reusable evidence layer can provide a common boundary for verifying whether an agent action actually produced the state transition it claims, especially around retries, recovery, delegation, external side effects, and partial failure.

The proposed tooling targets a concrete infrastructure gap: **execution telemetry is not the same thing as independently verifiable execution truth.**

## Research/tooling questions

### Q1 — Execution truth
Can a runtime-independent verifier determine whether a claimed agent action produced the intended external effect without trusting the agent's terminal claim?

### Q2 — Provenance
Can evidence be bound strongly enough to an execution identity, source commit, workflow run, artifact, and observed state that an independent observer can reconstruct the provenance chain?

### Q3 — Failure classification
Can the same evidence contract classify recurring cross-runtime failure modes such as false success, state drift, retry duplication, partial success, and ambiguous termination?

### Q4 — Interoperability
Can the evidence boundary sit across existing runtimes and observability standards without requiring each runtime to adopt a new benchmark or proprietary storage system?

## Existing evidence base

The work is grounded in real execution rather than synthetic benchmark claims.

- LangGraph / LangSmith: controlled execution experiments exposed an evidence-visibility/readback gap between accepted trace writes and independently readable exact-run evidence.
- CrewAI: controlled retry experiments demonstrated 30/30 exactly-once outcomes for clean/pre-effect cases and 30/30 duplicated effects for post-effect retry cases under a deterministic local runtime, with limitations explicitly preserved.
- Cross-runtime external incidents: public reports involving false-success and detached-liveness patterns motivate portable verification contracts, but are not counted as SABLE-native executions without inspectable evidence.
- SABLE v0.9: a public Reliability Record / evidence admission protocol that binds runtime evidence to GitHub run/job/artifact/commit provenance and exposes explicit structural and reachability states.

## Proposed work programme: 6–12 months

### Workstream 1 — Evidence protocol
Stabilise a minimal open specification for execution identity, claimed outcome, effect reference, observed state, provenance, limitations, and verifier result.

### Workstream 2 — Cross-runtime implementations
Validate the protocol on multiple agent runtimes with intentionally small, real executions. Prioritise retries, external side effects, durable resume, and state-transition verification.

### Workstream 3 — Independent verifier
Maintain a lightweight verifier that can reconstruct provenance and compare runtime claims against independently observable state without requiring access to private chain-of-thought or proprietary internal state.

### Workstream 4 — Failure corpus
Build a public corpus of reproducible reliability failures and ambiguous cases. Failed or UNKNOWN outcomes are first-class evidence rather than being discarded.

### Workstream 5 — Standards interoperability
Test the evidence model against OpenTelemetry GenAI semantic conventions and other emerging observability/evaluation systems. The goal is to identify what existing telemetry can prove, what it cannot, and what minimum additional evidence boundary is required.

### Workstream 6 — External challenge
Invite independent runtime maintainers, evaluation researchers, and operators to reproduce, falsify, or break the evidence model. A negative result is considered a successful research outcome if it identifies a boundary the protocol cannot currently establish.

## Milestones

### M1 — Evidence contract
A reviewed versioned protocol and verifier with a public conformance fixture.

### M2 — Independent executions
At least 3 genuinely external SABLE-native executions across distinct runtime families.

### M3 — Reproducible failure corpus
At least 3 independently inspectable failure cases spanning different runtime mechanisms.

### M4 — Standards cross-validation
At least one interoperability experiment with an observability/standards community, documenting what the existing semantic layer can and cannot establish.

### M5 — External challenge
At least one independent contributor attempts to falsify or break the protocol, with the outcome published regardless of whether the protocol survives.

## Success criteria

The project succeeds if it produces a reusable open-source verification primitive that independent operators can use without adopting a proprietary evaluation platform, and if the resulting evidence changes the level of confidence that can be placed in agent-reported success.

Quantitative targets:

- >= 3 external runtime executions;
- >= 1 independently promoted reliability record;
- >= 3 reproducible public failure/ambiguity cases;
- >= 1 standards interoperability study;
- >= 1 independent falsification attempt;
- all claims linked to inspectable public provenance where disclosure permits.

## Why this is open-source infrastructure

The verifier, record schema, fixtures, adapters, and reference implementations will be published under an open-source licence. The goal is to allow runtime vendors, observability systems, evaluators, enterprises, and researchers to use the same evidence boundary without a central authority controlling the underlying execution data.

## Risks and falsifiability

The core hypothesis may be wrong or narrower than expected. Examples of failure:

- some classes of external effects cannot be independently reconstructed from available telemetry;
- provenance links may be forgeable or insufficient under realistic adversaries;
- existing OpenTelemetry semantics may already cover the relevant evidence boundary;
- runtime-specific execution models may prevent a useful cross-runtime abstraction.

The programme explicitly records such failures and narrows the claim rather than converting them into marketing evidence.

## Applicant position

The project is currently maintained as an independent open-source research effort. The applicant is seeking collaborators and institutional support specifically to obtain independent executions, targeted reproductions, infrastructure, and standards-level validation. No affiliation with a university or company is claimed.

## Funding use

Requested support would primarily fund:

- compute/API usage for controlled cross-runtime experiments;
- hosting and public evidence infrastructure;
- targeted reproductions with real runtime versions;
- contributor/research collaboration;
- standards and research engagement;
- travel or presentation only where directly tied to evidence acquisition and collaboration.

A detailed budget will be matched to ARIA's application limits and evaluation requirements before submission.

## Non-goals

This project does not seek to:

- replace existing agent runtimes;
- define a universal benchmark score;
- require adoption of SABLE by runtime vendors;
- collect private customer traces by default;
- infer reliability from model text alone;
- claim that every external effect can be verified.

## Current public artefacts

Repository: https://github.com/socksninja/sable-agent-reliability

OpenTelemetry conformance fixture: `docs/OTEL_EXTERNAL_EFFECT_CONFORMANCE_V01.md`

External submission starter: `examples/external-submission-starter/`

External experiment adapters and evidence verifiers are maintained in the repository with provenance and limitations preserved.

## Application strategy note

This draft is intentionally a research/tooling programme rather than a product pitch. Before submission, map every section to the current ARIA call-for-proposals wording, programme thesis, eligibility, budget requirements, team expectations, IP terms, and any updated areas of interest.