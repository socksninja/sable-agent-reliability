# OpenClaw False-Success Reproduction v0.1

Target case: `SABLE-FS-0002` / `openclaw/openclaw#141454`.

## Target revision

`0d0e2852b2542c4d128c34d8fc9a1edb2100e1d2`

## Runtime path under test

`src/cron/service/timer-execution.ts` can return `{ status: "ok", summary: text }` after a deferred wake is queued when the wait budget is exhausted.

The same revision's `src/cron/completion-status.ts` maps an `ok` run with no required delivery to `succeeded`.

## Independent harness

1. Clone/check out OpenClaw at the target revision into `./openclaw` under the SABLE repository root.
2. Install/use a TypeScript runner such as `tsx`.
3. Run:

```bash
npx --yes tsx ./experiments/openclaw_false_success_repro_v02.mjs
```

The harness imports the exact OpenClaw source function; it does not copy the completion logic.

Expected observation:

```text
observed_completion_status = "succeeded"
```

The SABLE oracle treats `succeeded` as the observed failure because the test input contains no observed agent completion fact. This is a source-path reproduction of the completion-mapping boundary, not yet a full black-box scheduler/runtime reproduction.

## Evidence status

Current case remains `E1 / unverified` in `records/false_success_corpus_v01.jsonl` until the exact harness is executed in an inspectable external environment and the output is captured as evidence.
