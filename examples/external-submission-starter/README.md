# SABLE External Submission Starter

The fastest self-serve path to produce one independently verifiable SABLE execution is to copy the two files in this directory into your own agent repository.

## 1. Copy

Copy:

- `run_one_sable_task.py`
- `.github/workflows/sable-external.yml`

## 2. Replace one function

Edit `run_one_sable_task.py` so `run_real_agent_task()` calls your real agent and wraps real tool calls with `SableCapture`.

Do not hand-author execution evidence. `result`, `before`, and `after` must come from your actual runtime/environment.

## 3. Push

GitHub Actions runs the task, validates `sable.submission.v0.9`, normalizes it to the SABLE v0.5 trace, and uploads a SHA-256 evidence manifest.

The resulting artifact is the thing SABLE can inspect as external execution evidence.

## 4. Report the run

Open a SABLE submission PR only after the run exists. Keep the run URL, job ID, artifact ID, commit SHA, and artifact digest.

Docs: https://github.com/socksninja/sable-agent-reliability/blob/main/docs/EXTERNAL_SUBMISSION_QUICKSTART.md
