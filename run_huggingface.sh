#!/usr/bin/env bash
set -euo pipefail
: "${HF_TOKEN:?Set HF_TOKEN in the GitHub Actions repository secret}"
export SABLE_API_KEY="$HF_TOKEN"
export SABLE_BASE_URL="https://router.huggingface.co/v1"
# Official HF function-calling example model; provider is selected automatically.
export SABLE_MODEL="${SABLE_MODEL:-deepseek-ai/DeepSeek-R1-0528}"
python3 real_agent_runner.py \
  --tasks tasks/tasks_v0_4_140.json \
  --out results/huggingface_sable_v0.4.jsonl \
  --thinking disabled \
  "$@"
