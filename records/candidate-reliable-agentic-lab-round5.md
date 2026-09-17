# Candidate External Execution Record — reliable-agentic-lab Round 5

Status: `CANDIDATE / NOT_YET_VERIFIED`

## Execution identity

- Runtime: Agent SDK / Claude Code
- Repository: `RichardHightower/reliable-agentic-lab`
- Session ID: `49cfa77c-11fc-4df7-91e3-b32d344168ea`
- Source revision: `d5dd9c810de88f90babe4a0811b4ed2e24ffd815`
- Public workflow validation run: `34301543346`
- Public live-run status record: `docs/status/2026-09-08-sol2-t001-live-sdk-round5.md`

## Observed execution

The public Round-5 trace shows the agent's test-implementer wrote:

`tests/test_t001_due_dates.py`

inside the linked worktree, and the write reached the real red gate. The same status record reports four live model queries with real spend and a total spend of `$2.0880` under a `$3.96` cap.

## Current evidence boundary

This is **not** yet a SABLE `VERIFIED` record.

The execution identity is now public, but the observed mutation was only a local linked-worktree write. A third party cannot independently reread that resulting state from the public repository after the run.

## Required final link

The next live run should perform one harmless externally rereadable mutation and publish:

`session_id -> declared external effect -> fresh independent readback -> SHA-256(state)`

The readback must occur from a fresh process or independent observer, not from the agent's in-memory result.

No SABLE protocol/schema change is required to close this candidate.
