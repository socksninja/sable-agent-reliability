# SABLE-002 ↔ AgentScope-Java PR #3058

Status: **upstream-convergent; independent verification pending**

Updated: 2026-09-14

## Why this matters

SABLE-002 exposes a concrete streaming reliability failure: once partial content has been delivered, retrying the same streaming request can re-subscribe and duplicate already-delivered chunks.

The current AgentScope-Java PR #3058 explicitly adds an emission guard for `ModelUtils.applyTimeoutAndRetry`: streaming retries are allowed before the first `ChatResponse`, then rejected after an emission. This is semantically aligned with SABLE-002.

Upstream PR: https://github.com/agentscope-ai/agentscope-java/pull/3058

## SABLE-002 baseline

Pinned baseline revision:

`39cd304a7dc400eb3fb2a7daca750162e79bec05`

Independent copy-paste reproduction: Issue #49
https://github.com/socksninja/sable-agent-reliability/issues/49

Expected baseline observation:

```text
subscriptions=3
delivered=[Hello, world, Hello, world, Hello, world]
```

Evidence artifact digest:

`sha256:7bf64c6e549ddacebf8de01e1ce0f63c078fec1486bbd347bd70b6d0b3aa5e4`

## Verification target

Run the same SABLE test against the current PR head:

`826495a1237513c079cc7263caeeb5f6e9a23242`

PR branch: `wahllllll:fix/model-retry-null-status`

The useful question is not whether a different test passes. It is whether the exact SABLE-002 failure mechanism is eliminated without suppressing safe retries that occur before any content-bearing stream data is delivered.

## Review nuance

The PR currently describes the guard as occurring after the first `ChatResponse`. Review discussion has raised an important semantic boundary: role-only or empty `ChatResponse` objects may not be equivalent to content-bearing delivery. A production-safe implementation should distinguish transport recovery before meaningful stream content from recovery after content/tool-call deltas have become externally observable.

This distinction is a candidate reliability taxonomy boundary for future SABLE cases.

## Evidence status

- SABLE reproduction on pinned baseline: **confirmed**
- Matching upstream bug reports / fix direction: **confirmed**
- SABLE reproduction against PR #3058 head: **pending execution**
- Independent third-party reproduction of SABLE-002: **pending**
- SABLE adoption by AgentScope: **not claimed**

SABLE does not treat upstream semantic overlap as product adoption. The next evidence step is an independently run baseline or fixed-branch result with an attributable runtime revision/CI URL.