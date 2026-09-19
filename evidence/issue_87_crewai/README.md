# Evidence: CrewAI Issue #7449 — Duplicate-Effect Retry Boundary

**Bounty Issue:** socksninja/sable-agent-reliability#87  
**Upstream Bug:** crewAIInc/crewAI#7449  
**Verdict:** ✅ VERIFIED  
**SHA-256:** `03b78e738c7b28607dd177df103b64cb7d911b7ab7e575d56bcdcafd32fe7d33`

## Summary

With `crewai==1.15.21`, `ToolUsage._use()` contains an inner `try/except` around `tool.invoke()` that catches **any** exception, not just schema/parsing errors. This causes a tool that always fails to be invoked **twice per outer retry loop iteration** — producing 6 actual invocations instead of the expected 3 when `_max_parsing_attempts=3`.

## Results

| Case | `_max_parsing_attempts` | Actual Invocations | Pass? |
|------|------------------------|--------------------|-------|
| Control (tool succeeds) | 3 | 1 | ✅ |
| Bug (tool always raises) | 3 | **6** | ❌ Bug confirmed |

- **Multiplication factor:** 2.0×
- **External effect log (subprocess-read):** 6 entries
- **Runtime:** Python 3.13.7, crewai==1.15.21, linux

## Root Cause

`ToolUsage._use()` wraps `tool.invoke()` in a broad `try/except Exception`:
- On failure, it catches the error and re-raises (or wraps it)
- The outer loop in `ToolUsage.use()` then catches it and increments the attempt counter
- But **`_use` itself internally retried once before propagating**, doubling actual calls

This means every logical "attempt" produces 2 real tool executions — any real-world side effect (API calls, file writes, DB mutations) is duplicated.

## Files

- [`reproduce_crewai_7449.py`](reproduce_crewai_7449.py) — self-contained reproducer
- [`EVIDENCE_CREWAI_7449_VERIFICATION.json`](EVIDENCE_CREWAI_7449_VERIFICATION.json) — machine-readable evidence
