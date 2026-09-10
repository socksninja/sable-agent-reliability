# SABLE Reliability Matrix v0.1

This matrix compares versioned SABLE Reliability Records using the same corpus contract. It is descriptive evidence, not a general safety ranking.

| Model | Runtime | N | Task success | Native tool calls | Failure rate | Failure signature | Evidence scope |
|---|---|---:|---:|---:|---:|---|---|
| `deterministic-crewai-stub` | `CrewAI 1.15.21` | 1 | 1.000 | 1.000 | 0.000 | `none` | Framework/runtime probe; deterministic local reference LLM |
| `HuggingFaceTB/SmolLM2-135M-Instruct` | `Hugging Face Transformers (PyTorch)` | 4 | 0.000 | 0.000 | 1.000 | `protocol_or_parsing_failure:4` | Observed SABLE result only |
| `Qwen/Qwen2.5-0.5B-Instruct` | `Hugging Face Transformers Serve` | 8 | 0.875 | 1.000 | 0.125 | `constraint_violation:1` | Public pretrained-model observation; not general reliability |

Records included: **3**.

## Reliability Profiles

### deterministic-crewai-stub
- Failure rate: **0.000** (0/1)
- Signature: **none observed**
- Scope: verified framework/runtime integration; deterministic local reference LLM

### HuggingFaceTB/SmolLM2-135M-Instruct
- Failure rate: **1.000** (4/4)
- Signature: **protocol_or_parsing_failure ×4**
- Scope: observed SABLE result only

### Qwen/Qwen2.5-0.5B-Instruct
- Failure rate: **0.125** (1/8)
- Signature: **constraint_violation ×1**
- Scope: public pretrained-model observation; not a production-safety claim

Failure signatures are derived only from explicitly represented task-level outcomes. A framework/runtime probe using a deterministic reference LLM must not be interpreted as independent model evidence.

The matrix becomes more informative as independently executed model/runtime records accumulate under the same corpus and schema.
