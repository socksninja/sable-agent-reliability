# LangSmith second-backend execution

This integration is intentionally fail-closed. It is designed to run one harmless LangGraph tool execution with LangSmith tracing enabled, then emit a compact SABLE v0.9-compatible receipt linking:

- runtime execution identity
- LangSmith trace URL / run ID
- independently readable GitHub external effect
- authoritative final-state SHA-256

Required environment variables:

- `LANGSMITH_API_KEY`
- `LANGSMITH_TRACING=true`
- `LANGSMITH_PROJECT`
- `GITHUB_TOKEN`

The first run should use a dedicated sandbox project. Do not commit credentials.
