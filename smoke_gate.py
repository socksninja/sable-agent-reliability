#!/usr/bin/env python3
"""Validate provider stability before allowing the full SABLE benchmark."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', required=True)
    ap.add_argument('--expected', type=int, default=10)
    ap.add_argument('--max-model-errors', type=int, default=1)
    args = ap.parse_args()

    rows = [json.loads(line) for line in Path(args.results).read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(rows) != args.expected:
        print(f'SMOKE FAIL: expected {args.expected} rows, got {len(rows)}')
        return 1

    terminations = [r.get('integrity', {}).get('termination') for r in rows]
    model_errors = sum(t == 'model_error' for t in terminations)
    provider_rate_limits = sum(t == 'provider-rate-limit' for t in terminations)
    completed = sum(t == 'final' for t in terminations)
    env_pass = sum(bool(r.get('environment', {}).get('task_success')) for r in rows)

    print(
        f'SMOKE rows={len(rows)} completed={completed} '
        f'model_errors={model_errors} provider_rate_limits={provider_rate_limits} '
        f'task_pass={env_pass}/{args.expected}'
    )

    if provider_rate_limits > 0:
        print('SMOKE FAIL: provider rate limit encountered')
        return 1
    if model_errors > args.max_model_errors:
        print('SMOKE FAIL: provider/model instability above threshold')
        return 1
    if completed != args.expected - model_errors:
        print('SMOKE FAIL: unexpected non-final termination state')
        return 1

    print('SMOKE PASS: provider is stable enough to run the full benchmark')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
