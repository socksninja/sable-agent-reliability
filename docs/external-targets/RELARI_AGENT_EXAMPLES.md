# External Target: Relari Agent Examples

Target repository: https://github.com/relari-ai/agent-examples

## Why this target

This repository already contains agent applications implemented with multiple orchestration frameworks, including LangGraph, CrewAI, and OpenAI Swarm. It also documents verification with Agent Contracts. That makes it a high-fit candidate for comparing **verification of real execution evidence** rather than another synthetic benchmark.

## Smallest possible SABLE integration

The goal is one real task, not a migration and not an endorsement.

1. Pick one existing runnable agent app, preferably `apps/langgraph-fin-agent`.
2. Add `sable_capture_v09.py` from this repository.
3. Wrap one real tool call with:

```python
before = snapshot_environment()
result = real_tool(**args)
after = snapshot_environment()
capture.call("real_tool", args, result, before, after)
```

4. Write `artifacts/submission-v09.jsonl` with the original goal, claimed status, final report, and the real post-execution environment.
5. Add this minimal workflow:

```yaml
name: SABLE External Verification

on:
  workflow_dispatch:

jobs:
  sable:
    uses: socksninja/sable-agent-reliability/.github/workflows/external-verification-reusable.yml@main
    with:
      agent_command: poetry run python src/main.py
```

The command only needs to produce `artifacts/submission-v09.jsonl`; SABLE handles normalization and the evidence manifest.

## What to report

After the run, provide:

- the independent repository URL
- the GitHub Actions run URL
- the runtime/framework name
- the SABLE evidence artifact name

SABLE will then verify that the evidence is reachable and manually review the record.

## Important boundary

Do not use SABLE's own demo or a hand-authored fixture as external evidence. The value of this experiment is an independently maintained agent producing a trace from a real runtime and real environment.

## Source

SABLE 10-minute verification guide:
https://github.com/socksninja/sable-agent-reliability/blob/main/docs/10_MIN_EXTERNAL_VERIFICATION.md
