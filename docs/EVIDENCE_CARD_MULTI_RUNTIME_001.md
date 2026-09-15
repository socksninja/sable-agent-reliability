# SABLE Multi-Runtime Evidence Card — 001

## Why this matters
The evidence boundary is no longer tied to one runtime. SABLE now has reproducible third-party runtime executions that pass the existing v0.9 submission/evaluation path.

## LangGraph
- Runtime version: `1.2.11`
- GitHub Actions run: https://github.com/socksninja/sable-agent-reliability/actions/runs/34979126994
- Capture ID: `langgraph-6c4a373140024c8a9ea6a0ba49e0eae1`
- Task success: `true`
- SABLE v0.5 evaluation: `task_pass=1`, `pass_rate=1.0`
- Replay match rate: `1.0`
- Final-state hash: `937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354`
- Artifact: https://github.com/socksninja/sable-agent-reliability/actions/runs/34979126994/artifacts/10401010595

## CrewAI
- Runtime version: `1.15.21`
- GitHub Actions run: https://github.com/socksninja/sable-agent-reliability/actions/runs/34979126995
- Runtime trace ID: `crewai-5255ee89-97b9-4396-84c8-fb711e069ee6`
- Task success: `true`
- SABLE v0.5 evaluation: `task_pass=1`, `pass_rate=1.0`
- Replay match rate: `1.0`
- Final-state hash: `937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354`
- Artifact: https://github.com/socksninja/sable-agent-reliability/actions/runs/34979126995/artifacts/10400517799

## Langfuse reference
- Real public execution: https://github.com/socksninja/sable-agent-reliability/actions/runs/34971496689
- Trace ID: `fad2a88e996225507b7a21d61962fe94`
- External effect: https://github.com/socksninja/sable-agent-reliability/issues/63#issuecomment-5681069014
- Final-state SHA-256: `042b4ff60584f4c263c3bd644ae14c2ba63edd528e9ac0b9845c04c5a6791ad0`

## Current proof surface
`runtime execution -> trace/evidence -> SABLE normalization -> replay -> independently readable state`

## Next hard test
Use the same harmless external effect under a second observability backend, then run a production-like tool action supplied by an external design partner.
