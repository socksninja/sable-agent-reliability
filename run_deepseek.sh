#!/usr/bin/env bash
set -euo pipefail
: "${DEEPSEEK_API_KEY:?Set DEEPSEEK_API_KEY in the Codespaces secret/environment; never commit it}"
export SABLE_API_KEY="$DEEPSEEK_API_KEY"
export SABLE_BASE_URL="https://api.deepseek.com"
export SABLE_MODEL="${SABLE_MODEL:-deepseek-v4-flash}"
python3 real_agent_runner.py \
  --tasks tasks/tasks.json \
  --out results/deepseek_sable20_v0.3.jsonl \
  --thinking disabled \
  "$@"
