#!/usr/bin/env bash
set -euo pipefail
: "${GEMINI_API_KEY:?Set GEMINI_API_KEY in the GitHub Actions repository secret}"
export SABLE_API_KEY="$GEMINI_API_KEY"
export SABLE_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai"
export SABLE_MODEL="${SABLE_MODEL:-gemini-3.8-flash}"
python3 real_agent_runner.py --tasks tasks/tasks.json --out results/gemini_sable20_v0.3.jsonl --thinking disabled "$@"
