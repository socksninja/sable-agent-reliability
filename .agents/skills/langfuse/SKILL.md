---
name: langfuse
description: >-
  Interact with Langfuse and access its documentation: tracing, monitoring, creating datasets, running experiments, and evaluating AI applications. Use for Langfuse observability and AI engineering work.
---

# Langfuse

This skill is vendored from `github.com/langfuse/skills` so repository-aware coding agents can apply the current Langfuse workflow without relying on memory.

## Core principles

1. Documentation first: fetch current Langfuse docs before implementing.
2. Use the latest compatible Langfuse SDK/API unless the application pins another version.
3. Prefer framework integrations over hand-written instrumentation when an integration exists.
4. Every trace should have meaningful input/output, descriptive names, correct observation types, useful hierarchy, and no unnecessary sensitive data.
5. For short-lived scripts and CI jobs, call `langfuse.flush()` before exit.
6. Instrumentation is not complete until a real trace is emitted and then fetched/audited against the current Langfuse best-practices guidance.

## Repository credentials

Use environment variables:

```text
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

Never commit or paste secret keys into source, issues, or chat.

## Python instrumentation

Use `get_client()` and `start_as_current_observation()` so child observations inherit the active context. Use semantic observation types such as `agent`, `tool`, `generation`, `retriever`, or `chain` rather than generic spans when applicable.

Example:

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="agent",
    name="agent-run",
    input={"task": "..."},
) as agent:
    with langfuse.start_as_current_observation(
        as_type="tool",
        name="external-tool-call",
        input={"operation": "..."},
    ) as tool:
        result = do_work()
        tool.update(output={"result": result})
    agent.update(output={"status": "success"})

langfuse.flush()
```

Keep root trace input/output concise and useful to a reviewer. Put run-specific values in metadata rather than observation names. For agent workflows, nest tool calls under the agent observation.

## Verification

After implementing instrumentation:

1. Execute the instrumented path end-to-end.
2. Fetch the newly created trace using the Langfuse CLI/API/SDK.
3. Audit it against `https://langfuse.com/docs/observability/best-practices`.
4. Fix gaps and re-run until the trace is useful and complete.

Source: `github.com/langfuse/skills` (Langfuse Agent Skill).
