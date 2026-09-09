#!/usr/bin/env bash
set -euo pipefail
: "${HF_TOKEN:?Set HF_TOKEN in the GitHub Actions repository secret}"
export SABLE_API_KEY="$HF_TOKEN"
export SABLE_BASE_URL="https://router.huggingface.co/v1"
export SABLE_MODEL="${SABLE_MODEL:-openai/gpt-oss-20b:cheapest}"
python3 real_agent_runner.py \
  --tasks tasks/tasks_v0_4_140.json \
  --out results/huggingface_sable_v0.4.jsonl \
  --thinking disabled \
  "$@"
