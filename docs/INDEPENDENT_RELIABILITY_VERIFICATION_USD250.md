# Independent Reliability Verification — US$250 Fixed Scope

> **A bounded, independent test of one concrete AI-agent reliability claim.**

**Price: US$250 one-time**  
**Scope: one reliability question, one bounded verification cycle, one evidence package.**

SABLE provides an external verification service for teams that need to know whether a specific agent workflow, runtime behavior, or execution claim can be independently supported by evidence.

## What this service answers

Bring one concrete question such as:

- Did this agent actually complete the requested state transition?
- Did a retry or replay duplicate an external action?
- Did checkpoint recovery preserve the correct result-to-request association?
- Did an error get swallowed or silently converted into a fallback outcome?
- Does the published trace actually support the claimed result?

The goal is a **bounded engineering verdict**, not a broad certification.

## Included

1. **Claim definition**  
   We turn the reported reliability concern into one explicit, testable claim.

2. **Pinned execution boundary**  
   We record the relevant repository, version/revision, runtime boundary, and reproducibility assumptions.

3. **Bounded reproduction / verification**  
   We run or reproduce the smallest useful deterministic case in an isolated environment.

4. **Independent outcome check**  
   We check the claimed result against observable state, trace data, side effects, or another independently readable evidence source rather than trusting the agent's final message.

5. **Raw evidence package**  
   The returned package contains the relevant execution evidence needed to inspect the result.

6. **SHA-256 evidence digest**  
   The final evidence bundle is accompanied by an integrity digest.

7. **Scoped verdict**  
   The result is reported as **VERIFIED**, **NOT VERIFIED**, or **EVIDENCE GAP**, with explicit limits.

8. **One-page findings report**  
   A concise report states what was tested, what was observed, what the evidence proves, and what remains unknown.

## What you receive

- Reproduction / non-reproduction result
- Evidence boundary
- Relevant runtime and source identity
- Raw evidence reference
- SHA-256 digest
- Scoped verdict
- Concise engineering report

## What is not included

This fixed scope does **not** include:

- production credentials;
- full-system integration;
- framework patching;
- ongoing maintenance;
- security certification;
- production-wide reliability claims;
- a guarantee that unrelated failure modes do not exist.

If the bounded experiment exposes a separate engineering problem, remediation can be scoped independently.

## Buyer-provided input

A customer normally provides one of the following:

- a public issue or incident;
- a minimal reproducer;
- a trace or execution receipt;
- a redacted execution artifact;
- or a short description of the workflow and expected terminal state.

No proprietary production data is required when the issue can be reduced to a safe synthetic reproducer.

## Evidence standard

SABLE treats the execution environment as the judge.

A useful evidence chain is:

```
claim
  ↓
execution identity
  ↓
observable execution
  ↓
independent state/effect check
  ↓
evidence bundle
  ↓
scoped verdict
```

A successful model response is not by itself treated as proof of successful execution.

## Public evidence and track record

The SABLE repository contains reproducible reliability work and public evidence records, including:

- [Sample external agent reliability audit](SAMPLE_EXTERNAL_AUDIT_V01.md)
- [US$25 Evidence Snapshot](EVIDENCE_SNAPSHOT_USD25.md)
- [External Reliability Record Submission Protocol](EXTERNAL_RELIABILITY_RECORD_SUBMISSION_V0.1.md)
- [Reliability Review Offer](RELIABILITY_REVIEW_OFFER_V01.md)

Repository: <https://github.com/socksninja/sable-agent-reliability>

## How to start

Send:

```
URL or reproducer
+
one concrete reliability question
+
public/private evidence boundary
```

The first engagement remains bounded to the stated claim and evidence boundary.

## Payment

**US$250 fixed, one-time fee.**

Payment is handled through PayPal. The active checkout link is supplied with the assignment/payment request.

---

**SABLE — Agent Reliability Evidence Layer**  
Independent verification of concrete execution claims, with explicit evidence boundaries.
