# SABLE Reliability Matrix v0.1

This matrix compares versioned SABLE Reliability Records using the same corpus contract. It is descriptive evidence, not a general safety ranking.

| Model | Runtime | N | Task success | Native tool calls | Model errors | Environment mutations |
|---|---|---:|---:|---:|---:|---:|
| `deterministic-crewai-stub` | `CrewAI 1.15.21` | 1 | 1.000 | 1.000 | 0 | 1 |
| `HuggingFaceTB/SmolLM2-135M-Instruct` | `Hugging Face Transformers (PyTorch)` | 4 | 0.000 | 0.000 | 4 | 0 |
| `Qwen/Qwen2.5-0.5B-Instruct` | `Hugging Face Transformers Serve` | 8 | 0.875 | 1.000 | 0 | 4 |

Records included: **3**.

The matrix becomes more informative as independently executed model/runtime records accumulate under the same corpus and schema.

Important scope note: the CrewAI row is a verified framework/runtime integration using a deterministic local reference LLM; it is not independent model provenance.
