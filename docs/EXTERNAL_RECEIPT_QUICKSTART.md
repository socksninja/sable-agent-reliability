# External Receipt Quickstart

SABLE accepts real agent/runtime execution receipts for independent verification.

## Submit in one comment

Open Issue #20 and post:

```text
receipt_url: <public raw JSON URL>
runtime: <runtime/framework>
model: <model identifier>
execution_context: <one-line description>
```

The receipt must be produced by a real execution outside the SABLE producer workflow. Do not submit fixtures or self-generated examples.

## Minimum receipt fields

`RNCP-EXECUTION-RECEIPT-v1` receipts should contain:

- `protocol`
- `commitment`
- `providers`
- provider `protocol_version`, `commitment_id`, `commitment_hash`
- provider `execution_id`, `executor_id`, `executor_revision`
- provider `observed.status`
- provider `receipt_hash`
- top-level `content_address`

## Independent verification

SABLE fetches the URL itself and recomputes the hashes. A passing result means the public receipt is internally consistent and reproducible. It does not mean the agent is generally reliable, safe, or production-ready.

Local verifier:

```bash
python3 scripts/verify_public_receipt.py --url '<public raw JSON URL>'
```

Never include API keys, credentials, private URLs, or private execution data.
