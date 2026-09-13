# SABLE Strategy Alignment v0.1

## Final objective

Build an acquisition-grade, externally validated asset around one problem:

> **Can autonomous AI systems perform real-world actions reliably, and can an independent system prove what actually happened?**

Near-term success is not benchmark size. The next proof target is repeated external runtime use, independently inspectable evidence, and at least one real design-partner or paid workflow.

## Selection principle

A new SABLE case or engineering task should survive all four filters:

1. **Strategic pain** — it represents a failure boundary that real agent/runtime builders already face.
2. **Verifiability** — the failure can be observed from machine-checkable state/evidence rather than agent self-report.
3. **External pull** — a runtime maintainer, platform owner, infra/eval team, or prospective customer could plausibly care enough to reproduce or integrate it.
4. **Commercial leverage** — the work strengthens a reusable asset, verification layer, certification workflow, dataset, or integration surface rather than creating one-off consulting output.

If a proposed task fails two or more filters, stop and return to external validation.

## Current priority order

1. **External runtime execution** — real agents/runtimes running SABLE and producing inspectable receipts.
2. **Failure discovery** — convert externally observed reliability failures into minimal reproducible cases.
3. **Independent verification** — make the evidence replayable and difficult to fake.
4. **Integration surface** — make SABLE easy to adopt by runtimes, eval platforms, and agent infrastructure teams.
5. **Commercial conversion** — design-partner pilots, recurring verification, reliability reports/certification, or acquisition-relevant strategic value.
6. Benchmark expansion only when it is pulled by 1–5.

## Complement-not-compete commercialization

SABLE should primarily be sold or embedded as a **neutral reliability/evidence layer**, not as another agent runtime, model provider, or orchestration framework.

Potential complementary products:

- Agent runtimes / coding agents: use SABLE as an external regression and reliability gate.
- Agent frameworks: use SABLE-normalized traces to compare execution semantics across runtimes.
- Model/API providers: use SABLE to detect provider-boundary failures without claiming the provider itself is the root cause.
- Eval/observability platforms: use SABLE's deterministic environment oracle and terminal-truth cases as a stronger execution-verification substrate.
- Security/governance systems: combine authorization and state-transition evidence with policy controls.

Preferred commercial wedges:

`runtime integration → recurring regression verification → public/private reliability report → certification/evidence API`

The complementary position is important: SABLE gains distribution from systems that already own agents, tools, models, or observability workflows instead of attempting to replace them.

## Anti-drift rules

- No benchmark expansion merely to increase task count.
- No generic agent framework.
- No model-training detour.
- No dashboard-first SaaS build before external execution demand.
- No claiming third-party adoption from fixtures or self-tests.
- No acquisition narrative without external evidence of value.

## Reality scoreboard

The highest-priority signals remain, in order:

`real external execution > third-party reproduction > repeated use > design-partner intent > payment > integration/expansion`

GitHub green, code volume, taxonomy breadth, and internal architectural complexity are supporting evidence only.

## Current gap

SABLE currently has strong evidence-infrastructure direction and multiple external runtime failure signals, but commercial validation still lags the engineering surface. Therefore the next work after the current TTR execution gate should favor **one external runtime integration/reproduction and one concrete design-partner conversation** over another large internal benchmark expansion.
