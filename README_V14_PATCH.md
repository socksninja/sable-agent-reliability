# SABLE v1.4

SABLE v1.4 upgrades the external-model evidence loop from a one-task repeated run into a five-family multi-task campaign and adds a failure-taxonomy layer.

## What changed

- **Failure Taxonomy v1.4** normalizes observed failure labels into stable root causes and fault domains.
- The taxonomy accepts both single JSON objects and JSONL evidence/permission files, with strict per-file record-count pairing.
- **Multi-task campaign** runs file, records, inventory, schedule, and transaction tasks on every repetition.
- Each repetition produces independent raw traces, v0.9 submissions, normalized traces, evaluations, evidence, and permission records.
- A campaign is considered rate-estimating only after **10+ observations** (five tasks × two or more repetitions).
- Replay integrity is mandatory for the workflow gate.

## Reality boundary

The workflow requires the `SABLE_API_KEY` GitHub Actions secret. This commit adds the machinery and integrity gates; it does not claim a real external-model campaign has passed until a workflow run actually executes with a configured provider/model and produces verified artifacts.
