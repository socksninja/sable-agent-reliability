# ARIA Scaling Trust — Track 2 Concept Paper v0.1

**Applicant:** Tang Yuanlong / Independent Researcher
**Project:** SABLE — Cross-Runtime Agent Execution Evidence and Verification Layer
**Track:** Track 2 — Tooling
**Status:** pre-application concept paper; not yet submitted
**Target batch:** 31 October 2026, 14:00 GMT

## 1. One-sentence proposition

Build an open-source, runtime-agnostic evidence layer that lets an independent observer verify what an AI agent actually did — not merely what the model or runtime claimed it did — across untrusted environments, retries, external side effects, and multi-step state transitions.

## 2. Why this matters to Scaling Trust

Scaling Trust aims to create infrastructure that lets agents securely coordinate, negotiate and verify on our behalf. Verification is incomplete if a protocol can establish what an agent intended to do but cannot independently establish what execution actually caused in the external world.

SABLE targets this evidence boundary. It binds together four independently inspectable layers:

1. **Intent / requested action** — what the agent was asked or authorized to do.
2. **Execution provenance** — runtime, tool call, process/run identity, commit and immutable artifact references.
3. **Environment truth** — independently observed state or external effect, such as a file hash, ledger entry, API object, database state, or other authoritative state transition.
4. **Verification result** — a reproducible PASS / FAIL / UNKNOWN classification with explicit limitations.

The core hypothesis is that cross-runtime evidence records can make execution claims portable and independently falsifiable without requiring every runtime to adopt a common SDK or trust one vendor's telemetry.

## 3. Research questions

### RQ1 — Completion truth
Can an external verifier distinguish a tool call that returned success from a task that actually produced the intended externally observable state?

### RQ2 — Retry and side-effect truth
Can independently verifiable evidence identify duplicate or missing external effects across retry/recovery paths?

### RQ3 — Provenance portability
Can the same verification contract operate across materially different agent runtimes without changing the runtime's authority model?

### RQ4 — Evidence limits
Which reliability claims can a trace prove, which require independent environment observation, and which must remain UNKNOWN?

## 4. Existing evidence base

The project already has real executions and failure-oriented experiments rather than a purely synthetic benchmark:

- LangGraph execution with runtime trace identity and independently checked environment conditions.
- LangSmith eventual-consistency/readback-gap experiment showing that a submitted execution record and later readback can diverge.
- CrewAI retry experiment using a deterministic local model and an out-of-process side-effect ledger: 30/30 exactly-once in clean and pre-effect cases; 30/30 duplicated effects in the post-effect crash/retry case.
- A provider/runtime-agnostic Reliability Record and external-submission protocol designed to bind run → job → artifact → commit provenance.

These results are preliminary. They motivate the research questions; they are not presented as universal guarantees.

## 5. Proposed open-source capability

### Component A — Reliability Record
A versioned, machine-readable record containing action identity, runtime provenance, evidence references, observed environment state, verification result, and limitations.

### Component B — Independent verifier
A small verifier that does not depend on the agent runtime's own success signal and can reconstruct the evidence chain from public artifacts or controlled private evidence bundles.

### Component C — Cross-runtime adapters
Thin adapters for representative agent runtimes. Adapters preserve native provenance rather than replacing it.

### Component D — Failure corpus
A public corpus of reproducible reliability failures: false success, state drift, retry replay, partial success, stale readback, and authority/evidence discontinuity.

### Component E — Evidence boundary specification
A public specification describing what execution traces establish, what requires independent environmental observation, and when the correct result is UNKNOWN.

## 6. Adversarial evaluation plan

The tooling will be deliberately tested against hostile and ambiguous conditions:

- runtime reports success while environment state is unchanged;
- crash after external effect but before acknowledgement;
- retry after an uncertain effect boundary;
- stale or eventually consistent readback;
- missing or tampered provenance;
- partially completed multi-step actions;
- disagreement between runtime trace and authoritative external state.

Success is not defined as a high benchmark score. The core success criterion is whether an independent reviewer can reconstruct and falsify the claimed execution outcome.

## 7. External adoption pathway

The project will prioritize interoperability and external challenge over self-certification.

