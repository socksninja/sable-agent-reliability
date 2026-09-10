# SABLE × LangGraph v0.9

This integration runs a real LangGraph `StateGraph` execution and captures the resulting tool-use trace into the SABLE v0.9 submission protocol.

## Evidence class

`third_party_framework_runtime`

LangGraph is the third-party runtime. The reference agent policy is deterministic and local, so this integration **does not claim independent third-party agent provenance**. It proves that a real external agent framework can execute a state-changing task and emit a verifiable SABLE submission without a model-provider dependency.

## Run

```bash
pip install -r requirements.txt
python3 integrations/langgraph/run_real_trace_v09.py
python3 trace_submit_v09.py \
  --input results/third_party_langgraph_submission_v09.jsonl \
  --output results/third_party_langgraph_sable_v05.jsonl
python3 sable_v05.py \
  --tasks integrations/langgraph/task.json \
  --results results/third_party_langgraph_sable_v05.jsonl \
  --report results/third_party_langgraph_report.json \
  --replay
```

The generated files include the raw runtime capture and the v0.9 submission envelope, including a SHA-256 source trace hash and runtime provenance.
