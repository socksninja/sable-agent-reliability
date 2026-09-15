# SABLE: Verified Execution → Permission

SABLE turns agent execution evidence into a machine-readable permission decision.

## Core path

```text
Agent Runtime
    ↓
Observed tool execution
    ↓
Sandbox state + state hashes
    ↓
SABLE v0.9 provenance/integrity validation
    ↓
SABLE v0.5 deterministic evaluation + replay
    ↓
Permission Gate
    ↓
ALLOW / DENY
```

## Permission contract

The current protocol is `sable.permission.v0.1`.

`ALLOW` requires all of the following:

- environment state reaches the task target
- at least one observed tool execution exists
- execution terminates normally
- native tool calling is attested
- tool results are observed by the sandbox
- tool-result control is not delegated to the agent
- every observed step succeeds
- every observed step preserves a post-action state hash
- evaluation pass rate is 1.0 when an evaluation report is supplied
- replay match rate is 1.0 when an evaluation report is supplied

Anything else produces `DENY` with machine-readable reasons.

## Live runtime proof

The OpenAI Agents SDK integration runs a real `Runner`-managed agent loop against OpenRouter, executes a native inventory function tool against `SABLEEnvironment`, emits a v0.9 submission, and feeds the normalized result into deterministic evaluation and replay.

The integration evidence class is intentionally `third_party_framework_runtime`: it proves a real framework/runtime integration, but it does not claim independently sourced agent provenance.

## Why this matters

The value proposition is not “better logs”. It is a decision boundary:

```text
unverified execution → DENY
verified execution   → ALLOW
```

That boundary can later sit in front of higher-consequence actions such as payments, production changes, credentials, deployments, or other policy-controlled operations.

## Current scope

This is a protocol prototype and evaluation artifact, not a production authorization system. The next engineering steps are stronger provenance, adversarial denial tests, multiple independent runtimes, and integration with a real policy/authorization layer.
