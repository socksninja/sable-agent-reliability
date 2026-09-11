# SABLE: 10-minute external verification

The fastest path from an unfamiliar agent to real SABLE evidence is now:

```text
existing agent
  ↓
one small adapter around real tool calls
  ↓
artifacts/submission-v09.jsonl
  ↓
SABLE validator
  ↓
artifacts/sable-trace-v05.jsonl + evidence manifest
  ↓
GitHub Actions artifact
```

## 1. Copy the collector

Copy `sable_capture_v09.py` into the agent repository.

Wrap the **real** tool call, not a hand-authored fixture:

```python
from sable_capture_v09 import SableCapture

capture = SableCapture(
    agent_name="my-agent",
    agent_version="1.2.3",
    framework="my-runtime",
    framework_version="4.5.6",
    adapter="my-runtime-sable/0.1",
)

before = snapshot_environment()
result = real_tool(**args)
after = snapshot_environment()
capture.call("my_tool", args, result, before, after)

submission = capture.envelope(
    task_id="my-task-01",
    goal="The original task goal",
    claimed_status="success",
    final_report="What the agent claimed",
    environment=after,
)
```

The key requirement is that `result`, `before`, and `after` come from the real runtime/environment. Do not hand-author execution evidence.

## 2. Write one JSONL submission

```python
from sable_capture_v09 import write_envelope
write_envelope("artifacts/submission-v09.jsonl", submission)
```

## 3. Validate locally

```bash
python sable_capture_v09.py --help
python trace_submit_v09.py \
  --input artifacts/submission-v09.jsonl \
  --output artifacts/sable-trace-v05.jsonl
```

## 4. Use the reusable GitHub workflow

In the agent repository, add a tiny workflow job:

```yaml
jobs:
  sable:
    uses: socksninja/sable-agent-reliability/.github/workflows/external-verification-reusable.yml@main
    with:
      agent_command: python scripts/run_one_sable_task.py
```

Your command must create `artifacts/submission-v09.jsonl`. The reusable workflow validates it and uploads the normalized trace plus a SHA-256 evidence manifest as a GitHub Actions artifact.

## 5. What counts as External Reality

The quickstart demo in `examples/external_agent_10min.py` is only a deterministic smoke test. It is **not** external-agent evidence.

A record becomes external evidence only when an independently maintained agent/runtime produces the trace and the resulting GitHub Actions run/artifact can be inspected.

SABLE should report the funnel honestly:

```text
protocol ready
→ live external execution
→ structurally valid submission
→ evidence reachable
→ manual promotion
```

The goal of this path is to remove integration friction, not to manufacture adoption.
