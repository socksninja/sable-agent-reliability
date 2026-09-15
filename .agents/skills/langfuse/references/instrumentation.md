# Langfuse Observability Reference

This reference is synced from `github.com/langfuse/skills`.

## Baseline

- Check whether the Langfuse SDK/integration is already installed.
- Prefer an official framework integration when one exists.
- Capture model name and token usage for generations.
- Use descriptive, stable observation names.
- Nest multi-step operations correctly.
- Use semantic observation types (`agent`, `tool`, `generation`, `retriever`, `chain`, etc.).
- Exclude or mask sensitive data.
- Explicitly set meaningful trace input/output rather than dumping function arguments.
- Add session/user/feature metadata only when the application actually has those concepts.

## Agent traces

An agent run should normally be an `agent` observation. Tool/API actions should be nested `tool` observations. Do not represent one subagent dispatch twice; when the subagent execution is visible, use the `agent` observation for the execution.

## Verification loop

Instrumentation is only complete after a real execution emits a trace. Fetch that trace and audit it against the current Langfuse best-practices page. Fix gaps and repeat.

For short-lived scripts and CI jobs, call `langfuse.flush()` before process exit.

Current reference: https://langfuse.com/docs/observability/best-practices
