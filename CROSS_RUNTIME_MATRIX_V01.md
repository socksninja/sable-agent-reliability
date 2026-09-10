# SABLE Cross-Runtime Evidence Matrix v0.1

The same SABLE semantic task was executed through two independent third-party agent frameworks and normalized into the same SABLE v0.9 evidence contract.

| Runtime | Version | Task | Verification | Replay | Permission | Final state hash |
|---|---:|---|---|---|---|---|
| LangGraph | 1.2.11 | SABLE-LANGGRAPH-01 | PASS (2/2) | MATCH | ALLOW | `937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354` |
| CrewAI | 1.15.20 | SABLE-CREWAI-01 | PASS (2/2) | MATCH | ALLOW | `937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354` |

## Cross-runtime result

- **Runtime count:** 2
- **Independent framework versions:** 2
- **Common verified final state:** YES
- **Common final state hash:** `937e31b6d17219f92b26fb3c88acae6bf72108396cbd13c291624afa3fbee354`
- **Common permission semantics:** `ALLOW`

## Evidence provenance

### LangGraph
- Framework: LangGraph 1.2.11
- Capture method: `StateGraph.invoke`
- Runtime trace ID: `langgraph-b3c84b0e-e1c1-41d6-84da-c125eab0831a`
- Source trace hash: `5e869a1e1d0ddac8ee52a9324d9de48855856e3d832697d3b73f6a585a9a8967`
- Evidence hash: `cb3cec7635d4636e19655af469becba9097c5251e00865b312f3f14c8f96daa8`

### CrewAI
- Framework: CrewAI 1.15.20
- Capture method: `Crew.kickoff`
- Runtime trace ID: `crewai-8d7814ff-9689-4768-a51b-4e86ea87d5fa`
- Source trace hash: `d198e7eb2676bd3ccebe5ff2ea527cf1c6880ba261dac9b456ea0ebfd2998810`
- Evidence hash: `2bb6a444790e0f921e24a40f2148fd3d1b55682f8e00f9cffbe3c3e2ce408984`

## Claim boundary

This matrix establishes framework interoperability for **two runtime integrations** and convergence on the same verified environment state and permission semantics.

It does **not** by itself establish model-provider diversity, production safety, or independent external customers. The reference agents use deterministic local policies; the value demonstrated here is the runtime-to-evidence boundary.

A separate negative-control run is being treated as unverified until its resulting evidence is committed and independently inspectable in the repository.
