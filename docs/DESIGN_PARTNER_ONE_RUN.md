# Design Partner: one real agent execution

## The ask

Run one harmless agent/tool execution in your own environment and submit the resulting evidence. Do not send credentials, private traces, customer data, or secrets.

## Minimum evidence

1. Runtime/framework identity and version.
2. One real task execution.
3. The externally observable effect or authoritative final state.
4. A machine-readable trace/submission artifact.
5. The exact commit/run/job/artifact provenance when executed in GitHub Actions.

## Fastest path

Use any runtime you already operate (LangGraph, CrewAI, OpenAI Agents SDK, AgentScope, or another runtime). The only requirement is that the final state is independently readable outside the model's own claim.

Prepare a JSON object using the SABLE Reliability Record schema and open a PR under `submissions/`. SABLE CI performs structural and provenance checks; maintainers retain the final evidence-promotion decision.

Submission spec:
`docs/EXTERNAL_RELIABILITY_RECORD_SUBMISSION_V0.1.md`

## Ten-minute reality test

A good first test is deliberately boring: create one issue comment, a test row in a sandbox DB, or another harmless state mutation. The receipt should bind the runtime execution to that external effect and its authoritative final-state hash.