Target users and collaborators include agent runtimes, observability platforms, evaluation teams, security researchers, and operators of agents that produce real external effects. A first external run is intentionally bounded to one real workflow and one reliability question.

The project is designed so that a runtime can participate without changing its core SDK or endorsing SABLE. This lowers the adoption barrier while preserving the independent verification question.

## 8. UK contribution

The applicant is currently an independent researcher outside the UK. Because ARIA states that non-UK funding can be awarded where it increases net programme impact in the UK, the project should create explicit UK-facing commitments rather than assume eligibility.

Proposed commitments, subject to ARIA guidance and award terms:

- publish the verifier, evidence schema and failure corpus openly;
- collaborate with UK-based researchers or engineering teams working on AI security, multi-agent systems, verification, or evaluation;
- make the project and evidence corpus available for use in the Scaling Trust Arena and related ARIA projects where technically appropriate;
- participate in ARIA community activities and cross-project evaluation;
- document lessons from external deployments in a form reusable by UK researchers and companies.

## 9. Milestones

### Phase 1 — Evidence contract (months 0–3)
- freeze v1 Reliability Record specification;
- release independent verifier;
- reproduce at least three failure classes across at least two runtimes;
- publish the evidence-boundary report.

### Phase 2 — External interoperability (months 3–6)
- obtain at least three independently maintained external runtime executions;
- run adversarial verification against public/private evidence bundles;
- publish a cross-runtime failure corpus and verification results;
- document limitations and UNKNOWN cases.

### Phase 3 — Scaling Trust integration surface (months 6–12)
- provide a reusable verification component suitable for multi-agent coordination experiments;
- test how execution evidence interacts with authorization, negotiation, and external-effect boundaries;
- establish a public interoperability pathway for researchers and tool builders;
- produce a research report identifying which evidence primitives appear robust enough to support higher-level trust protocols.

## 10. Falsifiable success criteria

The project should be considered unsuccessful or substantially revised if:

- independent observers cannot reproduce the verification result from the published evidence;
- runtime-specific assumptions dominate the verifier and prevent cross-runtime use;
- authoritative environment observations do not add meaningful information beyond agent/runtime claims;
- the proposed record can be manipulated without detection through a realistic provenance or state-divergence attack.

A negative result is valuable if it identifies a boundary where execution evidence cannot support a claimed trust guarantee.

## 11. Requested support — planning range

This concept is intentionally not a final budget. A detailed budget should be derived from ARIA's application fields and project scope.

A credible initial planning range is **£200k–£400k for 9–12 months**, prioritizing:

- full-time research/engineering effort;
- secure execution and evidence infrastructure;
- controlled compute/API/runtime access;
- external reproduction and collaboration;
- travel/community participation where directly tied to UK collaboration and ARIA programme integration;
- independent security/reliability review.

The project should avoid spending heavily on generic product infrastructure before external evidence demonstrates the need.

## 12. Why SABLE rather than another benchmark

SABLE is deliberately positioned below benchmark-specific scoring and above raw runtime telemetry.

The unit of value is not another leaderboard number. It is a **portable, independently challengeable statement about what actually happened during an agent execution**.

That distinction matters for multi-agent coordination because negotiated intent, authorization, runtime execution, and external effect can occur in different systems owned by different parties. A trust protocol needs evidence that can cross those boundaries.

## 13. Current external-state ledger

As of 16 September 2026:

- SABLE has public real-runtime evidence from multiple runtime paths.
- An independent Crashpoint experiment demonstrates a concrete retry/duplicate-side-effect failure mode, with deterministic local-model limitations preserved.
- The generic external admission path exists.
- The first independently maintained SABLE-native external submission is still **not achieved**.
- The Agent Evaluation Science extended abstract is prepared; OpenReview account activation is pending.
- This ARIA concept is a **draft**, not a submitted proposal.

The next reality gates are therefore: external SABLE-native execution, OpenReview submission receipt, ARIA proposal submission, and first stranger payment.

## 14. Decision rule

No additional SABLE core complexity should be added solely to improve this proposal. New engineering is justified only when an external test, collaborator, applicant requirement, or runtime deployment demonstrates a missing capability.
