# SABLE External Case 003 — AgentOS governed execution

Status: **PROSPECT / NOT BENCHMARK-ADMITTED**

Target: `darrinbaldwindev/AgentOS#75`

## Why this case matters

The public AgentOS control-loop record exposes a reliability boundary around governed execution:

- physical Windows execution remains `NOT_PROVEN`;
- local-wake execution and power-loss durability remain unproven;
- one-owner-action boundaries are explicitly preserved;
- independent PRS assurance is kept separate from stale exact-head evidence;
- the control loop requires exact-marker lineage across A → B → C → watchdog.

This is a useful SABLE target because the claimed control-plane state can be compared against actual execution/evidence state rather than trusting an agent's prose.

## Smallest useful validation

Run one bounded governed action through the independently maintained AgentOS runtime and capture:

1. requested action and authorization boundary;
2. actual execution attempt;
3. authoritative runtime state;
4. durable checkpoint / exact marker;
5. terminal outcome;
6. independent assurance/replay evidence.

The key oracle is:

```text
requested governed action
→ authorized execution boundary
→ actual runtime execution
→ durable authoritative state
→ terminal outcome
→ independently inspectable receipt
```

A prose checkpoint, issue comment, or local-only implementation result is insufficient by itself.

## Admission rule

Do **not** count this case as external adoption, third-party execution, or benchmark evidence until an independently maintained AgentOS runtime produces an inspectable machine-verifiable receipt that closes the full chain.

## Next action

Contact the maintainer on AgentOS #75 with a narrow request for one 10–20 minute validation witness. Do not ask them to run the full SABLE benchmark.
