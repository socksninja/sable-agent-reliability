# Extended Abstract Draft — Agent Evaluation Science Fall 2026

## Working title

**From Agent Claims to Verifiable Execution Evidence: Cross-Runtime Reliability Failures and Independent Reconstruction**

## Author

Tang Yuanlong / socksninja

Independent AI Builder — Agent Reliability / Agent Systems

## Abstract

AI agents are increasingly evaluated by task success, benchmark scores, and model-level judgments. In deployed systems, however, many consequential failures occur at the boundary between an agent's claimed outcome and the external state that actually changed. Retries can duplicate side effects; traces can be incomplete or eventually consistent; an agent can report success while the environment remains in a different state; and runtime-specific evidence can be difficult for an independent observer to reconstruct.

This work presents a practical evidence layer for evaluating agent execution across runtimes rather than evaluating only model outputs. The approach combines (1) runtime traces, (2) explicit execution/environment observations, (3) provenance and content hashes, and (4) an admission and verification path that allows evidence to be checked outside the originating runtime. The goal is not to introduce another benchmark score, but to make reliability findings independently inspectable and reproducible.

Early experiments expose concrete failure modes. A deterministic CrewAI retry experiment observed exactly-once external effects in clean and pre-effect crash conditions, while post-effect retry conditions produced duplicated effects in all 30/30 trials. Separately, a LangSmith eventual-consistency/readback experiment showed that an execution record can be temporarily unavailable or incomplete at readback time even when the underlying execution has occurred. These experiments motivate a distinction between agent outcome claims, runtime traces, external state, and independently reachable evidence.

The resulting protocol records the execution context, task outcome, evidence locations, provenance identifiers, and verification status. A third-party submission can therefore be accepted only when its source execution, workflow/job/artifact lineage, and evidence digest remain independently reachable. The intended research question is whether agent reliability evaluation should treat independent reconstruction of execution as a first-class property alongside task success.

## Contributions

1. A provider- and runtime-agnostic evidence model for real agent execution.
2. Reproducible failure experiments targeting retries, external side effects, false success, state drift, and readback gaps.
3. An admission protocol separating structural validity from independently reachable execution evidence.
4. A research framing for evaluating reliability through externally reconstructable evidence rather than self-reported success alone.

## Evidence and limitations

The current evidence is early-stage and deliberately narrow. The CrewAI retry experiment used a deterministic local model rather than a live LLM/provider, did not include fresh-process crash recovery, checkpointing, or host power-loss durability, and did not implement an idempotency guard. The evidence therefore demonstrates a reproducible runtime failure mode, not a universal production probability. Additional independent runtime submissions are required before making cross-runtime prevalence claims.

## Relation to evaluation science

The work targets the operational gap between benchmark results and deployed-agent evidence. It is relevant to diagnosis (failure analysis and reliability gaps), measurement (validity and reproducibility of execution evidence), operationalization (traces, repeated runs, provenance, and verification), and application (real-world agent workflows).

## Public evidence

- SABLE repository: https://github.com/socksninja/sable-agent-reliability
- External experiment adapter: `docs/EXTERNAL_EXPERIMENT_ADAPTER_CRASHPOINT_V01.md`
- External verification starter: `examples/external-submission-starter/`
- Paid reliability audit pilot: issue #75 in the SABLE repository

## Target submission

Agent Evaluation Science Fall 2026, extended abstract track (2 pages, presentation-only). Submission system: OpenReview.

Current deadlines from the event page:
- Abstract registration: October 20, 2026
- Full submission: October 25, 2026
- Symposium: November 20, 2026, New York City

This draft is a submission candidate, not evidence of acceptance or institutional endorsement.
