# SABLE Cross-Runtime Evidence Matrix v1.0

This matrix records independently executed runtime integrations normalized through the same SABLE v0.9 submission contract and evaluated against environment state rather than agent self-report.

## Positive verified executions

| Runtime | Version | Task | Trace | Verification | Replay | Permission | Final state hash |
|---|---:|---|---|---|---|---|---|
| LangGraph | 1.2.11 | SABLE-LANGGRAPH-01 | CAPTURED | PASS (2/2) | MATCH | ALLOW | `937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354` |
| CrewAI | 1.15.20 | SABLE-CREWAI-01 | CAPTURED | PASS (2/2) | MATCH | ALLOW | `937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354` |

## Normalization invariants

- Same semantic goal: reserve 3 units of SKU-A without changing total stock.
- Same initial state hash: `5568307329d5e3a4b463a6f4ea1299a61226fc595a36f6dc95bde056c5d6ecec`.
- Same verified final state hash: `937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354`.
- Both runtimes produce native tool execution evidence observed by the SABLE sandbox.
- Both runtimes normalize to `sable.submission.v0.9` and `sable.v0.5`.
- Both runtimes replay to the same final state and receive `ALLOW` under `sable.permission.v0.1`.

## Provenance

### LangGraph
- Runtime trace ID: `langgraph-b3c84b0e-e1c1-41d6-84da-c125eab0831a`
- Source trace hash: `5e869a1e1d0ddac8ee52a9324d9de48855856e3d832697d3b73f6a585a9a8967`
- Evidence hash: `cb3cec7635d4636e19655af469becba9097c5251e00865b312f3f14c8f96daa8`

### CrewAI
- Runtime trace ID: `crewai-8d7814ff-9689-4768-a51b-4e86ea87d5fa`
- Source trace hash: `d198e7eb2676bd3ccebe5ff2ea527cf1c6880ba261dac9b456ea0ebfd2998810`
- Evidence hash: `2bb6a444790e0f921e24a40f2148fd3d1b55682f8e00f9cffbe3c3e2ce408984`

## Negative-control contract

The matrix requires at least one live failed execution before claiming symmetric ALLOW/DENY coverage. A failed runtime execution must satisfy:

`observed tool failure -> environment verification FAIL -> replay MATCH -> permission DENY`

The negative-control implementation exists in CI, but it is not counted as verified here until its resulting evidence is committed and inspectable.

## Claim boundary

This matrix demonstrates cross-runtime interoperability and convergence on a common evidence model for two framework integrations. It does not establish production safety, model-provider diversity, customer adoption, or an economic moat by itself.
