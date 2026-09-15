# Real Langfuse execution — required external credential

The workflow `.github/workflows/langfuse-real-execution.yml` is intentionally fail-closed.
It will not create a GitHub world-state effect unless the same run is actually instrumented by Langfuse.

## Required repository Actions secrets

Add these three repository secrets under GitHub → Settings → Secrets and variables → Actions:

- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_BASE_URL` (normally `https://cloud.langfuse.com` for the EU region)

The first two are the Langfuse project credentials. Do not put them in source control or issue comments.

## What the workflow proves

1. A GitHub Actions runner executes `sable_langfuse_execution.py` with Langfuse Python SDK v4.
2. The runner creates a deterministic Langfuse trace ID derived from repository/run/commit identity.
3. Inside the trace, a tool span creates one harmless public GitHub issue comment on SABLE issue #63.
4. The runner reads that comment back through the GitHub API and hashes the authoritative final state.
5. The workflow publishes a `sable.reliability_record.v0.9` artifact containing the Langfuse trace URL, GitHub effect URL, execution identity, and final-state hash.
6. The Langfuse trace is marked public so an independent verifier can inspect the telemetry without project membership.

The resulting evidence boundary is:

`real execution → Langfuse/OTel trace → external GitHub effect → independently readable final state → SABLE Reliability Record`

No claim of a real Langfuse execution should be made until the workflow produces the artifact and the public trace URL.
