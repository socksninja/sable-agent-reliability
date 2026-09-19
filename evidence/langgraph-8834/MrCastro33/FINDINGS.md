# Independent Verification — LangGraph #8834

**Verdict: VERIFIED** (bounded scope, see limits below)

- Bounty issue: https://github.com/socksninja/sable-agent-reliability/issues/86
- Target issue: https://github.com/langchain-ai/langgraph/issues/8834
- Verifier: `MrCastro33`
- Execution: Codex (OpenAI GPT-6 agent), locally executed
- Run IDs: `fe06486c-134b-4eba-a47b-584cd2563623` (run1), `28f3f714-89a9-47f6-9962-88ca9c0ac748` (run2)
- Evidence digest (run1 `EVIDENCE_8834_VERIFICATION.json`): `2424f7f9a2acf9b8b3e95dc876fe1f18390aa579d6646255eca730c4c7b22f9b`

## Evidence question

> Does the resumed runtime response agree with a fresh external readback of the downstream effect?

**Answer: yes, within this instrumented graph.** In every case the resumed response and the independent readback agree about whether the sink ran. The defect is therefore not a response/state divergence. After a conditional-router exception, the resumed `invoke` returns normally with an empty pending-task list while the selected downstream node never ran. A normal return with no pending work is not evidence of completion.

## Method

- **Isolation.** Each case runs in its own OS process, with its own `thread_id` and (for SqliteSaver) its own checkpoint database. The effects database is shared within a run, with rows separated by case ID. Six cases: failure location `route` / `node` / `none` crossed with `InMemorySaver` / `SqliteSaver`.
- **Durable effect.** The sink node, and only the sink node, commits one row to a separate local SQLite effects database keyed by run ID.
- **Fresh-process readback.** A separate process that never executes graph nodes re-opens the effects database read-only and re-opens the persisted checkpoint for SqliteSaver cases. InMemorySaver checkpoint state is only observed inside the execution process.
- **Controls.** The node-failure and no-failure cases prove the observer detects a real sink effect. A missing database or a failed observer would be an evidence gap, not proof that the sink was skipped.
- **Framework unmodified.** LangGraph source files were hashed, not patched (see `environment.json`).

## Results (identical across two independent runs)

| case | first invoke raised | pending before resume | resume raised | resume value | sink calls | external effect rows | pending after resume | runtime vs readback |
|---|---|---|---|---|---|---|---|---|
| route_memory | yes | [] | no | 1 | 0 | 0 | [] | agree |
| route_sqlite | yes | [] | no | 1 | 0 | 0 | [] | agree |
| node_memory (control) | yes | ["node"] | no | 2 | 1 | 1 | [] | agree |
| node_sqlite (control) | yes | ["node"] | no | 2 | 1 | 1 | [] | agree |
| none_memory (control) | no | [] | no | 2 | 1 | 1 | [] | agree |
| none_sqlite (control) | no | [] | no | 2 | 1 | 1 | [] | agree |

Router call count stays at 1 in the router-failure cases; the router is not re-entered on resume.

Fresh-process readback of `route_sqlite` (see `runs/run1/readback/route_sqlite.json`): persisted checkpoint values `{"value": 1}`, `next: []`, 3 checkpoints in history, and **0 rows** in the effects database. The durable state on disk and the durable effect on disk both confirm the sink never ran, while the runtime reported a clean completion.

Note the control asymmetry that isolates the defect: a **node** failure leaves `pending_before_resume = ["node"]` and the resume retries and reaches the sink; a **router** failure leaves `pending_before_resume = []` and the resume silently finishes with the intermediate state. The node's ordinary write is retained while the routing decision that consumed it is lost.

## Runtime boundary

- `langgraph==1.2.11`, `langgraph-checkpoint==4.2.0`, `langgraph-checkpoint-sqlite==3.1.1`, `langchain-core==1.6.3`, `pydantic==2.13.5`
- Python 3.13.14, macOS 27.0, arm64 (Apple Silicon), SQLite 3.53.1
- SHA-256 of the relevant unmodified LangGraph sources is recorded in `environment.json` (`graph/state.py`, `pregel/_loop.py`, `pregel/_runner.py`, `pregel/main.py`).

## Scope limits

1. Synchronous `StateGraph.invoke` only; async execution was not tested.
2. `InMemorySaver` and `SqliteSaver` only; no other persistence backend was tested.
3. Two-node graph (`node` and `sink`) with one conditional edge; subgraphs, parallel branches, interrupts and retry policies were not tested.
4. No production workload; no frequency or impact estimate in production.
5. Single machine, single OS and Python build, as recorded in `environment.json`.
6. LangGraph source was not modified and no patch is proposed.

## Contents of this package

- `EVIDENCE_8834_VERIFICATION.json` — machine-readable evidence record (run1).
- `runs/run1/MANIFEST.sha256` and `runs/run2/MANIFEST.sha256` — SHA-256 of the original artifacts in each run.
- `PACKAGE.sha256` — SHA-256 of the complete reviewed submission package.
- `harness/` — `verify_8834.py` (orchestrator), `run_case.py` (one case per process), `readback.py` (fresh observer).
- `runs/run1/`, `runs/run2/` — raw artifacts of both executions: `cases/`, `readback/`, `logs/` (stdout/stderr per process), `databases/` (checkpoint and effects SQLite files), `environment.json`, `MANIFEST.sha256`.

## Reproduce

```
python3.13 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python harness/verify_8834.py --outdir ./artifacts
```

Then compare `artifacts/EVIDENCE_8834_VERIFICATION.json` against the table above.

## Evidence interpretation and reproduction notes

- `value=1` is the intermediate graph state, not an external effect value. For router failures, the external effects table contains zero rows and `external_observed_value` is null. Agreement means absence of a sink effect, not numerical equality between two independently read values.
- Resume occurs inside the same worker process, on the same thread/checkpointer. The fresh process only reads the durable effect and, for SqliteSaver, persisted checkpoint state; recovery by a restarted execution process is not claimed.
- The no-failure controls also call `invoke(None, config)` after successful completion and return without raising.
- The raw historical artifacts and original harness are preserved byte-for-byte, including their original absolute execution paths and metadata wording. This reviewed report clarifies the two-node graph and SQLite-only checkpoint readback.
- The historical harness is not a general-purpose pass/fail test runner: its final verdict does not gate on every subprocess exit code, and its missing-effects-database readback returns zero rows. Before submission, all 12 case records were separately checked for successful execution/readback, existing effect databases, expected control rows, and matching SHA-256 manifests. Do not trust a fresh harness verdict without those checks.
- The original `pip_freeze` arrays are empty. `requirements.txt` is a supplemental distribution snapshot taken from the retained execution environment during submission review; it is not a historical freeze. The original five reported package versions and four source hashes were checked against that environment.
- Use a new output directory when reproducing: the original harness deletes an existing `--outdir`.
