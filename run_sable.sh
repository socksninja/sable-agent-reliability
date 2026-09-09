#!/usr/bin/env bash
set -euo pipefail
: "${SABLE_API_KEY:?Set SABLE_API_KEY in the environment}"
: "${SABLE_BASE_URL:?Set SABLE_BASE_URL in the environment}"
: "${SABLE_MODEL:?Set SABLE_MODEL in the environment}"
: "${SABLE_TASKS:?Set SABLE_TASKS in the environment}"
: "${SABLE_OUT:?Set SABLE_OUT in the environment}"
python3 real_agent_runner.py \
  --tasks "$SABLE_TASKS" \
  --out "$SABLE_OUT" \
  --thinking disabled
