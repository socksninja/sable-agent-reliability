# First third-party Agent integration

## Target

Use **LangGraph** as the first runtime-level integration target because the important boundary is framework execution events → SABLE trace, not a specific model provider.

The first real submission must be captured from a running LangGraph application. It must not be hand-authored and must retain the original runtime trace identifier or equivalent provenance identifier.

## Capture contract

The adapter should collect, at minimum:

- task identifier and original user goal;
- agent/runtime name and exact version;
- every tool invocation with tool arguments;
- observed tool result outside the model's control;
- state hash immediately before and after each mutation-capable tool call;
- final environment state/check result;
- agent's claimed status and final report;
- runtime capture timestamp and collector version.

The adapter then wraps the captured trace in `sable.submission.v0.9` and computes `integrity.source_trace_hash` over the exact embedded `trace` object.

## First acceptance run

The first external run should execute one existing SABLE task that requires a real state transition. The minimal evidence package is:

```text
raw-third-party-trace.jsonl
        ↓
adapter / collector
        ↓
submission-v09.jsonl
        ↓
trace_submit_v09.py
        ↓
sable-v05-trace.jsonl
        ↓
sable_v05.py + evidence_v06.py + reliability_score.py
```

Success criteria:

- the validator accepts the envelope;
- the embedded trace hash matches exactly;
- the deterministic evaluator reaches the same environment outcome recorded by the collector;
- provenance identifies the framework/runtime version and capture method;
- no secrets or unrelated personal data enter the public trace.

## Status

The repository currently contains the public v0.9 protocol, schema, validator, CI self-test, and a deterministic fixture. The fixture is explicitly **not** third-party execution evidence.

The remaining external step is a live capture from a real third-party runtime and its submission through this protocol. Until that capture exists, SABLE should describe v0.9 as **protocol-ready**, not as externally validated.
