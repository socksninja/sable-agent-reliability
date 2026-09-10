# SABLE External Submission Quickstart

SABLE accepts third-party agent/runtime evidence through the public `sable.submission.v0.9` protocol.

## 1. Produce a real runtime trace

Run the agent against a SABLE task and capture the execution envelope from the runtime. Do not hand-author execution evidence.

The envelope must contain:

- runtime/framework identity
- task goal and task id
- every tool call with arguments and observed result
- `before_state_hash` and `after_state_hash` for each step
- claimed final status
- environment outcome
- capture timestamp and collector identity
- canonical SHA-256 integrity hash

See:

- `docs/TRACE_SUBMISSION_PROTOCOL_V0.9.md`
- `schemas/submission_v09.schema.json`

## 2. Validate locally

```bash
python3 trace_submit_v09.py \
  --input submission.jsonl \
  --output sable_traces_v05.jsonl
```

Then run deterministic evaluation and replay:

```bash
python3 sable_v05.py \
  --tasks tasks/tasks.json \
  --results sable_traces_v05.jsonl \
  --report sable_report.json \
  --replay
```

A trustworthy trace should reproduce the captured state hashes under replay.

## 3. Publish the evidence

The strongest submission is a GitHub Actions run in a public repository that:

1. runs the agent for real;
2. writes the v0.9 submission;
3. validates it with SABLE;
4. runs deterministic evaluation/replay;
5. uploads the raw runtime trace and normalized evidence as an artifact.

Keep the run URL, job id, artifact id, commit SHA, and artifact digest.

## 4. Submit to SABLE

Create a file under `submissions/` using:

```text
submissions/<stable-record-id>.json
```

The file must conform to:

```text
schemas/reliability_record_submission_v01.schema.json
```

Open a pull request containing only the submission and its required metadata.

SABLE CI performs structural validation and evidence reachability checks. Maintainers then inspect the cited run, job, artifact, and task-level observations before promotion to `records/`.

## Evidence states

`STRUCTURALLY_VALID` means the submitted record is internally consistent.

`EVIDENCE_REACHABLE` means the cited GitHub execution evidence exists and matches the submitted provenance and digest fields.

`PROMOTED` means a maintainer completed the evidence review and accepted the record into the public corpus.

Promotion is intentionally manual. A green CI run is not equivalent to a production-safety claim.

## Reference

A deterministic protocol fixture is available at:

```text
examples/submissions/third_party_reference_v09.jsonl
```

That fixture demonstrates protocol shape only; it is not real third-party evidence.
