# SABLE Public Verifier v2.8

## Protocol

`POST /v1/verify` accepts either:

- `sable.submission.v0.9`: returns `STRUCTURALLY_VALID` when the submission is internally consistent. This is **not** cryptographic proof of execution.
- `sable.verification_receipt.v2.6`: returns `CRYPTOGRAPHICALLY_VERIFIED` only when the self-contained Ed25519-signed receipt verifies and its embedded evidence is marked successful and replay-clean.

`GET /v1/health` returns the service status.

## Trust boundary

A submitter can truthfully recompute a hash over altered data, so a hash on an untrusted submission is only an integrity/self-consistency check. SABLE therefore does not label a raw v0.9 submission as cryptographic execution proof.

A signed receipt is stronger: the verifier checks the receipt hash and Ed25519 signature using the public key carried by the receipt, plus the permission/evidence invariants required by the receipt protocol.

## Response levels

`STRUCTURALLY_VALID` → protocol accepted, execution proof absent.

`CRYPTOGRAPHICALLY_VERIFIED` → signed receipt independently verifies.

`REJECTED` → malformed, unsupported, tampered, or invariant-violating input.
