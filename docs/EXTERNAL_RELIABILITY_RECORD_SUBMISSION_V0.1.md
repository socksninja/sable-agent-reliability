# SABLE External Reliability Record Submission v0.1

SABLE accepts third-party model/runtime evaluations through a machine-validated Reliability Record. The purpose is to make additional observations comparable and auditable, not to turn one benchmark result into a general reliability claim.

## What a submission must contain

A submission is one JSON object conforming to `schemas/reliability_record_submission_v01.schema.json`.

Required evidence fields are:

- `schema_version = sable.reliability_record.v0.1`
- model and runtime identity
- benchmark name and corpus size `n`
- native tool-call rate
- task success rate and task successes
- model errors and observed environment mutations
- GitHub Actions provenance: run ID, job ID, repository, commit
- artifact name, artifact ID, and SHA-256 digest
- `task_results[]` with observed task outcomes

The authoritative semantics are defined in `docs/RELIABILITY_RECORD_V0.1.md`: task success is determined from observed sandbox state, not from the agent's textual claim.

## Submission path

1. Run the SABLE corpus or an explicitly versioned SABLE-compatible evaluation in GitHub Actions.
2. Preserve the raw task-level evidence as a workflow artifact.
3. Create a JSON Reliability Record using the exact run/job/commit/artifact provenance from that execution.
4. Add the JSON under `submissions/` in a pull request.
5. SABLE CI validates the record structure, arithmetic consistency, provenance shape, artifact digest format, and task-level consistency.
6. The evidence-admission gate resolves the cited GitHub Actions run, job, and artifact through GitHub's API and checks that repository, commit, run, job, artifact name, artifact ID, and artifact SHA-256 all agree.
7. Maintainers may promote accepted submissions into `records/` after evidence review.

A submission PR is **not** itself proof that the underlying evaluation is valid. The run, job, artifact, and task-level evidence must remain inspectable.

## Evidence admission states

- `STRUCTURALLY_VALID`: the submitted record passes local SABLE consistency checks.
- `EVIDENCE_REACHABLE`: the cited GitHub run/job/artifact exist, are internally linked, the cited job succeeded, the run commit matches the submitted commit, and the artifact digest matches GitHub.
- `PROMOTED`: a maintainer has reviewed the underlying task-level artifact and copied the record into the public `records/` dataset.

`EVIDENCE_REACHABLE` is stronger than a syntactically valid record but still does not mean the task-level evidence has been independently reviewed.

## Minimum task-level integrity

For every task result, submit enough information to reconstruct the observed outcome, including task ID, expected state, observed state (or a deterministic equivalent), whether tool execution occurred, whether the native transport carried the tool call, and the task-check result.

Do not replace missing observations with model-generated claims. Unknown or unverifiable observations must remain unknown and cannot be silently converted to success.

## What counts as acceptable provenance

`provenance.source` must be `GitHub Actions`, and `run_id`, `job_id`, and the 40-character commit SHA must refer to the execution that produced the submitted artifact. The artifact SHA-256 must be the digest of the uploaded evidence bundle.

The admission gate independently checks:

- the workflow run exists in the cited repository;
- the run's `head_sha` equals `provenance.commit`;
- the run belongs to `provenance.repository`;
- the cited job exists, belongs to the cited run, and concluded `success`;
- the cited artifact exists, has the submitted name/ID, belongs to the cited run, and has the submitted digest;
- the artifact is not expired.

## Promotion policy

A validated submission may be promoted to the public `records/` dataset only when maintainers can verify that:

- the cited GitHub Actions execution exists;
- the cited job completed successfully;
- the artifact exists and its digest matches the submitted value;
- the record arithmetic is internally consistent;
- task outcomes are derived from observed execution evidence;
- no model-generated claim is used as a substitute for sandbox observation.

Promotion does not imply production safety, universal reliability, or superiority across models. It means the observation is admissible as a versioned SABLE benchmark result.
