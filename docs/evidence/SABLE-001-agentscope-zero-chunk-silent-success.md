# SABLE-001 — AgentScope zero-chunk silent success

**Status:** CONFIRMED upstream; independently code-path verified; dynamic SABLE replay pending.

**Failure class:** silent success / false success / recovery bypass

**Upstream:** `agentscope-ai/agentscope-java#2962`

**Upstream report:** https://github.com/agentscope-ai/agentscope-java/issues/2962

## Claim under test

A model/gateway response can return HTTP 200 and then terminate its streaming response with **zero content-bearing chunks**. The AgentScope-Java runtime can treat that empty stream as a normal completion instead of surfacing an error.

Expected reliability behavior: empty model completion should become an explicit failure signal so retry/fallback logic can engage.

## Independent verification of the failure path

Verified against AgentScope-Java `main` at commit `39cd304a7dc400eb3fb2a7daca750162e79bec05`:

1. `ModelUtils.applyTimeoutAndRetry(...)` applies timeout and retry operators, but retry is error-driven and there is no empty-stream detection before `retryWhen`.
2. `ReasoningContext.buildFinalMessage()` returns `null` when no text, thinking, or tool-call content has been accumulated.
3. `ReActAgent` uses `Mono.justOrEmpty(finalMsg)`, so a null final message becomes an empty Mono and the downstream post-reasoning path is skipped.
4. The production issue report gives a concrete zero-chunk reproduction using an OpenAI-compatible stub returning `data: [DONE]` and states that the run completes without assistant message, error, retry, or fallback.
5. An AgentScope maintainer evaluation independently marked the issue **Confirmed / high severity** and stated that all five causal steps still hold on `main` at the same commit.

## Why this is SABLE-relevant

This is exactly the reliability boundary SABLE is designed to measure:

> **Agent/runtime says success; externally observable execution did not produce a valid completion.**

The interesting failure is not model quality. It is the mismatch between:

`transport outcome -> runtime signal -> retry/fallback -> agent-visible outcome -> persisted state`

A conventional task-success metric can miss this because the run terminates without a hard error.

## Reproduction status

### A. Public, deterministic reproduction

The upstream report provides this minimal reproduction shape:

- point `OpenAIChatModel` to a stub endpoint;
- return HTTP 200 with `data: [DONE]` and no content chunks;
- call the ReAct agent;
- observe normal completion with no assistant message and no error/retry/fallback.

### B. Dynamic SABLE replay

**Pending:** run the exact failure through SABLE's execution/evidence harness and capture the resulting trajectory + final state + reliability verdict.

This record deliberately does **not** claim that B has already been executed.

## Evidence links

- Upstream bug: https://github.com/agentscope-ai/agentscope-java/issues/2962
- SABLE Open Challenge #001: https://github.com/socksninja/sable-agent-reliability/issues/42
- AgentScope `ModelUtils.java`: https://github.com/agentscope-ai/agentscope-java/blob/39cd304a7dc400eb3fb2a7daca750162e79bec05/agentscope-core/src/main/java/io/agentscope/core/model/ModelUtils.java
- AgentScope `ReasoningContext.java`: https://github.com/agentscope-ai/agentscope-java/blob/39cd304a7dc400eb3fb2a7daca750162e79bec05/agentscope-core/src/main/java/io/agentscope/core/agent/accumulator/ReasoningContext.java

## SABLE verdict

**Failure type:** silent success

**Observed risk:** transient upstream/model-gateway anomaly is converted into a normal-looking empty agent completion, bypassing the defenses that are supposed to recover from the anomaly.

**SABLE value:** high — this is a concrete, externally reported production failure that can be expressed as an execution-level reliability invariant and independently replayed.
