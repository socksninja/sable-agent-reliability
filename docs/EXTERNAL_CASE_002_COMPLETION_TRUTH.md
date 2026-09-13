# SABLE External Case 002 — Completion / deployment truth boundaries

**Status:** EXTERNAL OBSERVATION / NOT BENCHMARK-ADMITTED

**Purpose:** capture a recurring reliability boundary visible across independently maintained systems: a hosted/local/test surface can report success while the exact artifact, installed revision, target environment, or terminal state is not yet proven. This document turns that boundary into a SABLE validation target without claiming reproduction, adoption, or verification that has not occurred.

## External signals

### A — Environment Studio: publishable locally, external work-machine qualification pending

Environment Studio `timaday/environment-studio#9` / PR #12 reports a PostgreSQL 16.11-only pilot candidate with extensive local evidence: backend and frontend suites, repository guards, Docker-backed PostgreSQL 16.11 witness tests, runtime image build, protected-container smoke, and browser-check Docker target all passed.

The project explicitly keeps the remaining boundary separate:

```text
local tests / Docker witness
→ runtime image
→ merge
→ GHCR publication
→ HiveForge pull/deploy
→ work-machine PostgreSQL 16.11 observation
```

The external deployment stages were not claimed as complete by the candidate report.

### B — Chase Sets: hosted green does not establish canonical/exact-head/pilot truth

Public delivery reporting in `chase-sets/chase-sets#4388` records a stronger form of the same boundary. Hosted execution remained green while a canonical local F2 remained outside its threshold (`4700.6502ms > 4500`). The delivery chain also requires serial progression through exact reviewed installs, and a partial `31/44` battery is explicitly not treated as a completed `44/44` run.

The report additionally preserves `INCONCLUSIVE` / `NOT_RUN` rather than treating an expired review window as a successful or failed execution, and distinguishes a repaired head from the still-owed exact-head install reconciliation.

## Reliability class

The shared failure class is:

```text
completion / deployment truth gap
```

Representative subtypes:

- `hosted_green_not_canonical_green`
- `artifact_published_not_target_environment_qualified`
- `exact_head_install_drift`
- `partial_battery_false_completion`
- `inconclusive_as_success`
- `repair_verified_but_not_installed`

These are not model-quality failures. They are failures of **authoritative execution-state semantics** and **evidence provenance**.

## SABLE question

Can an independent observer determine, from machine-checkable evidence, what the system is actually entitled to claim?

A reliability check should distinguish at least:

```text
code candidate
→ test execution
→ produced artifact
→ published artifact identity
→ installed artifact identity
→ target environment
→ runtime execution
→ terminal state
→ qualification result
```

A green result at one stage MUST NOT automatically authorize a green claim at a later stage.

## Minimal oracle

For each claimed completion, capture:

1. **Identity** — exact commit, artifact digest, or install revision.
2. **Environment** — runtime/client/database/OS constraints relevant to the claim.
3. **Execution receipt** — what actually ran and when.
4. **Terminal state** — independently observable success/failure/unknown.
5. **Scope** — exactly which battery/tests/paths completed.
6. **Uncertainty** — explicit `INCONCLUSIVE` / `NOT_RUN` where evidence is missing.

The oracle should reject claims such as:

```text
"CI is green"        → "production is qualified"
"repair tests pass"  → "fixed revision is installed"
"31/44 pass"         → "battery passed"
"timeout window ended" → "no failure occurred"
```

## Admission gate

This case becomes benchmark-admitted only after an independent runtime or project maintainer supplies an inspectable execution chain closing:

```text
exact artifact/revision
→ actual install
→ actual target-environment execution
→ independently observable terminal state
→ inspectable receipt
→ bounded claim scope
```

Until then, this is an external-case targeting artifact, not SABLE reproduction or adoption.

## Strategic value

This class generalizes SABLE beyond individual tool-call mistakes. The deeper reliability question is:

> **When may an automated system legitimately say DONE?**

The answer requires provenance across code, artifact, installation, execution, and terminal state. That makes completion truth a first-class reliability surface rather than a presentation-layer concern.
