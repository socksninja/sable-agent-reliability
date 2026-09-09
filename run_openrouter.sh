#!/usr/bin/env bash
set -euo pipefail
: "${OPENROUTER_API_KEY:?Set OPENROUTER_API_KEY in the GitHub Actions repository secret}"
export SABLE_API_KEY="$OPENROUTER_API_KEY"
export SABLE_BASE_URL="https://openrouter.ai/api/v1"
export SABLE_MODEL="${SABLE_MODEL:-openrouter/free}"
python3 real_agent_runner.py \
  --tasks tasks/tasks_v0_4_140.json \
  --out results/openrouter_sable_v0.4.jsonl \
  --thinking disabled \
  "$@"
