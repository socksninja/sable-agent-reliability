# SABLE v0.7 — Comparable Agent Reliability Leaderboard

SABLE v0.7 adds a comparison layer over the v0.5 Reliability Score and v0.6 Evidence Pack.

## Eligibility

A result may enter the same leaderboard only when the benchmark identity is held constant: task count, task definitions, tool definitions, verifier rules, and run conditions. Provider or model outages are reported as infrastructure failures and are never converted into agent successes.

## Ranking

Entries are sorted descending by:

1. `reliability_score`
2. `operational_score_excluding_provider_failures`
3. `pass_rate`

The leaderboard is a comparison convention for SABLE, not an industry-wide standard.

## Real results vs self-tests

Synthetic fixtures exist only to test the leaderboard implementation. They must never be presented as model benchmark results. Real model entries should carry the actual model/provider labels and an independently generated SABLE report.

## Reproducibility

Use the same benchmark ID and task count for every comparison. Keep the underlying JSON reports and Evidence Packs so a ranking can be audited back to the task-level evidence.
