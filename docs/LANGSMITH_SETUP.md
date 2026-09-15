# LangSmith setup

Create a dedicated LangSmith project for the SABLE reality test and add these GitHub Actions repository secrets:

- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`

The workflow also sets `LANGSMITH_TRACING=true` and uses the standard GitHub Actions token only for the harmless external effect/readback.

Do not put keys in source files, issues, PRs, or the artifact.

After secrets are present, rerun or update a pull request touching `integrations/langsmith/**` to execute `.github/workflows/langsmith-second-backend.yml`.
