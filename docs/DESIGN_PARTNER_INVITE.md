# SABLE Design Partner Reality Test

## One-sentence ask
Give SABLE one harmless production-like Agent/tool action that your team currently trusts because telemetry says it succeeded.

## What SABLE does
- capture the runtime execution
- bind the observability trace to the execution
- identify the real external effect
- reread the authoritative final state independently
- emit a compact `sable.reliability_record.v0.9`

## What you do not need to share
- proprietary prompts
- model outputs
- private traces
- production credentials
- customer data

## Success condition
An outside verifier can distinguish:

`runtime reported success` vs `externally evidenced success`

using only stable identifiers, provenance, the external effect reference, and a final-state hash.

## Current proof
- Real run: https://github.com/socksninja/sable-agent-reliability/actions/runs/34971496689
- Real external effect: https://github.com/socksninja/sable-agent-reliability/issues/63#issuecomment-5681069014
- Evidence card: `docs/EVIDENCE_CARD_LANGFUSE_001.md`

## Next step
Start with one side-effect-light action. If the evidence boundary is useful, we then choose the hardest production-relevant scenario together.
